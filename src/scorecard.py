"""Points-based scorecard: bins, Weight of Evidence, logistic regression, then points.

Weight of Evidence (WoE) replaces a value with how risky its bin is:
ln(share of non-defaulters in the bin / share of defaulters in the bin), so a positive
WoE means safer than average. Information Value (IV) sums this up into one number for
how well a feature separates defaulters.

WoE uses the target, so bins and feature selection are redone inside every training
fold. Fitting them on all dev rows first would leak the answers into the scores.
Dev rows only: the holdout stays unseen.

Gender, age and family columns are not candidates, as in the baseline. Step 8 tests them.

Run from the project root:  python -m src.scorecard
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

from src.baseline import EXTERNAL, FEATURE_SETS, calibration_table, cross_validate, ks_statistic, table
from src.features import OUT, RAW

REPORT = Path("reports/scorecard_results.md")
MODELS = Path("models")
SEED = 42
FOLDS = 5

MAX_BINS = 5
MIN_BIN_SHARE = 0.05  # each numeric bin holds at least this share of rows, so its risk is reliable
MIN_MISSING_SHARE = 0.005  # a smaller missing group gets a neutral WoE of 0
MIN_CATEGORY_SHARE = 0.01  # smaller categories are pooled together
SMOOTHING = 0.5  # stops a bin with no defaulters giving an infinite WoE

MIN_IV = 0.02  # below this a feature is too weak to earn a line on the scorecard
MAX_CORRELATION = 0.7
MAX_FEATURES = 15

# A score of BASE_SCORE means 50 non-defaulters for each defaulter. Every 50 points doubles the odds.
BASE_SCORE = 700
BASE_ODDS = 50
POINTS_TO_DOUBLE = 50
FACTOR = POINTS_TO_DOUBLE / np.log(2)
OFFSET = BASE_SCORE - FACTOR * np.log(BASE_ODDS)
SCORE_BAND = 50

POOLED = "Rare or new"
SENSITIVE = ["AGE_YEARS", "EMPLOYED_TO_AGE", "IS_PENSIONER_OR_UNEMPLOYED"]
REDUNDANT = ["EXT_SOURCE_MEAN"]  # an average of three scores that are already candidates
EXTRA_NUMERIC = ["AMT_CREDIT", "OWN_CAR_AGE", "DAYS_ID_PUBLISH", "DAYS_LAST_PHONE_CHANGE",
                 "REGION_RATING_CLIENT_W_CITY"]
CATEGORICAL = ["NAME_CONTRACT_TYPE", "NAME_EDUCATION_TYPE", "NAME_INCOME_TYPE", "OCCUPATION_TYPE",
               "ORGANIZATION_TYPE"]


def candidate_columns():
    """The features built in step 2, minus sensitive ones, plus a few application columns."""
    columns = pq.read_schema(OUT).names
    raw = pd.read_csv(RAW / "application_train.csv", nrows=0).columns
    built = [c for c in columns if c not in raw and c != "split" and c not in SENSITIVE + REDUNDANT]
    return built + EXTERNAL + EXTRA_NUMERIC, CATEGORICAL


def woe_values(groups, y, n_groups):
    """WoE and row counts for integer group labels 0 to n_groups - 1."""
    rows = np.bincount(groups, minlength=n_groups)
    bads = np.bincount(groups, weights=y, minlength=n_groups)
    goods = rows - bads
    share_good = (goods + SMOOTHING) / (goods.sum() + SMOOTHING * n_groups)
    share_bad = (bads + SMOOTHING) / (bads.sum() + SMOOTHING * n_groups)
    woe = np.log(share_good / share_bad)
    iv = float(((share_good - share_bad) * woe).sum())
    return woe, iv, rows, bads


def numeric_groups(x, cuts):
    """Bin number for each value. Missing values get the last group."""
    groups = np.searchsorted(cuts, x, side="left")
    groups[np.isnan(x)] = len(cuts) + 1
    return groups


def merge_to_monotonic(x, y, cuts):
    """Remove cuts until risk moves one way, so points never zigzag along a feature."""
    cuts = list(cuts)
    while len(cuts) > 1:
        groups = np.searchsorted(cuts, x, side="left")
        steps = np.diff(woe_values(groups, y, len(cuts) + 1)[0])
        direction = -np.sign(np.corrcoef(groups, y)[0, 1])
        wrong = np.flatnonzero(steps * direction < 0)
        if not wrong.size:
            break
        cuts.pop(wrong[np.argmin(np.abs(steps[wrong]))])
    return cuts


def fit_numeric(x, y):
    """Let a small decision tree pick cut points, and give missing its own bin."""
    known = ~np.isnan(x)
    cuts = []
    min_rows = int(MIN_BIN_SHARE * len(x))
    if known.sum() >= 2 * min_rows:
        tree = DecisionTreeClassifier(max_leaf_nodes=MAX_BINS, min_samples_leaf=min_rows, random_state=SEED)
        tree.fit(x[known].reshape(-1, 1), y[known])
        cuts = sorted(tree.tree_.threshold[tree.tree_.feature >= 0].tolist())
        cuts = merge_to_monotonic(x[known], y[known], cuts)
    groups = numeric_groups(x, cuts)
    woe, iv, rows, bads = woe_values(groups, y, len(cuts) + 2)
    if rows[-1] < MIN_MISSING_SHARE * len(x):
        woe[-1] = 0.0
    return {"kind": "numeric", "cuts": cuts, "woe": woe.tolist(), "iv": iv,
            "rows": rows.tolist(), "bads": bads.tolist()}


def fit_categorical(x, y):
    """One bin per common category. Rare and unseen ones share a bin, with neutral WoE if very few."""
    x = pd.Series(x).fillna("Missing")
    shares = x.value_counts(normalize=True)
    common = shares[shares >= MIN_CATEGORY_SHARE].index.tolist()
    labels = common + [POOLED]
    groups = x.map({label: i for i, label in enumerate(common)}).fillna(len(common)).astype(int).to_numpy()
    woe, iv, rows, bads = woe_values(groups, y, len(labels))
    if rows[-1] < MIN_MISSING_SHARE * len(x):
        woe[-1] = 0.0
    return {"kind": "categorical", "labels": labels, "woe": woe.tolist(), "iv": iv,
            "rows": rows.tolist(), "bads": bads.tolist()}


def apply_bins(x, bins):
    """Replace raw values with their bin's WoE."""
    woe = np.array(bins["woe"])
    if bins["kind"] == "numeric":
        return woe[numeric_groups(x, bins["cuts"])]
    lookup = dict(zip(bins["labels"], woe))
    return pd.Series(x).fillna("Missing").map(lookup).fillna(lookup[POOLED]).to_numpy(dtype="float64")


def fit_all_bins(X, y, numeric, categorical):
    bins = {col: fit_numeric(X[col].to_numpy(dtype="float64"), y) for col in numeric}
    bins.update({col: fit_categorical(X[col].to_numpy(dtype="object"), y) for col in categorical})
    return bins


def encode(X, bins, features):
    if not features:
        return np.empty((len(X), 0))
    return np.column_stack([apply_bins(X[col].to_numpy(dtype="object" if bins[col]["kind"] == "categorical"
                                                       else "float64"), bins[col]) for col in features])


def select_features(X, bins, candidates):
    """Strongest first, skipping weak features and those repeating one already chosen."""
    ranked = sorted((c for c in candidates if bins[c]["iv"] >= MIN_IV), key=lambda c: -bins[c]["iv"])
    if not ranked:
        return []
    woe = encode(X, bins, ranked)
    usable = woe.std(axis=0) > 0
    ranked = [c for c, ok in zip(ranked, usable) if ok]
    woe = woe[:, usable]
    corr = np.abs(np.corrcoef(woe, rowvar=False)).reshape(len(ranked), len(ranked))
    kept = []
    for i in range(len(ranked)):
        if len(kept) < MAX_FEATURES and all(corr[i, k] <= MAX_CORRELATION for k in kept):
            kept.append(i)
    return [ranked[i] for i in kept]


def fit_logistic(X, y, bins, features):
    """Higher WoE means safer, so a coefficient must be negative. Drop any that flips and refit."""
    features = list(features)
    while features:
        model = LogisticRegression(max_iter=1000).fit(encode(X, bins, features), y)
        worst = int(np.argmax(model.coef_[0]))
        if model.coef_[0][worst] <= 0:
            return model, features
        features.pop(worst)
    return None, []


def predict(model, X, bins, features):
    if model is None:
        return np.full(len(X), 0.08)
    return model.predict_proba(encode(X, bins, features))[:, 1]


def to_score(probability):
    return OFFSET + FACTOR * np.log((1 - probability) / probability)


def cross_validate_scorecards(X, y, numeric, categorical, variants):
    """Refit bins and selection in each fold, so every score comes from unseen applicants."""
    scores = {name: [] for name in variants}
    chosen = {name: Counter() for name in variants}
    predictions = {name: np.zeros(len(y)) for name in variants}
    for train, test in StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(X, y):
        X_train, y_train, X_test, y_test = X.iloc[train], y[train], X.iloc[test], y[test]
        bins = fit_all_bins(X_train, y_train, numeric, categorical)
        for name, candidates in variants.items():
            features = select_features(X_train, bins, candidates)
            model, features = fit_logistic(X_train, y_train, bins, features)
            predicted = predict(model, X_test, bins, features)
            predictions[name][test] = predicted
            chosen[name].update(features)
            auc = roc_auc_score(y_test, predicted)
            scores[name].append({"auc": auc, "gini": 2 * auc - 1, "ks": ks_statistic(y_test, predicted),
                                 "brier": brier_score_loss(y_test, predicted)})
    return {name: pd.DataFrame(rows) for name, rows in scores.items()}, predictions, chosen


def bin_labels(bins):
    if bins["kind"] == "categorical":
        return bins["labels"]
    cuts = bins["cuts"]
    edges = [f"{c:.4g}" for c in cuts]
    labels = [f"up to {edges[0]}"] if cuts else ["all known values"]
    labels += [f"{low} to {high}" for low, high in zip(edges, edges[1:])]
    labels += [f"above {edges[-1]}"] if cuts else []
    return labels + ["Missing"]


def points_table(model, bins, features):
    """Points for each bin. Adding the base points and one bin per feature gives the score."""
    rows = []
    for col, coef in zip(features, model.coef_[0]):
        b = bins[col]
        points = np.round(-FACTOR * coef * np.array(b["woe"])).astype(int)
        for label, value, woe, count, bad in zip(bin_labels(b), points, b["woe"], b["rows"], b["bads"]):
            rows.append({"feature": col, "bin": label, "points": int(value), "woe": round(woe, 3), "rows": int(count),
                         "default_rate": round(bad / count, 4) if count else None})
    return pd.DataFrame(rows)


def is_monotonic(bins):
    """Does risk move in one direction across the numeric bins, ignoring the missing bin?"""
    if bins["kind"] != "numeric" or len(bins["cuts"]) < 2:
        return True
    steps = np.diff(bins["woe"][:-1])
    return bool((steps >= 0).all() or (steps <= 0).all())


def score_from_points(table_, X, bins, features, base):
    """Add up the rounded points, to prove the printed scorecard matches the model."""
    total = np.full(len(X), float(base))
    for col in features:
        points = table_.loc[table_["feature"] == col, "points"].to_numpy(dtype="float64")
        adjusted = {**bins[col], "woe": points.tolist()}
        values = X[col].to_numpy(dtype="object" if bins[col]["kind"] == "categorical" else "float64")
        total += apply_bins(values, adjusted)
    return total


def score_band_table(y, probability):
    """Default rate by score band, using predictions from unseen folds."""
    band = (to_score(probability) // SCORE_BAND * SCORE_BAND).astype(int)
    grouped = pd.DataFrame({"band": band, "y": y}).groupby("band")["y"].agg(applicants="size", default_rate="mean")
    grouped["default_rate"] = grouped["default_rate"].round(4)
    return grouped.reset_index().rename(columns={"band": "score_from"})


def summarise(name, count, scores):
    return {"model": name, "features": count, "auc": f"{scores['auc'].mean():.4f} ± {scores['auc'].std():.4f}",
            "gini": f"{scores['gini'].mean():.4f}", "ks": f"{scores['ks'].mean():.4f}",
            "brier": f"{scores['brier'].mean():.4f}"}


def main():
    numeric, categorical = candidate_columns()
    candidates = numeric + categorical
    columns = sorted(set(candidates + FEATURE_SETS["With EXT_SOURCE"]))
    dev = pd.read_parquet(OUT, columns=["SK_ID_CURR", "TARGET", "split", *columns], filters=[("split", "==", "dev")])
    assert (dev["split"] == "dev").all()
    y = dev["TARGET"].to_numpy()
    X = dev[candidates]
    variants = {"Without EXT_SOURCE": [c for c in candidates if not c.startswith("EXT_SOURCE")],
                "With EXT_SOURCE": candidates}

    print("cross-validating...")
    scores, predictions, chosen = cross_validate_scorecards(X, y, numeric, categorical, variants)

    print("shuffled labels check...")
    shuffled = np.random.default_rng(SEED).permutation(y)
    shuffled_scores, _, _ = cross_validate_scorecards(X, shuffled, numeric, categorical,
                                                      {"With EXT_SOURCE": variants["With EXT_SOURCE"]})
    shuffled_auc = shuffled_scores["With EXT_SOURCE"]["auc"].mean()
    print(f"shuffled labels AUC: {shuffled_auc:.4f}")

    print("final fit on all dev rows...")
    bins = fit_all_bins(X, y, numeric, categorical)
    summary, sections = [], []
    MODELS.mkdir(exist_ok=True)
    for name, baseline_features in FEATURE_SETS.items():
        baseline_scores, _ = cross_validate(dev[baseline_features].to_numpy(dtype="float64"), y)
        summary.append(summarise(f"Baseline, {name}", len(baseline_features), baseline_scores))

        features = select_features(X, bins, variants[name])
        model, features = fit_logistic(X, y, bins, features)
        summary.append(summarise(f"Scorecard, {name}", len(features), scores[name]))
        print(summary[-2], summary[-1], sep="\n")

        points = points_table(model, bins, features)
        base = int(round(OFFSET - FACTOR * model.intercept_[0]))
        total = score_from_points(points, X, bins, features, base)
        exact = to_score(predict(model, X, bins, features))
        gap = float(np.abs(total - exact).max())
        assert gap <= 0.5 * (len(features) + 1) + 1e-9, f"points drifted {gap:.2f} from the model"

        shapes = pd.DataFrame([{"feature": c, "iv": round(bins[c]["iv"], 4), "monotonic": is_monotonic(bins[c]),
                                "folds_chosen": f"{chosen[name][c]} of {FOLDS}"} for c in features])
        slug = name.lower().replace(" ", "_")
        (MODELS / f"scorecard_{slug}.json").write_text(json.dumps({
            "base_points": base, "features": features, "bins": {c: bins[c] for c in features},
            "points": points.to_dict("records")}, indent=2))
        other = sorted(set(chosen[name]) - set(features))
        sections += [
            f"## Scorecard, {name}", "",
            f"Base points: {base}. Add one row per feature to get the score. "
            f"The rounded points stay within {gap:.1f} points of the exact model score. "
            f"Scores on dev rows run from {total.min():.0f} to {total.max():.0f}.", "",
            table(shapes), "",
            f"Chosen in some folds but not in the final fit: {other or 'none'}.", "",
            "Default rate by score band, on predictions from unseen folds:", "",
            table(score_band_table(y, predictions[name])), "",
            "Calibration on predictions from unseen folds:", "",
            table(calibration_table(y, predictions[name])), "",
            "Points:", "",
            table(points), ""]

    lines = [
        "# Scorecard results", "",
        f"{len(dev):,} dev rows, stratified {FOLDS}-fold cross-validation. Bins, feature selection and the "
        "model are refitted inside each fold. Written by `python -m src.scorecard`. The holdout was not used.", "",
        table(pd.DataFrame(summary)), "",
        f"Sanity check: with shuffled labels the AUC is {shuffled_auc:.4f}, where 0.5 means no signal.", "",
        f"Score scale: {BASE_SCORE} means {BASE_ODDS} non-defaulters for each defaulter, and every "
        f"{POINTS_TO_DOUBLE} points doubles those odds. Higher is safer.", "",
        *sections,
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

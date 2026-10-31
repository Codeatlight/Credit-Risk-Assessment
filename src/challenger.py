"""Challenger: LightGBM, to measure what extra accuracy costs in explainability.

Same dev rows, same five folds and same candidate features as the scorecard, so the
scores compare directly. Gender and age stay out here too. The holdout stays unseen.

Early stopping needs rows to watch, and using the fold being scored would flatter the
result, so each training fold gives up 10% for that job.

Settings are fixed, sensible defaults for this size of data, not tuned. A search would
add a little AUC and more risk of fitting the dev set.

Run from the project root:  python -m src.challenger
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, early_stopping
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

from src.baseline import calibration_table, ks_statistic, table
from src.features import OUT
from src.scorecard import candidate_columns, cross_validate_scorecards, summarise

REPORT = Path("reports/challenger_results.md")
MODELS = Path("models")
SEED = 42
FOLDS = 5
STOPPING_SHARE = 0.1
STOPPING_ROUNDS = 100
MAX_TREES = 3000
TOP_FEATURES = 15

PARAMS = {"learning_rate": 0.03, "num_leaves": 31, "min_child_samples": 100, "subsample": 0.8,
          "subsample_freq": 1, "colsample_bytree": 0.5, "reg_lambda": 10.0, "metric": "auc",
          "random_state": SEED, "verbose": -1}


def fit_with_stopping(X, y):
    fit_rows, stop_rows = train_test_split(np.arange(len(y)), test_size=STOPPING_SHARE, stratify=y, random_state=SEED)
    model = LGBMClassifier(n_estimators=MAX_TREES, **PARAMS)
    model.fit(X.iloc[fit_rows], y[fit_rows], eval_set=[(X.iloc[stop_rows], y[stop_rows])],
              callbacks=[early_stopping(STOPPING_ROUNDS, verbose=False)])
    return model


def cross_validate_lightgbm(X, y):
    rows, trees = [], []
    predictions = np.zeros(len(y))
    for train, test in StratifiedKFold(FOLDS, shuffle=True, random_state=SEED).split(X, y):
        model = fit_with_stopping(X.iloc[train], y[train])
        predictions[test] = model.predict_proba(X.iloc[test])[:, 1]
        trees.append(model.best_iteration_)
        auc = roc_auc_score(y[test], predictions[test])
        rows.append({"auc": auc, "gini": 2 * auc - 1, "ks": ks_statistic(y[test], predictions[test]),
                     "brier": brier_score_loss(y[test], predictions[test])})
    return pd.DataFrame(rows), predictions, trees


def size_of(model):
    """How much a person would have to read to follow this model."""
    nodes = model.booster_.trees_to_dataframe()
    return {"trees": model.booster_.num_trees(), "leaves": int(nodes["left_child"].isna().sum()),
            "features_used": int((model.booster_.feature_importance() > 0).sum())}


def importance_table(model, columns):
    gain = pd.Series(model.booster_.feature_importance("gain"), index=columns)
    share = (gain / gain.sum()).sort_values(ascending=False).head(TOP_FEATURES).round(4)
    return share.rename("share_of_gain").rename_axis("feature").reset_index()


def main():
    numeric, categorical = candidate_columns()
    candidates = numeric + categorical
    dev = pd.read_parquet(OUT, columns=["SK_ID_CURR", "TARGET", "split", *candidates], filters=[("split", "==", "dev")])
    assert (dev["split"] == "dev").all()
    y = dev["TARGET"].to_numpy()
    X = dev[candidates].copy()
    for col in categorical:
        X[col] = X[col].astype("category")  # labels only, the target isn't involved
    variants = {"Without EXT_SOURCE": [c for c in candidates if not c.startswith("EXT_SOURCE")],
                "With EXT_SOURCE": candidates}

    print("cross-validating the scorecards on the same folds...")
    card_scores, _, _ = cross_validate_scorecards(dev[candidates], y, numeric, categorical, variants)

    summary, gains, sections = [], [], []
    MODELS.mkdir(exist_ok=True)
    for name, columns in variants.items():
        print(f"LightGBM, {name}...")
        scores, predictions, trees = cross_validate_lightgbm(X[columns], y)
        summary += [summarise(f"Scorecard, {name}", 15, card_scores[name]),
                    summarise(f"LightGBM, {name}", len(columns), scores)]
        print(summary[-2], summary[-1], sep="\n")

        gain = scores["auc"] - card_scores[name]["auc"]
        gains.append({"comparison": name, "auc_gain": f"{gain.mean():.4f}", "fold_gains": ", ".join(f"{g:.4f}" for g in gain),
                      "ks_gain": f"{(scores['ks'] - card_scores[name]['ks']).mean():.4f}"})

        final = LGBMClassifier(n_estimators=int(np.mean(trees)), **PARAMS).fit(X[columns], y)
        slug = name.lower().replace(" ", "_")
        final.booster_.save_model(MODELS / f"lightgbm_{slug}.txt")
        (MODELS / f"lightgbm_{slug}.json").write_text(json.dumps(
            {"columns": columns, "categories": {c: X[c].cat.categories.tolist() for c in categorical}}, indent=2))
        size = size_of(final)
        sections += [
            f"## LightGBM, {name}", "",
            f"Trees per fold: {trees}. The final fit on all dev rows has {size['trees']} trees, {size['leaves']:,} "
            f"leaves and uses {size['features_used']} of {len(columns)} features.", "",
            "Calibration on predictions from unseen folds:", "",
            table(calibration_table(y, predictions)), "",
            "Features doing the most work:", "",
            table(importance_table(final, columns)), ""]

    print("shuffled labels check...")
    shuffled = np.random.default_rng(SEED).permutation(y)
    shuffled_scores, _, _ = cross_validate_lightgbm(X[variants["With EXT_SOURCE"]], shuffled)
    shuffled_auc = shuffled_scores["auc"].mean()
    print(f"shuffled labels AUC: {shuffled_auc:.4f}")

    lines = [
        "# Challenger results", "",
        f"LightGBM against the scorecard on {len(dev):,} dev rows, with the same {FOLDS} folds and candidate "
        "features. Settings are fixed, not tuned. Written by `python -m src.challenger`. The holdout was not used.", "",
        table(pd.DataFrame(summary)), "",
        "AUC and KS gained over the scorecard, fold by fold:", "",
        table(pd.DataFrame(gains)), "",
        f"Sanity check: with shuffled labels the AUC is {shuffled_auc:.4f}, where 0.5 means no signal.", "",
        *sections,
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

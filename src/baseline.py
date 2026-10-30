"""Baseline: logistic regression on a few strong features, with and without EXT_SOURCE.

Dev rows only, scored with stratified 5-fold cross-validation. The holdout stays unseen.
Caps, missing-value fills and scaling all sit inside the pipeline, so each is fitted
on the training folds alone and never sees the fold being scored.

Gender and age are left out on purpose: a lender may not be allowed to use them, and
step 8 tests their effect. EMPLOYED_YEARS stays, though its missing flag marks mostly
pensioners and so carries some age signal.

Run from the project root:  python -m src.baseline
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features import OUT

REPORT = Path("reports/baseline_results.md")
SEED = 42
FOLDS = 5
CAP_QUANTILES = (0.01, 0.99)

# Chosen by meaning, one for each idea, rather than by searching for the best mix
BEHAVIOUR = [
    "ANNUITY_TO_INCOME", "ANNUITY_TO_CREDIT", "CREDIT_TO_GOODS", "EMPLOYED_YEARS",
    "BUREAU_DEBT_TO_CREDIT", "BUREAU_ACTIVE_SHARE", "BUREAU_OPENED_COUNT_12M",
    "CC_UTILISATION_MEAN_12M", "INST_DAYS_LATE_MAX_12M", "INST_LATE_RATE",
    "PREV_REFUSED_RATE", "POS_LATE_RATE",
]
EXTERNAL = ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]
FEATURE_SETS = {"Without EXT_SOURCE": BEHAVIOUR, "With EXT_SOURCE": BEHAVIOUR + EXTERNAL}


class QuantileCapper(BaseEstimator, TransformerMixin):
    """Limit each column to quantiles learned from the data it is fitted on."""

    def __init__(self, quantiles=CAP_QUANTILES):
        self.quantiles = quantiles

    def fit(self, X, y=None):
        self.low_, self.high_ = np.nanquantile(X, self.quantiles, axis=0)
        return self

    def transform(self, X):
        return np.clip(X, self.low_, self.high_)


def make_model():
    return make_pipeline(
        QuantileCapper(),
        SimpleImputer(strategy="median", add_indicator=True),
        StandardScaler(),
        LogisticRegression(max_iter=1000),
    )


def ks_statistic(y, score):
    """Biggest gap between the share of defaulters and of non-defaulters caught at any cutoff."""
    false_rate, true_rate, _ = roc_curve(y, score)
    return (true_rate - false_rate).max()


def cross_validate(X, y):
    """Scores per fold, plus every applicant's prediction from the model that didn't train on them."""
    rows = []
    predictions = np.zeros(len(y))
    folds = StratifiedKFold(FOLDS, shuffle=True, random_state=SEED)
    for train, test in folds.split(X, y):
        model = clone(make_model()).fit(X[train], y[train])
        predictions[test] = model.predict_proba(X[test])[:, 1]
        auc = roc_auc_score(y[test], predictions[test])
        rows.append({"auc": auc, "gini": 2 * auc - 1, "ks": ks_statistic(y[test], predictions[test]),
                     "brier": brier_score_loss(y[test], predictions[test])})
    return pd.DataFrame(rows), predictions


def calibration_table(y, predictions):
    """Average predicted risk against the real default rate, by tenth of predicted risk."""
    bands = pd.qcut(predictions, 10, labels=False, duplicates="drop") + 1
    table = pd.DataFrame({"risk_band": bands, "predicted": predictions, "actual": y})
    return table.groupby("risk_band")[["predicted", "actual"]].mean().round(4).reset_index()


def coefficient_table(X, y, features):
    """Fit on all dev rows. Sizes are per standard deviation, so they compare across features."""
    model = make_model().fit(X, y)
    imputer = model.named_steps["simpleimputer"]
    names = features + [f"{features[i]} (missing)" for i in imputer.indicator_.features_]
    coefs = model.named_steps["logisticregression"].coef_[0]
    table = pd.DataFrame({"feature": names, "coefficient": coefs.round(3)})
    return table.reindex(table["coefficient"].abs().sort_values(ascending=False).index)


def table(df):
    rows = [list(df.columns), ["---"] * df.shape[1], *df.astype(str).values.tolist()]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def main():
    dev = pd.read_parquet(OUT, columns=["SK_ID_CURR", "TARGET", "split", *BEHAVIOUR, *EXTERNAL],
                          filters=[("split", "==", "dev")])
    assert (dev["split"] == "dev").all()
    y = dev["TARGET"].to_numpy()

    summary, sections = [], []
    for name, features in FEATURE_SETS.items():
        X = dev[features].to_numpy(dtype="float64")
        scores, predictions = cross_validate(X, y)
        summary.append({"model": name, "features": len(features),
                        "auc": f"{scores['auc'].mean():.4f} ± {scores['auc'].std():.4f}",
                        "gini": f"{scores['gini'].mean():.4f}", "ks": f"{scores['ks'].mean():.4f}",
                        "brier": f"{scores['brier'].mean():.4f}"})
        sections += [f"## {name}", "", "Calibration on predictions from unseen folds:", "",
                     table(calibration_table(y, predictions)), "",
                     "Coefficients from a fit on all dev rows. Positive means higher risk:", "",
                     table(coefficient_table(X, y, features)), ""]
        print(summary[-1])

    # With shuffled labels there is nothing to learn, so the AUC must land near 0.5
    shuffled = np.random.default_rng(SEED).permutation(y)
    scores, _ = cross_validate(dev[BEHAVIOUR + EXTERNAL].to_numpy(dtype="float64"), shuffled)
    shuffled_auc = scores["auc"].mean()
    print(f"shuffled labels AUC: {shuffled_auc:.4f}")

    lines = [
        "# Baseline results", "",
        f"Logistic regression on {len(dev):,} dev rows with stratified {FOLDS}-fold cross-validation. "
        "Written by `python -m src.baseline`. The holdout was not used.", "",
        table(pd.DataFrame(summary)), "",
        f"Sanity check: with shuffled labels the AUC is {shuffled_auc:.4f}, where 0.5 means no signal.", "",
        *sections,
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

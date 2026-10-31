"""Explain individual decisions: why did this applicant get this score?

Scorecard: reasons come straight from the points. Each line is compared with what a
typical applicant gets on it, and the biggest shortfalls become the reasons.

LightGBM: reasons come from SHAP values, which split one prediction into a push from
each feature. LightGBM computes them itself with the TreeSHAP method (pred_contrib).

No target is used here, so reasons don't touch what the holdout measures.

Run from the project root:  python -m src.reasons
"""
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.baseline import table
from src.evaluate import scorecard_probability, slug
from src.features import OUT
from src.scorecard import FACTOR, MODELS, OFFSET, apply_bins, candidate_columns

REPORT = Path("reports/reasons_results.md")
SEED = 42
TOP_REASONS = 4
SHAP_SAMPLE = 20_000
TOP_DRIVERS = 15
EXAMPLES = 3
MODEL_VARIANT = "With EXT_SOURCE"

READABLE = {
    "EXT_SOURCE_1": "External credit score 1", "EXT_SOURCE_2": "External credit score 2",
    "EXT_SOURCE_3": "External credit score 3", "EMPLOYED_YEARS": "Time in current job",
    "INST_LATE_RATE_RECENCY_WEIGHTED": "Share of recent instalments paid late",
    "INST_DAYS_LATE_MAX_12M": "Worst lateness in the last 12 months",
    "BUREAU_ACTIVE_SHARE": "Share of loans still open at other lenders",
    "BUREAU_OPENED_COUNT_12M": "Loans opened in the last 12 months",
    "BUREAU_HISTORY_DAYS": "Length of credit history", "BUREAU_DEBT_TO_CREDIT": "Debt left on open loans",
    "BUREAU_CARD_UTILISATION": "Credit card use at other lenders",
    "CC_UTILISATION_NOW": "Home Credit card use now", "CC_UTILISATION_MEAN": "Home Credit card use over time",
    "CREDIT_TO_GOODS": "Loan size compared with the goods price", "ANNUITY_TO_CREDIT": "Repayment speed of this loan",
    "ANNUITY_TO_INCOME": "Yearly payment compared with income", "PREV_REFUSED_RATE": "Share of past applications refused",
    "PREV_DAYS_SINCE_LAST_REFUSAL": "Time since the last refusal", "OCCUPATION_TYPE": "Occupation",
    "ORGANIZATION_TYPE": "Type of employer", "AMT_CREDIT": "Loan amount",
    "POS_FUTURE_INSTALMENTS": "Instalments left on open store and cash loans",
    "PREV_TERM_MEAN": "Average term of past Home Credit loans",
    "PREV_APPROVED_CREDIT_MEAN": "Average size of past approved loans", "OWN_CAR_AGE": "Age of the applicant's car",
    "NAME_EDUCATION_TYPE": "Education level",
}


def readable(feature):
    return READABLE.get(feature, feature)


def load_card(name):
    return json.loads((MODELS / f"scorecard_{slug(name)}.json").read_text())


def card_points(card, X):
    """Points each applicant gets on each scorecard line."""
    table_ = pd.DataFrame(card["points"])
    columns = {}
    for col in card["features"]:
        bins = card["bins"][col]
        points = table_.loc[table_["feature"] == col, "points"].to_numpy(dtype="float64")
        values = X[col].to_numpy(dtype="object" if bins["kind"] == "categorical" else "float64")
        columns[col] = apply_bins(values, {**bins, "woe": points.tolist()})
    return pd.DataFrame(columns, index=X.index)


def typical_points(card):
    """Average points on each line across the applicants the scorecard was built on."""
    table_ = pd.DataFrame(card["points"])
    return {col: float(np.average(rows["points"], weights=rows["rows"])) for col, rows in table_.groupby("feature")}


def scorecard_reasons(points_row, typical, top=TOP_REASONS):
    """The lines where this applicant fell furthest below typical."""
    shortfall = {col: typical[col] - points_row[col] for col in points_row.index}
    worst = sorted(shortfall, key=shortfall.get, reverse=True)[:top]
    return [{"reason": readable(col), "points_below_typical": round(shortfall[col], 1)}
            for col in worst if shortfall[col] > 0]


def load_lightgbm(name):
    booster = lgb.Booster(model_file=str(MODELS / f"lightgbm_{slug(name)}.txt"))
    meta = json.loads((MODELS / f"lightgbm_{slug(name)}.json").read_text())
    return booster, meta


def shap_values(booster, meta, X):
    """One push per feature for each applicant, in log-odds, plus the model's starting point."""
    rows = X[meta["columns"]].copy()
    for col, categories in meta["categories"].items():
        rows[col] = pd.Categorical(rows[col], categories=categories)
    contrib = booster.predict(rows, pred_contrib=True)
    return pd.DataFrame(contrib[:, :-1], columns=meta["columns"], index=X.index), contrib[:, -1], rows


def lightgbm_reasons(shap_row, top=TOP_REASONS):
    """The features that pushed this applicant's risk up the most."""
    worst = shap_row.sort_values(ascending=False).head(top)
    return [{"reason": readable(col), "risk_push": round(float(value), 3)} for col, value in worst.items() if value > 0]


def main():
    numeric, categorical = candidate_columns()
    columns = numeric + categorical
    holdout = pd.read_parquet(OUT, columns=["SK_ID_CURR", "split", *columns], filters=[("split", "==", "holdout")])
    max_risk = json.loads((MODELS / "cutoffs.json").read_text())["max_risk"]
    name = MODEL_VARIANT

    card = load_card(name)
    typical = typical_points(card)
    p_card = scorecard_probability(name, holdout[columns])[0]
    points = card_points(card, holdout)
    total = card["base_points"] + points.sum(axis=1)
    from_points = 1 / (1 + np.exp((total.to_numpy() - OFFSET) / FACTOR))
    assert np.allclose(from_points, p_card), "reason points don't add up to the score"

    booster, meta = load_lightgbm(name)
    rng = np.random.default_rng(SEED)
    sample = holdout.iloc[rng.choice(len(holdout), SHAP_SAMPLE, replace=False)]
    shap, base, rows = shap_values(booster, meta, sample)
    raw = booster.predict(rows, raw_score=True)
    gap = float(np.abs(shap.sum(axis=1).to_numpy() + base - raw).max())
    assert gap < 1e-6, f"SHAP values miss the prediction by {gap}"
    drivers = shap.abs().mean().sort_values(ascending=False).head(TOP_DRIVERS).round(4)

    refused = holdout[p_card > max_risk[f"Scorecard, {name}"]]
    picks = refused.iloc[rng.choice(len(refused), EXAMPLES, replace=False)]
    picks_shap, _, _ = shap_values(booster, meta, picks)
    picks_points = card_points(card, picks)
    examples = []
    for applicant in picks.index:
        examples += [
            f"### Applicant {holdout.loc[applicant, 'SK_ID_CURR']}, score {total[applicant]:.0f}", "",
            "Scorecard reasons:", "", table(pd.DataFrame(scorecard_reasons(picks_points.loc[applicant], typical))), "",
            "LightGBM reasons:", "", table(pd.DataFrame(lightgbm_reasons(picks_shap.loc[applicant]))), ""]

    lines = [
        "# Reasons for decisions", "",
        f"Models: {name}. Written by `python -m src.reasons`.", "",
        "Checks passed: scorecard reason points add up to each applicant's score, and SHAP values add up to each "
        f"LightGBM prediction (largest gap {gap:.1e}).", "",
        "## What drives LightGBM overall", "",
        f"Average size of each feature's push, on {SHAP_SAMPLE:,} holdout applicants:", "",
        table(drivers.rename("mean_abs_shap").rename_axis("feature").reset_index().assign(
            meaning=lambda d: d["feature"].map(readable))), "",
        f"## Examples: {EXAMPLES} applicants the scorecard refuses", "",
        *examples,
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

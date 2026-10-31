"""Fairness checks: do the models treat gender and age groups differently?

The models never see gender or age, but other features can carry them. This measures
the locked models on the holdout at the step 7 cutoffs, without changing them.

Removing job features would be a new model, and the holdout has already been used, so
that test runs on dev predictions from unseen folds only and is labelled as such.

These are measurements, not a legal judgement. When groups truly default at different
rates, equal approval rates and equal error rates can't generally all hold together.

Run from the project root:  python -m src.fairness
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.baseline import table
from src.cutoff import LOSS, MARGIN, best_cutoff, holdout_predictions
from src.features import OUT
from src.reasons import card_points, load_card
from src.scorecard import MODELS, candidate_columns, cross_validate_scorecards

REPORT = Path("reports/fairness_results.md")
AGE_EDGES = [0, 30, 45, 60, 120]
AGE_LABELS = ["Under 30", "30 to 44", "45 to 59", "60 and over"]
FOUR_FIFTHS = 0.8  # a common screening rule of thumb for approval rates, not a legal finding
JOB_LINES = ["EMPLOYED_YEARS", "ORGANIZATION_TYPE", "OCCUPATION_TYPE"]
NO_OCCUPATION = ["OCCUPATION_TYPE"]
NO_JOB_FEATURES = ["OCCUPATION_TYPE", "ORGANIZATION_TYPE", "NAME_INCOME_TYPE", "EMPLOYED_YEARS"]


def add_groups(frame):
    frame = frame.copy()
    frame["gender"] = frame["CODE_GENDER"]
    frame["age_group"] = pd.cut(frame["AGE_YEARS"], AGE_EDGES, labels=AGE_LABELS, right=False).astype("object")
    return frame


def group_rows(model, attribute, groups, p, y, risk):
    """Approval, both kinds of error, and calibration for each group."""
    rows = []
    approved = p <= risk
    for group in pd.Series(groups).dropna().unique():
        mask = (groups == group)
        good, bad = mask & (y == 0), mask & (y == 1)
        rows.append({"model": model, "attribute": attribute, "group": group, "applicants": int(mask.sum()),
                     "default_rate": round(float(y[mask].mean()), 4), "predicted_risk": round(float(p[mask].mean()), 4),
                     "approval_rate": round(float(approved[mask].mean()), 4),
                     "good_payers_refused": round(float((~approved[good]).mean()), 4),
                     "defaulters_approved": round(float(approved[bad].mean()), 4)})
    return sorted(rows, key=lambda r: str(r["group"]))


def gap_summary(rows):
    """Largest gaps between groups, for each model and attribute."""
    summary = []
    for (model, attribute), group in pd.DataFrame(rows).groupby(["model", "attribute"], sort=False):
        ratio = group["approval_rate"].min() / group["approval_rate"].max()
        summary.append({"model": model, "attribute": attribute, "approval_ratio": round(ratio, 3),
                        "passes_four_fifths": bool(ratio >= FOUR_FIFTHS),
                        "good_payers_refused_gap": round(group["good_payers_refused"].max() - group["good_payers_refused"].min(), 4),
                        "calibration_gap": round((group["predicted_risk"] - group["default_rate"]).abs().max(), 4)})
    return summary


def occupation_proxy(dev, holdout):
    """Can occupation alone tell men from women? Mapping built on dev, measured on holdout."""
    known = dev[dev["gender"].notna()]
    share = known.assign(male=known["gender"] == "M").groupby("OCCUPATION_TYPE", dropna=False)["male"].agg(["size", "mean"])
    test = holdout[holdout["gender"].notna()]
    lookup = share["mean"]
    missing_share = lookup[lookup.index.isna()].iloc[0]
    encoded = test["OCCUPATION_TYPE"].map(lookup.dropna()).fillna(missing_share)
    auc = roc_auc_score(test["gender"] == "M", encoded)
    shown = share[share["size"] >= 1000].sort_values("mean", ascending=False).round(3).reset_index()
    return auc, shown.rename(columns={"size": "applicants", "mean": "share_male"}).fillna("Missing")


def score_as_proxy(predictions, frame):
    """How well does each model's risk alone reveal gender or an age group?"""
    rows = []
    known = frame["gender"].notna().to_numpy()
    male = (frame["gender"] == "M").to_numpy()
    young = (frame["AGE_YEARS"] < AGE_EDGES[1]).to_numpy()
    senior = (frame["AGE_YEARS"] >= AGE_EDGES[3]).to_numpy()
    for name, p in predictions.items():
        rows.append({"model": name, "reveals_male": round(roc_auc_score(male[known], p[known]), 4),
                     "reveals_under_30": round(roc_auc_score(young, p), 4),
                     "reveals_60_plus": round(1 - roc_auc_score(senior, p), 4)})
    return rows


def job_line_points(frame, name):
    """Points from employment lines for older and younger applicants."""
    card = load_card(name)
    lines = [c for c in JOB_LINES if c in card["features"]]
    points = card_points(card, frame)[lines].sum(axis=1)
    senior = frame["AGE_YEARS"] >= AGE_EDGES[3]
    return {"model": name, "lines": ", ".join(lines), "points_60_plus": round(float(points[senior].mean()), 1),
            "points_under_60": round(float(points[~senior].mean()), 1)}


def job_feature_test(dev, numeric, categorical, y):
    """Dev-only: refit scorecards without job features and see what changes."""
    candidates = numeric + categorical
    base = {"Without EXT_SOURCE": [c for c in candidates if not c.startswith("EXT_SOURCE")], "With EXT_SOURCE": candidates}
    variants = {}
    for name, columns in base.items():
        variants[f"{name}, all features"] = columns
        variants[f"{name}, no occupation"] = [c for c in columns if c not in NO_OCCUPATION]
        variants[f"{name}, no job features"] = [c for c in columns if c not in NO_JOB_FEATURES]
    scores, predictions, _ = cross_validate_scorecards(dev[candidates], y, numeric, categorical, variants)
    credit = dev["AMT_CREDIT"].to_numpy()
    rows = []
    for name, p in predictions.items():
        risk = best_cutoff(p, y, credit, MARGIN, LOSS)
        approved = p <= risk
        by_gender = pd.Series(approved).groupby(dev["gender"].to_numpy()).mean()
        by_age = pd.Series(approved).groupby(dev["age_group"].to_numpy()).mean()
        rows.append({"scorecard": name, "dev_auc": round(float(scores[name]["auc"].mean()), 4), "max_risk": round(risk, 3),
                     "approval_rate": round(float(approved.mean()), 4), "approval_women": round(float(by_gender["F"]), 4),
                     "approval_men": round(float(by_gender["M"]), 4),
                     "age_approval_ratio": round(float(by_age.min() / by_age.max()), 3)})
    return rows


def main():
    numeric, categorical = candidate_columns()
    columns = sorted(set(numeric + categorical + ["CODE_GENDER", "AGE_YEARS"]))
    frame = add_groups(pd.read_parquet(OUT, columns=["SK_ID_CURR", "TARGET", "split", *columns]))
    dev = frame[frame["split"] == "dev"].reset_index(drop=True)
    holdout = frame[frame["split"] == "holdout"].reset_index(drop=True)
    y = holdout["TARGET"].to_numpy()
    candidates = numeric + categorical
    variants = {"Without EXT_SOURCE": [c for c in candidates if not c.startswith("EXT_SOURCE")],
                "With EXT_SOURCE": candidates}
    max_risk = json.loads((MODELS / "cutoffs.json").read_text())["max_risk"]

    predictions = holdout_predictions(holdout, variants)
    rows = []
    for name, p in predictions.items():
        rows += group_rows(name, "gender", holdout["gender"].to_numpy(dtype="object"), p, y, max_risk[name])
        rows += group_rows(name, "age", holdout["age_group"].to_numpy(dtype="object"), p, y, max_risk[name])
    summary = gap_summary(rows)
    print(pd.DataFrame(summary).to_string(index=False))

    auc, shares = occupation_proxy(dev, holdout)
    print(f"occupation reveals gender, AUC {auc:.4f}")
    proxy = score_as_proxy(predictions, holdout)
    jobs = [job_line_points(holdout, name) for name in variants]
    print(pd.DataFrame(proxy).to_string(index=False))
    print(pd.DataFrame(jobs).to_string(index=False))

    print("job feature test on dev...")
    tests = job_feature_test(dev, numeric, categorical, dev["TARGET"].to_numpy())
    print(pd.DataFrame(tests).to_string(index=False))

    lines = [
        "# Fairness results", "",
        f"Locked models at the step 7 cutoffs, measured on {len(holdout):,} holdout applicants. No model uses gender or "
        "age directly. These are measurements, not a legal judgement. Written by `python -m src.fairness`.", "",
        "## Largest gaps between groups", "",
        f"`approval_ratio` is the lowest group's approval rate divided by the highest. The four-fifths line of "
        f"{FOUR_FIFTHS} is a screening rule of thumb.", "",
        table(pd.DataFrame(summary)), "",
        "## Results by group", "",
        "`good_payers_refused` is the share of non-defaulters refused. `defaulters_approved` is the share of "
        "defaulters approved.", "",
        table(pd.DataFrame(rows)), "",
        "## Do features stand in for gender or age?", "",
        f"Occupation alone separates men from women with AUC {auc:.4f}. Shares are from dev rows:", "",
        table(shares), "",
        "How well each model's risk alone reveals a group, where 0.5 means not at all:", "",
        table(pd.DataFrame(proxy)), "",
        "Average points from employment lines, by age:", "",
        table(pd.DataFrame(jobs)), "",
        "## Scorecards refitted without job features", "",
        "Dev rows only, from unseen folds, with each cutoff rechosen on dev. These are new models with no untouched "
        "holdout, so their scores aren't comparable with the holdout results.", "",
        table(pd.DataFrame(tests)), "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

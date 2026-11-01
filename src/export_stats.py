"""Write the summary numbers behind the app's results explorer to app/stats.json.

Holdout applicants are grouped into 5-point score ranges, and the sparse tails are
merged, so the file holds group totals only and no applicant records. The models are
only measured here. The numbers are checked against the step 6 and 7 reports.

Run from the project root:  python -m src.export_stats
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.cutoff import LOSS, MARGIN, profit_per_loan
from src.export_app import MODEL, OUT_FILE
from src.features import OUT
from src.reasons import card_points, load_card
from src.scorecard import candidate_columns

STATS_FILE = Path("app/stats.json")
STEP = 5
LOWEST, HIGHEST = 430, 730  # scores beyond these are merged, so no group is tiny
BAND = 50
REPORTED_APPROVAL = 0.97
REPORTED_PROFIT = 56646

# Holdout results from reports/holdout_results.md and reports/cutoff_results.md
MODELS = [
    {"name": "Scorecard", "external": False, "auc": 0.7035, "profit": 56646},
    {"name": "LightGBM", "external": False, "auc": 0.7644, "profit": 58928},
    {"name": "Scorecard", "external": True, "auc": 0.7531, "profit": 58239},
    {"name": "LightGBM", "external": True, "auc": 0.7881, "profit": 60172},
]


def summarise(frame, groups):
    grouped = frame.groupby(groups).agg(
        applicants=("TARGET", "size"), defaults=("TARGET", "sum"),
        good_credit=("good_credit", "sum"), bad_credit=("bad_credit", "sum"))
    return grouped.reset_index().rename(columns={groups: "score"}).round(0).astype("int64").to_dict("records")


def main():
    numeric, categorical = candidate_columns()
    holdout = pd.read_parquet(OUT, columns=["split", "TARGET", *numeric, *categorical], filters=[("split", "==", "holdout")])
    card = load_card(MODEL)
    scores = (card["base_points"] + card_points(card, holdout).sum(axis=1)).to_numpy()
    credit = holdout["AMT_CREDIT"].to_numpy()
    y = holdout["TARGET"].to_numpy()

    frame = pd.DataFrame({"TARGET": y, "good_credit": credit * (1 - y), "bad_credit": credit * y})
    frame["bin"] = (np.clip(scores, LOWEST, HIGHEST) // STEP * STEP).astype(int)
    frame["band"] = (np.clip(scores, 400, 749) // BAND * BAND).astype(int)
    min_score = json.loads(OUT_FILE.read_text(encoding="utf-8"))["min_score"]

    approved = scores >= min_score
    profit = profit_per_loan(y, credit, MARGIN, LOSS)[approved].sum() / len(y)
    assert abs(approved.mean() - REPORTED_APPROVAL) < 0.001, f"approval {approved.mean():.4f} differs from the report"
    assert abs(profit - REPORTED_PROFIT) < 1, f"profit {profit:.0f} differs from the report"

    STATS_FILE.write_text(json.dumps({
        "min_score": min_score, "margin": MARGIN, "loss": LOSS, "applicants": len(y), "step": STEP,
        "bins": summarise(frame, "bin"), "bands": summarise(frame, "band"), "models": MODELS}), encoding="utf-8")
    print(f"wrote {STATS_FILE}: approval {approved.mean():.4f}, profit per applicant {profit:.0f}, "
          f"smallest group {frame.groupby('bin').size().min()}")


if __name__ == "__main__":
    main()

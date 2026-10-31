"""Choose the approval cutoff from expected profit.

Each approved loan earns MARGIN of its size if repaid and loses LOSS of its size if it
defaults. Both are assumptions, not data, so a sensitivity table shows what they change.

Cutoffs are chosen on dev predictions from unseen folds, then applied unchanged to the
holdout. The holdout only measures the fixed cutoffs, and no model is changed.

The target marks payment difficulty early in a loan, not a final write-off, and only
applicants who were given loans are in the data. Both limit how far these money figures
can be trusted.

Run from the project root:  python -m src.cutoff
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.baseline import table
from src.challenger import cross_validate_lightgbm
from src.evaluate import lightgbm_probability, scorecard_probability
from src.features import OUT
from src.scorecard import MODELS, candidate_columns, cross_validate_scorecards, to_score

REPORT = Path("reports/cutoff_results.md")
CUTOFFS = MODELS / "cutoffs.json"
SEED = 42
BOOTSTRAPS = 2000

MARGIN = 0.15  # earned over the life of a repaid loan, as a share of its size
LOSS = 0.60  # lost on a defaulted loan, as a share of its size
MARGINS = [0.10, 0.15, 0.20]
LOSSES = [0.40, 0.60, 0.80]
RISK_GRID = np.arange(0.02, 0.6005, 0.005)  # highest predicted risk the lender would approve


def profit_per_loan(y, credit, margin, loss):
    """What each applicant's loan would earn or lose if approved."""
    return credit * (margin * (1 - y) - loss * y)


def best_cutoff(p, y, credit, margin, loss):
    value = profit_per_loan(y, credit, margin, loss)
    profits = [value[p <= risk].sum() for risk in RISK_GRID]
    return round(float(RISK_GRID[int(np.argmax(profits))]), 3)


def outcome(p, y, credit, risk, margin, loss):
    approved = p <= risk
    value = profit_per_loan(y, credit, margin, loss)
    return {"approval_rate": round(float(approved.mean()), 4),
            "default_rate_approved": round(float(y[approved].mean()), 4),
            "profit_per_applicant": round(float(value[approved].sum() / len(y)))}


def dev_predictions(dev, y, numeric, categorical, variants):
    print("scorecards...")
    _, cards, _ = cross_validate_scorecards(dev[numeric + categorical], y, numeric, categorical, variants)
    predictions = {f"Scorecard, {name}": p for name, p in cards.items()}
    X = dev[numeric + categorical].copy()
    for col in categorical:
        X[col] = X[col].astype("category")
    for name, columns in variants.items():
        print(f"LightGBM, {name}...")
        predictions[f"LightGBM, {name}"] = cross_validate_lightgbm(X[columns], y)[1]
    return predictions


def holdout_predictions(X, variants):
    predictions = {}
    for name in variants:
        predictions[f"Scorecard, {name}"] = scorecard_probability(name, X)[0]
        predictions[f"LightGBM, {name}"] = lightgbm_probability(name, X)[0]
    return predictions


def profit_gap(first, second, y, credit):
    """Extra holdout profit per applicant, with an interval from resampling applicants."""
    value = profit_per_loan(y, credit, MARGIN, LOSS)
    p_first, risk_first = first
    p_second, risk_second = second
    gap = value * ((p_first <= risk_first).astype(float) - (p_second <= risk_second).astype(float))
    rng = np.random.default_rng(SEED)
    means = [gap[rng.integers(0, len(gap), len(gap))].mean() for _ in range(BOOTSTRAPS)]
    low, high = np.percentile(means, [2.5, 97.5])
    return round(float(gap.mean())), f"{low:.0f} to {high:.0f}"


def main():
    numeric, categorical = candidate_columns()
    candidates = numeric + categorical
    frame = pd.read_parquet(OUT, columns=["SK_ID_CURR", "TARGET", "split", *candidates])
    variants = {"Without EXT_SOURCE": [c for c in candidates if not c.startswith("EXT_SOURCE")],
                "With EXT_SOURCE": candidates}
    dev, holdout = frame[frame["split"] == "dev"], frame[frame["split"] == "holdout"]
    y_dev, y_hold = dev["TARGET"].to_numpy(), holdout["TARGET"].to_numpy()
    credit_dev, credit_hold = dev["AMT_CREDIT"].to_numpy(), holdout["AMT_CREDIT"].to_numpy()

    from_dev = dev_predictions(dev, y_dev, numeric, categorical, variants)
    from_holdout = holdout_predictions(holdout[candidates], variants)

    chosen = {name: best_cutoff(p, y_dev, credit_dev, MARGIN, LOSS) for name, p in from_dev.items()}
    all_approved = round(float(profit_per_loan(y_hold, credit_hold, MARGIN, LOSS).mean()))
    rows, sensitivity = [], []
    for name, p in from_holdout.items():
        risk = chosen[name]
        score = int(round(to_score(risk))) if name.startswith("Scorecard") else "n/a"
        result = outcome(p, y_hold, credit_hold, risk, MARGIN, LOSS)
        rows.append({"model": name, "max_risk": round(risk, 3), "min_score": score, **result,
                     "gain_over_approving_all": result["profit_per_applicant"] - all_approved})
        print(rows[-1])
        for margin in MARGINS:
            for loss in LOSSES:
                changed = best_cutoff(from_dev[name], y_dev, credit_dev, margin, loss)
                sensitivity.append({"model": name, "margin": margin, "loss": loss, "max_risk": round(changed, 3),
                                    **outcome(p, y_hold, credit_hold, changed, margin, loss)})

    pairs = [(f"LightGBM, {n}", f"Scorecard, {n}") for n in variants]
    pairs += [(f"{kind}, With EXT_SOURCE", f"{kind}, Without EXT_SOURCE") for kind in ["Scorecard", "LightGBM"]]
    gaps = []
    for first, second in pairs:
        gap, interval = profit_gap((from_holdout[first], chosen[first]), (from_holdout[second], chosen[second]),
                                   y_hold, credit_hold)
        gaps.append({"comparison": f"{first} minus {second}", "profit_gap": gap, "gap_95_interval": interval})
    print(pd.DataFrame(gaps).to_string(index=False))

    CUTOFFS.write_text(json.dumps({"margin": MARGIN, "loss": LOSS, "max_risk": chosen}, indent=2))
    lines = [
        "# Approval cutoff results", "",
        f"Assumptions: a repaid loan earns {MARGIN:.0%} of its size and a defaulted loan loses {LOSS:.0%}. These are "
        "assumptions, not data. Cutoffs were chosen on dev predictions from unseen folds, then applied unchanged to "
        f"{len(holdout):,} holdout applicants. Profit is in the data's currency units, averaged over all applicants "
        "including those refused. Written by `python -m src.cutoff`.", "",
        f"Approving everyone earns {all_approved:,} per applicant.", "",
        table(pd.DataFrame(rows)), "",
        "Holdout profit gaps at those cutoffs. An interval that excludes 0 means a real gap:", "",
        table(pd.DataFrame(gaps)), "",
        "## Sensitivity", "",
        "Cutoff rechosen on dev for each pair of assumptions, then measured on the holdout:", "",
        table(pd.DataFrame(sensitivity)), "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

"""Final evaluation: score the locked models on the holdout, once.

The models were fitted on dev rows in steps 3 to 5 and nothing here changes them. The
holdout must stay a one-shot test, so this refuses to run again once the report exists.
Test the code first with --dry-run, which scores dev rows and writes nothing.

Run from the project root:
  python -m src.evaluate --dry-run
  python -m src.evaluate
"""
import argparse
import hashlib
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

from src.baseline import EXTERNAL, FEATURE_SETS, calibration_table, ks_statistic, make_model, table
from src.features import OUT
from src.scorecard import FACTOR, MODELS, OFFSET, candidate_columns, score_band_table, score_from_points

REPORT = Path("reports/holdout_results.md")
SEED = 42
BOOTSTRAPS = 500

# Cross-validated dev AUCs from steps 3 to 5, written down before the holdout was scored
DEV_AUC = {
    "Baseline, Without EXT_SOURCE": 0.6906, "Baseline, With EXT_SOURCE": 0.7514,
    "Scorecard, Without EXT_SOURCE": 0.6995, "Scorecard, With EXT_SOURCE": 0.7494,
    "LightGBM, Without EXT_SOURCE": 0.7579, "LightGBM, With EXT_SOURCE": 0.7847,
}


def slug(name):
    return name.lower().replace(" ", "_")


def scorecard_probability(name, X):
    """Score with the rounded points people would actually read, then turn that into a risk."""
    path = MODELS / f"scorecard_{slug(name)}.json"
    card = json.loads(path.read_text())
    points = pd.DataFrame(card["points"])
    scores = score_from_points(points, X, card["bins"], card["features"], card["base_points"])
    return 1 / (1 + np.exp((scores - OFFSET) / FACTOR)), [path]


def lightgbm_probability(name, X):
    model_path = MODELS / f"lightgbm_{slug(name)}.txt"
    meta_path = MODELS / f"lightgbm_{slug(name)}.json"
    meta = json.loads(meta_path.read_text())
    rows = X[meta["columns"]].copy()
    for col, categories in meta["categories"].items():
        rows[col] = pd.Categorical(rows[col], categories=categories)
    return lgb.Booster(model_file=str(model_path)).predict(rows), [model_path, meta_path]


def baseline_probability(name, frame, is_test):
    """The baseline wasn't saved in step 3, so refit the same pipeline on dev rows."""
    features = FEATURE_SETS[name]
    train = frame.loc[frame["split"] == "dev"]
    model = make_model().fit(train[features].to_numpy(dtype="float64"), train["TARGET"].to_numpy())
    return model.predict_proba(frame.loc[is_test, features].to_numpy(dtype="float64"))[:, 1]


def metrics(y, p):
    auc = roc_auc_score(y, p)
    return {"auc": auc, "gini": 2 * auc - 1, "ks": ks_statistic(y, p), "brier": brier_score_loss(y, p)}


def bootstrap_aucs(y, predictions):
    """AUC on resampled applicants. Every model sees the same samples, so gaps are paired."""
    rng = np.random.default_rng(SEED)
    samples = [rng.integers(0, len(y), len(y)) for _ in range(BOOTSTRAPS)]
    return {name: np.array([roc_auc_score(y[s], p[s]) for s in samples]) for name, p in predictions.items()}


def interval(values):
    low, high = np.percentile(values, [2.5, 97.5])
    return f"{low:.4f} to {high:.4f}"


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="score dev rows to test the code, and write nothing")
    dry_run = parser.parse_args().dry_run
    if not dry_run and REPORT.exists():
        raise SystemExit(f"{REPORT} exists: the holdout has been used and must not be scored again.")

    numeric, categorical = candidate_columns()
    columns = sorted(set(numeric + categorical + FEATURE_SETS["With EXT_SOURCE"] + EXTERNAL))
    frame = pd.read_parquet(OUT, columns=["SK_ID_CURR", "TARGET", "split", *columns])
    is_test = frame["split"] == ("dev" if dry_run else "holdout")
    test = frame[is_test]
    X = test[columns]
    y = test["TARGET"].to_numpy()
    print(f"scoring {len(test):,} {'dev' if dry_run else 'holdout'} rows")

    predictions, locked = {}, []
    for name in FEATURE_SETS:
        predictions[f"Baseline, {name}"] = baseline_probability(name, frame, is_test)
        predictions[f"Scorecard, {name}"], files = scorecard_probability(name, X)
        locked += files
        predictions[f"LightGBM, {name}"], files = lightgbm_probability(name, X)
        locked += files

    boots = bootstrap_aucs(y, predictions)
    rows = []
    for name, p in predictions.items():
        m = metrics(y, p)
        rows.append({"model": name, "dev_auc": DEV_AUC[name], "holdout_auc": round(m["auc"], 4),
                     "auc_95_interval": interval(boots[name]), "gini": round(m["gini"], 4), "ks": round(m["ks"], 4),
                     "brier": round(m["brier"], 4), "mean_predicted": round(float(p.mean()), 4)})
    results = pd.DataFrame(rows)
    print(results.to_string(index=False))

    gaps = []
    for name in FEATURE_SETS:
        difference = boots[f"LightGBM, {name}"] - boots[f"Scorecard, {name}"]
        gaps.append({"comparison": f"LightGBM minus Scorecard, {name}", "auc_gap": round(float(np.mean(difference)), 4),
                     "gap_95_interval": interval(difference)})
    for kind in ["Scorecard", "LightGBM"]:
        difference = boots[f"{kind}, With EXT_SOURCE"] - boots[f"{kind}, Without EXT_SOURCE"]
        gaps.append({"comparison": f"{kind}, value of EXT_SOURCE", "auc_gap": round(float(np.mean(difference)), 4),
                     "gap_95_interval": interval(difference)})
    print(pd.DataFrame(gaps).to_string(index=False))

    if dry_run:
        print("dry run: no report written")
        return

    sections = []
    for name, p in predictions.items():
        if name.startswith("Baseline"):
            continue
        sections += [f"## {name}", "", "Calibration:", "", table(calibration_table(y, p)), ""]
        if name.startswith("Scorecard"):
            sections += ["Default rate by score band:", "", table(score_band_table(y, p)), ""]

    hashes = pd.DataFrame([{"file": path.name, "sha256_start": file_hash(path)} for path in locked])
    lines = [
        "# Holdout results", "",
        f"One scoring run on {len(test):,} holdout applicants ({y.mean():.2%} defaulted), with models fitted on "
        "dev rows only. Written by `python -m src.evaluate`, which refuses to run twice. "
        f"Intervals come from {BOOTSTRAPS} bootstrap resamples.", "",
        table(results), "",
        "AUC gaps between models, on the same bootstrap samples. An interval that excludes 0 means a real gap:", "",
        table(pd.DataFrame(gaps)), "",
        *sections,
        "## Locked model files", "",
        table(hashes), "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

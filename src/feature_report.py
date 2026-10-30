"""Sanity report on the feature table. Dev rows only: the holdout stays unseen.

Covers row and column counts, missing rates, leakage date checks, and how well
each single feature separates defaulters.

Run from the project root, after src.features:  python -m src.feature_report
"""
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score

from src.features import DAYS_PLACEHOLDER, OUT, RAW

REPORT = Path("reports/feature_sanity.md")
SUSPICIOUS_AUC = 0.72  # above the best single column seen in step 1, so worth a second look


def single_feature_auc(dev):
    rows = []
    for col in dev.select_dtypes("number").columns.drop(["SK_ID_CURR", "TARGET"]):
        mask = dev[col].notna()
        if mask.sum() < 1000 or dev.loc[mask, col].nunique() < 2:
            continue
        auc = roc_auc_score(dev.loc[mask, "TARGET"], dev.loc[mask, col])
        rows.append({"feature": col, "auc": round(max(auc, 1 - auc), 4), "coverage": round(mask.mean(), 3)})
    return pd.DataFrame(rows).sort_values("auc", ascending=False)


def date_checks(ids):
    """Latest date in each history field. Above 0 means after the application."""
    checks = {
        "bureau": ["DAYS_CREDIT", "DAYS_ENDDATE_FACT", "DAYS_CREDIT_UPDATE"],
        "bureau_balance": ["MONTHS_BALANCE"],
        "previous_application": ["DAYS_DECISION", "DAYS_FIRST_DUE", "DAYS_LAST_DUE", "DAYS_TERMINATION"],
        "installments_payments": ["DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT"],
        "POS_CASH_balance": ["MONTHS_BALANCE"],
        "credit_card_balance": ["MONTHS_BALANCE"],
    }
    bureau_ids = pd.read_csv(RAW / "bureau.csv", usecols=["SK_ID_CURR", "SK_ID_BUREAU"])
    bureau_ids = bureau_ids.loc[bureau_ids["SK_ID_CURR"].isin(ids), "SK_ID_BUREAU"]
    rows = []
    for name, cols in checks.items():
        key = "SK_ID_BUREAU" if name == "bureau_balance" else "SK_ID_CURR"
        df = pd.read_csv(RAW / f"{name}.csv", usecols=[key, *cols])
        df = df[df[key].isin(bureau_ids if key == "SK_ID_BUREAU" else ids)]
        for col in cols:
            real = df[col].where(df[col] != DAYS_PLACEHOLDER)
            rows.append({"table": name, "field": col, "latest": real.max(),
                         "rows_after_application": int((real > 0).sum()), "rows_at_0": int((real == 0).sum())})
    return pd.DataFrame(rows)


def current_loan_check(dev):
    """Does the loan being applied for show up in its own history? Look for same-size credits."""
    app = dev[["SK_ID_CURR", "AMT_CREDIT"]]
    bureau = pd.read_csv(RAW / "bureau.csv", usecols=["SK_ID_CURR", "DAYS_CREDIT", "AMT_CREDIT_SUM"])
    bureau = bureau[bureau["DAYS_CREDIT"] >= -7].merge(app, on="SK_ID_CURR")
    prev = pd.read_csv(RAW / "previous_application.csv", usecols=["SK_ID_CURR", "DAYS_DECISION", "AMT_CREDIT"])
    prev = prev[prev["DAYS_DECISION"] >= -7].merge(app, on="SK_ID_CURR", suffixes=("_prev", ""))
    return pd.DataFrame([
        {"table": "bureau", "records_in_last_7_days": len(bureau),
         "same_amount_as_current_loan": int((bureau["AMT_CREDIT_SUM"] == bureau["AMT_CREDIT"]).sum())},
        {"table": "previous_application", "records_in_last_7_days": len(prev),
         "same_amount_as_current_loan": int((prev["AMT_CREDIT_prev"] == prev["AMT_CREDIT"]).sum())}])


def table(df):
    """Markdown table, without needing the tabulate package."""
    rows = [list(df.columns), ["---"] * df.shape[1], *df.astype(str).values.tolist()]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def main():
    columns = pq.read_schema(OUT).names
    dev = pd.read_parquet(OUT, filters=[("split", "==", "dev")])
    assert (dev["split"] == "dev").all()

    raw_columns = pd.read_csv(RAW / "application_train.csv", nrows=0).columns
    new = [c for c in columns if c not in raw_columns and c != "split"]
    missing = dev[new].isna().mean().sort_values(ascending=False).round(3)
    flags = [c for c in new if c.endswith("_HAS_HISTORY")]
    power = single_feature_auc(dev)
    power["group"] = power["feature"].isin(new).map({True: "new", False: "existing"})
    no_ext = power[~power["feature"].str.startswith("EXT_SOURCE")]

    lines = [
        "# Feature sanity report", "",
        "Dev set only. Written by `python -m src.feature_report`.", "",
        "## Size", "",
        f"- Feature table: {len(columns)} columns, of which {len(new)} are new.",
        f"- Dev rows: {len(dev):,}, duplicate applicants: {int(dev['SK_ID_CURR'].duplicated().sum())}, "
        f"default rate: {dev['TARGET'].mean():.2%}.", "",
        "## Who has each history", "",
        table(dev[flags].mean().round(3).rename("share_of_applicants").rename_axis("flag").reset_index()), "",
        "## Missing rates of new features", "",
        f"- {int((missing == 0).sum())} of {len(new)} have no missing values; "
        f"{int((missing > 0.5).sum())} are over 50% missing.", "",
        "Most missing:", "",
        table(missing.head(12).rename("missing").rename_axis("feature").reset_index()), "",
        "## Single-feature AUC", "",
        "AUC of one column alone, flipped so it is always 0.5 or above, measured only on rows where the "
        "column has a value. Coverage is the share of dev rows that have a value, so a low-coverage "
        "feature is not directly comparable with a full-coverage one.", "",
        "Top new features:", "",
        table(power[power["group"] == "new"].head(15).drop(columns="group")), "",
        "Top new features, leaving out EXT_SOURCE ones:", "",
        table(no_ext[no_ext["group"] == "new"].head(10).drop(columns="group")), "",
        "Best existing columns:", "",
        table(power[power["group"] == "existing"].head(10).drop(columns="group")), "",
        f"Features above the {SUSPICIOUS_AUC} suspicion line: "
        f"{power.loc[power['auc'] > SUSPICIOUS_AUC, 'feature'].tolist() or 'none'}.", "",
        "## Date checks for leakage", "",
        "`DAYS_*` and `MONTHS_*` count back from the application, so above 0 means after it.", "",
        table(date_checks(set(dev["SK_ID_CURR"]))), "",
        "## Does the current loan appear in its own history?", "",
        table(current_loan_check(dev)), "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()

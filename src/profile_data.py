"""First look at the Home Credit tables: sizes, target, keys, missing values, oddities.

Run from the project root:  python -m src.profile_data
"""
from pathlib import Path

import pandas as pd
from sklearn.metrics import roc_auc_score

RAW = Path("data/raw")


def main():
    app = pd.read_csv(RAW / "application_train.csv")
    test = pd.read_csv(RAW / "application_test.csv", usecols=["SK_ID_CURR"])

    print("== application_train ==")
    print("rows, cols:", app.shape)
    print("duplicate SK_ID_CURR:", app["SK_ID_CURR"].duplicated().sum())
    print("defaults:", int(app["TARGET"].sum()), f"rate {app['TARGET'].mean():.4f}")
    print("ids shared with test:", len(set(app["SK_ID_CURR"]) & set(test["SK_ID_CURR"])))

    missing = app.isna().mean().sort_values(ascending=False)
    print("columns with any missing:", int((missing > 0).sum()), "of", app.shape[1])
    print("columns over 40% missing:", int((missing > 0.4).sum()))
    print("EXT_SOURCE missing:", app[["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]].isna().mean().round(3).to_dict())

    print("\n== oddities ==")
    print("DAYS_EMPLOYED == 365243:", int((app["DAYS_EMPLOYED"] == 365243).sum()))
    print("  default rate when placeholder:", round(app.loc[app["DAYS_EMPLOYED"] == 365243, "TARGET"].mean(), 4))
    print("  default rate otherwise:", round(app.loc[app["DAYS_EMPLOYED"] != 365243, "TARGET"].mean(), 4))
    print("  NAME_INCOME_TYPE when placeholder:", app.loc[app["DAYS_EMPLOYED"] == 365243, "NAME_INCOME_TYPE"].value_counts().to_dict())
    print("CODE_GENDER:", app["CODE_GENDER"].value_counts().to_dict())
    print("ORGANIZATION_TYPE XNA:", int((app["ORGANIZATION_TYPE"] == "XNA").sum()))
    print("max AMT_INCOME_TOTAL:", app["AMT_INCOME_TOTAL"].max(), "| 99.9th pct:", app["AMT_INCOME_TOTAL"].quantile(0.999))
    print("age range (years):", round(-app["DAYS_BIRTH"].max() / 365.25, 1), "to", round(-app["DAYS_BIRTH"].min() / 365.25, 1))
    print("AMT_CREDIT median:", app["AMT_CREDIT"].median(), "| AMT_ANNUITY median:", app["AMT_ANNUITY"].median())

    print("\n== single-column ranking power (AUC, oriented to 0.5+) ==")
    num = app.select_dtypes("number").drop(columns=["SK_ID_CURR", "TARGET"])
    rows = []
    for col in num.columns:
        mask = num[col].notna()
        if mask.sum() < 1000 or num.loc[mask, col].nunique() < 2:
            continue
        auc = roc_auc_score(app.loc[mask, "TARGET"], num.loc[mask, col])
        rows.append((col, round(max(auc, 1 - auc), 4), round(mask.mean(), 3)))
    print(pd.DataFrame(rows, columns=["feature", "auc", "coverage"]).sort_values("auc", ascending=False).head(12).to_string(index=False))

    print("\n== default rate by group ==")
    for col in ["CODE_GENDER", "NAME_CONTRACT_TYPE", "NAME_EDUCATION_TYPE"]:
        print(app.groupby(col)["TARGET"].agg(["size", "mean"]).round(4).to_string(), "\n")

    print("== linked tables ==")
    ids = set(app["SK_ID_CURR"])
    for name, key in [("bureau", "SK_ID_CURR"), ("previous_application", "SK_ID_CURR"),
                      ("POS_CASH_balance", "SK_ID_CURR"), ("installments_payments", "SK_ID_CURR"),
                      ("credit_card_balance", "SK_ID_CURR")]:
        df = pd.read_csv(RAW / f"{name}.csv", usecols=[key])
        covered = len(ids & set(df[key]))
        print(f"{name}: {len(df):,} rows; covers {covered / len(ids):.1%} of train applicants")
    bb = pd.read_csv(RAW / "bureau_balance.csv", usecols=["SK_ID_BUREAU"])
    print(f"bureau_balance: {len(bb):,} rows; {bb['SK_ID_BUREAU'].nunique():,} bureau records")


if __name__ == "__main__":
    main()

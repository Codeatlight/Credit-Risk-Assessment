"""Build one row of features per applicant from the Home Credit tables.

Leakage rules followed here:
- Anything fitted from data (the income cap) uses dev rows only, then applies to all rows.
- Summaries of an applicant's own history need no fitting, so they run on every row.
- Only events dated before the application are used. See reports/feature_dictionary.md.

History rule: an applicant with no records in a table gets missing values for that
table, not zeros, because "no history" is not the same as "a clean history". Each
table has a *_HAS_HISTORY flag. A 12-month rate is also missing if the applicant had
nothing in those 12 months.

Run from the project root:  python -m src.features
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
OUT = PROCESSED / "features.parquet"
PARAMS = PROCESSED / "feature_params.json"

EXPECTED_APPLICANTS = 307_511
DAYS_PLACEHOLDER = 365243
INCOME_CAP_QUANTILE = 0.999
RECENT_DAYS = -365
RECENT_MONTHS = -12
CURRENT_MONTHS = -3  # a loan or card seen this recently still counts as open
HALF_LIFE_DAYS = 365  # recency weight: a payment a year old counts half
UNDERPAID_TOLERANCE = 0.99  # ignores small rounding differences


def load(name, dtypes, ids):
    """Read only the needed columns, in small dtypes, for the applicants in `ids`."""
    df = pd.read_csv(RAW / f"{name}.csv", usecols=list(dtypes), dtype=dtypes)
    return df[df["SK_ID_CURR"].isin(ids)]


def ratio(top, bottom):
    """Divide, giving missing rather than infinity when the bottom is zero or missing."""
    return top / bottom.where(bottom > 0)


def application_features(app, dev_ids):
    placeholder = app["DAYS_EMPLOYED"] == DAYS_PLACEHOLDER
    app["IS_PENSIONER_OR_UNEMPLOYED"] = placeholder.astype("int8")
    app.loc[placeholder, "DAYS_EMPLOYED"] = np.nan
    app["CODE_GENDER"] = app["CODE_GENDER"].replace("XNA", np.nan)

    income_cap = float(app.loc[app["SK_ID_CURR"].isin(dev_ids), "AMT_INCOME_TOTAL"].quantile(INCOME_CAP_QUANTILE))
    app["AMT_INCOME_TOTAL"] = app["AMT_INCOME_TOTAL"].clip(upper=income_cap)

    app["CREDIT_TO_INCOME"] = ratio(app["AMT_CREDIT"], app["AMT_INCOME_TOTAL"])
    app["ANNUITY_TO_INCOME"] = ratio(app["AMT_ANNUITY"], app["AMT_INCOME_TOTAL"])
    app["CREDIT_TO_GOODS"] = ratio(app["AMT_CREDIT"], app["AMT_GOODS_PRICE"])
    app["ANNUITY_TO_CREDIT"] = ratio(app["AMT_ANNUITY"], app["AMT_CREDIT"])
    app["INCOME_PER_PERSON"] = ratio(app["AMT_INCOME_TOTAL"], app["CNT_FAM_MEMBERS"])
    app["AGE_YEARS"] = -app["DAYS_BIRTH"] / 365.25
    app["EMPLOYED_YEARS"] = -app["DAYS_EMPLOYED"] / 365.25
    app["EMPLOYED_TO_AGE"] = app["EMPLOYED_YEARS"] / app["AGE_YEARS"]

    ext = app[["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]]
    app["EXT_SOURCE_MEAN"] = ext.mean(axis=1)
    app["EXT_SOURCE_MISSING_COUNT"] = ext.isna().sum(axis=1).astype("int8")
    return app, {"income_cap": income_cap, "income_cap_quantile": INCOME_CAP_QUANTILE}


def bureau_features(ids):
    bureau = load("bureau", {
        "SK_ID_CURR": "int32", "SK_ID_BUREAU": "int32", "CREDIT_ACTIVE": "category",
        "CREDIT_CURRENCY": "category", "CREDIT_TYPE": "category", "DAYS_CREDIT": "float32",
        "CREDIT_DAY_OVERDUE": "float32", "AMT_CREDIT_MAX_OVERDUE": "float64",
        "CNT_CREDIT_PROLONG": "float32", "AMT_CREDIT_SUM": "float64", "AMT_CREDIT_SUM_DEBT": "float64",
        "AMT_CREDIT_SUM_OVERDUE": "float64", "DAYS_CREDIT_UPDATE": "float32"}, ids)

    # A few records were updated after the application date, so what they say now is not usable
    bureau = bureau[bureau["DAYS_CREDIT_UPDATE"] <= 0].copy()
    # Amounts in other currencies can't be added to the main one
    money = ["AMT_CREDIT_MAX_OVERDUE", "AMT_CREDIT_SUM", "AMT_CREDIT_SUM_DEBT", "AMT_CREDIT_SUM_OVERDUE"]
    bureau.loc[bureau["CREDIT_CURRENCY"] != "currency 1", money] = np.nan
    bureau["AMT_CREDIT_SUM_DEBT"] = bureau["AMT_CREDIT_SUM_DEBT"].clip(lower=0)

    active = bureau["CREDIT_ACTIVE"] == "Active"
    bureau["is_active"] = active
    bureau["is_closed"] = bureau["CREDIT_ACTIVE"] == "Closed"
    bureau["is_bad"] = bureau["CREDIT_ACTIVE"].isin(["Sold", "Bad debt"])
    bureau["is_microloan"] = bureau["CREDIT_TYPE"] == "Microloan"
    bureau["is_recent"] = bureau["DAYS_CREDIT"] >= RECENT_DAYS
    bureau["active_debt"] = bureau["AMT_CREDIT_SUM_DEBT"].where(active)
    bureau["active_credit"] = bureau["AMT_CREDIT_SUM"].where(active)
    card = active & (bureau["CREDIT_TYPE"] == "Credit card")
    bureau["card_debt"] = bureau["AMT_CREDIT_SUM_DEBT"].where(card)
    bureau["card_limit"] = bureau["AMT_CREDIT_SUM"].where(card)

    out = bureau.groupby("SK_ID_CURR", observed=True).agg(
        BUREAU_CREDIT_COUNT=("SK_ID_BUREAU", "size"),
        BUREAU_ACTIVE_COUNT=("is_active", "sum"),
        BUREAU_CLOSED_COUNT=("is_closed", "sum"),
        BUREAU_BAD_DEBT_COUNT=("is_bad", "sum"),
        BUREAU_MICROLOAN_COUNT=("is_microloan", "sum"),
        BUREAU_OPENED_COUNT_12M=("is_recent", "sum"),
        BUREAU_DAYS_SINCE_LAST_OPENED=("DAYS_CREDIT", "max"),
        BUREAU_HISTORY_DAYS=("DAYS_CREDIT", "min"),
        BUREAU_ACTIVE_DEBT_SUM=("active_debt", "sum"),
        BUREAU_ACTIVE_CREDIT_SUM=("active_credit", "sum"),
        BUREAU_OVERDUE_SUM=("AMT_CREDIT_SUM_OVERDUE", "sum"),
        BUREAU_MAX_OVERDUE_EVER=("AMT_CREDIT_MAX_OVERDUE", "max"),
        BUREAU_MAX_DAYS_OVERDUE_NOW=("CREDIT_DAY_OVERDUE", "max"),
        BUREAU_PROLONG_COUNT=("CNT_CREDIT_PROLONG", "sum"),
        card_debt=("card_debt", "sum"),
        card_limit=("card_limit", "sum"))
    out["BUREAU_DAYS_SINCE_LAST_OPENED"] *= -1
    out["BUREAU_HISTORY_DAYS"] *= -1
    out["BUREAU_ACTIVE_SHARE"] = ratio(out["BUREAU_ACTIVE_COUNT"], out["BUREAU_CREDIT_COUNT"])
    out["BUREAU_DEBT_TO_CREDIT"] = ratio(out["BUREAU_ACTIVE_DEBT_SUM"], out["BUREAU_ACTIVE_CREDIT_SUM"])
    out["BUREAU_CARD_UTILISATION"] = ratio(out.pop("card_debt"), out.pop("card_limit"))

    links = bureau[["SK_ID_BUREAU", "SK_ID_CURR"]]
    return out, bureau_balance_features(links)


def bureau_balance_features(links):
    """Monthly status of bureau loans: C closed, X unknown, 0 on time, 1-5 worsening lateness."""
    balance = pd.read_csv(RAW / "bureau_balance.csv",
                          dtype={"SK_ID_BUREAU": "int32", "MONTHS_BALANCE": "int8", "STATUS": "category"})
    # Month 0 is the application month itself: every other table stops at -1, so leave it out
    balance = balance[balance["MONTHS_BALANCE"] < 0]
    balance = balance.merge(links, on="SK_ID_BUREAU")

    known = balance["STATUS"].isin(list("012345"))
    balance = balance[known].copy()
    balance["level"] = balance["STATUS"].astype(str).astype("int8")
    balance["is_late"] = balance["level"] > 0
    balance["is_severe"] = balance["level"] >= 3  # 90+ days past due
    balance["late_month"] = balance["MONTHS_BALANCE"].where(balance["is_late"])

    by_id = balance.groupby("SK_ID_CURR")
    out = by_id.agg(
        BB_MONTHS_REPORTED=("level", "size"),
        BB_LATE_MONTHS=("is_late", "sum"),
        BB_SEVERE_LATE_MONTHS=("is_severe", "sum"),
        BB_WORST_STATUS=("level", "max"),
        BB_MONTHS_SINCE_LAST_LATE=("late_month", "max"))
    out["BB_MONTHS_SINCE_LAST_LATE"] *= -1
    out["BB_LATE_RATE"] = ratio(out["BB_LATE_MONTHS"], out["BB_MONTHS_REPORTED"])

    recent = balance[balance["MONTHS_BALANCE"] >= RECENT_MONTHS].groupby("SK_ID_CURR")
    out["BB_LATE_MONTHS_12M"] = recent["is_late"].sum()
    out["BB_LATE_RATE_12M"] = recent["is_late"].mean()
    return out


def previous_features(ids):
    prev = load("previous_application", {
        "SK_ID_CURR": "int32", "SK_ID_PREV": "int32", "NAME_CONTRACT_STATUS": "category",
        "CODE_REJECT_REASON": "category", "DAYS_DECISION": "float32", "AMT_APPLICATION": "float64",
        "AMT_CREDIT": "float64", "RATE_DOWN_PAYMENT": "float32", "CNT_PAYMENT": "float32",
        "FLAG_LAST_APPL_PER_CONTRACT": "category", "NFLAG_LAST_APPL_IN_DAY": "int8"}, ids)
    # Duplicates: the file itself says these are mistaken extra applications for one contract
    prev = prev[(prev["FLAG_LAST_APPL_PER_CONTRACT"] == "Y") & (prev["NFLAG_LAST_APPL_IN_DAY"] == 1)].copy()

    approved = prev["NAME_CONTRACT_STATUS"] == "Approved"
    refused = prev["NAME_CONTRACT_STATUS"] == "Refused"
    recent = prev["DAYS_DECISION"] >= RECENT_DAYS
    prev["is_approved"] = approved
    prev["is_refused"] = refused
    prev["is_canceled"] = prev["NAME_CONTRACT_STATUS"] == "Canceled"
    prev["is_score_refused"] = refused & prev["CODE_REJECT_REASON"].isin(["SCO", "SCOFR"])
    prev["is_recent"] = recent
    prev["approved_12m"] = approved & recent
    prev["refused_12m"] = refused & recent
    prev["refused_day"] = prev["DAYS_DECISION"].where(refused)
    prev["approved_day"] = prev["DAYS_DECISION"].where(approved)
    prev["approved_credit"] = prev["AMT_CREDIT"].where(approved)
    prev["asked_vs_granted"] = ratio(prev["AMT_APPLICATION"], prev["AMT_CREDIT"]).where(approved)

    out = prev.groupby("SK_ID_CURR").agg(
        PREV_COUNT=("SK_ID_PREV", "size"),
        PREV_APPROVED_COUNT=("is_approved", "sum"),
        PREV_REFUSED_COUNT=("is_refused", "sum"),
        PREV_CANCELED_COUNT=("is_canceled", "sum"),
        PREV_SCORE_REFUSED_COUNT=("is_score_refused", "sum"),
        recent_count=("is_recent", "sum"),
        PREV_APPROVED_COUNT_12M=("approved_12m", "sum"),
        PREV_REFUSED_COUNT_12M=("refused_12m", "sum"),
        PREV_DAYS_SINCE_LAST_REFUSAL=("refused_day", "max"),
        PREV_DAYS_SINCE_LAST_APPROVAL=("approved_day", "max"),
        PREV_APPROVED_CREDIT_MEAN=("approved_credit", "mean"),
        PREV_ASKED_VS_GRANTED_MEAN=("asked_vs_granted", "mean"),
        PREV_DOWN_PAYMENT_RATE_MEAN=("RATE_DOWN_PAYMENT", "mean"),
        PREV_TERM_MEAN=("CNT_PAYMENT", "mean"))
    out["PREV_DAYS_SINCE_LAST_REFUSAL"] *= -1
    out["PREV_DAYS_SINCE_LAST_APPROVAL"] *= -1
    out["PREV_REFUSED_RATE"] = ratio(out["PREV_REFUSED_COUNT"], out["PREV_COUNT"])
    out["PREV_REFUSED_RATE_12M"] = ratio(out["PREV_REFUSED_COUNT_12M"], out.pop("recent_count"))
    return out


def installment_summary(df, suffix=""):
    grouped = df.groupby("SK_ID_CURR")
    out = grouped.agg(**{
        f"INST_COUNT{suffix}": ("is_late", "size"),
        f"INST_LATE_COUNT{suffix}": ("is_late", "sum"),
        f"INST_LATE_RATE{suffix}": ("is_late", "mean"),
        f"INST_LATE_30_COUNT{suffix}": ("is_late_30", "sum"),
        f"INST_DAYS_LATE_MAX{suffix}": ("days_late", "max"),
        f"INST_DAYS_LATE_MEAN{suffix}": ("days_late", "mean"),
        f"INST_UNDERPAID_RATE{suffix}": ("is_underpaid", "mean"),
        "paid": ("AMT_PAYMENT", "sum"),
        "due": ("AMT_INSTALMENT", "sum")})
    out[f"INST_PAID_TO_DUE{suffix}"] = ratio(out.pop("paid"), out.pop("due"))
    return out


def installments_features(ids):
    pay = load("installments_payments", {
        "SK_ID_CURR": "int32", "SK_ID_PREV": "int32", "NUM_INSTALMENT_VERSION": "int16",
        "NUM_INSTALMENT_NUMBER": "int16", "DAYS_INSTALMENT": "int16", "DAYS_ENTRY_PAYMENT": "float32",
        "AMT_INSTALMENT": "float64", "AMT_PAYMENT": "float64"}, ids)

    # One instalment can be paid in several parts, so roll payments up to one row per instalment
    keys = ["SK_ID_CURR", "SK_ID_PREV", "NUM_INSTALMENT_VERSION", "NUM_INSTALMENT_NUMBER", "DAYS_INSTALMENT"]
    pay = pay.groupby(keys, sort=False, as_index=False).agg(
        AMT_INSTALMENT=("AMT_INSTALMENT", "first"),
        AMT_PAYMENT=("AMT_PAYMENT", "sum"),
        last_paid_day=("DAYS_ENTRY_PAYMENT", "max"))

    # No payment recorded by the application date: unpaid until then (day 0)
    days_late = pay["last_paid_day"].fillna(0) - pay["DAYS_INSTALMENT"]
    pay["days_late"] = days_late.clip(lower=0).astype("float32")
    pay["is_late"] = pay["days_late"] > 0
    pay["is_late_30"] = pay["days_late"] > 30
    pay["is_underpaid"] = pay["AMT_PAYMENT"] < pay["AMT_INSTALMENT"] * UNDERPAID_TOLERANCE

    out = installment_summary(pay)
    out = out.join(installment_summary(pay[pay["DAYS_INSTALMENT"] >= RECENT_DAYS], "_12M"))

    weight = 0.5 ** (-pay["DAYS_INSTALMENT"] / HALF_LIFE_DAYS)
    weighted = pd.DataFrame({"SK_ID_CURR": pay["SK_ID_CURR"], "late": pay["is_late"] * weight, "all": weight})
    totals = weighted.groupby("SK_ID_CURR")[["late", "all"]].sum()
    out["INST_LATE_RATE_RECENCY_WEIGHTED"] = totals["late"] / totals["all"]
    return out


def latest_rows(df):
    """The newest row of each previous loan or card."""
    return df.loc[df.groupby("SK_ID_PREV")["MONTHS_BALANCE"].idxmax()]


def pos_features(ids):
    pos = load("POS_CASH_balance", {
        "SK_ID_CURR": "int32", "SK_ID_PREV": "int32", "MONTHS_BALANCE": "int8",
        "CNT_INSTALMENT_FUTURE": "float32", "NAME_CONTRACT_STATUS": "category",
        "SK_DPD": "int16", "SK_DPD_DEF": "int16"}, ids).reset_index(drop=True)
    pos["is_late"] = pos["SK_DPD_DEF"] > 0

    out = pos.groupby("SK_ID_CURR").agg(
        POS_MONTHS=("is_late", "size"),
        POS_LOAN_COUNT=("SK_ID_PREV", "nunique"),
        POS_LATE_MONTHS=("is_late", "sum"),
        POS_LATE_RATE=("is_late", "mean"),
        POS_DPD_MAX=("SK_DPD", "max"),
        POS_DPD_DEF_MAX=("SK_DPD_DEF", "max"))
    recent = pos[pos["MONTHS_BALANCE"] >= RECENT_MONTHS].groupby("SK_ID_CURR")
    out["POS_LATE_MONTHS_12M"] = recent["is_late"].sum()
    out["POS_LATE_RATE_12M"] = recent["is_late"].mean()
    out["POS_DPD_DEF_MAX_12M"] = recent["SK_DPD_DEF"].max()

    latest = latest_rows(pos)
    latest = latest.assign(
        is_open=(latest["NAME_CONTRACT_STATUS"] == "Active") & (latest["MONTHS_BALANCE"] >= CURRENT_MONTHS),
        is_completed=latest["NAME_CONTRACT_STATUS"] == "Completed")
    latest["future"] = latest["CNT_INSTALMENT_FUTURE"].where(latest["is_open"])
    summary = latest.groupby("SK_ID_CURR").agg(
        POS_OPEN_COUNT=("is_open", "sum"),
        POS_COMPLETED_COUNT=("is_completed", "sum"),
        POS_FUTURE_INSTALMENTS=("future", "sum"))
    return out.join(summary)


def card_features(ids):
    card = load("credit_card_balance", {
        "SK_ID_CURR": "int32", "SK_ID_PREV": "int32", "MONTHS_BALANCE": "int8", "AMT_BALANCE": "float64",
        "AMT_CREDIT_LIMIT_ACTUAL": "float64", "AMT_DRAWINGS_ATM_CURRENT": "float64",
        "AMT_DRAWINGS_CURRENT": "float64", "AMT_INST_MIN_REGULARITY": "float64",
        "AMT_PAYMENT_TOTAL_CURRENT": "float64", "SK_DPD": "int16", "SK_DPD_DEF": "int16"}, ids).reset_index(drop=True)
    card["utilisation"] = ratio(card["AMT_BALANCE"].clip(lower=0), card["AMT_CREDIT_LIMIT_ACTUAL"])
    card["is_late"] = card["SK_DPD_DEF"] > 0
    owed = card["AMT_INST_MIN_REGULARITY"] > 0
    card["missed_minimum"] = (card["AMT_PAYMENT_TOTAL_CURRENT"] < card["AMT_INST_MIN_REGULARITY"]).where(owed).astype("float32")

    out = card.groupby("SK_ID_CURR").agg(
        CC_MONTHS=("is_late", "size"),
        CC_CARD_COUNT=("SK_ID_PREV", "nunique"),
        CC_UTILISATION_MEAN=("utilisation", "mean"),
        CC_UTILISATION_MAX=("utilisation", "max"),
        CC_LATE_MONTHS=("is_late", "sum"),
        CC_LATE_RATE=("is_late", "mean"),
        CC_DPD_MAX=("SK_DPD", "max"),
        CC_DPD_DEF_MAX=("SK_DPD_DEF", "max"),
        CC_MISSED_MINIMUM_RATE=("missed_minimum", "mean"),
        CC_ATM_DRAWINGS_MEAN=("AMT_DRAWINGS_ATM_CURRENT", "mean"))
    recent = card[card["MONTHS_BALANCE"] >= RECENT_MONTHS].groupby("SK_ID_CURR")
    out["CC_UTILISATION_MEAN_12M"] = recent["utilisation"].mean()
    out["CC_LATE_RATE_12M"] = recent["is_late"].mean()
    out["CC_DPD_DEF_MAX_12M"] = recent["SK_DPD_DEF"].max()
    out["CC_MISSED_MINIMUM_RATE_12M"] = recent["missed_minimum"].mean()

    latest = latest_rows(card)
    latest = latest[latest["MONTHS_BALANCE"] >= CURRENT_MONTHS].groupby("SK_ID_CURR")
    balance, limit = latest["AMT_BALANCE"].sum(), latest["AMT_CREDIT_LIMIT_ACTUAL"].sum()
    out["CC_BALANCE_NOW"] = balance
    out["CC_UTILISATION_NOW"] = ratio(balance.clip(lower=0), limit)
    return out


def add_table(df, table, flag):
    """Left-join a history table and record who has any history in it."""
    df = df.join(table, on="SK_ID_CURR")
    df[flag] = df["SK_ID_CURR"].isin(table.index).astype("int8")
    return df


def main():
    split = pd.read_csv(PROCESSED / "split.csv")
    dev_ids = set(split.loc[split["split"] == "dev", "SK_ID_CURR"])

    app = pd.read_csv(RAW / "application_train.csv")
    ids = set(app["SK_ID_CURR"])
    df, params = application_features(app, dev_ids)
    df = df.merge(split, on="SK_ID_CURR", how="left", validate="one_to_one")

    print("bureau...")
    bureau, balance = bureau_features(ids)
    df = add_table(df, bureau, "BUREAU_HAS_HISTORY")
    df = add_table(df, balance, "BB_HAS_HISTORY")
    print("previous applications...")
    df = add_table(df, previous_features(ids), "PREV_HAS_HISTORY")
    print("installments...")
    df = add_table(df, installments_features(ids), "INST_HAS_HISTORY")
    print("POS and cash...")
    df = add_table(df, pos_features(ids), "POS_HAS_HISTORY")
    print("credit cards...")
    df = add_table(df, card_features(ids), "CC_HAS_HISTORY")

    df = df.copy()  # many joins leave the frame fragmented
    df["BUREAU_DEBT_TO_INCOME"] = ratio(df["BUREAU_ACTIVE_DEBT_SUM"], df["AMT_INCOME_TOTAL"])
    df["NO_CREDIT_HISTORY"] = ((df["BUREAU_HAS_HISTORY"] == 0) & (df["PREV_HAS_HISTORY"] == 0)).astype("int8")

    assert len(df) == EXPECTED_APPLICANTS, f"expected {EXPECTED_APPLICANTS} rows, got {len(df)}"
    assert df["SK_ID_CURR"].is_unique, "duplicate applicants"
    assert df["split"].notna().all(), "applicant missing from split.csv"
    assert not np.isinf(df.select_dtypes("number")).any().any(), "infinite value in features"

    df.to_parquet(OUT, index=False)
    PARAMS.write_text(json.dumps(params, indent=2))
    print(f"wrote {OUT}: {df.shape[0]:,} rows, {df.shape[1]} columns")


if __name__ == "__main__":
    main()

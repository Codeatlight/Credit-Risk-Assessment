# Feature dictionary

`src/features.py` writes `data/processed/features.parquet`: one row per applicant (307,511), with the 122 original `application_train` columns, the `split` column and 104 new features. Checks are in [feature_sanity.md](feature_sanity.md).

## Ground rules

- **Missing means no information, not zero.** An applicant with no records in a table gets missing values for all of that table's features, because "no history" is different from "a clean history". Each table has a `*_HAS_HISTORY` flag.
- **`_12M` means the last 12 months before the application.** These are missing if the applicant had nothing in that window, and the flag still tells old history apart from no history.
- **Holdout:** the income cap is the only value fitted from data, and it uses dev rows only. It is saved in `data/processed/feature_params.json` (900,000 at the 99.9th percentile). Everything else is a summary of the applicant's own records.

## Application features

| Feature | Meaning |
| --- | --- |
| `DAYS_EMPLOYED` (changed) | The 365243 placeholder is now missing |
| `IS_PENSIONER_OR_UNEMPLOYED` | 1 if `DAYS_EMPLOYED` was the placeholder. These applicants default less, so the signal is kept |
| `CODE_GENDER` (changed) | `XNA` (4 rows) is now missing |
| `AMT_INCOME_TOTAL` (changed) | Capped at the dev 99.9th percentile |
| `CREDIT_TO_INCOME`, `ANNUITY_TO_INCOME` | Loan size and yearly payment, relative to capped income |
| `CREDIT_TO_GOODS` | Loan size relative to the price of the goods. Above 1 means borrowing more than the item costs |
| `ANNUITY_TO_CREDIT` | Share of the loan repaid each year, a stand-in for loan term |
| `INCOME_PER_PERSON` | Capped income divided by family size |
| `AGE_YEARS`, `EMPLOYED_YEARS`, `EMPLOYED_TO_AGE` | Age and employment in years, and the share of life spent employed |
| `EXT_SOURCE_MEAN`, `EXT_SOURCE_MISSING_COUNT` | Average of the available external scores, and how many are missing |
| `NO_CREDIT_HISTORY` | 1 if the applicant has no bureau and no previous Home Credit records |

## Credit bureau: `BUREAU_*`

Loans at other lenders. 85.7% of dev applicants have this history.

| Feature | Meaning |
| --- | --- |
| `BUREAU_CREDIT_COUNT`, `_ACTIVE_COUNT`, `_CLOSED_COUNT`, `_ACTIVE_SHARE` | Number of loans, and how many are still open |
| `BUREAU_BAD_DEBT_COUNT` | Loans marked `Sold` or `Bad debt` |
| `BUREAU_MICROLOAN_COUNT` | Microloans |
| `BUREAU_OPENED_COUNT_12M`, `_DAYS_SINCE_LAST_OPENED`, `_HISTORY_DAYS` | Recent borrowing, and length of history |
| `BUREAU_ACTIVE_DEBT_SUM`, `_ACTIVE_CREDIT_SUM` | Debt still owed, and the original size of open loans |
| `BUREAU_DEBT_TO_CREDIT`, `BUREAU_DEBT_TO_INCOME` | Debt owed relative to loan size and to income |
| `BUREAU_CARD_UTILISATION` | Debt on open credit cards relative to their limits |
| `BUREAU_OVERDUE_SUM`, `_MAX_OVERDUE_EVER`, `_MAX_DAYS_OVERDUE_NOW` | Amounts and days overdue |
| `BUREAU_PROLONG_COUNT` | Times a loan was extended |

Cleaning: non-main-currency amounts are excluded (they can't be added together), and negative debts are set to 0.

## Bureau monthly status: `BB_*`

Only 29.1% of dev applicants have a usable month, so most applicants are missing here. Status `C` (closed) and `X` (unknown) are not counted as reported months.

| Feature | Meaning |
| --- | --- |
| `BB_MONTHS_REPORTED`, `BB_LATE_MONTHS`, `BB_LATE_RATE` | Months with a known status, and how many were late |
| `BB_SEVERE_LATE_MONTHS`, `BB_WORST_STATUS` | Months 90+ days late, and the worst status (0 to 5) |
| `BB_MONTHS_SINCE_LAST_LATE` | Recency of lateness. Also missing if the applicant was never late |
| `BB_LATE_MONTHS_12M`, `BB_LATE_RATE_12M` | The same, last 12 months |

## Previous applications: `PREV_*`

Earlier applications to Home Credit. Rows the data description calls mistaken duplicates are dropped (`FLAG_LAST_APPL_PER_CONTRACT = N` or `NFLAG_LAST_APPL_IN_DAY = 0`).

| Feature | Meaning |
| --- | --- |
| `PREV_COUNT`, `_APPROVED_COUNT`, `_REFUSED_COUNT`, `_CANCELED_COUNT`, `_REFUSED_RATE` | Outcomes of past applications |
| `PREV_SCORE_REFUSED_COUNT` | Refusals with reason `SCO` or `SCOFR` |
| `PREV_APPROVED_COUNT_12M`, `_REFUSED_COUNT_12M`, `_REFUSED_RATE_12M` | The same, last 12 months |
| `PREV_DAYS_SINCE_LAST_REFUSAL`, `_LAST_APPROVAL` | Recency of each outcome |
| `PREV_APPROVED_CREDIT_MEAN`, `PREV_ASKED_VS_GRANTED_MEAN` | Size of approved loans, and amount asked for relative to amount granted |
| `PREV_DOWN_PAYMENT_RATE_MEAN`, `PREV_TERM_MEAN` | Average down payment rate and loan term |

## Instalment payments: `INST_*`

Each instalment on a past Home Credit loan. Part-payments are first added up, so one instalment paid in three parts counts once. All except the last row also have a `_12M` version.

| Feature | Meaning |
| --- | --- |
| `INST_COUNT` | Number of instalments due |
| `INST_LATE_COUNT`, `INST_LATE_RATE`, `INST_LATE_30_COUNT` | Instalments finished late, and more than 30 days late |
| `INST_DAYS_LATE_MAX`, `INST_DAYS_LATE_MEAN` | How late, with early or on-time counted as 0 |
| `INST_UNDERPAID_RATE` | Share of instalments paid under 99% of the amount due |
| `INST_PAID_TO_DUE` | Total paid relative to total due |
| `INST_LATE_RATE_RECENCY_WEIGHTED` | Late rate where a payment a year old counts half, two years old a quarter |

An instalment with no payment on record (2,905 raw rows) counts as unpaid until the application date, so one old unpaid instalment can give a very large `INST_DAYS_LATE_MAX`.

## POS and cash loans: `POS_*`

Monthly snapshots of past point-of-sale and cash loans. "Late" uses `SK_DPD_DEF`, which ignores very small debts.

| Feature | Meaning |
| --- | --- |
| `POS_MONTHS`, `POS_LOAN_COUNT` | Months of records and number of loans |
| `POS_LATE_MONTHS`, `POS_LATE_RATE`, `POS_LATE_MONTHS_12M`, `POS_LATE_RATE_12M` | Months late |
| `POS_DPD_MAX`, `POS_DPD_DEF_MAX`, `POS_DPD_DEF_MAX_12M` | Worst days past due |
| `POS_OPEN_COUNT`, `POS_COMPLETED_COUNT` | Loans open now (active and seen in the last 3 months) and completed |
| `POS_FUTURE_INSTALMENTS` | Instalments still to pay on open loans |

## Credit cards: `CC_*`

Monthly snapshots of Home Credit cards. Only 28.3% of dev applicants have this history, so read `CC_HAS_HISTORY` alongside these.

| Feature | Meaning |
| --- | --- |
| `CC_MONTHS`, `CC_CARD_COUNT` | Months of records and number of cards |
| `CC_UTILISATION_MEAN`, `_MAX`, `_MEAN_12M`, `_NOW` | Balance relative to limit, overall, recent, and in the latest month (last 3 months only) |
| `CC_BALANCE_NOW` | Balance on cards seen in the last 3 months |
| `CC_LATE_MONTHS`, `CC_LATE_RATE`, `CC_LATE_RATE_12M` | Months late |
| `CC_DPD_MAX`, `CC_DPD_DEF_MAX`, `CC_DPD_DEF_MAX_12M` | Worst days past due |
| `CC_MISSED_MINIMUM_RATE`, `_12M` | Share of months with a minimum due where less than the minimum was paid |
| `CC_ATM_DRAWINGS_MEAN` | Average monthly cash withdrawn at ATMs |

## Leakage review

**Dates.** All dates count back from the application. The checks in the sanity report show that repayment records, POS and card snapshots and previous decisions all stop at day or month -1, before the application.

**Removed or left out**

| Field | Problem | Action |
| --- | --- | --- |
| `DAYS_CREDIT_UPDATE` above 0 (17 bureau rows) | Record updated after the application, so its balances may reflect later events | Rows dropped |
| `bureau_balance` month 0 | The application month itself. Every other table stops at -1 | Rows dropped |
| `DAYS_LAST_DUE`, `DAYS_TERMINATION`, `DAYS_FIRST_DUE`, `DAYS_FIRST_DRAWING` | Describe how a past loan played out, and use the 365243 placeholder | Not used. No value after the application was found, so this is caution |
| `DAYS_ENDDATE_FACT`, `DAYS_CREDIT_ENDDATE` | Contain impossible dates (down to about -42,000 days), and the planned end date can be in the future | Not used |

**Kept, and worth knowing**

| Field | Note |
| --- | --- |
| `EXT_SOURCE_1/2/3` | Source and date are undocumented, so they could include information from after the application. They are the strongest columns, so results are reported with and without them |
| `OBS_*_SOCIAL_CIRCLE`, `DEF_*_SOCIAL_CIRCLE` | Defaults among people around the applicant, with no stated measurement date |
| `AMT_REQ_CREDIT_BUREAU_*` | Bureau enquiries before the application. The nearest window could include the lender's own check for this loan |
| Previous applications in the final week | In dev, 247 of 6,088 match the current loan amount exactly. The 125 refused ones look like repeat attempts. The 102 approved ones have no repayment rows, so they may be the current loan's own record. That could add 1 to `PREV_APPROVED_COUNT` for about 0.04% of applicants, and it carries no repayment information |

**Fairness.** `CODE_GENDER`, `DAYS_BIRTH` and `CNT_CHILDREN` are sensitive, and so are the derived `AGE_YEARS` and `EMPLOYED_TO_AGE`, which carry age. `IS_PENSIONER_OR_UNEMPLOYED` is also tied closely to age. Step 8 needs to treat all of these together.

## Known limits for later steps

- Some ratios have extreme values from tiny denominators, such as `BUREAU_CARD_UTILISATION` (up to 569,610) and `BUREAU_DEBT_TO_CREDIT` (up to 382). They are left as they are because the scorecard bins them. Any model that uses them unbinned must cap them on dev rows first.
- `ORGANIZATION_TYPE = XNA` is left as a category. It marks almost the same pensioner group as the flag.
- Single-feature AUCs are measured only where a feature has a value, so low-coverage features such as `CC_UTILISATION_NOW` (21% coverage) can't be compared directly with full-coverage ones.

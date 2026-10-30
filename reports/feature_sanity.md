# Feature sanity report

Dev set only. Written by `python -m src.feature_report`.

## Size

- Feature table: 227 columns, of which 104 are new.
- Dev rows: 246,008, duplicate applicants: 0, default rate: 8.07%.

## Who has each history

| flag | share_of_applicants |
| --- | --- |
| BUREAU_HAS_HISTORY | 0.857 |
| BB_HAS_HISTORY | 0.291 |
| PREV_HAS_HISTORY | 0.946 |
| INST_HAS_HISTORY | 0.948 |
| POS_HAS_HISTORY | 0.941 |
| CC_HAS_HISTORY | 0.283 |

## Missing rates of new features

- 14 of 104 have no missing values; 26 are over 50% missing.

Most missing:

| feature | missing |
| --- | --- |
| BB_MONTHS_SINCE_LAST_LATE | 0.901 |
| CC_MISSED_MINIMUM_RATE_12M | 0.878 |
| CC_MISSED_MINIMUM_RATE | 0.807 |
| CC_ATM_DRAWINGS_MEAN | 0.801 |
| CC_UTILISATION_NOW | 0.789 |
| CC_UTILISATION_MEAN_12M | 0.767 |
| BB_LATE_RATE_12M | 0.764 |
| BB_LATE_MONTHS_12M | 0.764 |
| CC_BALANCE_NOW | 0.722 |
| CC_UTILISATION_MAX | 0.72 |
| CC_UTILISATION_MEAN | 0.72 |
| CC_LATE_RATE_12M | 0.717 |

## Single-feature AUC

AUC of one column alone, flipped so it is always 0.5 or above, measured only on rows where the column has a value. Coverage is the share of dev rows that have a value, so a low-coverage feature is not directly comparable with a full-coverage one.

Top new features:

| feature | auc | coverage |
| --- | --- | --- |
| EXT_SOURCE_MEAN | 0.7165 | 0.999 |
| CC_UTILISATION_NOW | 0.6522 | 0.211 |
| CC_UTILISATION_MEAN_12M | 0.6391 | 0.233 |
| CC_UTILISATION_MEAN | 0.6307 | 0.28 |
| CC_UTILISATION_MAX | 0.6108 | 0.28 |
| BUREAU_CARD_UTILISATION | 0.6063 | 0.456 |
| CC_BALANCE_NOW | 0.6038 | 0.278 |
| AGE_YEARS | 0.5843 | 1.0 |
| BUREAU_ACTIVE_SHARE | 0.5835 | 0.857 |
| EMPLOYED_YEARS | 0.5823 | 0.821 |
| BUREAU_DAYS_SINCE_LAST_OPENED | 0.5815 | 0.857 |
| CC_ATM_DRAWINGS_MEAN | 0.581 | 0.199 |
| BUREAU_OPENED_COUNT_12M | 0.5802 | 0.857 |
| BUREAU_DEBT_TO_CREDIT | 0.5795 | 0.696 |
| INST_DAYS_LATE_MAX_12M | 0.5794 | 0.707 |

Top new features, leaving out EXT_SOURCE ones:

| feature | auc | coverage |
| --- | --- | --- |
| CC_UTILISATION_NOW | 0.6522 | 0.211 |
| CC_UTILISATION_MEAN_12M | 0.6391 | 0.233 |
| CC_UTILISATION_MEAN | 0.6307 | 0.28 |
| CC_UTILISATION_MAX | 0.6108 | 0.28 |
| BUREAU_CARD_UTILISATION | 0.6063 | 0.456 |
| CC_BALANCE_NOW | 0.6038 | 0.278 |
| AGE_YEARS | 0.5843 | 1.0 |
| BUREAU_ACTIVE_SHARE | 0.5835 | 0.857 |
| EMPLOYED_YEARS | 0.5823 | 0.821 |
| BUREAU_DAYS_SINCE_LAST_OPENED | 0.5815 | 0.857 |

Best existing columns:

| feature | auc | coverage |
| --- | --- | --- |
| EXT_SOURCE_3 | 0.6797 | 0.802 |
| EXT_SOURCE_1 | 0.6659 | 0.437 |
| EXT_SOURCE_2 | 0.6553 | 0.998 |
| DAYS_BIRTH | 0.5843 | 1.0 |
| DAYS_EMPLOYED | 0.5823 | 0.821 |
| OWN_CAR_AGE | 0.56 | 0.34 |
| DAYS_LAST_PHONE_CHANGE | 0.5549 | 1.0 |
| DAYS_ID_PUBLISH | 0.5537 | 1.0 |
| FLOORSMAX_AVG | 0.5502 | 0.503 |
| FLOORSMAX_MEDI | 0.5499 | 0.503 |

Features above the 0.72 suspicion line: none.

## Date checks for leakage

`DAYS_*` and `MONTHS_*` count back from the application, so above 0 means after it.

| table | field | latest | rows_after_application | rows_at_0 |
| --- | --- | --- | --- | --- |
| bureau | DAYS_CREDIT | 0.0 | 0 | 2 |
| bureau | DAYS_ENDDATE_FACT | 0.0 | 0 | 53 |
| bureau | DAYS_CREDIT_UPDATE | 372.0 | 15 | 372 |
| bureau_balance | MONTHS_BALANCE | 0.0 | 0 | 275902 |
| previous_application | DAYS_DECISION | -1.0 | 0 | 0 |
| previous_application | DAYS_FIRST_DUE | -2.0 | 0 | 0 |
| previous_application | DAYS_LAST_DUE | -2.0 | 0 | 0 |
| previous_application | DAYS_TERMINATION | -2.0 | 0 | 0 |
| installments_payments | DAYS_INSTALMENT | -1.0 | 0 | 0 |
| installments_payments | DAYS_ENTRY_PAYMENT | -1.0 | 0 | 0 |
| POS_CASH_balance | MONTHS_BALANCE | -1.0 | 0 | 0 |
| credit_card_balance | MONTHS_BALANCE | -1.0 | 0 | 0 |

## Does the current loan appear in its own history?

| table | records_in_last_7_days | same_amount_as_current_loan |
| --- | --- | --- |
| bureau | 534 | 3 |
| previous_application | 6088 | 247 |

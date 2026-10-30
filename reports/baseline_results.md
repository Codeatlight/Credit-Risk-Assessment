# Baseline results

Logistic regression on 246,008 dev rows with stratified 5-fold cross-validation. Written by `python -m src.baseline`. The holdout was not used.

| model | features | auc | gini | ks | brier |
| --- | --- | --- | --- | --- | --- |
| Without EXT_SOURCE | 12 | 0.6906 ± 0.0020 | 0.3812 | 0.2807 | 0.0711 |
| With EXT_SOURCE | 15 | 0.7514 ± 0.0022 | 0.5029 | 0.3801 | 0.0683 |

Sanity check: with shuffled labels the AUC is 0.5004, where 0.5 means no signal.

## Without EXT_SOURCE

Calibration on predictions from unseen folds:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.0233 | 0.0231 |
| 2 | 0.0346 | 0.034 |
| 3 | 0.043 | 0.0421 |
| 4 | 0.0514 | 0.0494 |
| 5 | 0.0604 | 0.06 |
| 6 | 0.0707 | 0.0705 |
| 7 | 0.0836 | 0.0842 |
| 8 | 0.1008 | 0.1029 |
| 9 | 0.1281 | 0.133 |
| 10 | 0.2114 | 0.2082 |

Coefficients from a fit on all dev rows. Positive means higher risk:

| feature | coefficient |
| --- | --- |
| EMPLOYED_YEARS | -0.265 |
| BUREAU_ACTIVE_SHARE | 0.226 |
| BUREAU_OPENED_COUNT_12M | 0.224 |
| CREDIT_TO_GOODS | 0.204 |
| EMPLOYED_YEARS (missing) | -0.2 |
| CC_UTILISATION_MEAN_12M | 0.196 |
| PREV_REFUSED_RATE | 0.182 |
| BUREAU_DEBT_TO_CREDIT | 0.149 |
| INST_LATE_RATE | 0.131 |
| BUREAU_DEBT_TO_CREDIT (missing) | 0.12 |
| ANNUITY_TO_INCOME | 0.119 |
| INST_DAYS_LATE_MAX_12M | 0.114 |
| CC_UTILISATION_MEAN_12M (missing) | 0.099 |
| INST_DAYS_LATE_MAX_12M (missing) | 0.051 |
| INST_LATE_RATE (missing) | -0.035 |
| POS_LATE_RATE | 0.03 |
| ANNUITY_TO_CREDIT | 0.024 |
| BUREAU_OPENED_COUNT_12M (missing) | 0.021 |
| BUREAU_ACTIVE_SHARE (missing) | 0.021 |
| ANNUITY_TO_INCOME (missing) | -0.013 |
| ANNUITY_TO_CREDIT (missing) | -0.013 |
| PREV_REFUSED_RATE (missing) | 0.01 |
| POS_LATE_RATE (missing) | 0.003 |
| CREDIT_TO_GOODS (missing) | 0.001 |

## With EXT_SOURCE

Calibration on predictions from unseen folds:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.0129 | 0.0131 |
| 2 | 0.0222 | 0.0242 |
| 3 | 0.0304 | 0.0282 |
| 4 | 0.0393 | 0.0376 |
| 5 | 0.0495 | 0.0465 |
| 6 | 0.062 | 0.059 |
| 7 | 0.0786 | 0.0779 |
| 8 | 0.1026 | 0.1093 |
| 9 | 0.1436 | 0.1472 |
| 10 | 0.2664 | 0.2643 |

Coefficients from a fit on all dev rows. Positive means higher risk:

| feature | coefficient |
| --- | --- |
| EXT_SOURCE_2 | -0.412 |
| EXT_SOURCE_3 | -0.39 |
| EXT_SOURCE_1 | -0.243 |
| EMPLOYED_YEARS | -0.17 |
| CREDIT_TO_GOODS | 0.166 |
| CC_UTILISATION_MEAN_12M | 0.166 |
| EMPLOYED_YEARS (missing) | -0.163 |
| EXT_SOURCE_1 (missing) | 0.159 |
| PREV_REFUSED_RATE | 0.131 |
| BUREAU_DEBT_TO_CREDIT (missing) | 0.124 |
| ANNUITY_TO_INCOME | 0.114 |
| BUREAU_ACTIVE_SHARE | 0.112 |
| INST_LATE_RATE | 0.108 |
| INST_DAYS_LATE_MAX_12M | 0.095 |
| BUREAU_DEBT_TO_CREDIT | 0.093 |
| BUREAU_OPENED_COUNT_12M | 0.072 |
| INST_DAYS_LATE_MAX_12M (missing) | 0.07 |
| CC_UTILISATION_MEAN_12M (missing) | 0.069 |
| INST_LATE_RATE (missing) | -0.041 |
| POS_LATE_RATE | 0.026 |
| BUREAU_OPENED_COUNT_12M (missing) | 0.026 |
| BUREAU_ACTIVE_SHARE (missing) | 0.026 |
| ANNUITY_TO_CREDIT | -0.017 |
| EXT_SOURCE_3 (missing) | 0.017 |
| EXT_SOURCE_2 (missing) | 0.015 |
| ANNUITY_TO_INCOME (missing) | -0.013 |
| ANNUITY_TO_CREDIT (missing) | -0.013 |
| PREV_REFUSED_RATE (missing) | 0.011 |
| POS_LATE_RATE (missing) | -0.002 |
| CREDIT_TO_GOODS (missing) | 0.0 |

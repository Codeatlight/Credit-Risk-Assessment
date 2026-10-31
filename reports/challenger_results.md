# Challenger results

LightGBM against the scorecard on 246,008 dev rows, with the same 5 folds and candidate features. Settings are fixed, not tuned. Written by `python -m src.challenger`. The holdout was not used.

| model | features | auc | gini | ks | brier |
| --- | --- | --- | --- | --- | --- |
| Scorecard, Without EXT_SOURCE | 15 | 0.6995 ± 0.0031 | 0.3990 | 0.2962 | 0.0709 |
| LightGBM, Without EXT_SOURCE | 109 | 0.7579 ± 0.0015 | 0.5159 | 0.3848 | 0.0680 |
| Scorecard, With EXT_SOURCE | 15 | 0.7494 ± 0.0019 | 0.4988 | 0.3764 | 0.0686 |
| LightGBM, With EXT_SOURCE | 113 | 0.7847 ± 0.0010 | 0.5693 | 0.4311 | 0.0662 |

AUC and KS gained over the scorecard, fold by fold:

| comparison | auc_gain | fold_gains | ks_gain |
| --- | --- | --- | --- |
| Without EXT_SOURCE | 0.0584 | 0.0544, 0.0566, 0.0617, 0.0565, 0.0630 | 0.0886 |
| With EXT_SOURCE | 0.0353 | 0.0355, 0.0328, 0.0379, 0.0332, 0.0371 | 0.0547 |

Sanity check: with shuffled labels the AUC is 0.4959, where 0.5 means no signal.

## LightGBM, Without EXT_SOURCE

Trees per fold: [1028, 931, 587, 606, 935]. The final fit on all dev rows has 817 trees, 25,327 leaves and uses 102 of 109 features.

Calibration on predictions from unseen folds:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.0128 | 0.0119 |
| 2 | 0.0211 | 0.019 |
| 3 | 0.0286 | 0.0267 |
| 4 | 0.0367 | 0.0359 |
| 5 | 0.0464 | 0.0496 |
| 6 | 0.0585 | 0.0605 |
| 7 | 0.075 | 0.0801 |
| 8 | 0.0995 | 0.1072 |
| 9 | 0.1426 | 0.1464 |
| 10 | 0.2762 | 0.2699 |

Features doing the most work:

| feature | share_of_gain |
| --- | --- |
| ORGANIZATION_TYPE | 0.0764 |
| ANNUITY_TO_CREDIT | 0.0542 |
| EMPLOYED_YEARS | 0.0485 |
| OCCUPATION_TYPE | 0.0384 |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.0374 |
| CREDIT_TO_GOODS | 0.032 |
| BUREAU_CARD_UTILISATION | 0.0289 |
| BUREAU_DAYS_SINCE_LAST_OPENED | 0.0287 |
| CC_UTILISATION_NOW | 0.0269 |
| REGION_RATING_CLIENT_W_CITY | 0.0251 |
| BUREAU_HISTORY_DAYS | 0.0243 |
| DAYS_LAST_PHONE_CHANGE | 0.0242 |
| BUREAU_ACTIVE_SHARE | 0.0224 |
| PREV_APPROVED_CREDIT_MEAN | 0.0223 |
| BUREAU_DEBT_TO_CREDIT | 0.021 |

## LightGBM, With EXT_SOURCE

Trees per fold: [649, 1394, 650, 808, 775]. The final fit on all dev rows has 855 trees, 26,505 leaves and uses 106 of 113 features.

Calibration on predictions from unseen folds:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.0099 | 0.009 |
| 2 | 0.0168 | 0.0158 |
| 3 | 0.0233 | 0.0221 |
| 4 | 0.0308 | 0.0307 |
| 5 | 0.0401 | 0.0396 |
| 6 | 0.0525 | 0.0556 |
| 7 | 0.0701 | 0.0761 |
| 8 | 0.0976 | 0.1059 |
| 9 | 0.1484 | 0.1548 |
| 10 | 0.3067 | 0.2978 |

Features doing the most work:

| feature | share_of_gain |
| --- | --- |
| EXT_SOURCE_2 | 0.1309 |
| EXT_SOURCE_3 | 0.1294 |
| ORGANIZATION_TYPE | 0.0721 |
| EXT_SOURCE_1 | 0.0478 |
| ANNUITY_TO_CREDIT | 0.0342 |
| EMPLOYED_YEARS | 0.0312 |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.0277 |
| OCCUPATION_TYPE | 0.0267 |
| CREDIT_TO_GOODS | 0.0235 |
| CC_UTILISATION_NOW | 0.0189 |
| AMT_CREDIT | 0.0175 |
| BUREAU_DEBT_TO_CREDIT | 0.0164 |
| PREV_TERM_MEAN | 0.0156 |
| PREV_APPROVED_CREDIT_MEAN | 0.0154 |
| BUREAU_CARD_UTILISATION | 0.0153 |

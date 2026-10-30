# Scorecard results

246,008 dev rows, stratified 5-fold cross-validation. Bins, feature selection and the model are refitted inside each fold. Written by `python -m src.scorecard`. The holdout was not used.

| model | features | auc | gini | ks | brier |
| --- | --- | --- | --- | --- | --- |
| Baseline, Without EXT_SOURCE | 12 | 0.6906 ± 0.0020 | 0.3812 | 0.2807 | 0.0711 |
| Scorecard, Without EXT_SOURCE | 15 | 0.6995 ± 0.0031 | 0.3990 | 0.2962 | 0.0709 |
| Baseline, With EXT_SOURCE | 15 | 0.7514 ± 0.0022 | 0.5029 | 0.3801 | 0.0683 |
| Scorecard, With EXT_SOURCE | 15 | 0.7494 ± 0.0019 | 0.4988 | 0.3764 | 0.0686 |

Sanity check: with shuffled labels the AUC is 0.5000, where 0.5 means no signal.

Score scale: 700 means 50 non-defaulters for each defaulter, and every 50 points doubles those odds. Higher is safer.

## Scorecard, Without EXT_SOURCE

Base points: 593. Add one row per feature to get the score. The rounded points stay within 4.0 points of the exact model score. Scores on dev rows run from 348 to 747.

| feature | iv | monotonic | folds_chosen |
| --- | --- | --- | --- |
| EMPLOYED_YEARS | 0.1119 | True | 5 of 5 |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.0922 | True | 5 of 5 |
| BUREAU_ACTIVE_SHARE | 0.0888 | True | 5 of 5 |
| BUREAU_OPENED_COUNT_12M | 0.0865 | True | 4 of 5 |
| INST_DAYS_LATE_MAX_12M | 0.0807 | True | 5 of 5 |
| BUREAU_HISTORY_DAYS | 0.0758 | True | 5 of 5 |
| OCCUPATION_TYPE | 0.0754 | True | 5 of 5 |
| BUREAU_CARD_UTILISATION | 0.0721 | True | 5 of 5 |
| CC_UTILISATION_NOW | 0.072 | True | 5 of 5 |
| CREDIT_TO_GOODS | 0.0713 | True | 5 of 5 |
| PREV_REFUSED_RATE | 0.0704 | True | 5 of 5 |
| PREV_DAYS_SINCE_LAST_REFUSAL | 0.0649 | True | 5 of 5 |
| ORGANIZATION_TYPE | 0.0596 | True | 5 of 5 |
| CC_UTILISATION_MEAN | 0.0592 | True | 5 of 5 |
| BUREAU_DEBT_TO_CREDIT | 0.0568 | True | 4 of 5 |

Chosen in some folds but not in the final fit: ['BUREAU_DAYS_SINCE_LAST_OPENED', 'NAME_INCOME_TYPE'].

Default rate by score band, on predictions from unseen folds:

| score_from | applicants | default_rate |
| --- | --- | --- |
| 350 | 30 | 0.7333 |
| 400 | 627 | 0.3876 |
| 450 | 5754 | 0.2775 |
| 500 | 26701 | 0.1739 |
| 550 | 67801 | 0.1026 |
| 600 | 88918 | 0.0548 |
| 650 | 49243 | 0.0282 |
| 700 | 6931 | 0.0201 |
| 750 | 3 | 0.0 |

Calibration on predictions from unseen folds:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.0219 | 0.0217 |
| 2 | 0.0318 | 0.0306 |
| 3 | 0.0401 | 0.0387 |
| 4 | 0.0484 | 0.0473 |
| 5 | 0.058 | 0.0574 |
| 6 | 0.0692 | 0.0726 |
| 7 | 0.0833 | 0.087 |
| 8 | 0.102 | 0.1066 |
| 9 | 0.1327 | 0.1324 |
| 10 | 0.2199 | 0.2131 |

Points:

| feature | bin | points | woe | rows | default_rate |
| --- | --- | --- | --- | --- | --- |
| EMPLOYED_YEARS | up to 2.608 | -15 | -0.364 | 62864 | 0.1122 |
| EMPLOYED_YEARS | 2.608 to 4.888 | -9 | -0.207 | 44527 | 0.0974 |
| EMPLOYED_YEARS | 4.888 to 6.646 | 0 | 0.001 | 22871 | 0.0807 |
| EMPLOYED_YEARS | 6.646 to 10.78 | 7 | 0.163 | 35471 | 0.0694 |
| EMPLOYED_YEARS | above 10.78 | 22 | 0.52 | 36132 | 0.0496 |
| EMPLOYED_YEARS | Missing | 18 | 0.437 | 44143 | 0.0537 |
| INST_LATE_RATE_RECENCY_WEIGHTED | up to 0.03761 | 10 | 0.225 | 147494 | 0.0656 |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.03761 to 0.07065 | -3 | -0.069 | 17833 | 0.086 |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.07065 to 0.2857 | -14 | -0.306 | 47519 | 0.1065 |
| INST_LATE_RATE_RECENCY_WEIGHTED | above 0.2857 | -28 | -0.604 | 20476 | 0.1385 |
| INST_LATE_RATE_RECENCY_WEIGHTED | Missing | 15 | 0.322 | 12686 | 0.0598 |
| BUREAU_ACTIVE_SHARE | up to 0.291 | 11 | 0.4 | 79780 | 0.0556 |
| BUREAU_ACTIVE_SHARE | 0.291 to 0.3455 | 6 | 0.227 | 21519 | 0.0654 |
| BUREAU_ACTIVE_SHARE | 0.3455 to 0.5093 | 0 | 0.007 | 51017 | 0.0802 |
| BUREAU_ACTIVE_SHARE | 0.5093 to 0.6742 | -7 | -0.234 | 22540 | 0.0999 |
| BUREAU_ACTIVE_SHARE | above 0.6742 | -11 | -0.385 | 35907 | 0.1143 |
| BUREAU_ACTIVE_SHARE | Missing | -7 | -0.249 | 35245 | 0.1012 |
| BUREAU_OPENED_COUNT_12M | up to 0.5 | 16 | 0.353 | 89218 | 0.0581 |
| BUREAU_OPENED_COUNT_12M | 0.5 to 1.5 | 2 | 0.043 | 65401 | 0.0776 |
| BUREAU_OPENED_COUNT_12M | 1.5 to 2.5 | -5 | -0.122 | 32366 | 0.0902 |
| BUREAU_OPENED_COUNT_12M | above 2.5 | -24 | -0.539 | 23778 | 0.1308 |
| BUREAU_OPENED_COUNT_12M | Missing | -11 | -0.249 | 35245 | 0.1012 |
| INST_DAYS_LATE_MAX_12M | up to 0.5 | 5 | 0.204 | 123945 | 0.0668 |
| INST_DAYS_LATE_MAX_12M | 0.5 to 2.5 | -4 | -0.161 | 17715 | 0.0935 |
| INST_DAYS_LATE_MAX_12M | 2.5 to 6.5 | -9 | -0.364 | 19090 | 0.1122 |
| INST_DAYS_LATE_MAX_12M | above 6.5 | -20 | -0.796 | 13117 | 0.1629 |
| INST_DAYS_LATE_MAX_12M | Missing | 1 | 0.034 | 72141 | 0.0782 |
| BUREAU_HISTORY_DAYS | up to 337.5 | -16 | -0.572 | 12444 | 0.1347 |
| BUREAU_HISTORY_DAYS | 337.5 to 582.5 | -10 | -0.348 | 12970 | 0.1106 |
| BUREAU_HISTORY_DAYS | 582.5 to 1064 | -5 | -0.175 | 29196 | 0.0947 |
| BUREAU_HISTORY_DAYS | 1064 to 1756 | 1 | 0.028 | 46799 | 0.0787 |
| BUREAU_HISTORY_DAYS | above 1756 | 8 | 0.292 | 109354 | 0.0616 |
| BUREAU_HISTORY_DAYS | Missing | -7 | -0.249 | 35245 | 0.1012 |
| OCCUPATION_TYPE | Missing | 10 | 0.235 | 76940 | 0.0649 |
| OCCUPATION_TYPE | Laborers | -13 | -0.292 | 44259 | 0.1052 |
| OCCUPATION_TYPE | Sales staff | -8 | -0.19 | 25606 | 0.096 |
| OCCUPATION_TYPE | Core staff | 11 | 0.253 | 22093 | 0.0638 |
| OCCUPATION_TYPE | Managers | 12 | 0.28 | 17096 | 0.0622 |
| OCCUPATION_TYPE | Drivers | -16 | -0.368 | 14944 | 0.1126 |
| OCCUPATION_TYPE | High skill tech staff | 12 | 0.27 | 9093 | 0.0628 |
| OCCUPATION_TYPE | Accountants | 26 | 0.592 | 7882 | 0.0463 |
| OCCUPATION_TYPE | Medicine staff | 7 | 0.156 | 6871 | 0.0699 |
| OCCUPATION_TYPE | Security staff | -14 | -0.31 | 5372 | 0.1069 |
| OCCUPATION_TYPE | Cooking staff | -13 | -0.291 | 4767 | 0.1051 |
| OCCUPATION_TYPE | Cleaning staff | -8 | -0.184 | 3741 | 0.0954 |
| OCCUPATION_TYPE | Rare or new | -11 | -0.251 | 7344 | 0.1014 |
| BUREAU_CARD_UTILISATION | up to 0.3041 | 13 | 0.336 | 49157 | 0.0591 |
| BUREAU_CARD_UTILISATION | 0.3041 to 0.5657 | 0 | 0.008 | 12550 | 0.0801 |
| BUREAU_CARD_UTILISATION | 0.5657 to 0.7738 | -5 | -0.127 | 12339 | 0.0906 |
| BUREAU_CARD_UTILISATION | 0.7738 to 0.97 | -12 | -0.328 | 23988 | 0.1087 |
| BUREAU_CARD_UTILISATION | above 0.97 | -26 | -0.693 | 14163 | 0.1493 |
| BUREAU_CARD_UTILISATION | Missing | 3 | 0.072 | 133811 | 0.0756 |
| CC_UTILISATION_NOW | up to 0.8713 | 8 | 0.281 | 37709 | 0.0622 |
| CC_UTILISATION_NOW | above 0.8713 | -25 | -0.85 | 14317 | 0.1705 |
| CC_UTILISATION_NOW | Missing | 1 | 0.041 | 193982 | 0.0777 |
| CREDIT_TO_GOODS | up to 1.158 | 11 | 0.205 | 157862 | 0.0667 |
| CREDIT_TO_GOODS | 1.158 to 1.211 | -7 | -0.126 | 36400 | 0.0906 |
| CREDIT_TO_GOODS | 1.211 to 1.317 | -17 | -0.312 | 28577 | 0.1071 |
| CREDIT_TO_GOODS | above 1.317 | -28 | -0.518 | 22948 | 0.1285 |
| CREDIT_TO_GOODS | Missing | 0 | 0.0 | 221 | 0.0769 |
| PREV_REFUSED_RATE | up to 0.06066 | 5 | 0.148 | 153822 | 0.0704 |
| PREV_REFUSED_RATE | 0.06066 to 0.155 | 3 | 0.094 | 13350 | 0.074 |
| PREV_REFUSED_RATE | 0.155 to 0.2795 | -3 | -0.092 | 25386 | 0.0878 |
| PREV_REFUSED_RATE | 0.2795 to 0.4361 | -11 | -0.328 | 21314 | 0.1087 |
| PREV_REFUSED_RATE | above 0.4361 | -21 | -0.638 | 18927 | 0.1425 |
| PREV_REFUSED_RATE | Missing | 11 | 0.315 | 13209 | 0.0602 |
| PREV_DAYS_SINCE_LAST_REFUSAL | up to 235.5 | -12 | -0.506 | 22972 | 0.1272 |
| PREV_DAYS_SINCE_LAST_REFUSAL | 235.5 to 486.5 | -8 | -0.344 | 22230 | 0.1103 |
| PREV_DAYS_SINCE_LAST_REFUSAL | 486.5 to 958.5 | -7 | -0.287 | 13674 | 0.1047 |
| PREV_DAYS_SINCE_LAST_REFUSAL | above 958.5 | 4 | 0.143 | 20278 | 0.0707 |
| PREV_DAYS_SINCE_LAST_REFUSAL | Missing | 4 | 0.16 | 166854 | 0.0697 |
| ORGANIZATION_TYPE | Business Entity Type 3 | -3 | -0.151 | 54436 | 0.0927 |
| ORGANIZATION_TYPE | XNA | 8 | 0.437 | 44143 | 0.0537 |
| ORGANIZATION_TYPE | Self-employed | -5 | -0.258 | 30572 | 0.1021 |
| ORGANIZATION_TYPE | Other | 1 | 0.081 | 13307 | 0.0749 |
| ORGANIZATION_TYPE | Medicine | 3 | 0.194 | 8985 | 0.0674 |
| ORGANIZATION_TYPE | Business Entity Type 2 | -1 | -0.074 | 8431 | 0.0863 |
| ORGANIZATION_TYPE | Government | 3 | 0.174 | 8341 | 0.0687 |
| ORGANIZATION_TYPE | School | 6 | 0.348 | 7179 | 0.0584 |
| ORGANIZATION_TYPE | Trade: type 7 | -3 | -0.171 | 6264 | 0.0943 |
| ORGANIZATION_TYPE | Kindergarten | 2 | 0.133 | 5552 | 0.0713 |
| ORGANIZATION_TYPE | Construction | -8 | -0.435 | 5399 | 0.1195 |
| ORGANIZATION_TYPE | Business Entity Type 1 | 0 | 0.002 | 4820 | 0.0805 |
| ORGANIZATION_TYPE | Transport: type 4 | -2 | -0.131 | 4311 | 0.0909 |
| ORGANIZATION_TYPE | Trade: type 3 | -5 | -0.26 | 2800 | 0.1021 |
| ORGANIZATION_TYPE | Industry: type 9 | 4 | 0.206 | 2720 | 0.0665 |
| ORGANIZATION_TYPE | Industry: type 3 | -6 | -0.321 | 2650 | 0.1079 |
| ORGANIZATION_TYPE | Security | -5 | -0.292 | 2607 | 0.1051 |
| ORGANIZATION_TYPE | Rare or new | 1 | 0.06 | 33491 | 0.0764 |
| CC_UTILISATION_MEAN | up to 0.1178 | 8 | 0.444 | 27725 | 0.0533 |
| CC_UTILISATION_MEAN | 0.1178 to 0.5502 | 0 | 0.01 | 22116 | 0.08 |
| CC_UTILISATION_MEAN | above 0.5502 | -12 | -0.63 | 19138 | 0.1415 |
| CC_UTILISATION_MEAN | Missing | 1 | 0.03 | 177029 | 0.0785 |
| BUREAU_DEBT_TO_CREDIT | up to 0.0001931 | 10 | 0.377 | 24450 | 0.0568 |
| BUREAU_DEBT_TO_CREDIT | 0.0001931 to 0.5424 | 5 | 0.2 | 55243 | 0.0671 |
| BUREAU_DEBT_TO_CREDIT | 0.5424 to 0.7609 | 1 | 0.04 | 36622 | 0.0778 |
| BUREAU_DEBT_TO_CREDIT | 0.7609 to 0.8488 | -5 | -0.179 | 17560 | 0.095 |
| BUREAU_DEBT_TO_CREDIT | above 0.8488 | -11 | -0.428 | 37390 | 0.1187 |
| BUREAU_DEBT_TO_CREDIT | Missing | 1 | 0.041 | 74743 | 0.0777 |

## Scorecard, With EXT_SOURCE

Base points: 593. Add one row per feature to get the score. The rounded points stay within 4.0 points of the exact model score. Scores on dev rows run from 304 to 813.

| feature | iv | monotonic | folds_chosen |
| --- | --- | --- | --- |
| EXT_SOURCE_3 | 0.3256 | True | 5 of 5 |
| EXT_SOURCE_2 | 0.2948 | True | 5 of 5 |
| EXT_SOURCE_1 | 0.1471 | True | 5 of 5 |
| EMPLOYED_YEARS | 0.1119 | True | 5 of 5 |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.0922 | True | 5 of 5 |
| BUREAU_ACTIVE_SHARE | 0.0888 | True | 5 of 5 |
| BUREAU_OPENED_COUNT_12M | 0.0865 | True | 4 of 5 |
| INST_DAYS_LATE_MAX_12M | 0.0807 | True | 5 of 5 |
| BUREAU_HISTORY_DAYS | 0.0758 | True | 5 of 5 |
| OCCUPATION_TYPE | 0.0754 | True | 5 of 5 |
| BUREAU_CARD_UTILISATION | 0.0721 | True | 5 of 5 |
| CC_UTILISATION_NOW | 0.072 | True | 5 of 5 |
| CREDIT_TO_GOODS | 0.0713 | True | 5 of 5 |
| PREV_REFUSED_RATE | 0.0704 | True | 5 of 5 |
| PREV_DAYS_SINCE_LAST_REFUSAL | 0.0649 | True | 5 of 5 |

Chosen in some folds but not in the final fit: ['BUREAU_DAYS_SINCE_LAST_OPENED'].

Default rate by score band, on predictions from unseen folds:

| score_from | applicants | default_rate |
| --- | --- | --- |
| 300 | 22 | 0.6364 |
| 350 | 285 | 0.5018 |
| 400 | 2090 | 0.3981 |
| 450 | 9309 | 0.293 |
| 500 | 26635 | 0.1804 |
| 550 | 53188 | 0.1067 |
| 600 | 69467 | 0.0523 |
| 650 | 57595 | 0.0281 |
| 700 | 24115 | 0.0156 |
| 750 | 3254 | 0.0098 |
| 800 | 48 | 0.0625 |

Calibration on predictions from unseen folds:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.0139 | 0.0145 |
| 2 | 0.0226 | 0.0225 |
| 3 | 0.0304 | 0.028 |
| 4 | 0.039 | 0.0375 |
| 5 | 0.0491 | 0.0477 |
| 6 | 0.0617 | 0.0591 |
| 7 | 0.0784 | 0.0803 |
| 8 | 0.1024 | 0.1079 |
| 9 | 0.1431 | 0.1512 |
| 10 | 0.266 | 0.2587 |

Points:

| feature | bin | points | woe | rows | default_rate |
| --- | --- | --- | --- | --- | --- |
| EXT_SOURCE_3 | up to 0.1761 | -51 | -1.163 | 12398 | 0.2193 |
| EXT_SOURCE_3 | 0.1761 to 0.3163 | -28 | -0.635 | 23851 | 0.1421 |
| EXT_SOURCE_3 | 0.3163 to 0.5038 | -3 | -0.073 | 51486 | 0.0863 |
| EXT_SOURCE_3 | 0.5038 to 0.6472 | 20 | 0.465 | 52121 | 0.0523 |
| EXT_SOURCE_3 | above 0.6472 | 38 | 0.86 | 57347 | 0.0358 |
| EXT_SOURCE_3 | Missing | -7 | -0.152 | 48805 | 0.0928 |
| EXT_SOURCE_2 | up to 0.1505 | -65 | -1.133 | 14204 | 0.2143 |
| EXT_SOURCE_2 | 0.1505 to 0.3542 | -28 | -0.491 | 38148 | 0.1255 |
| EXT_SOURCE_2 | 0.3542 to 0.4883 | -9 | -0.154 | 36741 | 0.0929 |
| EXT_SOURCE_2 | 0.4883 to 0.6161 | 8 | 0.137 | 63141 | 0.0712 |
| EXT_SOURCE_2 | above 0.6161 | 37 | 0.651 | 93243 | 0.0438 |
| EXT_SOURCE_2 | Missing | 0 | 0.0 | 531 | 0.0772 |
| EXT_SOURCE_1 | up to 0.2733 | -30 | -0.724 | 18407 | 0.1533 |
| EXT_SOURCE_1 | 0.2733 to 0.413 | -6 | -0.148 | 20797 | 0.0924 |
| EXT_SOURCE_1 | 0.413 to 0.5295 | 8 | 0.191 | 18364 | 0.0676 |
| EXT_SOURCE_1 | 0.5295 to 0.7006 | 20 | 0.495 | 26891 | 0.0508 |
| EXT_SOURCE_1 | above 0.7006 | 42 | 1.037 | 22954 | 0.0302 |
| EXT_SOURCE_1 | Missing | -2 | -0.059 | 138595 | 0.0852 |
| EMPLOYED_YEARS | up to 2.608 | -12 | -0.364 | 62864 | 0.1122 |
| EMPLOYED_YEARS | 2.608 to 4.888 | -7 | -0.207 | 44527 | 0.0974 |
| EMPLOYED_YEARS | 4.888 to 6.646 | 0 | 0.001 | 22871 | 0.0807 |
| EMPLOYED_YEARS | 6.646 to 10.78 | 5 | 0.163 | 35471 | 0.0694 |
| EMPLOYED_YEARS | above 10.78 | 17 | 0.52 | 36132 | 0.0496 |
| EMPLOYED_YEARS | Missing | 14 | 0.437 | 44143 | 0.0537 |
| INST_LATE_RATE_RECENCY_WEIGHTED | up to 0.03761 | 9 | 0.225 | 147494 | 0.0656 |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.03761 to 0.07065 | -3 | -0.069 | 17833 | 0.086 |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.07065 to 0.2857 | -12 | -0.306 | 47519 | 0.1065 |
| INST_LATE_RATE_RECENCY_WEIGHTED | above 0.2857 | -24 | -0.604 | 20476 | 0.1385 |
| INST_LATE_RATE_RECENCY_WEIGHTED | Missing | 13 | 0.322 | 12686 | 0.0598 |
| BUREAU_ACTIVE_SHARE | up to 0.291 | 7 | 0.4 | 79780 | 0.0556 |
| BUREAU_ACTIVE_SHARE | 0.291 to 0.3455 | 4 | 0.227 | 21519 | 0.0654 |
| BUREAU_ACTIVE_SHARE | 0.3455 to 0.5093 | 0 | 0.007 | 51017 | 0.0802 |
| BUREAU_ACTIVE_SHARE | 0.5093 to 0.6742 | -4 | -0.234 | 22540 | 0.0999 |
| BUREAU_ACTIVE_SHARE | above 0.6742 | -7 | -0.385 | 35907 | 0.1143 |
| BUREAU_ACTIVE_SHARE | Missing | -4 | -0.249 | 35245 | 0.1012 |
| BUREAU_OPENED_COUNT_12M | up to 0.5 | 5 | 0.353 | 89218 | 0.0581 |
| BUREAU_OPENED_COUNT_12M | 0.5 to 1.5 | 1 | 0.043 | 65401 | 0.0776 |
| BUREAU_OPENED_COUNT_12M | 1.5 to 2.5 | -2 | -0.122 | 32366 | 0.0902 |
| BUREAU_OPENED_COUNT_12M | above 2.5 | -8 | -0.539 | 23778 | 0.1308 |
| BUREAU_OPENED_COUNT_12M | Missing | -4 | -0.249 | 35245 | 0.1012 |
| INST_DAYS_LATE_MAX_12M | up to 0.5 | 4 | 0.204 | 123945 | 0.0668 |
| INST_DAYS_LATE_MAX_12M | 0.5 to 2.5 | -3 | -0.161 | 17715 | 0.0935 |
| INST_DAYS_LATE_MAX_12M | 2.5 to 6.5 | -7 | -0.364 | 19090 | 0.1122 |
| INST_DAYS_LATE_MAX_12M | above 6.5 | -16 | -0.796 | 13117 | 0.1629 |
| INST_DAYS_LATE_MAX_12M | Missing | 1 | 0.034 | 72141 | 0.0782 |
| BUREAU_HISTORY_DAYS | up to 337.5 | -5 | -0.572 | 12444 | 0.1347 |
| BUREAU_HISTORY_DAYS | 337.5 to 582.5 | -3 | -0.348 | 12970 | 0.1106 |
| BUREAU_HISTORY_DAYS | 582.5 to 1064 | -1 | -0.175 | 29196 | 0.0947 |
| BUREAU_HISTORY_DAYS | 1064 to 1756 | 0 | 0.028 | 46799 | 0.0787 |
| BUREAU_HISTORY_DAYS | above 1756 | 2 | 0.292 | 109354 | 0.0616 |
| BUREAU_HISTORY_DAYS | Missing | -2 | -0.249 | 35245 | 0.1012 |
| OCCUPATION_TYPE | Missing | 9 | 0.235 | 76940 | 0.0649 |
| OCCUPATION_TYPE | Laborers | -11 | -0.292 | 44259 | 0.1052 |
| OCCUPATION_TYPE | Sales staff | -7 | -0.19 | 25606 | 0.096 |
| OCCUPATION_TYPE | Core staff | 9 | 0.253 | 22093 | 0.0638 |
| OCCUPATION_TYPE | Managers | 10 | 0.28 | 17096 | 0.0622 |
| OCCUPATION_TYPE | Drivers | -14 | -0.368 | 14944 | 0.1126 |
| OCCUPATION_TYPE | High skill tech staff | 10 | 0.27 | 9093 | 0.0628 |
| OCCUPATION_TYPE | Accountants | 22 | 0.592 | 7882 | 0.0463 |
| OCCUPATION_TYPE | Medicine staff | 6 | 0.156 | 6871 | 0.0699 |
| OCCUPATION_TYPE | Security staff | -11 | -0.31 | 5372 | 0.1069 |
| OCCUPATION_TYPE | Cooking staff | -11 | -0.291 | 4767 | 0.1051 |
| OCCUPATION_TYPE | Cleaning staff | -7 | -0.184 | 3741 | 0.0954 |
| OCCUPATION_TYPE | Rare or new | -9 | -0.251 | 7344 | 0.1014 |
| BUREAU_CARD_UTILISATION | up to 0.3041 | 10 | 0.336 | 49157 | 0.0591 |
| BUREAU_CARD_UTILISATION | 0.3041 to 0.5657 | 0 | 0.008 | 12550 | 0.0801 |
| BUREAU_CARD_UTILISATION | 0.5657 to 0.7738 | -4 | -0.127 | 12339 | 0.0906 |
| BUREAU_CARD_UTILISATION | 0.7738 to 0.97 | -10 | -0.328 | 23988 | 0.1087 |
| BUREAU_CARD_UTILISATION | above 0.97 | -21 | -0.693 | 14163 | 0.1493 |
| BUREAU_CARD_UTILISATION | Missing | 2 | 0.072 | 133811 | 0.0756 |
| CC_UTILISATION_NOW | up to 0.8713 | 11 | 0.281 | 37709 | 0.0622 |
| CC_UTILISATION_NOW | above 0.8713 | -32 | -0.85 | 14317 | 0.1705 |
| CC_UTILISATION_NOW | Missing | 2 | 0.041 | 193982 | 0.0777 |
| CREDIT_TO_GOODS | up to 1.158 | 10 | 0.205 | 157862 | 0.0667 |
| CREDIT_TO_GOODS | 1.158 to 1.211 | -6 | -0.126 | 36400 | 0.0906 |
| CREDIT_TO_GOODS | 1.211 to 1.317 | -15 | -0.312 | 28577 | 0.1071 |
| CREDIT_TO_GOODS | above 1.317 | -25 | -0.518 | 22948 | 0.1285 |
| CREDIT_TO_GOODS | Missing | 0 | 0.0 | 221 | 0.0769 |
| PREV_REFUSED_RATE | up to 0.06066 | 4 | 0.148 | 153822 | 0.0704 |
| PREV_REFUSED_RATE | 0.06066 to 0.155 | 3 | 0.094 | 13350 | 0.074 |
| PREV_REFUSED_RATE | 0.155 to 0.2795 | -3 | -0.092 | 25386 | 0.0878 |
| PREV_REFUSED_RATE | 0.2795 to 0.4361 | -9 | -0.328 | 21314 | 0.1087 |
| PREV_REFUSED_RATE | above 0.4361 | -18 | -0.638 | 18927 | 0.1425 |
| PREV_REFUSED_RATE | Missing | 9 | 0.315 | 13209 | 0.0602 |
| PREV_DAYS_SINCE_LAST_REFUSAL | up to 235.5 | -7 | -0.506 | 22972 | 0.1272 |
| PREV_DAYS_SINCE_LAST_REFUSAL | 235.5 to 486.5 | -5 | -0.344 | 22230 | 0.1103 |
| PREV_DAYS_SINCE_LAST_REFUSAL | 486.5 to 958.5 | -4 | -0.287 | 13674 | 0.1047 |
| PREV_DAYS_SINCE_LAST_REFUSAL | above 958.5 | 2 | 0.143 | 20278 | 0.0707 |
| PREV_DAYS_SINCE_LAST_REFUSAL | Missing | 2 | 0.16 | 166854 | 0.0697 |

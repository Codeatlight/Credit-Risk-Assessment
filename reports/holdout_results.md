# Holdout results

One scoring run on 61,503 holdout applicants (8.07% defaulted), with models fitted on dev rows only. Written by `python -m src.evaluate`, which refuses to run twice. Intervals come from 500 bootstrap resamples.

| model | dev_auc | holdout_auc | auc_95_interval | gini | ks | brier | mean_predicted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline, Without EXT_SOURCE | 0.6906 | 0.6911 | 0.6829 to 0.6987 | 0.3822 | 0.2778 | 0.071 | 0.0804 |
| Scorecard, Without EXT_SOURCE | 0.6995 | 0.7035 | 0.6951 to 0.7109 | 0.407 | 0.304 | 0.0708 | 0.0806 |
| LightGBM, Without EXT_SOURCE | 0.7579 | 0.7644 | 0.7574 to 0.7718 | 0.5288 | 0.3987 | 0.0673 | 0.0801 |
| Baseline, With EXT_SOURCE | 0.7514 | 0.7522 | 0.7450 to 0.7589 | 0.5044 | 0.3804 | 0.0681 | 0.0802 |
| Scorecard, With EXT_SOURCE | 0.7494 | 0.7531 | 0.7459 to 0.7601 | 0.5062 | 0.389 | 0.0682 | 0.0806 |
| LightGBM, With EXT_SOURCE | 0.7847 | 0.7881 | 0.7815 to 0.7946 | 0.5762 | 0.4384 | 0.0654 | 0.0799 |

AUC gaps between models, on the same bootstrap samples. An interval that excludes 0 means a real gap:

| comparison | auc_gap | gap_95_interval |
| --- | --- | --- |
| LightGBM minus Scorecard, Without EXT_SOURCE | 0.0613 | 0.0560 to 0.0664 |
| LightGBM minus Scorecard, With EXT_SOURCE | 0.0352 | 0.0310 to 0.0392 |
| Scorecard, value of EXT_SOURCE | 0.0497 | 0.0439 to 0.0550 |
| LightGBM, value of EXT_SOURCE | 0.0235 | 0.0196 to 0.0275 |

## Scorecard, Without EXT_SOURCE

Calibration:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.0225 | 0.0222 |
| 2 | 0.0324 | 0.0285 |
| 3 | 0.0408 | 0.0399 |
| 4 | 0.0493 | 0.0507 |
| 5 | 0.0588 | 0.0582 |
| 6 | 0.0699 | 0.0668 |
| 7 | 0.0842 | 0.0816 |
| 8 | 0.1031 | 0.1159 |
| 9 | 0.1335 | 0.1314 |
| 10 | 0.2195 | 0.2202 |

Default rate by score band:

| score_from | applicants | default_rate |
| --- | --- | --- |
| 400 | 147 | 0.3537 |
| 450 | 1382 | 0.2829 |
| 500 | 6545 | 0.1806 |
| 550 | 16959 | 0.1035 |
| 600 | 22459 | 0.0538 |
| 650 | 12422 | 0.028 |
| 700 | 1588 | 0.0176 |
| 750 | 1 | 0.0 |

## LightGBM, Without EXT_SOURCE

Calibration:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.013 | 0.0115 |
| 2 | 0.0213 | 0.0215 |
| 3 | 0.0286 | 0.026 |
| 4 | 0.0368 | 0.0348 |
| 5 | 0.0464 | 0.0458 |
| 6 | 0.0585 | 0.0579 |
| 7 | 0.0747 | 0.0767 |
| 8 | 0.0994 | 0.1046 |
| 9 | 0.1436 | 0.145 |
| 10 | 0.279 | 0.2834 |

## Scorecard, With EXT_SOURCE

Calibration:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.0141 | 0.0142 |
| 2 | 0.023 | 0.0225 |
| 3 | 0.0308 | 0.03 |
| 4 | 0.0394 | 0.0383 |
| 5 | 0.0496 | 0.0442 |
| 6 | 0.0623 | 0.059 |
| 7 | 0.079 | 0.0745 |
| 8 | 0.1025 | 0.1112 |
| 9 | 0.143 | 0.1538 |
| 10 | 0.2655 | 0.2623 |

Default rate by score band:

| score_from | applicants | default_rate |
| --- | --- | --- |
| 350 | 68 | 0.7206 |
| 400 | 543 | 0.407 |
| 450 | 2238 | 0.3003 |
| 500 | 6651 | 0.1855 |
| 550 | 13181 | 0.1062 |
| 600 | 17492 | 0.0508 |
| 650 | 14504 | 0.0269 |
| 700 | 6057 | 0.0167 |
| 750 | 767 | 0.0117 |
| 800 | 2 | 0.0 |

## LightGBM, With EXT_SOURCE

Calibration:

| risk_band | predicted | actual |
| --- | --- | --- |
| 1 | 0.01 | 0.0086 |
| 2 | 0.0169 | 0.0154 |
| 3 | 0.0234 | 0.0249 |
| 4 | 0.0308 | 0.0325 |
| 5 | 0.0401 | 0.0402 |
| 6 | 0.0526 | 0.0528 |
| 7 | 0.0705 | 0.068 |
| 8 | 0.0986 | 0.0992 |
| 9 | 0.1497 | 0.153 |
| 10 | 0.3068 | 0.3126 |

## Locked model files

| file | sha256_start |
| --- | --- |
| scorecard_without_ext_source.json | 47ebe6ae7064 |
| lightgbm_without_ext_source.txt | 818f02d3916e |
| lightgbm_without_ext_source.json | 6e036257090d |
| scorecard_with_ext_source.json | 90f6d6a663c9 |
| lightgbm_with_ext_source.txt | 01384dc596ec |
| lightgbm_with_ext_source.json | fffa3e5a64f6 |

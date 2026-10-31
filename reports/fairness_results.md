# Fairness results

Locked models at the step 7 cutoffs, measured on 61,503 holdout applicants. No model uses gender or age directly. These are measurements, not a legal judgement. Written by `python -m src.fairness`.

## Largest gaps between groups

`approval_ratio` is the lowest group's approval rate divided by the highest. The four-fifths line of 0.8 is a screening rule of thumb.

| model | attribute | approval_ratio | passes_four_fifths | good_payers_refused_gap | calibration_gap |
| --- | --- | --- | --- | --- | --- |
| Scorecard, Without EXT_SOURCE | gender | 0.986 | True | 0.0111 | 0.0122 |
| Scorecard, Without EXT_SOURCE | age | 0.951 | True | 0.0403 | 0.0063 |
| LightGBM, Without EXT_SOURCE | gender | 0.958 | True | 0.0281 | 0.0107 |
| LightGBM, Without EXT_SOURCE | age | 0.855 | True | 0.1155 | 0.0047 |
| Scorecard, With EXT_SOURCE | gender | 0.957 | True | 0.0311 | 0.009 |
| Scorecard, With EXT_SOURCE | age | 0.82 | True | 0.1493 | 0.012 |
| LightGBM, With EXT_SOURCE | gender | 0.949 | True | 0.0338 | 0.0083 |
| LightGBM, With EXT_SOURCE | age | 0.838 | True | 0.1265 | 0.0045 |

## Results by group

`good_payers_refused` is the share of non-defaulters refused. `defaulters_approved` is the share of defaulters approved.

| model | attribute | group | applicants | default_rate | predicted_risk | approval_rate | good_payers_refused | defaulters_approved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Scorecard, Without EXT_SOURCE | gender | F | 40561 | 0.0699 | 0.076 | 0.9748 | 0.0196 | 0.9002 |
| Scorecard, Without EXT_SOURCE | gender | M | 20940 | 0.1017 | 0.0895 | 0.9608 | 0.0307 | 0.8859 |
| Scorecard, Without EXT_SOURCE | age | 30 to 44 | 24744 | 0.0883 | 0.0871 | 0.9637 | 0.0274 | 0.8715 |
| Scorecard, Without EXT_SOURCE | age | 45 to 59 | 20663 | 0.0685 | 0.0729 | 0.9781 | 0.0172 | 0.9145 |
| Scorecard, Without EXT_SOURCE | age | 60 and over | 7191 | 0.0496 | 0.0483 | 0.9962 | 0.0035 | 0.9916 |
| Scorecard, Without EXT_SOURCE | age | Under 30 | 8905 | 0.113 | 0.1067 | 0.9476 | 0.0438 | 0.8797 |
| LightGBM, Without EXT_SOURCE | gender | F | 40561 | 0.0699 | 0.0745 | 0.9186 | 0.0638 | 0.6844 |
| LightGBM, Without EXT_SOURCE | gender | M | 20940 | 0.1017 | 0.091 | 0.8798 | 0.0919 | 0.6299 |
| LightGBM, Without EXT_SOURCE | age | 30 to 44 | 24744 | 0.0883 | 0.0845 | 0.8957 | 0.0797 | 0.6414 |
| LightGBM, Without EXT_SOURCE | age | 45 to 59 | 20663 | 0.0685 | 0.0732 | 0.9235 | 0.0596 | 0.6949 |
| LightGBM, Without EXT_SOURCE | age | 60 and over | 7191 | 0.0496 | 0.0483 | 0.9751 | 0.0189 | 0.8599 |
| LightGBM, Without EXT_SOURCE | age | Under 30 | 8905 | 0.113 | 0.1098 | 0.8339 | 0.1344 | 0.5855 |
| Scorecard, With EXT_SOURCE | gender | F | 40561 | 0.0699 | 0.0744 | 0.9293 | 0.0561 | 0.7355 |
| Scorecard, With EXT_SOURCE | gender | M | 20940 | 0.1017 | 0.0927 | 0.8894 | 0.0872 | 0.6825 |
| Scorecard, With EXT_SOURCE | age | 30 to 44 | 24744 | 0.0883 | 0.0855 | 0.9064 | 0.0728 | 0.6917 |
| Scorecard, With EXT_SOURCE | age | 45 to 59 | 20663 | 0.0685 | 0.0662 | 0.9518 | 0.0369 | 0.7987 |
| Scorecard, With EXT_SOURCE | age | 60 and over | 7191 | 0.0496 | 0.0502 | 0.9814 | 0.0154 | 0.9188 |
| Scorecard, With EXT_SOURCE | age | Under 30 | 8905 | 0.113 | 0.125 | 0.8047 | 0.1647 | 0.5646 |
| LightGBM, With EXT_SOURCE | gender | F | 40561 | 0.0699 | 0.073 | 0.919 | 0.0608 | 0.6495 |
| LightGBM, With EXT_SOURCE | gender | M | 20940 | 0.1017 | 0.0934 | 0.872 | 0.0946 | 0.5763 |
| LightGBM, With EXT_SOURCE | age | 30 to 44 | 24744 | 0.0883 | 0.0849 | 0.8922 | 0.0792 | 0.597 |
| LightGBM, With EXT_SOURCE | age | 45 to 59 | 20663 | 0.0685 | 0.0688 | 0.9305 | 0.0506 | 0.673 |
| LightGBM, With EXT_SOURCE | age | 60 and over | 7191 | 0.0496 | 0.0483 | 0.9711 | 0.0212 | 0.8235 |
| LightGBM, With EXT_SOURCE | age | Under 30 | 8905 | 0.113 | 0.1175 | 0.814 | 0.1477 | 0.5139 |

## Do features stand in for gender or age?

Occupation alone separates men from women with AUC 0.7868. Shares are from dev rows:

| OCCUPATION_TYPE | applicants | share_male |
| --- | --- | --- |
| Drivers | 14944 | 0.949 |
| Low-skill Laborers | 1695 | 0.854 |
| Security staff | 5372 | 0.697 |
| Laborers | 44259 | 0.58 |
| Managers | 17096 | 0.458 |
| High skill tech staff | 9093 | 0.349 |
| Missing | 76939 | 0.241 |
| Core staff | 22093 | 0.212 |
| Waiters/barmen staff | 1046 | 0.122 |
| Sales staff | 25606 | 0.12 |
| Cooking staff | 4767 | 0.095 |
| Cleaning staff | 3741 | 0.073 |
| Private service staff | 2094 | 0.043 |
| Secretaries | 1047 | 0.042 |
| Accountants | 7882 | 0.029 |
| Medicine staff | 6871 | 0.029 |

How well each model's risk alone reveals a group, where 0.5 means not at all:

| model | reveals_male | reveals_under_30 | reveals_60_plus |
| --- | --- | --- | --- |
| Scorecard, Without EXT_SOURCE | 0.5784 | 0.6821 | 0.7296 |
| LightGBM, Without EXT_SOURCE | 0.5667 | 0.6464 | 0.6619 |
| Scorecard, With EXT_SOURCE | 0.5813 | 0.707 | 0.6527 |
| LightGBM, With EXT_SOURCE | 0.5744 | 0.6583 | 0.6384 |

Average points from employment lines, by age:

| model | lines | points_60_plus | points_under_60 |
| --- | --- | --- | --- |
| Without EXT_SOURCE | EMPLOYED_YEARS, ORGANIZATION_TYPE, OCCUPATION_TYPE | 31.1 | 0.1 |
| With EXT_SOURCE | EMPLOYED_YEARS, OCCUPATION_TYPE | 20.1 | 0.3 |

## Scorecards refitted without job features

Dev rows only, from unseen folds, with each cutoff rechosen on dev. These are new models with no untouched holdout, so their scores aren't comparable with the holdout results.

| scorecard | dev_auc | max_risk | approval_rate | approval_women | approval_men | age_approval_ratio |
| --- | --- | --- | --- | --- | --- | --- |
| Without EXT_SOURCE, all features | 0.6995 | 0.23 | 0.9688 | 0.9732 | 0.9603 | 0.944 |
| Without EXT_SOURCE, no occupation | 0.6961 | 0.21 | 0.959 | 0.9617 | 0.9539 | 0.924 |
| Without EXT_SOURCE, no job features | 0.6886 | 0.195 | 0.9514 | 0.9515 | 0.9514 | 0.949 |
| With EXT_SOURCE, all features | 0.7494 | 0.19 | 0.9155 | 0.9291 | 0.8894 | 0.818 |
| With EXT_SOURCE, no occupation | 0.7476 | 0.195 | 0.9214 | 0.9313 | 0.9025 | 0.827 |
| With EXT_SOURCE, no job features | 0.7439 | 0.195 | 0.9227 | 0.9303 | 0.908 | 0.86 |

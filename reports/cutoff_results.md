# Approval cutoff results

Assumptions: a repaid loan earns 15% of its size and a defaulted loan loses 60%. These are assumptions, not data. Cutoffs were chosen on dev predictions from unseen folds, then applied unchanged to 61,503 holdout applicants. Profit is in the data's currency units, averaged over all applicants including those refused. Written by `python -m src.cutoff`.

Approving everyone earns 55,822 per applicant.

| model | max_risk | min_score | approval_rate | default_rate_approved | profit_per_applicant | gain_over_approving_all |
| --- | --- | --- | --- | --- | --- | --- |
| Scorecard, Without EXT_SOURCE | 0.23 | 505 | 0.97 | 0.0744 | 56646 | 824 |
| LightGBM, Without EXT_SOURCE | 0.185 | n/a | 0.9054 | 0.0589 | 58928 | 3106 |
| Scorecard, With EXT_SOURCE | 0.19 | 522 | 0.9157 | 0.0628 | 58239 | 2417 |
| LightGBM, With EXT_SOURCE | 0.195 | n/a | 0.903 | 0.0553 | 60172 | 4350 |

Holdout profit gaps at those cutoffs. An interval that excludes 0 means a real gap:

| comparison | profit_gap | gap_95_interval |
| --- | --- | --- |
| LightGBM, Without EXT_SOURCE minus Scorecard, Without EXT_SOURCE | 2281 | 1850 to 2716 |
| LightGBM, With EXT_SOURCE minus Scorecard, With EXT_SOURCE | 1933 | 1542 to 2305 |
| Scorecard, With EXT_SOURCE minus Scorecard, Without EXT_SOURCE | 1592 | 1203 to 2003 |
| LightGBM, With EXT_SOURCE minus LightGBM, Without EXT_SOURCE | 1244 | 872 to 1619 |

## Sensitivity

Cutoff rechosen on dev for each pair of assumptions, then measured on the holdout:

| model | margin | loss | max_risk | approval_rate | default_rate_approved | profit_per_applicant |
| --- | --- | --- | --- | --- | --- | --- |
| Scorecard, Without EXT_SOURCE | 0.1 | 0.4 | 0.23 | 0.97 | 0.0744 | 37764 |
| Scorecard, Without EXT_SOURCE | 0.1 | 0.6 | 0.14 | 0.8723 | 0.063 | 30617 |
| Scorecard, Without EXT_SOURCE | 0.1 | 0.8 | 0.105 | 0.7655 | 0.054 | 25056 |
| Scorecard, Without EXT_SOURCE | 0.15 | 0.4 | 0.285 | 0.9865 | 0.0777 | 64947 |
| Scorecard, Without EXT_SOURCE | 0.15 | 0.6 | 0.23 | 0.97 | 0.0744 | 56646 |
| Scorecard, Without EXT_SOURCE | 0.15 | 0.8 | 0.15 | 0.8935 | 0.0648 | 49309 |
| Scorecard, Without EXT_SOURCE | 0.2 | 0.4 | 0.395 | 0.9978 | 0.0801 | 92497 |
| Scorecard, Without EXT_SOURCE | 0.2 | 0.6 | 0.25 | 0.9771 | 0.0758 | 83742 |
| Scorecard, Without EXT_SOURCE | 0.2 | 0.8 | 0.23 | 0.97 | 0.0744 | 75529 |
| LightGBM, Without EXT_SOURCE | 0.1 | 0.4 | 0.185 | 0.9054 | 0.0589 | 39285 |
| LightGBM, Without EXT_SOURCE | 0.1 | 0.6 | 0.14 | 0.8477 | 0.052 | 33303 |
| LightGBM, Without EXT_SOURCE | 0.1 | 0.8 | 0.1 | 0.7538 | 0.0433 | 28513 |
| LightGBM, Without EXT_SOURCE | 0.15 | 0.4 | 0.305 | 0.9712 | 0.0712 | 65809 |
| LightGBM, Without EXT_SOURCE | 0.15 | 0.6 | 0.185 | 0.9054 | 0.0589 | 58928 |
| LightGBM, Without EXT_SOURCE | 0.15 | 0.8 | 0.155 | 0.8704 | 0.0545 | 52834 |
| LightGBM, Without EXT_SOURCE | 0.2 | 0.4 | 0.365 | 0.9834 | 0.0748 | 92952 |
| LightGBM, Without EXT_SOURCE | 0.2 | 0.6 | 0.255 | 0.9531 | 0.0672 | 85318 |
| LightGBM, Without EXT_SOURCE | 0.2 | 0.8 | 0.185 | 0.9054 | 0.0589 | 78571 |
| Scorecard, With EXT_SOURCE | 0.1 | 0.4 | 0.19 | 0.9157 | 0.0628 | 38826 |
| Scorecard, With EXT_SOURCE | 0.1 | 0.6 | 0.125 | 0.8146 | 0.0502 | 33130 |
| Scorecard, With EXT_SOURCE | 0.1 | 0.8 | 0.1 | 0.7434 | 0.0436 | 28580 |
| Scorecard, With EXT_SOURCE | 0.15 | 0.4 | 0.265 | 0.9629 | 0.0705 | 65596 |
| Scorecard, With EXT_SOURCE | 0.15 | 0.6 | 0.19 | 0.9157 | 0.0628 | 58239 |
| Scorecard, With EXT_SOURCE | 0.15 | 0.8 | 0.155 | 0.8724 | 0.0569 | 52146 |
| Scorecard, With EXT_SOURCE | 0.2 | 0.4 | 0.37 | 0.9874 | 0.0764 | 92783 |
| Scorecard, With EXT_SOURCE | 0.2 | 0.6 | 0.24 | 0.9522 | 0.0683 | 85052 |
| Scorecard, With EXT_SOURCE | 0.2 | 0.8 | 0.19 | 0.9157 | 0.0628 | 77652 |
| LightGBM, With EXT_SOURCE | 0.1 | 0.4 | 0.195 | 0.903 | 0.0553 | 40115 |
| LightGBM, With EXT_SOURCE | 0.1 | 0.6 | 0.135 | 0.8307 | 0.0461 | 34788 |
| LightGBM, With EXT_SOURCE | 0.1 | 0.8 | 0.1 | 0.756 | 0.0389 | 30603 |
| LightGBM, With EXT_SOURCE | 0.15 | 0.4 | 0.27 | 0.9489 | 0.0641 | 66534 |
| LightGBM, With EXT_SOURCE | 0.15 | 0.6 | 0.195 | 0.903 | 0.0553 | 60172 |
| LightGBM, With EXT_SOURCE | 0.15 | 0.8 | 0.15 | 0.8539 | 0.0491 | 54403 |
| LightGBM, With EXT_SOURCE | 0.2 | 0.4 | 0.315 | 0.9645 | 0.0681 | 93464 |
| LightGBM, With EXT_SOURCE | 0.2 | 0.6 | 0.27 | 0.9489 | 0.0641 | 86368 |
| LightGBM, With EXT_SOURCE | 0.2 | 0.8 | 0.195 | 0.903 | 0.0553 | 80230 |

# Reasons for decisions

Models: With EXT_SOURCE. Written by `python -m src.reasons`.

Checks passed: scorecard reason points add up to each applicant's score, and SHAP values add up to each LightGBM prediction (largest gap 2.7e-14).

## What drives LightGBM overall

Average size of each feature's push, on 20,000 holdout applicants:

| feature | mean_abs_shap | meaning |
| --- | --- | --- |
| EXT_SOURCE_2 | 0.3075 | External credit score 2 |
| EXT_SOURCE_3 | 0.2536 | External credit score 3 |
| EXT_SOURCE_1 | 0.1557 | External credit score 1 |
| ANNUITY_TO_CREDIT | 0.1222 | Repayment speed of this loan |
| INST_LATE_RATE_RECENCY_WEIGHTED | 0.1189 | Share of recent instalments paid late |
| POS_FUTURE_INSTALMENTS | 0.1114 | Instalments left on open store and cash loans |
| EMPLOYED_YEARS | 0.1084 | Time in current job |
| CREDIT_TO_GOODS | 0.106 | Loan size compared with the goods price |
| ORGANIZATION_TYPE | 0.1031 | Type of employer |
| AMT_CREDIT | 0.0943 | Loan amount |
| PREV_TERM_MEAN | 0.0848 | Average term of past Home Credit loans |
| PREV_APPROVED_CREDIT_MEAN | 0.084 | Average size of past approved loans |
| OWN_CAR_AGE | 0.0763 | Age of the applicant's car |
| OCCUPATION_TYPE | 0.0746 | Occupation |
| NAME_EDUCATION_TYPE | 0.0713 | Education level |

## Examples: 3 applicants the scorecard refuses

### Applicant 112137, score 517

Scorecard reasons:

| reason | points_below_typical |
| --- | --- |
| External credit score 2 | 71.6 |
| External credit score 3 | 12.8 |
| Occupation | 12.2 |
| Time in current job | 8.4 |

LightGBM reasons:

| reason | risk_push |
| --- | --- |
| External credit score 2 | 1.182 |
| Type of employer | 0.178 |
| Average size of past approved loans | 0.171 |
| External credit score 1 | 0.155 |

### Applicant 359371, score 506

Scorecard reasons:

| reason | points_below_typical |
| --- | --- |
| External credit score 2 | 71.6 |
| Credit card use at other lenders | 21.7 |
| Loan size compared with the goods price | 16.5 |
| Time in current job | 13.4 |

LightGBM reasons:

| reason | risk_push |
| --- | --- |
| External credit score 2 | 0.91 |
| External credit score 3 | 0.214 |
| Loan size compared with the goods price | 0.192 |
| Type of employer | 0.187 |

### Applicant 179369, score 474

Scorecard reasons:

| reason | points_below_typical |
| --- | --- |
| External credit score 2 | 71.6 |
| External credit score 3 | 33.8 |
| Loan size compared with the goods price | 16.5 |
| Time in current job | 13.4 |

LightGBM reasons:

| reason | risk_push |
| --- | --- |
| External credit score 2 | 1.118 |
| External credit score 3 | 0.344 |
| Average size of past approved loans | 0.226 |
| Time in current job | 0.159 |

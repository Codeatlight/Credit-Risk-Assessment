# Credit Risk Scorecard

Should a lender approve this applicant? This project predicts the chance of default, turns it into an explainable points-based score, and picks an approval cutoff by weighing the money lost on defaults against the interest earned.

> Status: all 9 planned steps are done, from data exploration to a working app. Final results are below.

## Data

[Home Credit Default Risk](https://www.kaggle.com/competitions/home-credit-default-risk) on Kaggle.

| Table | What it holds |
| --- | --- |
| `application_train` | One row per loan application: about 307,511 rows, 122 columns, with the `TARGET` label (1 = defaulted) |
| `bureau`, `bureau_balance` | The applicant's past loans at other lenders, and their monthly status |
| `previous_application`, `installments_payments`, `POS_CASH_balance`, `credit_card_balance` | Past applications and repayment behaviour with Home Credit |

**To get it:** sign in to Kaggle, accept the competition rules, download the data, and unzip the CSV files into `data/raw/`. The data stays out of git.

## Plan

1. **Explore the data.** Default rate, missing values, leakage risks, data quality problems.
2. **Build features.** Combine the tables into one row per applicant: past late payments, debt relative to income, credit history length. Run `python -m src.features`, then `python -m src.feature_report` for the checks. See the [feature dictionary](reports/feature_dictionary.md) and [sanity report](reports/feature_sanity.md).
3. **Baseline.** Logistic regression on a few strong features, using a stratified holdout that is only touched once at the end. Run `python -m src.baseline`. Cross-validated dev results are in the [baseline report](reports/baseline_results.md).
4. **Scorecard.** Bin features, compute Weight of Evidence and Information Value, and fit a logistic model that converts to points, like a CIBIL-style score. Run `python -m src.scorecard`. Cross-validated dev results and the points table are in the [scorecard report](reports/scorecard_results.md).
5. **Challenger model.** LightGBM with cross-validation. Report what extra accuracy costs in explainability. Run `python -m src.challenger`. Cross-validated dev results are in the [challenger report](reports/challenger_results.md).
6. **Evaluate.** AUC, Gini, KS statistic, and calibration (does a predicted 10% risk really default about 10% of the time?). `python -m src.evaluate` scores the holdout once and then refuses to run again. Full tables are in the [holdout report](reports/holdout_results.md).
7. **Business decision.** Choose the approval cutoff from expected profit. Loss per default and interest margin are assumptions, stated openly, with a sensitivity table. Run `python -m src.cutoff`. Results are in the [cutoff report](reports/cutoff_results.md).
8. **Explain and check fairness.** SHAP reasons for individual decisions; compare approval and error rates across gender and age groups. Run `python -m src.reasons` and `python -m src.fairness`. See the [reasons report](reports/reasons_results.md) and [fairness report](reports/fairness_results.md).
9. **App.** A Streamlit page: enter an applicant, see the score, decision and top reasons. It uses the scorecard without `EXT_SOURCE`, so every point can be explained, and needs only `app/scorecard.json`, not the raw data. `python -m src.export_app` rebuilds that file.

## Project layout

```
data/raw/          Kaggle CSVs (not in git)
data/processed/    Built feature tables (not in git)
notebooks/         Exploration and experiments, numbered in order
src/               Reusable code: features, scorecard, evaluation
models/            Saved models (not in git)
app/               Streamlit app and the points it needs
reports/           Feature dictionary, sanity report, baseline, scorecard, challenger, holdout, cutoff, reasons and fairness results
reports/figures/   Charts for the README
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

To run the app:

```bash
streamlit run app/streamlit_app.py
```

## Results

Scored once on the 61,503 holdout applicants, using models fitted on dev rows only. Gender and age are not used. The AUC range is a 95% bootstrap interval.

| Model | Size | AUC | AUC range | Gini | KS |
| --- | --- | --- | --- | --- | --- |
| Baseline, without `EXT_SOURCE` | 12 features | 0.691 | 0.683 to 0.699 | 0.382 | 0.278 |
| Scorecard, without `EXT_SOURCE` | 15 lines | 0.704 | 0.695 to 0.711 | 0.407 | 0.304 |
| LightGBM, without `EXT_SOURCE` | About 800 trees | 0.764 | 0.757 to 0.772 | 0.529 | 0.399 |
| Baseline, with `EXT_SOURCE` | 15 features | 0.752 | 0.745 to 0.759 | 0.504 | 0.380 |
| Scorecard, with `EXT_SOURCE` | 15 lines | 0.753 | 0.746 to 0.760 | 0.506 | 0.389 |
| LightGBM, with `EXT_SOURCE` | About 850 trees | 0.788 | 0.782 to 0.795 | 0.576 | 0.438 |

Explainability costs 0.035 to 0.061 of AUC.

**Approval cutoff.** Assuming a repaid loan earns 15% of its size and a defaulted loan loses 60%, cutoffs chosen on dev rows and measured on the holdout give:

| Model | Approved | Default rate if approved | Profit per applicant | Gain over approving everyone |
| --- | --- | --- | --- | --- |
| Scorecard, without `EXT_SOURCE` | 97.0% | 7.4% | 56,646 | 824 |
| LightGBM, without `EXT_SOURCE` | 90.5% | 5.9% | 58,928 | 3,106 |
| Scorecard, with `EXT_SOURCE` | 91.6% | 6.3% | 58,239 | 2,417 |
| LightGBM, with `EXT_SOURCE` | 90.3% | 5.5% | 60,172 | 4,350 |

These money figures depend on the assumptions, not on observed lending profit.

**Fairness.** No model uses gender or age directly, and all four pass the four-fifths screening rule on approval rates. The tightest case is age for the scorecard with `EXT_SOURCE`, with a ratio of 0.82. Age gaps are the main concern: that model refuses about 15 percentage points more good payers in one age group than in another. These are measurements, not a legal judgement.

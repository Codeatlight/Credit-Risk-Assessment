# Credit Risk Scorecard

Should a lender approve this applicant? This project predicts the chance of default, turns it into an explainable points-based score, and picks an approval cutoff by weighing the money lost on defaults against the interest earned.

> Status: data explored, holdout set aside, and features built, a baseline set, and a scorecard built (steps 1 to 4 done). Results get filled in as the work is done.

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
5. **Challenger model.** LightGBM with cross-validation. Report what extra accuracy costs in explainability.
6. **Evaluate.** AUC, Gini, KS statistic, and calibration (does a predicted 10% risk really default about 10% of the time?).
7. **Business decision.** Choose the approval cutoff from expected profit. Loss per default and interest margin are assumptions, stated openly, with a sensitivity table.
8. **Explain and check fairness.** SHAP reasons for individual decisions; compare approval and error rates across gender and age groups.
9. **App.** A Streamlit page: enter an applicant, see the score, decision and top reasons.

## Project layout

```
data/raw/          Kaggle CSVs (not in git)
data/processed/    Built feature tables (not in git)
notebooks/         Exploration and experiments, numbered in order
src/               Reusable code: features, scorecard, evaluation
models/            Saved models (not in git)
app/               Streamlit app
reports/           Feature dictionary, sanity report, baseline and scorecard results
reports/figures/   Charts for the README
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Results

To be filled in from the final holdout.

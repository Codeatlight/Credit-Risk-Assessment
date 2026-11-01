"""Write the scorecard the app needs to app/scorecard.json.

models/ stays out of git, so a deployed app can't read it. This file holds questions,
answers and points only: no applicant records and no raw data.

Run from the project root:  python -m src.export_app
"""
import json
import math
from pathlib import Path

from src.reasons import load_card, readable, typical_points
from src.scorecard import FACTOR, MODELS, OFFSET, to_score

OUT_FILE = Path("app/scorecard.json")
MODEL = "Without EXT_SOURCE"
OTHER = "Rare or new"

UNITS = {
    "EMPLOYED_YEARS": "years", "INST_LATE_RATE_RECENCY_WEIGHTED": "percent", "BUREAU_ACTIVE_SHARE": "percent",
    "BUREAU_OPENED_COUNT_12M": "count", "INST_DAYS_LATE_MAX_12M": "days", "BUREAU_HISTORY_DAYS": "months",
    "BUREAU_CARD_UTILISATION": "percent", "CC_UTILISATION_NOW": "percent", "CREDIT_TO_GOODS": "times",
    "PREV_REFUSED_RATE": "percent", "PREV_DAYS_SINCE_LAST_REFUSAL": "months", "CC_UTILISATION_MEAN": "percent",
    "BUREAU_DEBT_TO_CREDIT": "percent",
}
GROUPS = {
    "Job": ["EMPLOYED_YEARS", "OCCUPATION_TYPE", "ORGANIZATION_TYPE"],
    "This loan": ["CREDIT_TO_GOODS"],
    "Loans at other lenders": ["BUREAU_HISTORY_DAYS", "BUREAU_OPENED_COUNT_12M", "BUREAU_ACTIVE_SHARE",
                               "BUREAU_DEBT_TO_CREDIT", "BUREAU_CARD_UTILISATION"],
    "History with Home Credit": ["INST_LATE_RATE_RECENCY_WEIGHTED", "INST_DAYS_LATE_MAX_12M", "PREV_REFUSED_RATE",
                                 "PREV_DAYS_SINCE_LAST_REFUSAL", "CC_UTILISATION_NOW", "CC_UTILISATION_MEAN"],
}
SPECIAL_ANSWERS = {
    "EMPLOYED_YEARS": {"Missing": "Pensioner or not employed"},
    "INST_LATE_RATE_RECENCY_WEIGHTED": {"Missing": "No instalment history"},
    "BUREAU_ACTIVE_SHARE": {"Missing": "No record at other lenders"},
    "BUREAU_OPENED_COUNT_12M": {"Missing": "No record at other lenders"},
    "BUREAU_HISTORY_DAYS": {"Missing": "No record at other lenders"},
    "BUREAU_DEBT_TO_CREDIT": {"Missing": "No open loans at other lenders"},
    "BUREAU_CARD_UTILISATION": {"Missing": "No open card at other lenders"},
    "INST_DAYS_LATE_MAX_12M": {"Missing": "Nothing due in the last 12 months"},
    "PREV_REFUSED_RATE": {"Missing": "No past applications"},
    "PREV_DAYS_SINCE_LAST_REFUSAL": {"Missing": "No refusal on record"},
    "CC_UTILISATION_NOW": {"Missing": "No Home Credit card in use"},
    "CC_UTILISATION_MEAN": {"Missing": "No Home Credit card"},
    "CREDIT_TO_GOODS": {"Missing": "Not recorded"},
    "OCCUPATION_TYPE": {"Missing": "Not stated", OTHER: "Another occupation"},
    "ORGANIZATION_TYPE": {"XNA": "Pensioner or no employer", OTHER: "Another employer type"},
}


def format_value(value, unit):
    if unit == "percent":
        return f"{value * 100:.0f}%"
    if unit == "years":
        return f"{value:.1f} years"
    if unit == "months":
        return f"{value / 30.4:.0f} months"
    return f"{value:.2f} times"


def whole_number_answers(cuts, unit):
    """Cuts like 0.5 and 2.5 sit between whole numbers, so answers can be exact."""
    suffix = " days" if unit == "days" else ""
    starts = [0] + [math.ceil(c) for c in cuts]
    ends = [math.floor(c) for c in cuts]
    answers = [f"{s}{suffix}" if s == e else f"{s} to {e}{suffix}" for s, e in zip(starts, ends)]
    return answers + [f"{starts[-1]} or more{suffix}"]


def numeric_ranges(edges):
    return [f"{low} to {high}" for low, high in zip(edges, edges[1:])]


def numeric_answers(cuts, unit):
    if unit in ("count", "days"):
        return whole_number_answers(cuts, unit)
    edges = [format_value(c, unit) for c in cuts]
    if edges[0] == "0%":  # a cut this close to zero really means "none at all"
        return ["0%", f"Up to {edges[1]}"] + numeric_ranges(edges[1:]) + [f"Over {edges[-1]}"]
    answers = [f"Up to {edges[0]}"] + numeric_ranges(edges)
    return answers + [f"Over {edges[-1]}"]


def answers_for(feature, card, rows):
    special = SPECIAL_ANSWERS.get(feature, {})
    bins = card["bins"][feature]
    if bins["kind"] == "numeric":
        return numeric_answers(bins["cuts"], UNITS[feature]) + [special["Missing"]]
    return [special.get(row["bin"], row["bin"]) for row in rows]


def main():
    card = load_card(MODEL)
    typical = typical_points(card)
    max_risk = json.loads((MODELS / "cutoffs.json").read_text())["max_risk"][f"Scorecard, {MODEL}"]
    questions = []
    grouped = [c for columns in GROUPS.values() for c in columns]
    assert sorted(grouped) == sorted(card["features"]), "every scorecard line needs a place on the form"
    for group, columns in GROUPS.items():
        for feature in columns:
            rows = [r for r in card["points"] if r["feature"] == feature]
            answers = answers_for(feature, card, rows)
            assert len(answers) == len(rows), f"{feature}: answers don't match bins"
            most_common = max(range(len(rows)), key=lambda i: rows[i]["rows"])
            questions.append({"feature": feature, "group": group, "question": readable(feature), "default": most_common,
                              "typical": round(typical[feature], 1), "answers": [
                                  {"label": answer, "points": row["points"]} for answer, row in zip(answers, rows)]})
    OUT_FILE.write_text(json.dumps({
        "model": f"Scorecard, {MODEL}", "base_points": card["base_points"], "offset": OFFSET, "factor": FACTOR,
        "min_score": math.ceil(to_score(max_risk)), "max_risk": max_risk, "questions": questions}, indent=2), encoding="utf-8")
    print(f"wrote {OUT_FILE}")


if __name__ == "__main__":
    main()

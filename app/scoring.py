"""Score one applicant from their answers. Needs only app/scorecard.json."""
import json
import math
from pathlib import Path

CARD_FILE = Path(__file__).parent / "scorecard.json"
TOP_REASONS = 3


def load_card():
    return json.loads(CARD_FILE.read_text(encoding="utf-8"))


def score(card, answers):
    """`answers` maps each feature to its chosen answer's position in the list."""
    return card["base_points"] + sum(q["answers"][answers[q["feature"]]]["points"] for q in card["questions"])


def risk_of_default(card, total):
    return 1 / (1 + math.exp((total - card["offset"]) / card["factor"]))


def is_approved(card, total):
    return total >= card["min_score"]


def compare_with_typical(card, answers):
    """Each line's points against a typical applicant, biggest shortfall first."""
    lines = []
    for q in card["questions"]:
        answer = q["answers"][answers[q["feature"]]]
        lines.append({"question": q["question"], "answer": answer["label"], "points": answer["points"],
                      "gap": round(answer["points"] - q["typical"], 1)})
    return sorted(lines, key=lambda line: line["gap"])


def reasons(card, answers):
    """The lines pulling the score down most, and those lifting it most."""
    lines = compare_with_typical(card, answers)
    against = [line for line in lines[:TOP_REASONS] if line["gap"] < 0]
    helping = [line for line in reversed(lines[-TOP_REASONS:]) if line["gap"] > 0]
    return against, helping

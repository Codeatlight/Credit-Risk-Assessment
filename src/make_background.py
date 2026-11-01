"""Draw the app's background from real data: how dev applicants' scores are spread.

Each bar counts applicants in a 10-point score range, and bars below the cutoff are
tinted. The file holds only those counts, so no applicant records reach the app.

Run from the project root:  python -m src.make_background
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.export_app import MODEL, OUT_FILE
from src.features import OUT
from src.reasons import card_points, load_card
from src.scorecard import candidate_columns

BACKGROUND = Path("app/background.svg")
WIDTH, HEIGHT = 1600, 900
TALLEST_BAR = 640
BAR_GAP = 3
SCORE_RANGE = (400, 770)
STEP = 10
APPROVED_COLOUR = "#DCE6E4"
REFUSED_COLOUR = "#EFDAD6"


def main():
    numeric, categorical = candidate_columns()
    dev = pd.read_parquet(OUT, columns=["split", *numeric, *categorical], filters=[("split", "==", "dev")])
    card = load_card(MODEL)
    scores = card["base_points"] + card_points(card, dev).sum(axis=1)
    min_score = json.loads(OUT_FILE.read_text(encoding="utf-8"))["min_score"]

    edges = np.arange(SCORE_RANGE[0], SCORE_RANGE[1] + STEP, STEP)
    counts = np.histogram(scores, bins=edges)[0]
    bar_width = WIDTH / len(counts)
    bars = []
    for i, count in enumerate(counts):
        height = TALLEST_BAR * count / counts.max()
        colour = REFUSED_COLOUR if edges[i] < min_score else APPROVED_COLOUR
        bars.append(f'<rect x="{i * bar_width:.1f}" y="{HEIGHT - height:.1f}" width="{bar_width - BAR_GAP:.1f}" '
                    f'height="{height:.1f}" fill="{colour}"/>')
    BACKGROUND.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
                          f'preserveAspectRatio="none">{"".join(bars)}</svg>', encoding="utf-8")
    print(f"wrote {BACKGROUND}: {int(counts.sum()):,} of {len(scores):,} dev applicants in range")


if __name__ == "__main__":
    main()

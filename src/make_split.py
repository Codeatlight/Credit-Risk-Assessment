"""Set aside the final holdout before any modelling.

20% of applicants, stratified on TARGET with a fixed seed, so the split is the
same every time. Holdout rows are only used once, for the final results.

Run from the project root:  python -m src.make_split
"""
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
SEED = 42
HOLDOUT_SHARE = 0.2


def main():
    app = pd.read_csv(RAW / "application_train.csv", usecols=["SK_ID_CURR", "TARGET"])
    dev, holdout = train_test_split(app, test_size=HOLDOUT_SHARE, stratify=app["TARGET"], random_state=SEED)
    split = pd.concat([dev.assign(split="dev"), holdout.assign(split="holdout")])
    split[["SK_ID_CURR", "split"]].sort_values("SK_ID_CURR").to_csv(PROCESSED / "split.csv", index=False)
    print(split.groupby("split")["TARGET"].agg(["size", "sum", "mean"]).round(4).to_string())


if __name__ == "__main__":
    main()

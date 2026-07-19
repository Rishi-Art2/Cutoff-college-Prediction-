# """
# One-time helper script that generates data/cutoff_data.csv using NumPy.

# IMPORTANT: All college names below are FICTIONAL, and the cutoff numbers
# are randomly generated for demo purposes only. Replace data/cutoff_data.csv
# with your own real cutoff dataset (e.g. exported from official CAP / CET
# cutoff PDFs) before using this project for real predictions.
# """

import os

import numpy as np
import pandas as pd

np.random.seed(42)

# Always resolve paths relative to THIS script's own location -- not the
# current working directory -- so it works correctly no matter which folder
# your terminal happens to be open in when you run it.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(DATA_DIR, "cutoff_data.csv")

colleges = [
    "Alpha Institute of Technology",
    "Bright Future College of Engineering",
    "Metro City Engineering College",
    "Horizon Institute of Technology",
    "Greenfield College of Engineering",
    "Summit Engineering College",
    "Riverside Institute of Technology",
    "Skyline College of Engineering",
]

# Roughly reflects real-world demand patterns (CS/IT usually toughest)
branches = {
    "Computer Engineering": 97.0,
    "Information Technology": 95.0,
    "Electronics & Telecommunication": 88.0,
    "Electrical Engineering": 82.0,
    "Mechanical Engineering": 80.0,
    "Civil Engineering": 74.0,
}

# How much lower the cutoff typically is for each reserved category
category_offset = {
    "OPEN": 0.0,
    "EWS": -3.0,
    "OBC": -7.0,
    "SC": -22.0,
    "ST": -28.0,
}

# A fixed "prestige" offset per college so results aren't all identical
college_offset = {c: v for c, v in zip(colleges, np.linspace(6, -6, len(colleges)))}

rows = []
for college in colleges:
    for branch, base in branches.items():
        for category, cat_off in category_offset.items():
            jitter = np.random.normal(0, 1.5)
            cutoff_r1 = base + college_offset[college] + cat_off + jitter
            cutoff_r1 = float(np.clip(cutoff_r1, 35, 99.98))

            # CAP Round 2 / Round 3: cutoffs typically ease a little further
            # each round as top-ranked students migrate to better options and
            # remaining seats get filled by the next candidates in line.
            drop_r2 = np.random.uniform(2, 7)
            cutoff_r2 = float(np.clip(cutoff_r1 - drop_r2, 30, 99.98))

            drop_r3 = np.random.uniform(1, 5)
            cutoff_r3 = float(np.clip(cutoff_r2 - drop_r3, 30, 99.98))

            for round_name, cutoff in [
                ("Round 1", cutoff_r1),
                ("Round 2", cutoff_r2),
                ("Round 3", cutoff_r3),
            ]:
                rows.append(
                    {
                        "College": college,
                        "Branch": branch,
                        "Category": category,
                        "Round": round_name,
                        "Cutoff_Percentile": round(cutoff, 2),
                    }
                )

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_PATH, index=False)
print(f"Generated {len(df)} rows -> {OUTPUT_PATH}")
print(df.head(12))
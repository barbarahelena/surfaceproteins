#!/usr/bin/env python3
import sys
import pandas as pd

GRAM_MAP = {"gram-positive": "positive", "gram-negative": "negative"}

manifest = pd.read_csv("${manifest}", sep="\\t")

frames = []
for _, row in manifest.iterrows():
    df = pd.read_csv(row["filename"], index_col=0)
    df.insert(0, "sample_id", row["sample_id"])
    df.insert(1, "gram_stain", GRAM_MAP.get(row["gram"], "unknown"))
    frames.append(df)

merged = pd.concat(frames, ignore_index=True)
merged.to_csv("all_samples_mergedtable.csv", index=False)
print(f"Collated {len(manifest)} sample tables into all_samples_mergedtable.csv ({merged.shape[0]} rows, {merged.shape[1]} cols)")

with open("versions.yml", "w") as vf:
    vf.write('"${task.process}":\\n')
    vf.write(f"    python: {sys.version.split()[0]}\\n")
    vf.write(f"    pandas: {pd.__version__}\\n")

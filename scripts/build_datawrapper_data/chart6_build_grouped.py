"""
=============================================================================
  Chart 6 — Regional Variations in Education Discourse (Grouped Columns)
  
  Computes mean weight of 4 education topics by U.S. Census region.
  Uses deduped corpus (doc-topics_K25_S2.txt) + dataset.csv region_bin.
  
  Output format: rows = regions, columns = education topics.
  Datawrapper Grouped Columns will show 4 groups × 4 colored columns.
  
  Input files:
    - doc-topics_K25_S2.txt
    - dataset.csv           (has region_bin column)
    - topic_labels.csv
  
  Output:
    - regional_education_topics.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import os

DIR = r"."

DOC_TOPICS_FILE = os.path.join(DIR, "doc-topics_K25_S2.txt")
DATASET_FILE    = os.path.join(DIR, "dataset.csv")
LABELS_FILE     = os.path.join(DIR, "topic_labels.csv")
OUTPUT_FILE     = os.path.join(DIR, "regional_education_topics.csv")

# 4 education topics to compare
EDU_TOPICS = [
    "Chinese Educational Mission",
    "Classroom Instruction",
    "Public School Admission",
    "Missionary & Church Schools",
]

# Region display order
REGION_ORDER = ["West", "South", "Midwest", "Northeast"]


# ── 1. PARSE DOC-TOPICS ───────────────────────────────────────────────────
print("Step 1/4  Parsing doc-topics...")

rows = []
with open(DOC_TOPICS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) < 3:
            continue
        doc_id = parts[1]
        props  = [float(x) for x in parts[2:]]
        row = {"doc_id": doc_id}
        for i, p in enumerate(props):
            row[f"topic_{i}"] = p
        rows.append(row)

df_topics = pd.DataFrame(rows)
print(f"          → {len(df_topics):,} documents")


# ── 2. LOAD METADATA ──────────────────────────────────────────────────────
print("Step 2/4  Loading metadata...")

df_meta = pd.read_csv(DATASET_FILE, dtype=str, usecols=["doc_id", "region_bin"])
df_meta.columns = df_meta.columns.str.strip()
df_meta["doc_id"] = df_meta["doc_id"].str.strip()
df_topics["doc_id"] = df_topics["doc_id"].str.strip()
print(f"          → {len(df_meta):,} rows")


# ── 3. MAP TOPIC LABELS → COLUMN NAMES ────────────────────────────────────
print("Step 3/4  Loading topic labels...")

df_labels = pd.read_csv(LABELS_FILE, dtype=str)
df_labels.columns = df_labels.columns.str.strip()
df_labels["topic_num"] = df_labels["topic_id"].str.extract(r"(\d+)").astype(int)

edu_cols = {}
for _, row in df_labels.iterrows():
    if row["analytic_label"] in EDU_TOPICS:
        edu_cols[row["analytic_label"]] = f"topic_{row['topic_num']}"

print(f"          → Mapped: {edu_cols}")


# ── 4. MERGE & AGGREGATE BY REGION ────────────────────────────────────────
print("Step 4/4  Aggregating by region...")

df = df_topics.merge(df_meta, on="doc_id", how="left")

# Filter out Unknown region
df = df[df["region_bin"].isin(REGION_ORDER)].copy()

# Compute mean weight per region for each education topic
agg_dict = {col: "mean" for col in edu_cols.values()}
regional = df.groupby("region_bin").agg(agg_dict).reset_index()

# Also get doc counts per region
counts = df.groupby("region_bin").size().reset_index(name="n")
regional = regional.merge(counts, on="region_bin")

# Rename columns
rename = {col: label for label, col in edu_cols.items()}
regional = regional.rename(columns=rename)
regional = regional.rename(columns={"region_bin": "Region"})

# Convert to percentage
for label in EDU_TOPICS:
    regional[label] = (regional[label] * 100).round(2)

# Reorder rows
regional["_sort"] = regional["Region"].map({r: i for i, r in enumerate(REGION_ORDER)})
regional = regional.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

# Append region label with sample size: "West (n=469)"
regional["Region"] = regional.apply(lambda r: f"{r['Region']} (n={r['n']})", axis=1)

# Output: Region + 4 education topic columns
out = regional[["Region"] + EDU_TOPICS].copy()
out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Done! → {OUTPUT_FILE}")
print(f"{'='*60}")
print(out.to_string(index=False))

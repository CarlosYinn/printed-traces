"""
=============================================================================
  Chart 2 — Education Topics Over Time (Multiple Lines)
  
  Aggregates doc-topic weights by month for 4 education-related topics,
  producing a Datawrapper-ready CSV with one column per topic.
  
  Input files (same directory):
    - doc-topics_K25_S2.txt
    - dataset.csv
    - topic_labels.csv
  
  Output:
    - education_topics_over_time.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import os

DIR = r"."

DOC_TOPICS_FILE = os.path.join(DIR, "doc-topics_K25_S2.txt")
DATASET_FILE    = os.path.join(DIR, "dataset.csv")
LABELS_FILE     = os.path.join(DIR, "topic_labels.csv")
OUTPUT_FILE     = os.path.join(DIR, "education_topics_over_time.csv")

# ── 4 education topics to track ───────────────────────────────────────────
# These must match analytic_label in topic_labels.csv exactly
EDU_TOPICS = [
    "Chinese Educational Mission",
    "Classroom Instruction",
    "Public School Admission",
    "Missionary & Church Schools",
]


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

df_meta = pd.read_csv(DATASET_FILE, dtype=str)
df_meta.columns = df_meta.columns.str.strip()
df_meta["doc_id"] = df_meta["doc_id"].str.strip()
df_topics["doc_id"] = df_topics["doc_id"].str.strip()
print(f"          → {len(df_meta):,} rows")


# ── 3. LOAD TOPIC LABELS → find topic indices for our 4 topics ────────────
print("Step 3/4  Loading topic labels...")

df_labels = pd.read_csv(LABELS_FILE, dtype=str)
df_labels.columns = df_labels.columns.str.strip()
df_labels["topic_num"] = df_labels["topic_id"].str.extract(r"(\d+)").astype(int)

# Map analytic_label → topic column name
edu_topic_cols = {}
for _, row in df_labels.iterrows():
    if row["analytic_label"] in EDU_TOPICS:
        col_name = f"topic_{row['topic_num']}"
        edu_topic_cols[row["analytic_label"]] = col_name

print(f"          → Mapped {len(edu_topic_cols)} education topics:")
for label, col in edu_topic_cols.items():
    print(f"            {col} = {label}")

if len(edu_topic_cols) != 4:
    print("⚠️  Warning: expected 4 topics, check label names")


# ── 4. MERGE & AGGREGATE BY MONTH ─────────────────────────────────────────
print("Step 4/4  Merging and aggregating by month...")

df = df_topics.merge(df_meta[["doc_id", "Date"]], on="doc_id", how="left")

# Parse date → year_month
df["Date"] = df["Date"].str.strip().str[:10]
df["year_month"] = df["Date"].str[:7]  # "1880-09"

# Drop rows without valid year_month
df = df.dropna(subset=["year_month"])
df = df[df["year_month"].str.match(r"^\d{4}-\d{2}$")]

# Compute monthly mean weight for each education topic
agg_dict = {col: "mean" for col in edu_topic_cols.values()}
monthly = df.groupby("year_month").agg(agg_dict).reset_index()

# Also count articles per month (for reference)
counts = df.groupby("year_month").size().reset_index(name="article_count")
monthly = monthly.merge(counts, on="year_month")

# Rename columns: topic_N → readable label
rename_map = {col: label for label, col in edu_topic_cols.items()}
monthly = monthly.rename(columns=rename_map)

# Sort by year_month
monthly = monthly.sort_values("year_month").reset_index(drop=True)

# Convert weights to percentages (easier to read on Y axis)
for label in EDU_TOPICS:
    monthly[label] = (monthly[label] * 100).round(2)

# ── OUTPUT ─────────────────────────────────────────────────────────────────
# Datawrapper Multiple Lines expects:
#   first column = X axis (year_month)
#   remaining columns = one per line

out = monthly[["year_month"] + EDU_TOPICS + ["article_count"]]
out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Done! → {OUTPUT_FILE}")
print(f"   {len(out)} months × {len(out.columns)} columns")
print(f"   Date range: {out['year_month'].iloc[0]} – {out['year_month'].iloc[-1]}")
print(f"{'='*60}")

print("\n── Column names (for Datawrapper) ──")
for c in out.columns:
    print(f"   {c}")

print("\n── Monthly averages (%) ──")
for label in EDU_TOPICS:
    print(f"   {label}: {monthly[label].mean():.2f}%")

print("\n── Key event months (for annotations) ──")
print("   1881-06  CEM recall ordered (students recalled to China)")
print("   1882-05  Chinese Exclusion Act signed")
print("   1885-01  Tape v. Hurley ruling")
print("   1885-04  Separate school bill passed (CA)")
print("   1885-09  Rock Springs massacre")

"""
=============================================================================
  Chart 7 — Keyword × Topic Heatmap (Datawrapper Table)
  
  For each of the 7 search keywords, computes the mean weight of every
  non-NOISE topic. Outputs a pivot table ready for Datawrapper Table
  with heatmap cell coloring.
  
  Two versions:
    A) All topics (wide table, full picture)
    B) Education topics only (4 columns, focused)
  
  Uses deduped corpus.
  
  Input:
    - doc-topics_K25_S2.txt
    - dataset.csv (has Keyword column)
    - topic_labels.csv
  
  Output:
    - keyword_topic_heatmap_full.csv    (all non-NOISE topics)
    - keyword_topic_heatmap_edu.csv     (4 education topics only)
=============================================================================
"""

import pandas as pd
import numpy as np
import os

DIR = r"."

DOC_TOPICS_FILE = os.path.join(DIR, "doc-topics_K25_S2.txt")
DATASET_FILE    = os.path.join(DIR, "dataset.csv")
LABELS_FILE     = os.path.join(DIR, "topic_labels.csv")
OUT_FULL        = os.path.join(DIR, "keyword_topic_heatmap_full.csv")
OUT_EDU         = os.path.join(DIR, "keyword_topic_heatmap_edu.csv")

EDU_TOPICS = [
    "Chinese Educational Mission",
    "Classroom Instruction",
    "Public School Admission",
    "Missionary & Church Schools",
]

# Keyword display order (by count descending)
KEYWORD_ORDER = [
    "Chinese student",
    "Chinese boy",
    "Chinese children",
    "Chinese girl",
    "Chinese school",
    "Chinese child",
    "Chinese education",
]


# ── 1. PARSE DOC-TOPICS ───────────────────────────────────────────────────
print("Step 1/3  Parsing doc-topics...")

rows = []
with open(DOC_TOPICS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) < 3:
            continue
        doc_id = parts[1].strip()
        props  = [float(x) for x in parts[2:]]
        row = {"doc_id": doc_id}
        for i, p in enumerate(props):
            row[f"topic_{i}"] = p
        rows.append(row)

df_topics = pd.DataFrame(rows)
print(f"          → {len(df_topics):,} documents")


# ── 2. LOAD METADATA & LABELS ─────────────────────────────────────────────
print("Step 2/3  Loading metadata and labels...")

df_meta = pd.read_csv(DATASET_FILE, dtype=str, usecols=["doc_id", "Keyword"])
df_meta.columns = df_meta.columns.str.strip()
df_meta["doc_id"] = df_meta["doc_id"].str.strip()

df_labels = pd.read_csv(LABELS_FILE, dtype=str)
df_labels.columns = df_labels.columns.str.strip()
df_labels["topic_num"] = df_labels["topic_id"].str.extract(r"(\d+)").astype(int)

# Build topic column → label map (exclude NOISE)
topic_col_to_label = {}
for _, row in df_labels.iterrows():
    if row["exclude"] == "yes":
        continue
    topic_col_to_label[f"topic_{row['topic_num']}"] = row["analytic_label"]

# Also get category for sorting
label_to_category = dict(zip(df_labels["analytic_label"], df_labels["category"]))

topic_cols = list(topic_col_to_label.keys())
print(f"          → {len(topic_cols)} non-NOISE topics")


# ── 3. MERGE & COMPUTE ────────────────────────────────────────────────────
print("Step 3/3  Computing keyword × topic means...")

df = df_topics.merge(df_meta, on="doc_id", how="left")
df = df.dropna(subset=["Keyword"])

# Compute mean weight per keyword for each topic
results = []
for kw in KEYWORD_ORDER:
    subset = df[df["Keyword"] == kw]
    n = len(subset)
    row = {"Keyword": f"{kw} (n={n})"}
    for col in topic_cols:
        label = topic_col_to_label[col]
        row[label] = round(subset[col].mean() * 100, 2)
    results.append(row)

# Also add corpus average as reference row
row_avg = {"Keyword": f"Corpus average (n={len(df)})"}
for col in topic_cols:
    label = topic_col_to_label[col]
    row_avg[label] = round(df[col].mean() * 100, 2)
results.append(row_avg)

df_result = pd.DataFrame(results)

# ── SORT COLUMNS BY CATEGORY ─────────────────────────────────────────────
# Group topic columns by category, then by weight descending within category
topic_labels_sorted = sorted(
    topic_col_to_label.values(),
    key=lambda l: (
        list(label_to_category.values()).index(label_to_category.get(l, ""))
        if label_to_category.get(l, "") in label_to_category.values() else 99,
        -df_result[l].iloc[:-1].mean()  # exclude corpus avg row for sorting
    )
)

# ── OUTPUT A: CATEGORY-LEVEL TABLE (10 categories) ───────────────────────
# Aggregate individual topic columns into their parent categories
CATEGORY_ORDER = [
    "Chinese Educational Mission",
    "Education & Schools",
    "Children & Family",
    "Law, Politics & Exclusion",
    "Violence & War",
    "Commerce & Material Culture",
    "Daily Life & Urban Space",
    "Land, Migration & Labor",
    "Culture, Perception & Acculturation",
    "Diplomacy",
]

# Group topic labels by category
cat_to_labels = {}
for label in topic_col_to_label.values():
    cat = label_to_category.get(label, "")
    if cat:
        cat_to_labels.setdefault(cat, []).append(label)

# Sum topic weights within each category
out_full = df_result[["Keyword"]].copy()
for cat in CATEGORY_ORDER:
    labels_in_cat = cat_to_labels.get(cat, [])
    if labels_in_cat:
        out_full[cat] = df_result[labels_in_cat].sum(axis=1).round(2)
    else:
        out_full[cat] = 0.0

out_full.to_csv(OUT_FULL, index=False, encoding="utf-8-sig")
print(f"\n✅ Category table → {OUT_FULL}")
print(f"   {len(out_full)} rows × {len(out_full.columns)} columns")

# ── OUTPUT B: EDUCATION TOPICS ONLY ───────────────────────────────────────
edu_cols = [t for t in topic_labels_sorted if t in EDU_TOPICS]
out_edu = df_result[["Keyword"] + edu_cols].copy()
out_edu.to_csv(OUT_EDU, index=False, encoding="utf-8-sig")
print(f"✅ Edu table  → {OUT_EDU}")
print(f"   {len(out_edu)} rows × {len(out_edu.columns)} columns")

# ── PREVIEW ───────────────────────────────────────────────────────────────
print("\n── Education topics heatmap ──")
print(out_edu.to_string(index=False))

print("\n── Full table (first 5 columns) ──")
preview_cols = ["Keyword"] + topic_labels_sorted[:5]
print(df_result[preview_cols].to_string(index=False))
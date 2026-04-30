"""
=============================================================================
  Chart 3 — Corpus Composition by Dominant Topic (Stacked Bars)
  
  Uses ALL corpus (all_doc-topics_K25_S1.txt + all_topic_labels.csv)
  to get the full sub-topic breakdown, especially the 4 CEM sub-topics
  that are merged into one in the deduped corpus.
  
  Input files (same directory):
    - all_doc-topics_K25_S1.txt    ← all corpus
    - all_topic_labels.csv         ← all corpus labels
    - dataset.csv                  ← metadata (for doc_id matching)
  
  Output:
    - corpus_composition_stacked.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import os

DIR = r"."

DOC_TOPICS_FILE = os.path.join(DIR, "all_doc-topics_K25_S1.txt")   # ← ALL corpus
LABELS_FILE     = os.path.join(DIR, "all_topic_labels.csv")         # ← ALL corpus labels
OUTPUT_FILE     = os.path.join(DIR, "corpus_composition_stacked.csv")

# Category display order
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


# ── 1. PARSE DOC-TOPICS ───────────────────────────────────────────────────
print("Step 1/3  Parsing all_doc-topics...")

rows = []
with open(DOC_TOPICS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) < 3:
            continue
        doc_id = parts[1]
        props  = [float(x) for x in parts[2:]]
        dom    = int(np.argmax(props))
        rows.append({"doc_id": doc_id, "dominant_topic": dom})

df_topics = pd.DataFrame(rows)
print(f"          → {len(df_topics):,} documents (all corpus)")


# ── 2. LOAD TOPIC LABELS (all corpus) ─────────────────────────────────────
print("Step 2/3  Loading all_topic_labels...")

df_labels = pd.read_csv(LABELS_FILE, dtype=str)
df_labels.columns = df_labels.columns.str.strip()
df_labels["topic_num"] = df_labels["topic_id"].str.extract(r"(\d+)").astype(int)

label_map    = dict(zip(df_labels["topic_num"], df_labels["analytic_label"]))
category_map = dict(zip(df_labels["topic_num"], df_labels["category"]))
exclude_map  = dict(zip(df_labels["topic_num"], df_labels["exclude"]))

df_topics["topic_label"] = df_topics["dominant_topic"].map(label_map)
df_topics["category"]    = df_topics["dominant_topic"].map(category_map)
df_topics["exclude"]     = df_topics["dominant_topic"].map(exclude_map)

# Filter out NOISE
n0 = len(df_topics)
df_topics = df_topics[df_topics["exclude"] != "yes"].copy()
print(f"          → {n0 - len(df_topics)} NOISE removed, {len(df_topics):,} remain")

# Show CEM sub-topics found
cem_topics = df_topics[df_topics["category"] == "Chinese Educational Mission"]["topic_label"].unique()
print(f"          → CEM sub-topics found: {list(cem_topics)}")


# ── 3. COUNT & PIVOT ──────────────────────────────────────────────────────
print("Step 3/3  Counting and pivoting...")

counts = df_topics.groupby(["category", "topic_label"]).size().reset_index(name="count")

# Pivot: rows = category, columns = topic_label, values = count
pivot = counts.pivot(index="category", columns="topic_label", values="count").fillna(0).astype(int)

# Reorder rows by CATEGORY_ORDER
pivot = pivot.reindex([c for c in CATEGORY_ORDER if c in pivot.index])

# Sort columns by total count descending (largest sub-topics first)
col_totals = pivot.sum().sort_values(ascending=False)
pivot = pivot[col_totals.index]

# Drop columns that are all zeros
pivot = pivot.loc[:, (pivot != 0).any()]

# Add row totals
pivot["_TOTAL"] = pivot.sum(axis=1)

# Reset index
pivot = pivot.reset_index()
pivot = pivot.rename(columns={"category": "Category"})

# ── OUTPUT ─────────────────────────────────────────────────────────────────
pivot.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Done! → {OUTPUT_FILE}")
print(f"   {len(pivot)} categories × {len(pivot.columns) - 2} sub-topics")
print(f"{'='*60}")

print("\n── Result ──")
print(pivot.to_string(index=False))

print("\n── Sub-topics per category ──")
for _, row in pivot.iterrows():
    cat = row["Category"]
    subtopics = [(c, row[c]) for c in pivot.columns
                 if c not in ["Category", "_TOTAL"] and row[c] > 0]
    subtopics.sort(key=lambda x: x[1], reverse=True)
    print(f"\n   {cat} (total: {row['_TOTAL']})")
    for name, ct in subtopics:
        print(f"     {ct:>4}  {name}")
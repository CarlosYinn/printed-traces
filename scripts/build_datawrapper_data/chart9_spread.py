"""
=============================================================================
  Chart 9 — Topic Spread: Presence vs. Propagation (Scatter Plot)
  
  For each of the 10 categories, computes:
    - total_articles: how many articles this category dominates (presence)
    - avg_reprint_count: mean reprint count of those articles (propagation)
    - pct_original: % of articles that are originals vs reprints
    - avg_sim_score: mean text similarity score (text fidelity)
  
  Uses ALL corpus (includes reprints).
  
  X = total_articles, Y = avg_reprint_count
  Bubble size = avg_sim_score (optional)
  Color = category color
  
  Input:
    - all_doc-topics_K25_S1.txt
    - dataset.csv
    - all_topic_labels.csv
  
  Output:
    - topic_spread_scatter.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import os

DIR = r"."

DOC_TOPICS_FILE = os.path.join(DIR, "all_doc-topics_K25_S1.txt")
DATASET_FILE    = os.path.join(DIR, "dataset.csv")
LABELS_FILE     = os.path.join(DIR, "all_topic_labels.csv")
OUTPUT_FILE     = os.path.join(DIR, "topic_spread_scatter.csv")

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

CATEGORY_COLORS = {
    "Chinese Educational Mission": "#fe640b",
    "Education & Schools": "#209fb5",
    "Children & Family": "#40a02b",
    "Law, Politics & Exclusion": "#8839ef",
    "Violence & War": "#d20f39",
    "Commerce & Material Culture": "#179299",
    "Daily Life & Urban Space": "#1e66f5",
    "Land, Migration & Labor": "#df8e1d",
    "Culture, Perception & Acculturation": "#ea76cb",
    "Diplomacy": "#7287fd",
}


# ── 1. PARSE DOC-TOPICS → DOMINANT CATEGORY ───────────────────────────────
print("Step 1/3  Parsing doc-topics → dominant category...")

# Load labels
labels = pd.read_csv(LABELS_FILE, dtype=str)
labels.columns = labels.columns.str.strip()
labels["topic_num"] = labels["topic_id"].str.extract(r"(\d+)").astype(int)

cat_map = {}
exclude_set = set()
for _, row in labels.iterrows():
    t = row["topic_num"]
    if row["exclude"] == "yes":
        exclude_set.add(t)
    else:
        cat_map[t] = row.get("category", "Unknown")

# Parse doc-topics
rows = []
with open(DOC_TOPICS_FILE) as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) < 3:
            continue
        doc_id = parts[1].strip()
        props = [float(x) for x in parts[2:]]
        
        # Sum proportions by category, pick dominant
        cat_weights = {}
        for t, p in enumerate(props):
            if t in exclude_set:
                continue
            cat = cat_map.get(t, "Unknown")
            cat_weights[cat] = cat_weights.get(cat, 0) + p
        
        dominant_cat = max(cat_weights, key=cat_weights.get) if cat_weights else "Unknown"
        rows.append({"doc_id": doc_id, "dominant_category": dominant_cat})

df_docs = pd.DataFrame(rows)
print(f"          → {len(df_docs):,} documents")


# ── 2. MERGE WITH METADATA ────────────────────────────────────────────────
print("Step 2/3  Merging with dataset metadata...")

df_meta = pd.read_csv(DATASET_FILE, dtype=str,
                       usecols=["doc_id", "reprint_count", "sim_score", "is_original"])
df_meta.columns = df_meta.columns.str.strip()
df_meta["doc_id"] = df_meta["doc_id"].str.strip()
df_meta["reprint_count"] = pd.to_numeric(df_meta["reprint_count"], errors="coerce").fillna(0)
df_meta["sim_score"] = pd.to_numeric(df_meta["sim_score"], errors="coerce")
df_meta["is_original_num"] = (df_meta["is_original"].str.strip().str.lower() == "true").astype(int)

df = df_docs.merge(df_meta, on="doc_id", how="left")
print(f"          → {len(df):,} rows merged")


# ── 3. AGGREGATE BY CATEGORY ──────────────────────────────────────────────
print("Step 3/3  Aggregating by category...")

agg = df.groupby("dominant_category").agg(
    total_articles=("doc_id", "count"),
    avg_reprint_count=("reprint_count", "mean"),
    avg_sim_score=("sim_score", "mean"),
    pct_original=("is_original_num", "mean"),
    total_reprints=("reprint_count", "sum"),
).reset_index()

# Round
agg["avg_reprint_count"] = agg["avg_reprint_count"].round(2)
agg["avg_sim_score"] = agg["avg_sim_score"].round(3)
agg["pct_original"] = (agg["pct_original"] * 100).round(1)

# Add color
agg["category_color"] = agg["dominant_category"].map(CATEGORY_COLORS)

# Reorder
cat_order_map = {c: i for i, c in enumerate(CATEGORY_ORDER)}
agg["_sort"] = agg["dominant_category"].map(cat_order_map).fillna(99)
agg = agg.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

# Rename for Datawrapper
out = agg.rename(columns={
    "dominant_category": "Category",
    "total_articles": "Total Articles",
    "avg_reprint_count": "Avg Reprint Count",
    "avg_sim_score": "Text Fidelity",
    "pct_original": "% Original",
    "total_reprints": "Total Reprints",
})

out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Done! → {OUTPUT_FILE}")
print(f"   {len(out)} categories")
print(f"{'='*60}")

print(f"\n{'Category':<42} {'Articles':>8} {'AvgRepr':>8} {'Fidelity':>8} {'%Orig':>6}")
print("-" * 76)
for _, r in out.iterrows():
    print(f"{r['Category']:<42} {r['Total Articles']:>8} {r['Avg Reprint Count']:>8.2f} {r['Text Fidelity']:>8.3f} {r['% Original']:>5.1f}%")

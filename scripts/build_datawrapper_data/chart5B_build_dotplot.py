"""
=============================================================================
  Chart 5 — Deduped vs. All: Category-Level Discourse Shift (Multiple Donuts)
  
  Aggregates topic weights to 10 categories for both corpora.
  Output format for Datawrapper Multiple Donuts:
    Column 1 = category name
    Column 2 = Deduped value
    Column 3 = All value
  
  Small categories (< 3% in BOTH corpora) are merged into "Other".
  
  Uses:
    - doc-topics (both)
    - topic_labels / all_topic_labels
    - merged_topic_labels (category order + colors)
=============================================================================
"""

import pandas as pd
import numpy as np
import os

DIR = r"."

DEDUP_TOPICS  = os.path.join(DIR, "doc-topics_K25_S2.txt")
ALL_TOPICS    = os.path.join(DIR, "all_doc-topics_K25_S1.txt")
DEDUP_LABELS  = os.path.join(DIR, "topic_labels.csv")
ALL_LABELS    = os.path.join(DIR, "all_topic_labels.csv")
OUTPUT_FILE   = os.path.join(DIR, "category_donuts.csv")

# Threshold: categories below this in BOTH corpora get merged into "Other"
MERGE_THRESHOLD = 3.0  # percent

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


def parse_doc_topics(filepath):
    rows = []
    with open(filepath) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            rows.append([float(x) for x in parts[2:]])
    n = len(rows[0])
    return pd.DataFrame(rows, columns=[f"topic_{i}" for i in range(n)])


def compute_category_means(df, labels_file):
    labels = pd.read_csv(labels_file, dtype=str)
    labels.columns = labels.columns.str.strip()
    labels["topic_num"] = labels["topic_id"].str.extract(r"(\d+)").astype(int)
    
    cat_topics = {}
    for _, row in labels.iterrows():
        if row["exclude"] == "yes":
            continue
        cat = row.get("category", "")
        if not cat:
            continue
        col = f"topic_{row['topic_num']}"
        if col in df.columns:
            cat_topics.setdefault(cat, []).append(col)
    
    cat_weights = {}
    for cat, cols in cat_topics.items():
        cat_weights[cat] = round(df[cols].sum(axis=1).mean() * 100, 2)
    
    return cat_weights


# ── COMPUTE ───────────────────────────────────────────────────────────────
print("Computing category means...")

df_ded = parse_doc_topics(DEDUP_TOPICS)
ded_cats = compute_category_means(df_ded, DEDUP_LABELS)
print(f"  Deduped: {len(df_ded):,} docs")

df_all = parse_doc_topics(ALL_TOPICS)
all_cats = compute_category_means(df_all, ALL_LABELS)
print(f"  All:     {len(df_all):,} docs")


# ── MERGE SMALL CATEGORIES ────────────────────────────────────────────────
print(f"\nMerging categories below {MERGE_THRESHOLD}% in both corpora...")

other_ded = 0
other_all = 0
keep_cats = []

for cat in CATEGORY_ORDER:
    d = ded_cats.get(cat, 0)
    a = all_cats.get(cat, 0)
    if d < MERGE_THRESHOLD and a < MERGE_THRESHOLD:
        print(f"  → Merged: {cat} (ded={d:.1f}%, all={a:.1f}%)")
        other_ded += d
        other_all += a
    else:
        keep_cats.append(cat)

# ── BUILD OUTPUT ──────────────────────────────────────────────────────────
rows = []
for cat in keep_cats:
    rows.append({
        "Category": cat,
        f"Deduped ({len(df_ded):,} articles)": ded_cats.get(cat, 0),
        f"All ({len(df_all):,} articles)": all_cats.get(cat, 0),
    })

# Add "Other" if any categories were merged
if other_ded > 0 or other_all > 0:
    rows.append({
        "Category": "Other",
        f"Deduped ({len(df_ded):,} articles)": round(other_ded, 2),
        f"All ({len(df_all):,} articles)": round(other_all, 2),
    })

out = pd.DataFrame(rows)
out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Done! → {OUTPUT_FILE}")
print(f"   {len(out)} slices (categories)")
print(f"{'='*60}")

print(f"\n{'Category':<42} {'Deduped':>8} {'All':>8} {'Diff':>8}")
print("-" * 68)
for _, r in out.iterrows():
    d = r.iloc[1]
    a = r.iloc[2]
    diff = a - d
    arrow = "↑" if diff > 0.5 else ("↓" if diff < -0.5 else "≈")
    print(f"{r['Category']:<42} {d:>7.1f}% {a:>7.1f}% {arrow}{abs(diff):>6.1f}")
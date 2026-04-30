"""
=============================================================================
  Chart 4 — Original vs. Reprint Topic Difference (Bar Chart, diverging)
  
  Single column `difference`: positive = amplified by reprinting,
  negative = confined to local press.
  Datawrapper Bar Chart auto-diverges from zero baseline.
  
  Input files (same directory):
    - all_doc-topics_K25_S1.txt
    - dataset.csv
    - all_topic_labels.csv
  
  Output:
    - original_vs_reprint_diverging.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import os

DIR = r"."

DOC_TOPICS_FILE = os.path.join(DIR, "all_doc-topics_K25_S1.txt")
DATASET_FILE    = os.path.join(DIR, "dataset.csv")
LABELS_FILE     = os.path.join(DIR, "all_topic_labels.csv")
OUTPUT_FILE     = os.path.join(DIR, "original_vs_reprint_diverging.csv")


# ── 1. PARSE DOC-TOPICS ───────────────────────────────────────────────────
print("Step 1/4  Parsing all_doc-topics...")

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

if "is_reprint" in df_meta.columns:
    df_meta["_is_reprint"] = df_meta["is_reprint"].str.strip().str.lower() == "true"
elif "is_original" in df_meta.columns:
    df_meta["_is_reprint"] = df_meta["is_original"].str.strip().str.lower() != "true"
else:
    print("⚠️  No is_reprint or is_original column found!")
    exit(1)

print(f"          → Originals: {(~df_meta['_is_reprint']).sum():,}")
print(f"          → Reprints:  {df_meta['_is_reprint'].sum():,}")


# ── 3. LOAD TOPIC LABELS ──────────────────────────────────────────────────
print("Step 3/4  Loading all_topic_labels...")

df_labels = pd.read_csv(LABELS_FILE, dtype=str)
df_labels.columns = df_labels.columns.str.strip()
df_labels["topic_num"] = df_labels["topic_id"].str.extract(r"(\d+)").astype(int)

label_map    = dict(zip(df_labels["topic_num"], df_labels["analytic_label"]))
category_map = dict(zip(df_labels["topic_num"], df_labels["category"]))
color_map    = dict(zip(df_labels["topic_num"], df_labels["color"]))
exclude_set  = set(df_labels[df_labels["exclude"] == "yes"]["topic_num"])

topic_nums = [i for i in range(len(df_labels)) if i not in exclude_set]
print(f"          → {len(topic_nums)} non-NOISE topics")


# ── 4. COMPUTE DIFFERENCE ─────────────────────────────────────────────────
print("Step 4/4  Computing differences...")

df = df_topics.merge(df_meta[["doc_id", "_is_reprint"]], on="doc_id", how="left")
df = df.dropna(subset=["_is_reprint"])

originals = df[~df["_is_reprint"]]
reprints  = df[df["_is_reprint"]]

results = []
for t in topic_nums:
    col = f"topic_{t}"
    orig_mean    = originals[col].mean() * 100
    reprint_mean = reprints[col].mean() * 100
    diff         = reprint_mean - orig_mean

    results.append({
        "Topic": label_map.get(t, col),
        "Difference": round(diff, 2),
        "Original (%)": round(orig_mean, 2),
        "Reprint (%)": round(reprint_mean, 2),
        "category": category_map.get(t, ""),
    })

df_result = pd.DataFrame(results)

# Sort by difference: most positive on top, most negative at bottom
df_result = df_result.sort_values("Difference", ascending=False).reset_index(drop=True)

# Output: Topic + Difference (single value column)
# Keep Original/Reprint columns for tooltip reference but Datawrapper
# only needs Topic + Difference for the bar chart
out = df_result[["Topic", "Difference", "Original (%)", "Reprint (%)"]].copy()
out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Done! → {OUTPUT_FILE}")
print(f"   {len(out)} topics")
print(f"{'='*60}")

print("\n── Amplified by reprinting (positive) ──")
for _, r in df_result[df_result["Difference"] > 0].iterrows():
    print(f"   +{r['Difference']:>5.2f}  {r['Topic']}")

print("\n── Confined to local press (negative) ──")
for _, r in df_result[df_result["Difference"] < 0].iterrows():
    print(f"   {r['Difference']:>5.2f}  {r['Topic']}")
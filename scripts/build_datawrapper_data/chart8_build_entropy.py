"""
=============================================================================
  Chart 8 — Discourse Diversity Over Time (Area Chart)
  
  Computes monthly Shannon entropy of topic distributions.
  High entropy = diverse discourse (many topics equally represented)
  Low entropy = concentrated discourse (few topics dominate)
  
  Uses deduped corpus.
  
  Input:
    - doc-topics_K25_S2.txt
    - dataset.csv (for date)
    - topic_labels.csv (for NOISE exclusion)
  
  Output:
    - discourse_diversity.csv
=============================================================================
"""

import pandas as pd
import numpy as np
from scipy.stats import entropy
import os

DIR = r"."

DOC_TOPICS_FILE = os.path.join(DIR, "doc-topics_K25_S2.txt")
DATASET_FILE    = os.path.join(DIR, "dataset.csv")
LABELS_FILE     = os.path.join(DIR, "topic_labels.csv")
OUTPUT_FILE     = os.path.join(DIR, "discourse_diversity.csv")


# ── 1. IDENTIFY NON-NOISE TOPICS ──────────────────────────────────────────
print("Step 1/4  Loading topic labels...")

df_labels = pd.read_csv(LABELS_FILE, dtype=str)
df_labels.columns = df_labels.columns.str.strip()
df_labels["topic_num"] = df_labels["topic_id"].str.extract(r"(\d+)").astype(int)

exclude_set = set(df_labels[df_labels["exclude"] == "yes"]["topic_num"])
valid_cols = [f"topic_{i}" for i in range(len(df_labels)) if i not in exclude_set]
print(f"          → {len(valid_cols)} non-NOISE topics, {len(exclude_set)} excluded")


# ── 2. PARSE DOC-TOPICS ───────────────────────────────────────────────────
print("Step 2/4  Parsing doc-topics...")

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


# ── 3. LOAD DATES ─────────────────────────────────────────────────────────
print("Step 3/4  Loading dates...")

df_meta = pd.read_csv(DATASET_FILE, dtype=str, usecols=["doc_id", "Date"])
df_meta.columns = df_meta.columns.str.strip()
df_meta["doc_id"] = df_meta["doc_id"].str.strip()

df = df_topics.merge(df_meta, on="doc_id", how="left")
df["Date"] = df["Date"].str.strip().str[:10]
df["year_month"] = df["Date"].str[:7]
df = df.dropna(subset=["year_month"])
df = df[df["year_month"].str.match(r"^\d{4}-\d{2}$")]
print(f"          → {df['year_month'].nunique()} months")


# ── 4. COMPUTE MONTHLY ENTROPY ────────────────────────────────────────────
print("Step 4/4  Computing Shannon entropy...")

def doc_entropy(row):
    """Shannon entropy of a single document's topic distribution (non-NOISE only)."""
    probs = row[valid_cols].values.astype(float)
    # Renormalize after excluding NOISE
    total = probs.sum()
    if total == 0:
        return 0
    probs = probs / total
    return entropy(probs)

df["entropy"] = df.apply(doc_entropy, axis=1)

# Monthly aggregation
monthly = df.groupby("year_month").agg(
    avg_entropy=("entropy", "mean"),
    median_entropy=("entropy", "median"),
    article_count=("doc_id", "count"),
).reset_index()

monthly = monthly.sort_values("year_month").reset_index(drop=True)

# Round
monthly["avg_entropy"] = monthly["avg_entropy"].round(3)
monthly["median_entropy"] = monthly["median_entropy"].round(3)

# ── OUTPUT ─────────────────────────────────────────────────────────────────
out = monthly[["year_month", "avg_entropy", "article_count"]].copy()
out.columns = ["Month", "Discourse Diversity", "Articles"]
out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Done! → {OUTPUT_FILE}")
print(f"   {len(out)} months")
print(f"   Entropy range: {out['Discourse Diversity'].min():.3f} – {out['Discourse Diversity'].max():.3f}")
print(f"{'='*60}")

# ── KEY EVENTS ────────────────────────────────────────────────────────────
print("\n── Entropy at key events ──")
events = {
    "1881-06": "CEM recall",
    "1882-05": "Exclusion Act",
    "1882-06": "Month after Act",
    "1885-01": "Tape v. Hurley",
    "1885-09": "Rock Springs",
}
for ym, label in events.items():
    row = monthly[monthly["year_month"] == ym]
    if not row.empty:
        val = row.iloc[0]["avg_entropy"]
        n = row.iloc[0]["article_count"]
        print(f"   {ym}  {label:<20}  entropy={val:.3f}  (n={n})")
    else:
        print(f"   {ym}  {label:<20}  (no data)")

print("\n── Monthly overview ──")
print(out.to_string(index=False))

"""
=============================================================================
  RAWGraphs Alluvial — Discourse Flow: Deduped → All Category Assignment
  
  For each of the 1,100 shared articles, finds:
    - Dominant category in deduped model
    - Dominant category in all model
  Then counts flows between category pairs.
  
  The 425 reprint-only articles get a special "Source: Reprints" origin.
  
  Output: alluvial_category_flow.csv
    Columns: Deduped Category, All Category, Count
    
  RAWGraphs Alluvial mapping:
    Steps = [Deduped Category, All Category]
    Size  = Count
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
OUTPUT_FILE   = os.path.join(DIR, "alluvial_category_flow.csv")


def parse_doc_topics_with_ids(filepath):
    rows = []
    with open(filepath) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue
            doc_id = parts[1].strip()
            props = [float(x) for x in parts[2:]]
            rows.append({"doc_id": doc_id, "props": props})
    return rows


def get_dominant_category(props, labels_file):
    """Given a list of topic proportions, return the dominant category."""
    labels = pd.read_csv(labels_file, dtype=str)
    labels.columns = labels.columns.str.strip()
    labels["topic_num"] = labels["topic_id"].str.extract(r"(\d+)").astype(int)
    
    # Build topic_num → category map, excluding NOISE
    cat_map = {}
    exclude = set()
    for _, row in labels.iterrows():
        t = row["topic_num"]
        if row["exclude"] == "yes":
            exclude.add(t)
        else:
            cat_map[t] = row.get("category", "Unknown")
    
    # Sum proportions by category
    cat_weights = {}
    for t, p in enumerate(props):
        if t in exclude:
            continue
        cat = cat_map.get(t, "Unknown")
        cat_weights[cat] = cat_weights.get(cat, 0) + p
    
    if not cat_weights:
        return "Unknown"
    return max(cat_weights, key=cat_weights.get)


# ── 1. LOAD LABEL MAPPINGS ────────────────────────────────────────────────
print("Step 1/4  Loading labels...")

ded_labels = pd.read_csv(DEDUP_LABELS, dtype=str)
ded_labels.columns = ded_labels.columns.str.strip()
ded_labels["topic_num"] = ded_labels["topic_id"].str.extract(r"(\d+)").astype(int)
ded_cat_map = {}
ded_exclude = set()
for _, row in ded_labels.iterrows():
    t = row["topic_num"]
    if row["exclude"] == "yes":
        ded_exclude.add(t)
    else:
        ded_cat_map[t] = row.get("category", "Unknown")

all_labels = pd.read_csv(ALL_LABELS, dtype=str)
all_labels.columns = all_labels.columns.str.strip()
all_labels["topic_num"] = all_labels["topic_id"].str.extract(r"(\d+)").astype(int)
all_cat_map = {}
all_exclude = set()
for _, row in all_labels.iterrows():
    t = row["topic_num"]
    if row["exclude"] == "yes":
        all_exclude.add(t)
    else:
        all_cat_map[t] = row.get("category", "Unknown")


def dominant_cat(props, cat_map, exclude):
    cat_weights = {}
    for t, p in enumerate(props):
        if t in exclude:
            continue
        cat = cat_map.get(t, "Unknown")
        cat_weights[cat] = cat_weights.get(cat, 0) + p
    if not cat_weights:
        return "Unknown"
    return max(cat_weights, key=cat_weights.get)


# ── 2. PARSE BOTH DOC-TOPICS ─────────────────────────────────────────────
print("Step 2/4  Parsing deduped doc-topics...")
ded_docs = parse_doc_topics_with_ids(DEDUP_TOPICS)
ded_dict = {}
for d in ded_docs:
    ded_dict[d["doc_id"]] = dominant_cat(d["props"], ded_cat_map, ded_exclude)
print(f"          → {len(ded_dict):,} documents")

print("Step 3/4  Parsing all doc-topics...")
all_docs = parse_doc_topics_with_ids(ALL_TOPICS)
all_dict = {}
for d in all_docs:
    all_dict[d["doc_id"]] = dominant_cat(d["props"], all_cat_map, all_exclude)
print(f"          → {len(all_dict):,} documents")


# ── 3. BUILD FLOW TABLE ──────────────────────────────────────────────────
print("Step 4/4  Building alluvial flows...")

flows = {}

# Shared docs (1,100): track category change
shared = set(ded_dict.keys()) & set(all_dict.keys())
for doc_id in shared:
    ded_cat = ded_dict[doc_id]
    all_cat = all_dict[doc_id]
    key = (ded_cat, all_cat)
    flows[key] = flows.get(key, 0) + 1

# Reprint-only docs (425): origin = "New (reprints)"
reprint_only = set(all_dict.keys()) - set(ded_dict.keys())
for doc_id in reprint_only:
    all_cat = all_dict[doc_id]
    key = ("New (reprints)", all_cat)
    flows[key] = flows.get(key, 0) + 1

# Build output
rows = []
for (src, dst), count in flows.items():
    rows.append({
        "Deduped Category": src,
        "All Category": dst,
        "Count": count,
    })

df_flow = pd.DataFrame(rows)
df_flow = df_flow.sort_values("Count", ascending=False).reset_index(drop=True)

df_flow.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Done! → {OUTPUT_FILE}")
print(f"   {len(df_flow)} flow pairs")
print(f"   Shared docs: {len(shared):,}")
print(f"   Reprint-only: {len(reprint_only):,}")
print(f"{'='*60}")

# ── REPORT ────────────────────────────────────────────────────────────────
print("\n── Top 15 flows ──")
for _, r in df_flow.head(15).iterrows():
    arrow = "→" if r["Deduped Category"] != r["All Category"] else "="
    print(f"   {r['Count']:>4}  {r['Deduped Category']:<42} {arrow} {r['All Category']}")

# Category stability: how many stay in the same category
same = sum(c for (s, d), c in flows.items() if s == d and s != "New (reprints)")
total_shared = len(shared)
print(f"\n── Stability ──")
print(f"   {same:,} / {total_shared:,} articles ({same/total_shared*100:.1f}%) stay in same category")
print(f"   {total_shared - same:,} articles ({(total_shared-same)/total_shared*100:.1f}%) shift category")
print(f"   {len(reprint_only):,} new articles from reprints")
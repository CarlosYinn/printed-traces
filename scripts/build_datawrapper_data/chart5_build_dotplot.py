"""
=============================================================================
  Chart 5 — Deduped vs. All Corpus Comparison (Range Plot)
  
  For topics in both corpora: shows a range bar from ded to all.
  For single-corpus topics: leaves the missing side as empty (NaN),
    so Range Plot shows a single dot, not a line to zero.
  
  Uses all project files.
  Output: range_deduped_vs_all.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import os

DIR = r"."

DEDUP_TOPICS  = os.path.join(DIR, "doc-topics_K25_S2.txt")
ALL_TOPICS    = os.path.join(DIR, "all_doc-topics_K25_S1.txt")
DEDUP_LABELS  = os.path.join(DIR, "topic_labels.csv")
ALL_LABELS    = os.path.join(DIR, "all_topic_labels.csv")
DEDUP_DIAG    = os.path.join(DIR, "diag_K25_S2.xml")
ALL_DIAG      = os.path.join(DIR, "all_diag_K25_S1.xml")
DEDUP_KEYS    = os.path.join(DIR, "keys_K25_S2.txt")
ALL_KEYS      = os.path.join(DIR, "all_keys_K25_S1.txt")
MERGED_LABELS = os.path.join(DIR, "merged_topic_labels.csv")
DATASET       = os.path.join(DIR, "dataset.csv")
OUTPUT_FILE   = os.path.join(DIR, "range_deduped_vs_all.csv")

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
            if len(parts) < 3: continue
            rows.append([float(x) for x in parts[2:]])
    n = len(rows[0])
    return pd.DataFrame(rows, columns=[f"topic_{i}" for i in range(n)])


def compute_means(df, labels_file):
    labels = pd.read_csv(labels_file, dtype=str)
    labels.columns = labels.columns.str.strip()
    labels["topic_num"] = labels["topic_id"].str.extract(r"(\d+)").astype(int)
    results = {}
    for _, row in labels.iterrows():
        if row["exclude"] == "yes": continue
        col = f"topic_{row['topic_num']}"
        if col in df.columns:
            results[row["analytic_label"]] = round(df[col].mean() * 100, 2)
    return results


def parse_diagnostics(xml_file, labels_file):
    labels = pd.read_csv(labels_file, dtype=str)
    labels.columns = labels.columns.str.strip()
    labels["topic_num"] = labels["topic_id"].str.extract(r"(\d+)").astype(int)
    label_map = dict(zip(labels["topic_num"], labels["analytic_label"]))
    exclude = set(labels[labels["exclude"] == "yes"]["topic_num"])
    tree = ET.parse(xml_file)
    results = {}
    for topic in tree.getroot().findall("topic"):
        tid = int(topic.get("id"))
        if tid in exclude: continue
        results[label_map.get(tid, f"topic_{tid}")] = {
            "coherence": round(float(topic.get("coherence", 0)), 1),
            "exclusivity": round(float(topic.get("exclusivity", 0)), 3),
            "tokens": int(float(topic.get("tokens", 0))),
        }
    return results


def parse_keys(keys_file, labels_file, top_n=5):
    labels = pd.read_csv(labels_file, dtype=str)
    labels.columns = labels.columns.str.strip()
    labels["topic_num"] = labels["topic_id"].str.extract(r"(\d+)").astype(int)
    label_map = dict(zip(labels["topic_num"], labels["analytic_label"]))
    exclude = set(labels[labels["exclude"] == "yes"]["topic_num"])
    results = {}
    with open(keys_file) as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 3: continue
            tid = int(parts[0])
            if tid in exclude: continue
            results[label_map.get(tid, f"topic_{tid}")] = ", ".join(parts[2].strip().split()[:top_n])
    return results


# ── MAIN ──────────────────────────────────────────────────────────────────

print("Step 1/5  Corpus means...")
ded_means = compute_means(parse_doc_topics(DEDUP_TOPICS), DEDUP_LABELS)
all_means = compute_means(parse_doc_topics(ALL_TOPICS), ALL_LABELS)

print("Step 2/5  Diagnostics...")
ded_diag = parse_diagnostics(DEDUP_DIAG, DEDUP_LABELS)
all_diag = parse_diagnostics(ALL_DIAG, ALL_LABELS)

print("Step 3/5  Keywords...")
ded_keys = parse_keys(DEDUP_KEYS, DEDUP_LABELS)
all_keys = parse_keys(ALL_KEYS, ALL_LABELS)

print("Step 4/5  Dataset stats...")
ds = pd.read_csv(DATASET, dtype=str, usecols=["doc_id", "is_reprint", "is_original"])

print("Step 5/5  Building range table...")
merged = pd.read_csv(MERGED_LABELS, dtype=str)
merged.columns = merged.columns.str.strip()

results = []
for _, row in merged.iterrows():
    if row.get("exclude", "") == "yes":
        continue

    label    = row["analytic_label"]
    category = row["category"]
    source   = row["source"]

    # KEY CHANGE: use NaN instead of 0 for missing corpus
    if source == "both":
        ded_val = ded_means.get(label, np.nan)
        all_val = all_means.get(label, np.nan)
        presence = "Both"
    elif source == "deduped":
        ded_val = ded_means.get(label, np.nan)
        all_val = np.nan  # ← not 0, so Range Plot won't draw to zero
        presence = "Deduped only"
    else:
        ded_val = np.nan  # ← not 0
        all_val = all_means.get(label, np.nan)
        presence = "All only"

    # Difference (only meaningful for "both")
    if source == "both" and not np.isnan(ded_val) and not np.isnan(all_val):
        diff = round(all_val - ded_val, 2)
        shift = "Amplified" if diff > 0.3 else ("Reduced" if diff < -0.3 else "Stable")
    else:
        diff = ""
        shift = "N/A"

    diag = ded_diag.get(label, all_diag.get(label, {}))
    keywords = ded_keys.get(label, all_keys.get(label, ""))

    results.append({
        "Topic": label,
        "Deduped (written)": ded_val,
        "All (circulated)": all_val,
        "Category": category,
        "Difference": diff,
        "Shift": shift,
        "Presence": presence,
        "Keywords": keywords,
        "Coherence": diag.get("coherence", ""),
        "Exclusivity": diag.get("exclusivity", ""),
        "Tokens": diag.get("tokens", ""),
    })

df_result = pd.DataFrame(results)

# Sort by category order, then by max weight descending
cat_map = {c: i for i, c in enumerate(CATEGORY_ORDER)}
df_result["_sc"] = df_result["Category"].map(cat_map).fillna(99)
df_result["_sw"] = df_result[["Deduped (written)", "All (circulated)"]].max(axis=1)
df_result = df_result.sort_values(["_sc", "_sw"], ascending=[True, False]).reset_index(drop=True)

out = df_result.drop(columns=["_sc", "_sw"])
out.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print(f"\n✅ Done! → {OUTPUT_FILE}")
print(f"   {len(out)} topics")

# Report
for pres in ["Both", "Deduped only", "All only"]:
    subset = df_result[df_result["Presence"] == pres]
    print(f"\n── {pres} ({len(subset)}) ──")
    for _, r in subset.iterrows():
        d = f"{r['Deduped (written)']:.1f}%" if not pd.isna(r['Deduped (written)']) else "  —  "
        a = f"{r['All (circulated)']:.1f}%" if not pd.isna(r['All (circulated)']) else "  —  "
        print(f"   {r['Topic']:<45} ded={d:>6}  all={a:>6}  {r['Shift']}")
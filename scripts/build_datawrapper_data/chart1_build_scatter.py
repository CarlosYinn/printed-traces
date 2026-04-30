"""
=============================================================================
  Chart 1 — Scatter Plots: Topics Over Time
  Produces TWO Datawrapper-ready CSVs:
  
    A) scatter_showcase.csv   — homepage showcase chart: X=date, Y=topic_pct
    B) scatter_analysis.csv   — analysis chart:          X=x_display, Y=y_display
  
  Input files (same directory):
    - doc-topics_K25_S2.txt
    - dataset.csv
    - topic_labels.csv
  
=============================================================================
"""

import pandas as pd
import numpy as np
import re
import os

# ── 0. CONFIG ──────────────────────────────────────────────────────────────

DIR = r"."

DOC_TOPICS_FILE = os.path.join(DIR, "doc-topics_K25_S2.txt")
DATASET_FILE    = os.path.join(DIR, "dataset.csv")
LABELS_FILE     = os.path.join(DIR, "topic_labels.csv")
OUT_SHOWCASE    = os.path.join(DIR, "scatter_showcase.csv")
OUT_ANALYSIS    = os.path.join(DIR, "scatter_analysis.csv")

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

JITTER_Y = 0.35
JITTER_X = 0.4

# ── KWIC ───────────────────────────────────────────────────────────────────

KWIC_TIERS = [
    [
        r"chinese\s+(?:child|children|boy|girl|boys|girls|student|students|pupil|pupils)",
        r"(?:child|children|boy|girl|boys|girls|student|students|pupil|pupils)\s+(?:of\s+)?chinese",
        r"chinese\s+(?:school|education|sunday\s+school|mission\s+school)",
    ],
    [
        r"chinese", r"china", r"celestial", r"chinaman", r"mongolian",
        r"pigtail", r"queue", r"coolie", r"joss\s+house", r"opium",
        r"chinatown", r"exclusion", r"treaty",
    ],
    [
        r"child(?:ren)?", r"boys?", r"girls?", r"baby", r"infant",
        r"daughter", r"sons?", r"family", r"mother", r"father",
        r"school", r"education", r"student", r"teacher", r"pupil",
        r"missionary", r"mission", r"church", r"sunday\s+school",
        r"bapti[sz]", r"convert",
    ],
]

KWIC_WINDOW = 80
SNIPPET_MAX = 250

HIGHLIGHT_WORDS = [
    r"chinese", r"china", r"celestial", r"chinaman",
    r"child(?:ren)?", r"boys?", r"girls?", r"baby", r"infant",
    r"students?", r"pupils?", r"schools?",
    r"education", r"teachers?", r"missionaries?", r"missions?",
]


def extract_kwic(text, max_snippets=2):
    if not text or not isinstance(text, str):
        return ""
    clean = text.strip()
    for tier_patterns in KWIC_TIERS:
        hits = []
        for pat in tier_patterns:
            for m in re.finditer(pat, clean, flags=re.IGNORECASE):
                hits.append((m.start(), m.end(), pat))
        if not hits:
            continue
        hits.sort(key=lambda x: x[0])
        snippets, used = [], []
        for start, end, pat in hits:
            if len(snippets) >= max_snippets:
                break
            ws = max(0, start - KWIC_WINDOW)
            we = min(len(clean), end + KWIC_WINDOW)
            if any(a <= ws <= b or a <= we <= b for a, b in used):
                continue
            while ws > 0 and clean[ws - 1] not in " \t\n":
                ws -= 1
            while we < len(clean) and clean[we] not in " \t\n":
                we += 1
            frag = clean[ws:we].strip()
            if ws > 0:
                frag = "…" + frag
            if we < len(clean):
                frag = frag + "…"
            for hw in HIGHLIGHT_WORDS:
                frag = re.sub(
                    rf"(?<![<\w])({hw})(?![>\w])",
                    r"<b>\1</b>",
                    frag, flags=re.IGNORECASE
                )
            snippets.append(frag)
            used.append((ws, we))
        if snippets:
            result = " … ".join(snippets)
            if len(result) > SNIPPET_MAX:
                result = result[:SNIPPET_MAX].rsplit(" ", 1)[0] + "…"
            return result
    fallback = clean[:SNIPPET_MAX]
    if len(clean) > SNIPPET_MAX:
        fallback = fallback.rsplit(" ", 1)[0] + "…"
    return fallback


# ── 1. PARSE DOC-TOPICS ───────────────────────────────────────────────────
print("Step 1/5  Parsing doc-topics...")
rows = []
with open(DOC_TOPICS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) < 3:
            continue
        doc_id = parts[1]
        props  = [float(x) for x in parts[2:]]
        dom    = int(np.argmax(props))
        rows.append({"doc_id": doc_id, "dominant_topic": dom,
                      "dominant_weight": props[dom]})
df_topics = pd.DataFrame(rows)
print(f"          → {len(df_topics):,} documents")

# ── 2. LOAD METADATA ──────────────────────────────────────────────────────
print("Step 2/5  Loading dataset metadata...")
df_meta = pd.read_csv(DATASET_FILE, dtype=str)
df_meta.columns = df_meta.columns.str.strip()
df_meta["doc_id"]  = df_meta["doc_id"].str.strip()
df_topics["doc_id"] = df_topics["doc_id"].str.strip()
print(f"          → {len(df_meta):,} rows")

# ── 3. LOAD TOPIC LABELS ──────────────────────────────────────────────────
print("Step 3/5  Loading topic labels...")
df_labels = pd.read_csv(LABELS_FILE, dtype=str)
df_labels.columns = df_labels.columns.str.strip()
df_labels["topic_num"] = df_labels["topic_id"].str.extract(r"(\d+)").astype(int)
label_map     = dict(zip(df_labels["topic_num"], df_labels["analytic_label"]))
category_map  = dict(zip(df_labels["topic_num"], df_labels["category"]))
catcolor_map  = dict(zip(df_labels["topic_num"], df_labels["category_color"]))
topcolor_map  = dict(zip(df_labels["topic_num"], df_labels["color"]))
exclude_map   = dict(zip(df_labels["topic_num"], df_labels["exclude"]))
print(f"          → {len(df_labels)} topics")

# ── 4. MERGE ──────────────────────────────────────────────────────────────
print("Step 4/5  Merging...")
df = df_topics.merge(df_meta, on="doc_id", how="left")

df["topic_label"]    = df["dominant_topic"].map(label_map)
df["category"]       = df["dominant_topic"].map(category_map)
df["category_color"] = df["dominant_topic"].map(catcolor_map)
df["topic_color"]    = df["dominant_topic"].map(topcolor_map)
df["exclude"]        = df["dominant_topic"].map(exclude_map)

n0 = len(df)
df = df[df["exclude"] != "yes"].copy()
print(f"          → {n0 - len(df)} NOISE removed, {len(df):,} remain")

# ── DATE HANDLING ─────────────────────────────────────────────────────────
# Keep only YYYY-MM-DD; remove time/timezone details.
df["Date"] = df["Date"].str.strip().str[:10]   # "1880-09-10"
df["year"]  = pd.to_numeric(df["Date"].str[:4], errors="coerce")
df = df.dropna(subset=["year"])
df["year"] = df["year"].astype(int)
print(f"          → Date range: {df['Date'].min()} – {df['Date'].max()}")

# ── DERIVED COLUMNS ───────────────────────────────────────────────────────

# Numeric Y (for analysis chart)
cat_y_map = {cat: len(CATEGORY_ORDER) - i
             for i, cat in enumerate(CATEGORY_ORDER)}
df["category_y"] = df["category"].map(cat_y_map)

np.random.seed(42)
df["y_display"] = (df["category_y"]
                   + np.random.uniform(-JITTER_Y, JITTER_Y, len(df))).round(3)

# Numeric X (for analysis chart)
df["x_display"] = (df["year"]
                   + np.random.uniform(-JITTER_X, JITTER_X, len(df))).round(3)

# topic_pct (for showcase chart Y axis & both tooltips)
df["topic_pct"] = (df["dominant_weight"].astype(float) * 100).round(1)

# ── KWIC ──────────────────────────────────────────────────────────────────
print("Step 5/5  Extracting KWIC snippets...")
df["_txt"]    = df["dedup_text"].fillna(df.get("model_text", ""))
df["snippet"] = df["_txt"].apply(extract_kwic)

# ── SHARED FORMATTING ─────────────────────────────────────────────────────
df["location"] = (df["Pub_City"].fillna("") + ", "
                  + df["Pub_State"].fillna("")).str.strip(", ")
df["snippet"]  = df["snippet"].str.replace('"', "'", regex=False)

# Pretty date for tooltip: "Sep 10, 1880"
df["date_display"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%b %d, %Y")

# ═══════════════════════════════════════════════════════════════════════════
#  OUTPUT A — scatter_showcase.csv (homepage showcase chart)
#  X = date,  Y = topic_pct
# ═══════════════════════════════════════════════════════════════════════════

showcase = df[[
    "doc_id", "Date", "topic_pct", "date_display",
    "category", "category_color",
    "topic_label", "topic_color",
    "Newspaper_Name", "location", "Pub_State",
    "Page_URL", "snippet",
]].copy()

showcase.columns = [
    "doc_id", "date", "topic_confidence", "date_display",
    "category", "category_color",
    "topic", "topic_color",
    "newspaper", "location", "state",
    "loc_url", "snippet",
]

showcase = showcase.sort_values("date").reset_index(drop=True)
showcase.to_csv(OUT_SHOWCASE, index=False, encoding="utf-8-sig")
print(f"\n✅ Showcase → {OUT_SHOWCASE}  ({len(showcase):,} rows)")

# ═══════════════════════════════════════════════════════════════════════════
#  OUTPUT B — scatter_analysis.csv (analysis chart)
#  X = x_display,  Y = y_display
# ═══════════════════════════════════════════════════════════════════════════

analysis = df[[
    "doc_id", "x_display", "y_display",
    "year", "Date", "date_display",
    "category", "category_y", "category_color",
    "topic_label", "topic_color", "topic_pct",
    "Newspaper_Name", "location", "Pub_State",
    "Page_URL", "snippet",
]].copy()

analysis.columns = [
    "doc_id", "Publication Year", "Topic Category",
    "year", "date", "date_display",
    "category", "category_y", "category_color",
    "topic", "topic_color", "topic_confidence",
    "newspaper", "location", "state",
    "loc_url", "snippet",
]

analysis = analysis.sort_values(["year", "category_y"],
                                 ascending=[True, False]).reset_index(drop=True)
analysis.to_csv(OUT_ANALYSIS, index=False, encoding="utf-8-sig")
print(f"✅ Analysis → {OUT_ANALYSIS}  ({len(analysis):,} rows)")

# ── REPORT ────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"   Categories: {df['category'].nunique()}")
print(f"   Topics:     {df['topic_label'].nunique()}")
print(f"{'='*60}")

print("\n── Y-axis ticks for analysis chart ──")
for cat in CATEGORY_ORDER:
    print(f"   {cat_y_map[cat]:>2} = {cat}")

print("\n── Distribution ──")
print(df.groupby("category").size().sort_values(ascending=False).to_string())

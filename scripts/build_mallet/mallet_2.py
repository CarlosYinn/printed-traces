import re
import pandas as pd

# =========================
# Dataset pipeline: Step 6
# MALLET preprocessing: Step 2 of 3
#
# Takes mallet_1.xlsx and performs reprint detection, sentence-level
# deduplication, and propagation chain analysis. Produces the final
# mallet_ready_text column — the text to be fed directly into MALLET.
# Output: mallet_2.xlsx
# =========================
INPUT_EXCEL  = "mallet_1.xlsx"
OUTPUT_EXCEL = "mallet_2.xlsx"

# Word trigram shingle size for article-level similarity detection.
SHINGLE_SIZE = 3

# Jaccard threshold for two full-length articles (both >= SHORT_TEXT_WORDS).
# 0.20 = 20% of all trigrams match — strong evidence of copying.
JACCARD_THRESHOLD = 0.20

# Articles with fewer words than this are checked via containment instead of Jaccard.
SHORT_TEXT_WORDS = 60

# Containment threshold for short/truncated texts.
# 0.5 = 50% of the short text's trigrams appear in the other article.
CONTAINMENT_THRESHOLD = 0.5

# --- Sentence-level deduplication ---
# A sentence is considered "shared" (reprinted boilerplate) if this fraction
# of its trigrams appear in at least one other article in the same reprint group.
SENTENCE_SHARED_THRESHOLD = 0.5

# After stripping shared sentences, the remaining unique text must contain at
# least this many words to be worth sending to MALLET as a deduplicated entry.
MIN_UNIQUE_WORDS = 20


# =========================
# HELPERS
# =========================
def parse_date_safe(series):
    return pd.to_datetime(series, errors="coerce")

def make_shingles(text: str, k: int) -> set:
    """Return the set of k-word shingles in text. Falls back to unigrams if text is very short."""
    words = text.split()
    if len(words) < k:
        return set(words)
    return {" ".join(words[i:i+k]) for i in range(len(words) - k + 1)}

def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0

def containment(short: set, long_: set) -> float:
    """Fraction of short's shingles that appear in long_."""
    if not short:
        return 0.0
    return len(short & long_) / len(short)

def split_sentences(text: str) -> list:
    """Split text into sentences on . ! ? boundaries."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if s.strip()]

def union_find_groups(pairs, n):
    """Cluster index pairs into connected components. Returns root -> [members]."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i, j in pairs:
        union(i, j)

    clusters = {}
    for i in range(n):
        clusters.setdefault(find(i), []).append(i)
    return clusters


# =========================
# STEP 6A — article-level reprint detection
# =========================
def detect_reprints(df):
    """
    Detect reprinted articles using word-trigram Jaccard similarity and containment.

    Jaccard measures whether sequences of words were copied (not just shared
    vocabulary), making it robust against two independently written articles on
    the same topic being falsely grouped together.

    Two-pass strategy:
        Pass 1 — both texts long (>= SHORT_TEXT_WORDS words): use Jaccard.
        Pass 2 — at least one text short (OCR-truncated): use containment,
                  which is not penalised by the long text's extra shingles.

    sim_score (max score per article) is stored for human auditing.
    """
    df = df.copy()
    df = df.reset_index(drop=True)
    df["dedup_text"] = df["dedup_text"].fillna("").astype(str).str.strip()

    for col in ["duplicate_group", "reprint_count", "is_reprint", "sim_score"]:
        if col in df.columns:
            df = df.drop(columns=[col])

    df["duplicate_group"] = ""
    df["reprint_count"]   = 0
    df["is_reprint"]      = "false"
    df["sim_score"]       = ""

    valid_mask    = df["dedup_text"] != ""
    valid_indices = df.index[valid_mask].tolist()
    valid_texts   = df.loc[valid_mask, "dedup_text"].tolist()

    if len(valid_texts) < 2:
        return df

    n            = len(valid_texts)
    word_counts  = [len(t.split()) for t in valid_texts]
    shingle_sets = [make_shingles(t, SHINGLE_SIZE) for t in valid_texts]
    similar_pairs = {}

    print(f"  Computing shingle similarity across {n} articles...")
    for i in range(n):
        for j in range(i + 1, n):
            si, sj = shingle_sets[i], shingle_sets[j]
            wi, wj = word_counts[i], word_counts[j]
            score  = 0.0

            if wi >= SHORT_TEXT_WORDS and wj >= SHORT_TEXT_WORDS:
                score = jaccard(si, sj)
                if score >= JACCARD_THRESHOLD:
                    similar_pairs[(i, j)] = score
            else:
                short_set = si if wi <= wj else sj
                long_set  = sj if wi <= wj else si
                score = containment(short_set, long_set)
                if score >= CONTAINMENT_THRESHOLD:
                    similar_pairs[(i, j)] = score

    print(f"  Found {len(similar_pairs)} similar pairs.")

    clusters = union_find_groups(list(similar_pairs.keys()), n)
    reprint_clusters = {root: members for root, members in clusters.items()
                        if len(members) > 1}

    print(f"  Identified {len(reprint_clusters)} reprint groups.")

    max_score = {}
    for (i, j), score in similar_pairs.items():
        max_score[i] = max(max_score.get(i, 0.0), score)
        max_score[j] = max(max_score.get(j, 0.0), score)

    for group_num, (_, members) in enumerate(reprint_clusters.items(), start=1):
        group_id = f"REP_{group_num:04d}"
        orig_idx = [valid_indices[m] for m in members]
        df.loc[orig_idx, "duplicate_group"] = group_id
        df.loc[orig_idx, "reprint_count"]   = len(members)
        df.loc[orig_idx, "is_reprint"]      = "true"

    for local_i, global_i in enumerate(valid_indices):
        if local_i in max_score:
            df.loc[global_i, "sim_score"] = f"{max_score[local_i]:.2f}"

    return df


# =========================
# STEP 6B — sentence-level deduplication
# =========================
def strip_shared_sentences(df):
    """
    For each article in a reprint group, identify sentences that are largely
    shared with other articles in the same group and remove them.

    A sentence is "shared" if >= SENTENCE_SHARED_THRESHOLD of its trigrams
    appear in the combined shingle pool of the other articles in the group.

    The result is stored in model_text_deduped:
        - Articles not in any group: model_text_deduped = model_text (unchanged)
        - Articles in a group: unique sentences only (shared boilerplate removed)

    unique_word_count records how many words remain after stripping, so the
    MALLET selection step can decide whether the remainder is worth including.
    """
    df = df.copy()
    df["model_text"] = df["model_text"].fillna("").astype(str)
    df["model_text_deduped"] = df["model_text"]
    df["unique_word_count"]  = df["model_text"].str.split().str.len()

    groups = [g for g in df["duplicate_group"].unique() if g]
    print(f"  Stripping shared sentences from {len(groups)} reprint groups...")

    for group_id in groups:
        mask    = df["duplicate_group"] == group_id
        members = df.index[mask].tolist()

        # Build a shingle pool for each article (sentence-level trigrams)
        article_shingles = {}
        for idx in members:
            article_shingles[idx] = make_shingles(df.loc[idx, "model_text"], SHINGLE_SIZE)

        for idx in members:
            # Pool = all shingles in the group EXCEPT this article's own
            other_shingles = set()
            for other_idx, s in article_shingles.items():
                if other_idx != idx:
                    other_shingles |= s

            if not other_shingles:
                continue

            sentences = split_sentences(df.loc[idx, "model_text"])
            unique_sentences = []
            for sent in sentences:
                sent_shingles = make_shingles(sent, SHINGLE_SIZE)
                if not sent_shingles:
                    unique_sentences.append(sent)
                    continue
                overlap = len(sent_shingles & other_shingles) / len(sent_shingles)
                if overlap < SENTENCE_SHARED_THRESHOLD:
                    unique_sentences.append(sent)

            deduped = " ".join(unique_sentences).strip()
            df.loc[idx, "model_text_deduped"] = deduped
            df.loc[idx, "unique_word_count"]  = len(deduped.split()) if deduped else 0

    return df


# =========================
# STEP 6C — propagation chain and MALLET selection
# =========================
def build_propagation_chains(df):
    """
    For each reprint group, rank articles chronologically and by text length.

    MALLET selection rules (in priority order):
        1. Articles not in any reprint group: use_for_mallet = include_in_mallet.
        2. Within a reprint group:
           a. The longest article (mallet_rank=1) among core articles is always selected.
           b. Any other core article whose unique content after sentence-level
              deduplication is >= MIN_UNIQUE_WORDS is also selected, using
              model_text_deduped as its MALLET input.
              This captures articles that contain reprinted passages alongside
              substantive unique reporting not found in any other group member.

    mallet_input indicates which text field to use: 'model_text' or 'model_text_deduped'.
    """
    df = df.copy()
    df["Date_parsed"] = parse_date_safe(df["Date"])
    df["text_length"]  = df["model_text"].fillna("").astype(str).str.len()

    df["chain_position"]    = ""
    df["mallet_rank"]       = ""
    df["is_original"]       = "false"
    df["propagation_chain"] = ""
    df["use_for_mallet"]    = "no"
    df["mallet_type"]       = ""   # "full" or "deduped"
    df["mallet_ready_text"] = ""   # the actual text to feed into MALLET

    non_duplicate = df["duplicate_group"] == ""
    df.loc[non_duplicate, "use_for_mallet"] = "yes"
    df.loc[non_duplicate, "is_original"]    = "true"

    chain_position_map    = {}
    mallet_rank_map       = {}
    propagation_chain_map = {}

    for group_id in [g for g in df["duplicate_group"].unique() if g]:
        sub = df.loc[df["duplicate_group"] == group_id].copy()

        sub_by_date = sub.sort_values(
            by=["Date_parsed", "doc_id"], ascending=[True, True], na_position="last"
        )
        for pos, doc_id in enumerate(sub_by_date["doc_id"], start=1):
            chain_position_map[doc_id] = str(pos)

        sub_by_len = sub.sort_values(
            by=["text_length", "Date_parsed", "doc_id"],
            ascending=[False, True, True], na_position="last"
        )
        for pos, doc_id in enumerate(sub_by_len["doc_id"], start=1):
            mallet_rank_map[doc_id] = str(pos)

        chain_parts = []
        for _, row in sub_by_date.iterrows():
            paper    = row.get("Newspaper_Name", "") or "unknown"
            date_str = row.get("Date", "")           or "unknown date"
            city     = row.get("Pub_City", "")       or ""
            state    = row.get("Pub_State", "")      or ""
            location = ", ".join(filter(None, [city, state]))
            label    = f"{paper} ({date_str}{', ' + location if location else ''})"
            chain_parts.append(label)
        chain_str = " → ".join(chain_parts)
        for doc_id in sub_by_date["doc_id"]:
            propagation_chain_map[doc_id] = chain_str

    df["chain_position"]    = df["doc_id"].map(chain_position_map).fillna("")
    df["mallet_rank"]       = df["doc_id"].map(mallet_rank_map).fillna("")
    df["propagation_chain"] = df["doc_id"].map(propagation_chain_map).fillna("")
    df.loc[df["chain_position"] == "1", "is_original"] = "true"

    duplicate_mask = df["duplicate_group"] != ""

    # Rule 2a: longest article in each group — enters MALLET with full text
    df.loc[duplicate_mask & (df["mallet_rank"] == "1"),
           "use_for_mallet"] = "yes"
    df.loc[duplicate_mask & (df["mallet_rank"] == "1"),
           "mallet_type"] = "full"

    # Rule 2b: other articles with enough unique content after sentence deduplication
    has_unique = df["unique_word_count"].apply(
        lambda x: int(x) >= MIN_UNIQUE_WORDS if str(x).isdigit() else False
    )
    not_already_selected = df["use_for_mallet"] != "yes"
    df.loc[duplicate_mask & has_unique & not_already_selected,
           "use_for_mallet"] = "yes"
    df.loc[duplicate_mask & has_unique & not_already_selected,
           "mallet_type"] = "deduped"

    # Everything else in a group is excluded
    df.loc[duplicate_mask & (df["use_for_mallet"] != "yes"),
           "use_for_mallet"] = "no"

    # Non-duplicate articles selected for MALLET always use full text
    df.loc[non_duplicate & (df["use_for_mallet"] == "yes"),
           "mallet_type"] = "full"

    # Populate mallet_ready_text based on mallet_type
    df["mallet_ready_text"] = df.apply(
        lambda row: (
            row["model_text_deduped"] if row["mallet_type"] == "deduped"
            else row["model_text"] if row["mallet_type"] == "full"
            else ""
        ),
        axis=1,
    )

    df = df.drop(columns=["Date_parsed", "text_length"])
    return df


# =========================
# MAIN
# =========================
def main():
    print(f"Reading: {INPUT_EXCEL}")
    df = pd.read_excel(INPUT_EXCEL, dtype=str).fillna("")

    required = [
        "doc_id", "Date", "dedup_text", "model_text",
        "Newspaper_Name", "Pub_City", "Pub_State",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Source sheet is missing columns: {missing}")

    df = detect_reprints(df)
    df = strip_shared_sentences(df)
    df = build_propagation_chains(df)

    total          = len(df)
    reprinted_rows = (df["is_reprint"] == "true").sum()
    dup_groups     = df[df["duplicate_group"] != ""]["duplicate_group"].nunique()
    dup_rows       = (df["duplicate_group"] != "").sum()
    originals      = ((df["duplicate_group"] != "") & (df["is_original"] == "true")).sum()
    mallet         = (df["use_for_mallet"] == "yes").sum()
    full_in    = ((df["use_for_mallet"] == "yes") & (df["mallet_type"] == "full")).sum()
    deduped_in = ((df["use_for_mallet"] == "yes") & (df["mallet_type"] == "deduped")).sum()

    print("\nSummary")
    print("-------")
    print("Total rows                  :", total)
    print("Reprinted rows              :", reprinted_rows)
    print("Reprint groups              :", dup_groups)
    print("Rows in reprint groups      :", dup_rows)
    print("Original pubs (in groups)   :", originals)
    print("Selected for MALLET         :", mallet)
    print("  — full text (mallet_type=full)      :", full_in)
    print("  — deduped text (mallet_type=deduped):", deduped_in)

    df.to_excel(OUTPUT_EXCEL, index=False, engine="openpyxl")
    print(f"\nSaved: {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()

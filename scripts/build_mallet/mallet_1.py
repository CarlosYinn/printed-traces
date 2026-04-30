import re
import pandas as pd

# =========================
# Dataset pipeline: Step 5
# MALLET preprocessing: Step 1 of 3
#
# Reads the source spreadsheet, slices down to the relevant columns,
# assigns unique doc IDs, and generates the two text fields used
# downstream: dedup_text (normalised for similarity detection) and
# model_text (lightly cleaned for topic modelling).
# Output: mallet_1.xlsx — passed directly into MALLET Step 2 (mallet_2.py).
# =========================
INPUT_EXCEL = "dataset_revised.xlsx"
OUTPUT_EXCEL = "mallet_1.xlsx"

# Columns carried forward from the source spreadsheet
KEEP_COLUMNS = [
    "Keyword",
    "Date",
    "Newspaper_Name",
    "Pub_City",
    "Pub_State",
    "Coverage_Region",
    "OCR_cleaned",
    "relevance_tier",
    "topic_tags",
]

# New columns generated in this step
NEW_COLUMNS = [
    "doc_id",
    "dedup_text",
    "model_text",
    "token_count",
]

FRAGMENT_MARKER = "[SEPARATE FRAGMENT]"


# =========================
# HELPERS
# =========================
def normalize_for_dedup(text: str) -> str:
    """
    Produce a normalised version of the text for use in Step 2 similarity
    detection. Strips punctuation, digits, and casing so that minor OCR
    differences do not prevent matching.
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    t = text

    # strip fragment separators
    t = t.replace(FRAGMENT_MARKER, " ")

    # lowercase
    t = t.lower()

    # remove digits
    t = re.sub(r"\d+", " ", t)

    # keep only letters and whitespace
    t = re.sub(r"[^a-z\s]", " ", t)

    # collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()

    return t


def build_model_text(text: str) -> str:
    """
    Produce a lightly cleaned version of OCR_cleaned for topic modelling.
    Preserves the original wording — only normalises whitespace and line
    endings so the text is safe to pass into MALLET.
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""

    t = text

    # strip fragment separators
    t = t.replace(FRAGMENT_MARKER, " ")

    # normalize line endings and whitespace
    t = t.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    t = re.sub(r"\s+", " ", t).strip()

    return t


def count_tokens(text: str) -> int:
    """Whitespace-based word count. Used for a quick size check in Step 2."""
    if not isinstance(text, str) or not text.strip():
        return 0
    return len(text.split())


def make_doc_id(n: int) -> str:
    """Generate a zero-padded unique document ID, e.g. DOC_000001."""
    return f"DOC_{n:06d}"


# =========================
# MAIN
# =========================
def main():
    print(f"Reading: {INPUT_EXCEL}")
    df = pd.read_excel(INPUT_EXCEL, dtype=str).fillna("")

    missing = [c for c in KEEP_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Source sheet is missing columns: {missing}")

    working = df[KEEP_COLUMNS].copy()

    for col in NEW_COLUMNS:
        if col not in working.columns:
            working[col] = ""

    # Assign a unique ID to every row
    working["doc_id"] = [make_doc_id(i) for i in range(1, len(working) + 1)]

    # Build dedup_text — used by Step 2 for reprint detection
    working["dedup_text"] = working["OCR_cleaned"].apply(normalize_for_dedup)

    # Build model_text — used by Step 2 for sentence deduplication and
    # as the final text fed into MALLET
    working["model_text"] = working["OCR_cleaned"].apply(build_model_text)

    # Token count for reference
    working["token_count"] = working["model_text"].apply(count_tokens)

    print(f"Rows loaded: {len(working)}")
    print("Preview:")
    print(working[[
        "doc_id",
        "Date",
        "Newspaper_Name",
        "relevance_tier",
        "token_count",
        "dedup_text"
    ]].head(5))

    working.to_excel(OUTPUT_EXCEL, index=False, engine="openpyxl")
    print(f"Saved: {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()

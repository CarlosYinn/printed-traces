# heavy_ocr_clean_v2.py
# Heavy OCR cleanup ONLY: removes garbage symbol/code-like noise, repairs hyphenation/linebreaks,
# conservative spelling correction for news-like blocks. Outputs a single new column: cleaned_ocr.
#
# Install:
#   pip install pandas ftfy symspellpy wordfreq
#
# Run:
#   python heavy_ocr_clean_v2.py

import re
import sys
import hashlib
from pathlib import Path
from typing import List, Tuple, Set, Optional

import pandas as pd
import ftfy
from wordfreq import zipf_frequency

# =========================
# USER CONFIG (EDIT THESE)
# =========================
INPUT_CSV = "input.csv"
OUTPUT_CSV = "dataset_with_cleaned_ocr.csv"

RAW_COL = "OCR_Text"      # raw OCR column
OUT_COL = "cleaned_ocr"     # output column

SYMSPELL_DICT_PATH = r"resources/frequency_dictionary_en_82_765.txt"  # optional

PROTECT_FROM_COLS = [
    "Keyword", "Newspaper_Name", "Pub_City", "Pub_County", "Pub_State", "Coverage_Region", "Page_URL"
]

# =========================
# HEAVY TUNING (DEFAULTS)
# =========================
GARBAGE_WINDOW = 280
GARBAGE_STEP = 120
MIN_BLOCK_LEN = 60
MIN_DOC_CHARS = 120

NORMALIZE_QUOTES = True

SAFE_CHAR_MAP = {
    "\ufeff": " ",  # BOM
    "\ufffd": " ",  # replacement char
    "ﬁ": "fi",
    "ﬂ": "fl",
    "’": "'" if NORMALIZE_QUOTES else "’",
    "“": '"' if NORMALIZE_QUOTES else "“",
    "”": '"' if NORMALIZE_QUOTES else "”",
    "—": "-",
    "–": "-",
}

WORD_RE = re.compile(r"[A-Za-z']+")

AD_WORDS = {
    "dealer", "dealers", "co", "company", "bros", "bro", "agent", "insurance", "store", "prices",
    "sale", "wholesale", "retail", "manufacturers", "manufacture", "undertaking", "office", "notary",
    "plaza", "avenue", "block", "bank", "stock", "broker", "real", "estate", "hats", "trimmed",
    "boots", "shoes", "beer", "saloon", "lunch", "cocktails", "cents", "invoice", "received",
    "made", "order", "specialty", "goods", "furniture", "fixtures", "lowest", "cash",
    "paid", "flour", "hides", "wool", "trunks", "valises", "cloth", "clothing",
    "mortgage", "sale", "default", "notice", "sheriff", "bidder"
}

# =========================
# SymSpell (optional)
# =========================
def load_symspell(dict_path: str, max_edit_distance=2, prefix_length=7):
    from symspellpy.symspellpy import SymSpell
    sym = SymSpell(max_dictionary_edit_distance=max_edit_distance, prefix_length=prefix_length)
    ok = sym.load_dictionary(dict_path, term_index=0, count_index=1, separator=" ")
    if not ok:
        raise RuntimeError(f"Failed to load dictionary: {dict_path}")
    return sym

# =========================
# Protection vocabulary
# =========================
def build_protect_words(df: pd.DataFrame) -> Set[str]:
    protect: Set[str] = set()

    for col in PROTECT_FROM_COLS:
        if col not in df.columns:
            continue
        series = df[col].dropna().astype(str)
        for val in series.head(30000).tolist():
            for w in WORD_RE.findall(val.lower()):
                if 2 <= len(w) <= 32:
                    protect.add(w)

    protect.update({
        "mr", "mrs", "dr", "st", "mt", "ft", "gen", "sen", "gov", "hon",
        "jan", "feb", "mar", "apr", "may", "jun", "june", "jul", "july", "aug",
        "sep", "sept", "oct", "nov", "dec",
        "a", "m", "p", "u", "s",
    })
    return protect

# =========================
# Core normalization
# =========================
def normalize_and_fix_encoding(raw: str) -> str:
    if not isinstance(raw, str):
        return ""
    t = ftfy.fix_text(raw)
    t = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", t)
    for k, v in SAFE_CHAR_MAP.items():
        t = t.replace(k, v)
    return t

def fix_hyphen_linebreaks(t: str) -> str:
    return re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)

def rescue_linebreaks(t: str) -> str:
    t = re.sub(r"\r\n?", "\n", t)
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

def normalize_spaces(t: str) -> str:
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"([!?.,;:])\1{2,}", r"\1", t)
    t = re.sub(r"[|_]{3,}", " ", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([,.;:!?])(?=[A-Za-z])", r"\1 ", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()

# =========================
# NEW: brutal symbol-noise killer (targets ^^ \ | ~ etc.)
# =========================
SYMBOL_RUN_RE = re.compile(r"[\^`~_=|\\/<>]{2,}")  # runs of OCR garbage symbols
MIXED_GARBAGE_RE = re.compile(r"(?:[\^`~_=|\\/<>]{1,}\w{0,3}){6,}", re.IGNORECASE)

def strip_symbol_garbage(t: str) -> str:
    if not t:
        return t
    # Remove long symbol runs
    t = SYMBOL_RUN_RE.sub(" ", t)
    # Remove "mixed garbage" like ^^i -Tr^^^w^^?^r-j^rest patterns
    t = MIXED_GARBAGE_RE.sub(" ", t)
    # Remove leftover weird sequences like |\" or \H. or /H. when it looks like OCR artifacts
    t = re.sub(r"\|\s*\\\s*\"", " ", t)
    t = re.sub(r"\|\s*\\", " ", t)
    t = re.sub(r"\\{2,}", " ", t)
    # Replace remaining lone carets that cling to letters: a^b^c -> a b c
    t = re.sub(r"(\w)\^(\w)", r"\1 \2", t)
    t = re.sub(r"\^+", " ", t)
    return normalize_spaces(t)

# =========================
# Line removal
# =========================
def drop_noise_lines(t: str) -> str:
    lines = [ln.strip() for ln in t.split("\n")]
    out = []
    for ln in lines:
        if not ln:
            out.append("")
            continue

        if re.fullmatch(r"[-_=*~|.]{6,}", ln):
            continue

        if len(ln) <= 10 and re.fullmatch(r"\d{1,10}", ln):
            continue

        # remove lines dominated by garbage symbols/carets/slashes
        bad_sym = len(re.findall(r"[\^`~_=|\\/<>]", ln))
        if len(ln) >= 20 and bad_sym / max(len(ln), 1) > 0.18:
            # but keep if it's clearly a normal sentence (alpha strong)
            alpha = len(re.findall(r"[A-Za-z]", ln))
            if alpha / max(len(ln), 1) < 0.55:
                continue

        sym = len(re.findall(r"[^A-Za-z0-9\s]", ln))
        if len(ln) >= 20 and sym / max(len(ln), 1) > 0.58:
            continue

        alpha = len(re.findall(r"[A-Za-z]", ln))
        if len(ln) < 45 and alpha / max(len(ln), 1) < 0.25:
            continue

        out.append(ln)
    return "\n".join(out)

def remove_repeated_lines(t: str) -> str:
    lines = [ln.strip() for ln in re.split(r"\n+", t)]
    if len(lines) < 10:
        return t

    counts = {}
    hashes = []
    for ln in lines:
        if 18 <= len(ln) <= 160:
            h = hashlib.md5(ln.lower().encode("utf-8", errors="ignore")).hexdigest()
            hashes.append(h)
            counts[h] = counts.get(h, 0) + 1
        else:
            hashes.append("")

    out = []
    for ln, h in zip(lines, hashes):
        if h and counts.get(h, 0) >= 3:
            continue
        out.append(ln)
    return normalize_spaces("\n".join(out))

# =========================
# Garbage-segment detection (stronger)
# =========================
def lexicon_hit_ratio(seg: str, protect: Set[str]) -> float:
    toks = [m.group(0).lower() for m in WORD_RE.finditer(seg)]
    if len(toks) < 20:
        return 0.0
    toks = toks[:500]
    hits = 0
    for w in toks:
        if w in protect:
            hits += 1
        elif zipf_frequency(w, "en") >= 2.0:
            hits += 1
    return hits / max(len(toks), 1)

def nonword_token_ratio(seg: str, protect: Set[str]) -> float:
    toks = [m.group(0).lower() for m in WORD_RE.finditer(seg)]
    if not toks:
        return 1.0
    toks = toks[:500]
    bad = 0
    for w in toks:
        if w in protect:
            continue
        if len(w) >= 6 and zipf_frequency(w, "en") < 1.0:
            bad += 1
    return bad / max(len(toks), 1)

def drop_garbage_segments(t: str, protect: Set[str]) -> str:
    if len(t) < 700:
        return t

    keep = [True] * len(t)

    for start in range(0, len(t), GARBAGE_STEP):
        seg = t[start:start + GARBAGE_WINDOW]
        if len(seg) < 160:
            continue

        n = len(seg)
        alpha = len(re.findall(r"[A-Za-z]", seg))
        punct = len(re.findall(r"[^A-Za-z0-9\s]", seg))
        carets = len(re.findall(r"[\^`~_=|\\/<>]", seg))

        alpha_ratio = alpha / max(n, 1)
        symbol_ratio = punct / max(n, 1)
        caret_ratio = carets / max(n, 1)

        lex = lexicon_hit_ratio(seg, protect)
        nonword = nonword_token_ratio(seg, protect)

        # Stronger garbage rules specifically for "code-like" OCR noise
        is_garbage = (
            (caret_ratio > 0.04 and alpha_ratio < 0.70) or                 # lots of ^ \ | etc.
            (alpha_ratio < 0.45 and symbol_ratio > 0.22) or
            (lex > 0 and lex < 0.32 and alpha_ratio < 0.65) or
            (nonword > 0.40 and alpha_ratio < 0.72)                        # too many nonwords
        )

        if is_garbage:
            for i in range(start, min(start + GARBAGE_WINDOW, len(t))):
                keep[i] = False

    out = []
    in_drop = False
    for i, ch in enumerate(t):
        if keep[i]:
            out.append(ch)
            in_drop = False
        else:
            if not in_drop:
                out.append(" ")
                in_drop = True
    return normalize_spaces("".join(out))

# =========================
# Block classification
# =========================
def block_features(block: str, protect: Set[str]) -> dict:
    n = len(block)
    alpha = len(re.findall(r"[A-Za-z]", block))
    upper = len(re.findall(r"[A-Z]", block))
    digit = len(re.findall(r"\d", block))
    punct = len(re.findall(r"[^A-Za-z0-9\s]", block))
    carets = len(re.findall(r"[\^`~_=|\\/<>]", block))

    tokens = [t.lower() for t in WORD_RE.findall(block)]
    ad_hits = sum(1 for t in tokens[:350] if t in AD_WORDS)
    tok_n = len(tokens) if tokens else 0
    lex = lexicon_hit_ratio(block, protect)
    nonword = nonword_token_ratio(block, protect)

    return {
        "n": n,
        "alpha_ratio": alpha / max(n, 1),
        "upper_ratio": upper / max(alpha, 1),
        "digit_ratio": digit / max(n, 1),
        "symbol_ratio": punct / max(n, 1),
        "caret_ratio": carets / max(n, 1),
        "ad_hits": ad_hits,
        "tok_n": tok_n,
        "lex": lex,
        "nonword": nonword
    }

def classify_block(block: str, protect: Set[str]) -> str:
    b = block.strip()
    if not b:
        return "garbage"

    f = block_features(b, protect)

    if f["n"] < MIN_BLOCK_LEN:
        return "news" if f["alpha_ratio"] >= 0.55 else "garbage"

    # Garbage blocks: symbol-noise or extremely low lexicon quality
    if (f["caret_ratio"] > 0.03 and f["alpha_ratio"] < 0.75) or (f["lex"] > 0 and f["lex"] < 0.30 and f["alpha_ratio"] < 0.68) or (f["nonword"] > 0.45):
        return "garbage"

    # Ads: lots of uppercase/digits/commerce words
    if f["upper_ratio"] > 0.68 or f["digit_ratio"] > 0.06 or f["ad_hits"] >= 6:
        return "ad"

    return "news"

# =========================
# Spelling correction (conservative, news blocks only)
# =========================
def looks_like_ocr_error(tok: str, protect: Set[str]) -> bool:
    low = tok.lower()
    if low in protect:
        return False
    if len(low) < 4 or len(low) > 20:
        return False
    alpha_ratio = len(re.findall(r"[A-Za-z]", low)) / max(len(low), 1)
    if alpha_ratio < 0.85:
        return True
    if re.search(r"(.)\1\1", low):
        return True
    if zipf_frequency(low, "en") < 1.4:
        return True
    return False

def try_ocr_confusions(low: str) -> str:
    cand = re.sub(r"rn", "m", low)
    if cand != low and zipf_frequency(cand, "en") >= 2.0:
        return cand
    cand2 = re.sub(r"cl", "d", low)
    if cand2 != low and zipf_frequency(cand2, "en") >= 2.0:
        return cand2
    return low

def heavy_spell_correct(text: str, sym, protect: Set[str], max_ed: int = 2) -> str:
    # mask initials like "D. W. Bliss"
    masks: List[Tuple[str, str]] = []
    def mask_initials(m):
        s = m.group(0)
        key = f"__INITMASK{len(masks)}__"
        masks.append((key, s))
        return key

    masked = re.sub(r"\b(?:[A-Z]\.\s*){2,}[A-Z][a-z]+", mask_initials, text)

    def fix(m):
        tok = m.group(0)
        low = tok.lower()

        if not looks_like_ocr_error(tok, protect):
            return tok

        pre = try_ocr_confusions(low)
        if pre != low:
            return pre

        sug = sym.lookup(low, verbosity=0, max_edit_distance=max_ed)
        if not sug:
            return tok
        best = sug[0].term
        if best == low:
            return tok

        # Evidence gate
        if zipf_frequency(best, "en") < 2.0:
            return tok
        if zipf_frequency(best, "en") - zipf_frequency(low, "en") < 1.2:
            return tok
        if abs(len(best) - len(low)) > 3:
            return tok

        return best

    corrected = WORD_RE.sub(fix, masked)
    for key, orig in masks:
        corrected = corrected.replace(key, orig)
    return corrected

# =========================
# Main per-document cleaner
# =========================
def clean_one_ocr(raw: str, protect: Set[str], symspell=None) -> str:
    t = normalize_and_fix_encoding(raw)
    t = fix_hyphen_linebreaks(t)
    t = rescue_linebreaks(t)

    # NEW: kill symbol garbage early
    t = strip_symbol_garbage(t)

    t = drop_noise_lines(t)
    t = strip_symbol_confetti(t)
    t = normalize_spaces(t)

    t = remove_repeated_lines(t)

    # Remove garbage segments (stronger)
    t = drop_garbage_segments(t, protect)
    t = strip_symbol_confetti(t)

    # One more pass after segment dropping (often reveals new symbol runs)
    t = strip_symbol_garbage(t)

    # Block split + classify
    blocks = re.split(r"\n{2,}", t)
    out_blocks: List[str] = []

    for b in blocks:
        b = normalize_spaces(b)
        if not b:
            continue

        kind = classify_block(b, protect)

        if kind == "garbage":
            continue

        if kind == "ad":
            # Ads: just denoise, no spell correction
            out_blocks.append(strip_symbol_garbage(b))
        else:
            # News: spell correction if available
            if symspell is not None:
                b = heavy_spell_correct(b, symspell, protect, max_ed=2)
            b = strip_symbol_garbage(b)
            out_blocks.append(normalize_spaces(b))

    result = "\n\n".join(out_blocks).strip()

    # Final cleanup: if any leftover dense symbol junk appears, strip again
    result = strip_symbol_garbage(result)
    result = normalize_spaces(result)

    return result

# =========================
# Runner
# =========================
def main():
    in_path = Path(INPUT_CSV)
    if not in_path.exists():
        print(f"[ERROR] Input CSV not found: {in_path.resolve()}")
        sys.exit(1)

    df = pd.read_csv(in_path)

    if RAW_COL not in df.columns:
        print(f"[ERROR] RAW_COL '{RAW_COL}' not found. Columns are:\n{list(df.columns)}")
        sys.exit(1)

    protect = build_protect_words(df)

    symspell = None
    dict_path = Path(SYMSPELL_DICT_PATH)
    if dict_path.exists():
        try:
            symspell = load_symspell(str(dict_path), max_edit_distance=2)
            print(f"[OK] SymSpell dictionary loaded: {dict_path}")
        except Exception as e:
            print(f"[WARN] Failed to load SymSpell dictionary, will run without spelling correction.\n  {e}")
            symspell = None
    else:
        print(f"[WARN] SymSpell dictionary not found: {dict_path.resolve()}\n       Will run without spelling correction.")

    cleaned_list = []
    total = len(df)

    for i, raw in enumerate(df[RAW_COL].fillna("").astype(str).tolist(), start=1):
        cleaned = clean_one_ocr(raw, protect, symspell=symspell)
        cleaned_list.append(cleaned)
        if i % 200 == 0 or i == total:
            print(f"Processed {i}/{total}")

    df[OUT_COL] = cleaned_list
    out_path = Path(OUTPUT_CSV)
    df.to_csv(out_path, index=False)
    print(f"[DONE] Wrote: {out_path.resolve()} (added column: {OUT_COL})")
    
# =========================
# Addon 1
# =========================

# common box/shape glyphs from scans
BOX_GLYPHS_RE = re.compile(r"[■□▪▫◆◇●○◼◻◾◽▲△▼▽◆◊◌]+")
BOX_DRAWING_RE = re.compile(r"[\u2500-\u257F]+")   # box drawing unicode
BLOCKS_RE = re.compile(r"[\u2580-\u259F]+")        # block elements

# "confetti" lines: lots of tiny tokens like iV S> I 5' f-i- ~f ...
CONFETTI_LINE_RE = re.compile(
    r"(?:\b[A-Za-z]{1,2}\b|\b\d{1,2}\b|[^\w\s])(?:\s+|$)"
)

def strip_symbol_confetti(text: str) -> str:
    if not text:
        return text

    # remove box/shape glyphs
    text = BOX_GLYPHS_RE.sub(" ", text)
    text = BOX_DRAWING_RE.sub(" ", text)
    text = BLOCKS_RE.sub(" ", text)

    # line-level pruning: drop lines that look like pure "confetti"
    lines = re.split(r"\n+", text)
    kept = []
    for ln in lines:
        s = ln.strip()
        if not s:
            kept.append("")
            continue

        # If line contains shapes/blocks heavily, drop
        if len(re.findall(r"[■□▪▫◆◇●○◼◻◾◽]", s)) >= 1 and len(s) < 120:
            continue

        # confetti density: proportion of confetti tokens to line length
        confetti_tokens = CONFETTI_LINE_RE.findall(s)
        # many tiny tokens + low alphabet ratio -> junk
        alpha = len(re.findall(r"[A-Za-z]", s))
        alpha_ratio = alpha / max(len(s), 1)
        if len(confetti_tokens) >= 18 and alpha_ratio < 0.62:
            continue

        # lots of punctuation/symbols with sparse words
        sym = len(re.findall(r"[^A-Za-z0-9\s]", s))
        if len(s) >= 30 and sym / max(len(s), 1) > 0.35 and alpha_ratio < 0.70:
            continue

        kept.append(s)

    out = "\n".join(kept)

    # final cleanup: remove leftover isolated weird symbols
    out = re.sub(r"[•·¨´¸°¬§¶†‡※]+", " ", out)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()

if __name__ == "__main__":
    main()
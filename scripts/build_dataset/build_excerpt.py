# build_excerpt.py
# Excerpt extraction pipeline: reduces full-page OCR text to topic-relevant passages.
# Scores paragraphs and sliding windows against Chinese-education keyword patterns,
# then selects the highest-scoring extract for each document.
#
# Install:
#   pip install pandas openpyxl
#
# Run:
#   python build_excerpt.py

import re
import pandas as pd
from typing import List, Tuple
from difflib import SequenceMatcher

# =========================
# USER CONFIG (EDIT THESE)
# =========================
INPUT_CSV = "input.csv"
OUTPUT_CSV = "output_excerpts.csv"

KEYWORDS_LIST = [
    '"Chinese school"', '"Chinese education"', '"Chinese child"',
    '"Chinese children"', '"Chinese student"', '"Chinese boy"',
    '"Chinese girl"', '"Chinese students"', '"Chinese boys"', '"Chinese girls"'
]

# =========================
# EXTRACTION PARAMETERS
# =========================
MIN_REDUCED_CHARS = 180
MAX_OUTPUT_CHARS = 3500

PARA_WINDOW = 1           # paragraphs of context to include around each scored paragraph
MAX_PARAS_KEEP = 12       # hard cap on paragraph count in final output

WIN_SIZE = 800            # sliding window width in characters
WIN_STEP = 400            # step size between windows
TOPK_WINDOWS = 8          # max windows to keep

SENT_BACK_MAX = 500
SENT_FWD_MAX = 800

PARA_SIM_THRESHOLD = 0.92
SENT_SIM_THRESHOLD = 0.94

JOIN = "\n\n"

# Isolation marker: explicitly separates unrelated stories found on the same newspaper page
OMISSION_MARKER = "\n\n... [UNRELATED CONTENT] ...\n\n"

# =========================
# SCORING PATTERNS
# =========================
RX_CHINESE_EDU = re.compile(
    r"\b(?:chinese|china|chinaman|chinamen|chinee|celestial)(?:'s)?[\s\-]+"
    r"(?:[a-z]{1,15}[\s\-]+){0,1}"
    r"(?:education|school|schools|class|classes|teacher|teachers|pupil|pupils|scholar|scholars|student|students|child|children|boy|boys|girl|girls|youth|youths|infant|infants|kindergarten|instruction)\b",
    re.IGNORECASE
)

RX_CHINESE = re.compile(r"\b(chinese|chinaman|chinamen|china|chinee|celestial)\b", re.IGNORECASE)

CONTEXT_TERMS = [
    r"school", r"schools", r"education", r"educational", r"educat(?:e|ed|ing|ion)",
    r"student", r"students", r"pupil", r"pupils", r"class", r"classroom",
    r"teacher", r"teachers", r"principal", r"kindergarten", r"primary", r"elementary",
    r"grammar school", r"high school", r"academy", r"college", r"university",
    r"tuition", r"scholarship", r"lesson", r"lessons", r"curriculum", r"grade", r"graded", r"attendance",
    r"enroll", r"enrol", r"enrollment", r"admission", r"board of education", r"school board", r"public school",
    r"mission", r"missionary", r"sunday school", r"settlement", r"settlement house",
    r"night school", r"language school", r"child", r"children",
    r"boy", r"boys", r"girl", r"girls", r"youth", r"youths", r"parent", r"parents",
]
RX_CONTEXT = [re.compile(rf"\b{pat}\b", re.IGNORECASE) for pat in CONTEXT_TERMS]

EXCLUDE_TERMS = [
    r"ship", r"shipping", r"cargo", r"vessel", r"freight", r"import", r"export", r"tea", r"silk",
    r"market", r"prices", r"company", r"stock", r"dividend", r"railroad",
]
RX_EXCLUDE = [re.compile(rf"\b{pat}\b", re.IGNORECASE) for pat in EXCLUDE_TERMS]
RX_SENT_END = re.compile(r"[.!?]['\"\)\]]*$")

# =========================
# TEXT SCORING AND EXTRACTION
# =========================
def normalize_text(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)  # repair hyphenated line breaks
    t = t.replace("\n\n", "￿")
    t = t.replace("\n", " ")
    t = t.replace("￿", "\n\n")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def split_paragraphs(t: str) -> List[str]:
    paras = [p.strip() for p in t.split("\n\n") if p.strip()]
    return paras if len(paras) > 1 else ([t] if t else [])

def detect_exact_phrases(t: str) -> str:
    tl = t.lower()
    hits = []
    for kw in KEYWORDS_LIST:
        phrase = kw.strip().strip('"').lower()
        if phrase and phrase in tl:
            hits.append(phrase)
    return "|".join(hits)

def context_hits(s: str) -> int:
    return sum(1 for rx in RX_CONTEXT if rx.search(s))

def exclude_hits(s: str) -> int:
    return sum(1 for rx in RX_EXCLUDE if rx.search(s))

def score_text(s: str) -> int:
    if not RX_CHINESE.search(s):
        return -9999
    p1_hits = len(RX_CHINESE_EDU.findall(s))
    c_hits = context_hits(s)
    e_hits = exclude_hits(s)
    return 50 + (p1_hits * 500) + (c_hits * 50) - (e_hits * 5)

def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def dedup_similar(texts: List[str], threshold: float) -> List[str]:
    kept = []
    kept_norm = []
    for s in texts:
        ns = _norm(s)
        dup = False
        for kn in kept_norm:
            if _sim(ns, kn) >= threshold:
                dup = True
                break
        if not dup:
            kept.append(s)
            kept_norm.append(ns)
    return kept

def expand_to_sentence_bounds(full_text: str, start: int, end: int) -> Tuple[int, int]:
    n = len(full_text)
    start = max(0, start)
    end = min(n, end)

    back_start = max(0, start - SENT_BACK_MAX)
    back = full_text[back_start:start]
    m = list(re.finditer(r"[.!?]\s+", back))
    if m:
        start2 = back_start + m[-1].end()
    else:
        start2 = back_start

    fwd_end = min(n, end + SENT_FWD_MAX)
    fwd = full_text[end:fwd_end]
    m2 = re.search(r"[.!?]['\"\)\]]*\s+", fwd)
    if m2:
        end2 = end + m2.end()
    else:
        end2 = fwd_end

    return max(0, start2), min(n, end2)

def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return out

def truncate_by_sentences(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    sents = split_sentences(text)
    out = []
    cur = 0
    for s in sents:
        add = (s + " ")
        if cur + len(add) > max_chars and out:
            break
        if cur + len(add) <= max_chars:
            out.append(s)
            cur += len(add)
        else:
            break
    return " ".join(out).strip()

def reduce_by_paragraph(t: str) -> Tuple[str, int, str]:
    paras = split_paragraphs(t)
    keep = []
    for i, p in enumerate(paras):
        if score_text(p) > 0:
            for j in range(max(0, i - PARA_WINDOW), min(len(paras), i + PARA_WINDOW + 1)):
                keep.append(paras[j])
    if not keep:
        return "", -9999, "paragraph_none"
    keep = dedup_similar(keep, PARA_SIM_THRESHOLD)

    final_keep = []
    current_len = 0
    scored = [(score_text(p), p) for p in keep]
    scored.sort(reverse=True, key=lambda x: x[0])

    for _, p in scored:
        if current_len + len(p) > MAX_OUTPUT_CHARS:
            continue
        final_keep.append(p)
        current_len += len(p)
        if len(final_keep) >= MAX_PARAS_KEEP:
            break

    final_keep = [p for p in keep if p in final_keep]
    reduced = "\n\n".join(final_keep).strip()
    return reduced, score_text(reduced), "paragraph_topk_budgeted"

def windows(text: str, win_size: int, step: int) -> List[Tuple[int, int, str]]:
    out = []
    n = len(text)
    start = 0
    while start < n:
        end = min(n, start + win_size)
        out.append((start, end, text[start:end]))
        if end == n:
            break
        start += step
    return out

def reduce_by_sliding_window(t: str) -> Tuple[str, int, str]:
    wins = windows(t, WIN_SIZE, WIN_STEP)
    scored = []
    for s, e, w in wins:
        sc = score_text(w)
        if sc > 0:
            scored.append((sc, s, e, w))
    if not scored:
        return "", -9999, "window_none"

    scored.sort(reverse=True, key=lambda x: x[0])

    picked = []
    current_char_count = 0

    for sc, s, e, w in scored:
        too_much = False
        for _, ps, pe, _ in picked:
            overlap = max(0, min(e, pe) - max(s, ps))
            if overlap / max(1, (e - s)) > 0.6:
                too_much = True
                break
        if too_much:
            continue

        s2, e2 = expand_to_sentence_bounds(t, s, e)
        w2 = t[s2:e2].strip()

        if current_char_count + len(w2) > MAX_OUTPUT_CHARS:
            if not picked:
                w2 = truncate_by_sentences(w2, MAX_OUTPUT_CHARS)
            else:
                continue

        picked.append((sc, s2, e2, w2))
        current_char_count += len(w2)

        if len(picked) >= TOPK_WINDOWS:
            break

    # Sort by original text position; insert isolation marker between fragments
    # separated by more than 100 characters to prevent silent story merging
    picked_sorted = sorted(picked, key=lambda x: x[1])

    final_fragments = []
    last_end = -1

    for sc, s, e, w in picked_sorted:
        # Check for a large positional gap between this fragment and the previous one
        if last_end != -1 and s > last_end + 100:
            final_fragments.append(OMISSION_MARKER)

        final_fragments.append(w)
        last_end = e

    reduced = "".join(final_fragments).strip()
    return reduced, score_text(reduced), "sliding_topk_budgeted"

def extract_reduced(text: str) -> Tuple[str, str, float, int]:
    t = normalize_text(text)
    if not t:
        return "", "empty", 0.0, 0

    p_text, p_score, p_method = reduce_by_paragraph(t)
    w_text, w_score, w_method = reduce_by_sliding_window(t)

    if w_score >= p_score and len(w_text) > 0:
        chosen_text, chosen_method, chosen_score = w_text, w_method, w_score
    else:
        chosen_text, chosen_method, chosen_score = p_text, p_method, p_score

    # Preserve all paragraph breaks and isolation markers — do not flatten
    keep_ratio = (len(chosen_text) / len(t)) if len(t) else 0.0
    return chosen_text, chosen_method, round(keep_ratio, 4), chosen_score

# =========================
# MAIN
# =========================
def main():
    try:
        df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")
    except FileNotFoundError:
        print(f"[ERROR] Input file not found: {INPUT_CSV}")
        return

    if "cleaned_ocr" not in df.columns:
        raise KeyError("Column 'cleaned_ocr' not found. Check your input column names.")

    df["OCR_cleaned"] = ""
    df["token_count"] = ""
    df["relevance_tier"] = ""
    df["topic_tags"] = ""

    # Auxiliary diagnostics
    df["reduced_method"] = ""
    df["reduced_keep_ratio"] = ""
    df["reduced_score"] = ""

    total = len(df)
    for i in range(total):
        raw_text = df.at[i, "cleaned_ocr"]

        norm_text = normalize_text(raw_text)
        df.at[i, "topic_tags"] = detect_exact_phrases(norm_text)

        reduced, method, ratio, score = extract_reduced(raw_text)
        df.at[i, "OCR_cleaned"] = reduced
        df.at[i, "token_count"] = str(len(reduced.split()))
        df.at[i, "relevance_tier"] = "core" if score >= 550 else "secondary"
        df.at[i, "reduced_method"] = method
        df.at[i, "reduced_keep_ratio"] = str(ratio)
        df.at[i, "reduced_score"] = str(score)

        if (i + 1) % 50 == 0 or (i + 1) == total:
            print(f"Processed {i + 1}/{total}")

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"[DONE] Saved: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

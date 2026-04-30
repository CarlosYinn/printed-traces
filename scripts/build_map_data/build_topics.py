"""
Build topics.json from merged_topic_labels.csv.

Usage:
    python scripts/build_map_data/build_topics.py

Output:
    docs/public/data/topics.json
"""

import json
import logging
import re
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = ROOT / "data/merged_topic_labels.csv"
OUTPUT_JSON = ROOT / "docs/public/data/topics.json"


# ── ID helpers ────────────────────────────────────────────────────────────────

_STOPWORDS = {"and", "the", "of", "a", "an"}


def _category_prefix(cat: str) -> str:
    """Acronym from initials of significant words; fallback to first 3 chars."""
    words = re.split(r"[\s,&]+", cat)
    initials = [w[0].lower() for w in words if w and w.lower() not in _STOPWORDS]
    if len(initials) >= 2:
        return "".join(initials)
    first = next((w for w in words if w), cat)
    return first[:3].lower()


def _snake(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower())
    return s.strip("_")


def _topic_id(cat: str, label: str) -> str:
    prefix = _category_prefix(cat)
    # Strip any leading "ABBR: " that mirrors the category prefix to avoid double-prefix IDs
    # e.g. "CEM: Government Policy..." → strip the "CEM: " part
    cleaned = re.sub(r"^[A-Za-z]{2,5}:\s*", "", label)
    return prefix + "_" + _snake(cleaned)


def _nullable(val) -> str | None:
    """Convert pandas NaN/None to Python None for JSON serialisation."""
    return None if pd.isna(val) else val


# ── Aggregation ───────────────────────────────────────────────────────────────

def _effective_weight(row: pd.Series) -> float:
    """Max of deduped_weight and all_weight, ignoring NaN."""
    vals = [v for v in (row["deduped_weight"], row["all_weight"]) if pd.notna(v)]
    return round(max(vals), 4) if vals else 0.0


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group by (category, analytic_label) and collapse duplicate rows.
    Each group keeps: first non-null of every metadata column,
    deduped_topic_id / all_topic_id merged across rows,
    weight = max(deduped_weight, all_weight).
    """
    def _agg(g: pd.DataFrame) -> pd.Series:
        deduped_ids = g["deduped_topic_id"].dropna().unique().tolist()
        all_ids = g["all_topic_id"].dropna().unique().tolist()
        dw = g["deduped_weight"].max()
        aw = g["all_weight"].max()
        weight_vals = [v for v in (dw, aw) if pd.notna(v)]
        weight = round(max(weight_vals), 4) if weight_vals else 0.0
        first = g.iloc[0]
        return pd.Series(
            {
                "category_color": first["category_color"],
                "category_hue": first["category_hue"],
                "topic_color": first["topic_color"],
                "deduped_topic_id": deduped_ids[0] if deduped_ids else None,
                "all_topic_id": all_ids[0] if all_ids else None,
                "weight": weight,
                "exclude": first["exclude"],
            }
        )

    return df.groupby(["category", "analytic_label"], sort=False).apply(_agg).reset_index()


# ── Build output ──────────────────────────────────────────────────────────────

def build(df: pd.DataFrame) -> dict:
    # Preserve category order as they appear in the CSV
    cat_order = list(dict.fromkeys(df["category"]))

    categories = []
    for cat in cat_order:
        rows = df[df["category"] == cat]
        first = rows.iloc[0]

        topics = []
        for _, row in rows.iterrows():
            excl = str(row["exclude"]).strip().lower() in ("yes", "true", "1")
            # NOISE category: force exclude
            if cat == "NOISE":
                excl = True
            topics.append(
                {
                    "id": _topic_id(cat, row["analytic_label"]),
                    "label": row["analytic_label"],
                    "color": row["topic_color"],
                    "deduped_topic_id": _nullable(row["deduped_topic_id"]),
                    "all_topic_id": _nullable(row["all_topic_id"]),
                    "weight": row["weight"],
                    "exclude": excl,
                }
            )

        categories.append(
            {
                "name": cat,
                "color": first["category_color"],
                "hue": first["category_hue"],
                "topics": topics,
            }
        )

    return {"categories": categories}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    log.info("Reading %s", INPUT_CSV)
    df = pd.read_csv(INPUT_CSV)
    log.info("Loaded %d rows, columns: %s", len(df), df.columns.tolist())

    agg = aggregate(df)
    log.info("After aggregation: %d (category, label) pairs", len(agg))

    out = build(agg)

    n_cats = len(out["categories"])
    n_topics = sum(len(c["topics"]) for c in out["categories"])
    n_exclude = sum(t["exclude"] for c in out["categories"] for t in c["topics"])

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    log.info("Wrote %s", OUTPUT_JSON)
    log.info("── Stats ──────────────────────────────────────────────")
    log.info("  categories : %d", n_cats)
    log.info("  topics     : %d", n_topics)
    log.info("  excluded   : %d", n_exclude)

    if n_cats != 10:
        log.warning("Expected 10 categories, got %d", n_cats)
    if n_topics != 25:
        log.warning("Expected 25 topics, got %d", n_topics)


if __name__ == "__main__":
    main()

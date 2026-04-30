"""
Build records.json from dataset.csv + county boundaries + topic labels.

Usage:
    python scripts/build_map_data/build_records.py

Requires (run first):
    build_boundaries.py  → docs/public/data/counties_1882.geojson
    build_topics.py      → docs/public/data/topics.json

Output:
    docs/public/data/records.json
"""

import hashlib
import json
import logging
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "docs/public/data"

COUNTIES_GEOJSON = OUT_DIR / "counties_1882.geojson"
TOPICS_JSON = OUT_DIR / "topics.json"
DATASET_CSV = DATA_DIR / "dataset.csv"
DOC_TOPICS_S2_TXT = DATA_DIR / "doc-topics_K25_S2.txt"
DOC_TOPICS_ALL_TXT = DATA_DIR / "all_doc-topics_K25_S1.txt"
TOPIC_LABELS_CSV = DATA_DIR / "merged_topic_labels.csv"

HONOLULU = (21.3099, -157.8581)  # fixed coords for Hawaii records

# ── State name → 1882-era state_abbr (matches counties GeoJSON state_abbr) ──
STATE_NAME_TO_ABBR = {
    "alabama": "AL", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "district of columbia": "DC", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "idaho territory": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT",
    "nebraska": "NE", "nevada": "NV", "new hampshire": "NH",
    "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC",
    "north dakota": "DT",    # Dakota Territory in 1882
    "south dakota": "DT",    # Dakota Territory in 1882
    "dakota territory": "DT",
    "ohio": "OH", "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI",
    "south carolina": "SC", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    "alaska": "AK",
    "indian territory": "IT",
    "v.i.": "VI",
}

# Fallback centroids for states/territories with no county data in geojson
_HARDCODED_CENTROIDS = {
    "IT": (35.5, -96.9),   # Indian Territory (approx. Oklahoma)
    "VI": (18.0, -64.8),   # Virgin Islands
    "HI": (20.798, -156.332),  # Hawaii general centroid
}

# ── city_to_county_1882 ───────────────────────────────────────────────────────
# key = (city_lower, state_lower),  value = county_name_lower (or None for HI)
# Covers top-110 city/state combos by frequency; uncertain entries omitted.
city_to_county_1882 = {
    # Top 20 (user-specified)
    ("sacramento", "california"): "sacramento",
    ("honolulu", "hawaii"): None,          # special: Level 3 Hawaii
    ("los angeles", "california"): "los angeles",
    ("new york", "new york"): "new york",
    ("new haven", "connecticut"): "new haven",
    ("cheyenne", "wyoming"): "laramie",
    ("wilmington", "delaware"): "new castle",
    ("savannah", "georgia"): "chatham",
    ("richmond", "virginia"): "henrico",
    ("salt lake city", "utah"): "salt lake",
    ("indianapolis", "indiana"): "marion",
    ("washington", "district of columbia"): "district of columbia",
    ("eureka", "nevada"): "eureka",
    ("chicago", "illinois"): "cook",
    ("augusta", "maine"): "kennebec",
    ("saint paul", "minnesota"): "ramsey",
    ("charleston", "georgia"): "chatham",   # NOTE: Charleston GA (not SC)
    ("portland", "maine"): "cumberland",
    ("greenville", "south carolina"): "greenville",
    ("springfield", "massachusetts"): "hampden",
    # 21-110 (historical research)
    ("oakland", "maryland"): "garrett",
    ("rock island", "illinois"): "rock island",
    ("st. paul", "minnesota"): "ramsey",    # alias for Saint Paul
    ("omaha", "nebraska"): "douglas",
    ("salisbury", "connecticut"): "litchfield",
    ("dallas", "texas"): "dallas",
    ("hillsborough", "ohio"): "highland",   # Hillsboro, county seat of Highland Co.
    ("lancaster", "pennsylvania"): "lancaster",
    ("unionville", "nevada"): "humboldt",
    ("owosso", "michigan"): "shiawassee",
    ("helena", "montana"): "lewis and clark",
    ("medicine lodge", "kansas"): "barber",
    ("seattle", "washington"): "king",
    ("astoria", "oregon"): "clatsop",
    ("iola", "kansas"): "allen",
    ("eaton", "ohio"): "preble",
    ("ironton", "missouri"): "iron",
    ("milan", "tennessee"): "gibson",
    ("charleston", "south carolina"): "charleston",
    ("opelousas", "louisiana"): "saint landry",
    ("redwood falls", "minnesota"): "redwood",
    ("bismarck", "north dakota"): "burleigh",   # Burleigh County DT in 1882
    ("butte", "montana"): "silver bow",
    ("yankton", "dakota territory"): "yankton",
    ("morrisville", "vermont"): "lamoille",
    ("annapolis", "maryland"): "anne arundel",
    ("watertown", "wisconsin"): "jefferson",
    ("wellington", "ohio"): "lorain",
    ("deer lodge", "montana"): "deer lodge",    # Powell County not created until 1901
    ("ottawa", "illinois"): "la salle",
    ("olympia", "washington"): "thurston",
    ("morgantown", "west virginia"): "monongalia",
    ("carson city", "nevada"): "ormsby",        # Ormsby County (modern Carson City Co.)
    ("canton", "south dakota"): "lincoln",      # Lincoln County DT
    ("morris", "minnesota"): "stevens",
    ("central falls", "rhode island"): "providence",
    ("memphis", "tennessee"): "shelby",
    ("abbeville", "south carolina"): "abbeville",
    ("springfield", "ohio"): "clark",
    ("woodbury", "new jersey"): "gloucester",
    ("kimball", "dakota territory"): "brule",
    ("kimball", "south dakota"): "brule",
    ("las vegas", "new mexico"): "san miguel",
    ("manitowoc", "wisconsin"): "manitowoc",
    ("magnolia", "mississippi"): "pike",
    ("washington city", "district of columbia"): "district of columbia",
    ("east providence", "rhode island"): "providence",
    ("dodge city", "kansas"): "ford",
    ("idaho city", "idaho"): "boise",
    ("red cloud", "nebraska"): "webster",
    ("winnsboro", "south carolina"): "fairfield",
    ("ridgway", "pennsylvania"): "elk",
    ("raleigh", "north carolina"): "wake",
    ("pinal city", "arizona"): "pinal",
    ("ravenna", "ohio"): "portage",
    ("columbus", "nebraska"): "platte",
    ("hopkinsville", "kentucky"): "christian",
    ("grenada", "mississippi"): "grenada",
    ("wheeling", "west virginia"): "ohio",      # Ohio County WV
    ("grand rapids", "wisconsin"): "wood",      # became Wisconsin Rapids 1920
    ("colfax", "louisiana"): "grant",
    ("corvallis", "oregon"): "benton",
    ("willimantic", "connecticut"): "windham",
    ("livingston", "montana"): "park",
    ("maysville", "kentucky"): "mason",
    ("jackson", "mississippi"): "hinds",
    ("covington", "louisiana"): "saint tammany",
    ("osceola", "arkansas"): "mississippi",
    ("canton", "illinois"): "fulton",
    ("mineral point", "wisconsin"): "iowa",
    ("charlotte", "north carolina"): "mecklenburg",
    ("butler", "pennsylvania"): "butler",
    ("port tobacco", "maryland"): "charles",
    ("paw paw", "michigan"): "van buren",
    ("o'neill city", "nebraska"): "holt",
    ("staunton", "virginia"): "augusta",
    ("cairo", "illinois"): "alexander",
    ("burlington", "vermont"): "chittenden",
    ("superior", "wisconsin"): "douglas",
    ("elko", "nevada"): "elko",
    ("albany", "oregon"): "linn",
    ("concord", "new hampshire"): "merrimack",
    # Remaining from top-110 with uncertain 1882 attribution (TODO):
    # ('wheeling', 'ohio') → unclear small Wheeling OH; falls to Level 2/3
    # ('narragansett pier', 'washington') → data anomaly; likely RI not WA
    # ('clifton', 'south dakota') → unclear DT county
    # ('memphis', 'alabama') → unclear small town
    # ('memphis', 'georgia') → unclear small town
    # ('lansing', 'minnesota') → unclear
    # ('mineral point', 'iowa') → no prominent Mineral Point in IA
    # ('bellevue', 'louisiana') → unclear parish
}

log.info("city_to_county_1882 loaded: %d entries", len(city_to_county_1882))


# ── Helpers ───────────────────────────────────────────────────────────────────

_COUNTY_SUFFIXES = (
    " county", " parish", " co.", " co",
    " district", " dist.", " dist",
)


def _strip_county(name: str) -> str:
    """Lowercase and strip common county/parish suffixes."""
    n = name.lower().strip()
    for sfx in _COUNTY_SUFFIXES:
        if n.endswith(sfx):
            return n[: -len(sfx)].strip()
    return n


def _jitter(doc_id: str, base_lat: float, base_lng: float, tier: int) -> tuple[float, float]:
    """Deterministic lat/lng jitter based on doc_id hash."""
    h = int(hashlib.md5(doc_id.encode()).hexdigest()[:8], 16)
    angle = (h & 0xFFFF) / 0xFFFF * 2 * math.pi
    if tier <= 2:
        radius_km = 2 + ((h >> 16) & 0xFFFF) / 0xFFFF * 6   # 2–8 km
    else:
        radius_km = 20 + ((h >> 16) & 0xFFFF) / 0xFFFF * 30  # 20–50 km
    lat_off = radius_km / 111.0 * math.sin(angle)
    lng_off = radius_km / (111.0 * math.cos(math.radians(base_lat))) * math.cos(angle)
    return round(base_lat + lat_off, 5), round(base_lng + lng_off, 5)


def _excerpt(text: str | None, max_chars: int = 240) -> str:
    if not text or pd.isna(text):
        return ""
    s = str(text)
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars]
    last_space = cut.rfind(" ")
    if last_space > 0:
        cut = cut[:last_space]
    return cut + "…"


def _parse_coverage_region(cr) -> list[list]:
    """Return list of [city, county_or_None] pairs from Coverage_Region."""
    if not cr or pd.isna(cr):
        return []
    segs = [s.strip() for s in str(cr).split("|") if s.strip()]
    pairs = []
    for i in range(0, len(segs), 2):
        pairs.append([segs[i], segs[i + 1] if i + 1 < len(segs) else None])
    return pairs


# ── Prerequisite checks ───────────────────────────────────────────────────────

def _check_prereqs() -> None:
    missing = []
    if not COUNTIES_GEOJSON.exists():
        missing.append(f"{COUNTIES_GEOJSON}  → run build_boundaries.py first")
    if not TOPICS_JSON.exists():
        missing.append(f"{TOPICS_JSON}  → run build_topics.py first")
    for p in (DATASET_CSV, DOC_TOPICS_S2_TXT, TOPIC_LABELS_CSV):
        if not p.exists():
            missing.append(str(p))
    if missing:
        for m in missing:
            log.error("Missing: %s", m)
        sys.exit(1)


# ── County / state centroids ──────────────────────────────────────────────────

def build_centroids(
    gdf: gpd.GeoDataFrame,
) -> tuple[dict, dict]:
    """
    Returns:
        county_centroids: dict[(state_abbr, county_lower), (lat, lng)]
        state_centroids:  dict[state_abbr, (lat, lng)]
    """
    county_centroids: dict = {}
    state_geoms: dict = defaultdict(list)

    for _, row in gdf.iterrows():
        abbr = row["state_abbr"]
        raw_name = row["NAME"]
        geom = row["geometry"]
        if geom is None or geom.is_empty:
            continue

        key = (abbr, _strip_county(raw_name))
        c = geom.centroid
        county_centroids[key] = (round(c.y, 5), round(c.x, 5))
        state_geoms[abbr].append(geom)

    state_centroids: dict = {}
    for abbr, geoms in state_geoms.items():
        union = unary_union(geoms)
        c = union.centroid
        state_centroids[abbr] = (round(c.y, 5), round(c.x, 5))

    # Add hardcoded fallbacks for territories without county data
    for abbr, coords in _HARDCODED_CENTROIDS.items():
        if abbr not in state_centroids:
            state_centroids[abbr] = coords

    log.info("county_centroids: %d entries", len(county_centroids))
    log.info("state_centroids: %d entries (+ %d hardcoded)", len(state_centroids), len(_HARDCODED_CENTROIDS))
    return county_centroids, state_centroids


# ── Topics loading ────────────────────────────────────────────────────────────

def load_topics_lookup(path: Path) -> dict[str, dict]:
    """label.lower() → topic info dict, from topics.json."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    lut: dict[str, dict] = {}
    for cat in data["categories"]:
        for t in cat["topics"]:
            lut[t["label"].lower()] = {
                "id": t["id"],
                "label": t["label"],
                "color": t["color"],
                "category": cat["name"],
                "category_color": cat["color"],
                "exclude": t["exclude"],
            }
    return lut


def build_mallet_to_analytic(
    labels_df: pd.DataFrame,
    label_to_topic: dict,
    source_filter: tuple[str, ...] = ("deduped", "both"),
    id_column: str = "deduped_topic_id",
) -> dict[int, dict]:
    """int topic_index → analytic info dict.

    source_filter: which rows of merged_topic_labels.csv to include.
    id_column:     which column holds the MALLET topic index for this model.
    """
    result: dict[int, dict] = {}
    for _, row in labels_df[labels_df["source"].isin(source_filter)].iterrows():
        if pd.isna(row.get(id_column)):
            continue
        idx = int(str(row[id_column]).split("_")[1])
        label_lower = str(row["analytic_label"]).lower()
        info = label_to_topic.get(
            label_lower,
            {
                "id": f"unmapped_topic_{idx}",
                "label": row["analytic_label"],
                "color": str(row.get("topic_color", "#9ca0b0")),
                "category": str(row.get("category", "Other")),
                "category_color": str(row.get("category_color", "#9ca0b0")),
                "exclude": str(row.get("exclude", "no")).strip().lower() == "yes",
            },
        )
        result[idx] = info
    return result


def _sanity_check_mallet(
    mallet_to_analytic: dict[int, dict],
    s2_index_by_doc: dict[str, int],
    dataset_df: pd.DataFrame,
) -> None:
    missing = [i for i in range(25) if i not in mallet_to_analytic]
    if not missing:
        log.info("Sanity: all 25 MALLET topic indices mapped ✓")
        return

    log.warning("Missing MALLET topic indices in deduped mapping: %s", missing)

    # For each missing index, find the most common first topic_tag among docs
    # whose dominant S2 topic is that index → use as fallback label
    tags_by_idx: dict[int, list[str]] = {i: [] for i in missing}
    for doc_id, idx in s2_index_by_doc.items():
        if idx not in tags_by_idx:
            continue
        row = dataset_df[dataset_df["doc_id"] == doc_id]
        if row.empty:
            continue
        tags_raw = row.iloc[0].get("topic_tags", "")
        if pd.notna(tags_raw) and str(tags_raw).strip():
            tags_by_idx[idx].append(str(tags_raw).split("|")[0].strip())

    for idx in missing:
        top_tag = Counter(tags_by_idx[idx]).most_common(1)
        label = top_tag[0][0] if top_tag else f"Unmapped Topic {idx}"
        fallback = {
            "id": f"unmapped_topic_{idx}",
            "label": label,
            "color": "#9ca0b0",
            "category": "Other",
            "category_color": "#9ca0b0",
            "exclude": False,
        }
        mallet_to_analytic[idx] = fallback
        log.warning(
            "  topic_%d → fallback label=%r (from %d docs' top tag)",
            idx, label, len(tags_by_idx[idx]),
        )


# ── S2 doc-topic index ────────────────────────────────────────────────────────

def load_topic_index(path: Path, label: str = "") -> tuple[dict[str, int], dict[str, float]]:
    """doc_id → (dominant topic index, confidence).  Works for any MALLET doc-topics file."""
    index: dict[str, int] = {}
    confidence: dict[str, float] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 27:
                continue
            doc_id = parts[1]
            props = [float(x) for x in parts[2:]]
            m = max(props)
            index[doc_id] = props.index(m)
            confidence[doc_id] = m
    log.info("%s topic index loaded: %d docs", label or path.name, len(index))
    return index, confidence


def build_group_to_s2_topic(
    dataset_df: pd.DataFrame,
    s2_index: dict[str, int],
    s2_confidence: dict[str, float],
) -> tuple[dict[str, int], dict[str, str]]:
    """
    Returns:
        group_to_s2_topic:  duplicate_group → dominant topic index
        group_to_best_text: duplicate_group → model_text of the best S2 member

    Topic is chosen by confidence-weighted majority vote across all S2 members
    in the group.  The excerpt text still comes from the highest-priority member
    (is_original > chain_position=1 > any), so the two choices are independent.
    """
    doc_to_text: dict[str, str] = {
        row["doc_id"]: str(row["model_text"])
        for _, row in dataset_df.iterrows()
        if pd.notna(row.get("model_text"))
    }

    # group → list of (priority, doc_id) for all S2 members
    group_candidates: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for _, row in dataset_df.iterrows():
        grp = row["duplicate_group"]
        if pd.isna(grp):
            continue
        doc_id = row["doc_id"]
        if doc_id not in s2_index:
            continue
        prio = 2
        if row["is_original"] is True or str(row["is_original"]).lower() == "true":
            prio = 0
        elif str(row.get("chain_position", "")).strip() in ("1", "1.0"):
            prio = 1
        group_candidates[str(grp)].append((prio, doc_id))

    topic_result: dict[str, int] = {}
    text_result: dict[str, str] = {}
    for grp, candidates in group_candidates.items():
        # ── Topic: confidence-weighted majority vote across all S2 members ──
        # Each member casts a vote for its argmax topic, weighted by its
        # confidence (max proportion).  This is more robust than picking a
        # single member, especially when no is_original member is in S2.
        topic_votes: Counter = Counter()
        for _, doc_id in candidates:
            topic_votes[s2_index[doc_id]] += s2_confidence[doc_id]
        topic_result[grp] = topic_votes.most_common(1)[0][0]

        # ── Text: still from the highest-priority member ──
        best_doc = sorted(candidates)[0][1]
        if best_doc in doc_to_text:
            text_result[grp] = doc_to_text[best_doc]

    log.info("group_to_s2_topic: %d groups", len(topic_result))
    return topic_result, text_result


# ── Topic tags fallback ───────────────────────────────────────────────────────

# Tags shorter than this are too generic to anchor a topic match reliably.
_MIN_TAG_LEN = 5


def _best_topic_from_tags(tags: list[str], label_to_topic: dict) -> dict | None:
    """
    Score every analytic label across ALL topic_tags, then return the best.

    Scoring:
      - Each tag that matches a label (tag ⊂ label or label ⊂ tag) adds
        len(tag) points to that label's score.  Longer tags are more specific
        and thus count for more.
      - Tags shorter than _MIN_TAG_LEN are skipped (too generic).
      - Excluded topics are never candidates.
      - In case of a tie, the shorter label wins (more targeted).
    """
    label_scores: Counter = Counter()
    label_to_info: dict = {}

    for tag in tags:
        t = tag.lower().strip()
        if len(t) < _MIN_TAG_LEN:
            continue
        # Exact match → give a large bonus so it always dominates
        if t in label_to_topic and not label_to_topic[t].get("exclude"):
            label_scores[t] += len(t) * 10
            label_to_info[t] = label_to_topic[t]
            continue
        for label, info in label_to_topic.items():
            if info.get("exclude"):
                continue
            if t in label or label in t:
                # Prefix match (label starts with the tag) is a stronger signal
                # than a mid-string match, so give it a 2× bonus.
                multiplier = 2 if label.startswith(t) or t.startswith(label) else 1
                label_scores[label] += len(t) * multiplier
                label_to_info[label] = info

    if not label_scores:
        return None

    top_score = label_scores.most_common(1)[0][1]
    # Among equally-scored labels prefer the shorter one (more targeted)
    candidates = [(label, info) for label, info in label_to_info.items()
                  if label_scores[label] == top_score]
    best_label = min(candidates, key=lambda x: len(x[0]))[0]
    return label_to_info[best_label]


_FALLBACK_TOPIC = {
    "id": "other_unmapped",
    "label": "Unmapped",
    "color": "#9ca0b0",
    "category": "Other",
    "category_color": "#9ca0b0",
    "exclude": False,
}


def resolve_topic(
    row: pd.Series,
    s2_index: dict[str, int],
    all_index: dict[str, int],
    group_to_s2: dict[str, int],
    s2_mallet_to_analytic: dict[int, dict],
    all_mallet_to_analytic: dict[int, dict],
    all_only_ids: set[str],
    label_to_topic: dict,
) -> tuple[dict, str]:
    """Return (topic_info, topic_source).

    Priority:
      1. "all" model when it yields a source=all fine-grained sub-label
         (e.g. CEM sub-topics, Diplomacy).  These labels exist only in the
         "all" corpus and would otherwise always be zero.
      2. S2 direct — preserves deduped-only labels (Sino-French War, etc.)
         that have no equivalent in the "all" model.
      3. "all" direct for records not in S2 (reprints and edge cases).
      4. Group inheritance from the best S2 member.
      5. topic_tags scoring fallback.
    """
    doc_id = row["doc_id"]

    # 1. "all" model → fine-grained sub-label
    if doc_id in all_index:
        idx = all_index[doc_id]
        if idx in all_mallet_to_analytic:
            info = all_mallet_to_analytic[idx]
            if not info.get("exclude") and info["id"] in all_only_ids:
                return info, "all_direct"

    # 2. S2 direct
    if doc_id in s2_index:
        return s2_mallet_to_analytic[s2_index[doc_id]], "s2_direct"

    # 3. "all" direct for non-S2 records
    if doc_id in all_index:
        idx = all_index[doc_id]
        if idx in all_mallet_to_analytic:
            info = all_mallet_to_analytic[idx]
            if not info.get("exclude"):
                return info, "all_direct"

    # 4. Inherited from duplicate group (S2 original's topic)
    grp = row["duplicate_group"]
    if pd.notna(grp) and str(grp) in group_to_s2:
        idx = group_to_s2[str(grp)]
        return s2_mallet_to_analytic[idx], "s2_inherited"

    # 5. topic_tags scoring fallback
    tags_raw = row.get("topic_tags", "")
    tags = [t.strip() for t in str(tags_raw).split("|")] if pd.notna(tags_raw) else []
    match = _best_topic_from_tags(tags, label_to_topic)
    if match:
        return match, "topic_tags_fallback"
    return {**_FALLBACK_TOPIC, "label": tags[0] if tags else "Unmapped"}, "topic_tags_fallback"


# ── Geo lookup ────────────────────────────────────────────────────────────────

def locate(
    row: pd.Series,
    county_centroids: dict,
    state_centroids: dict,
) -> tuple[float, float, int]:
    """
    Return (lat, lng, tier).
    Applies deterministic jitter for all tiers.
    Hawaii records → fixed Honolulu coords, tier=3, no jitter.
    """
    doc_id = row["doc_id"]
    pub_city = str(row["Pub_City"]).strip().lower() if pd.notna(row["Pub_City"]) else ""
    pub_state = str(row["Pub_State"]).strip().lower() if pd.notna(row["Pub_State"]) else ""
    state_abbr = STATE_NAME_TO_ABBR.get(pub_state, "")

    # Special: Hawaii
    if pub_state == "hawaii":
        return HONOLULU[0], HONOLULU[1], 3

    # ── Level 1: city_to_county_1882 lookup ──────────────────────────────────
    county_l1 = city_to_county_1882.get((pub_city, pub_state))
    if county_l1 is not None and county_l1 and state_abbr:
        coords = county_centroids.get((state_abbr, county_l1))
        if coords:
            lat, lng = _jitter(doc_id, coords[0], coords[1], tier=1)
            return lat, lng, 1

    # ── Level 2: Coverage_Region county segments ─────────────────────────────
    if state_abbr:
        cr = row.get("Coverage_Region", "")
        segs = [s.strip() for s in str(cr).split("|") if s.strip()] if pd.notna(cr) else []
        for seg in segs:
            cleaned = _strip_county(seg)
            coords = county_centroids.get((state_abbr, cleaned))
            if coords:
                lat, lng = _jitter(doc_id, coords[0], coords[1], tier=2)
                return lat, lng, 2

    # ── Level 3: state centroid ───────────────────────────────────────────────
    coords = state_centroids.get(state_abbr) if state_abbr else None
    if coords:
        lat, lng = _jitter(doc_id, coords[0], coords[1], tier=3)
        return lat, lng, 3

    # Ultimate fallback: US geographic center
    lat, lng = _jitter(doc_id, 39.5, -98.35, tier=3)
    log.warning("No location for doc_id=%s pub_state=%r — using US center", doc_id, pub_state)
    return lat, lng, 3


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _check_prereqs()

    # ── Load all inputs ───────────────────────────────────────────────────────
    log.info("Loading dataset.csv …")
    df = pd.read_csv(DATASET_CSV, encoding="utf-8-sig")
    log.info("dataset.csv: %d rows", len(df))
    if len(df) != 1535:
        log.warning("Expected 1535 rows, got %d", len(df))

    log.info("Loading counties_1882.geojson …")
    counties_gdf = gpd.read_file(COUNTIES_GEOJSON)
    county_centroids, state_centroids = build_centroids(counties_gdf)

    log.info("Loading topics.json …")
    label_to_topic = load_topics_lookup(TOPICS_JSON)

    log.info("Loading merged_topic_labels.csv …")
    labels_df = pd.read_csv(TOPIC_LABELS_CSV)
    # S2 model: deduped + both rows → broad labels (Sino-French War, etc.)
    s2_mallet_to_analytic = build_mallet_to_analytic(
        labels_df, label_to_topic, ("deduped", "both"), "deduped_topic_id"
    )
    # "all" model: all + both rows → fine-grained sub-labels (CEM sub-topics, Diplomacy…)
    all_mallet_to_analytic = build_mallet_to_analytic(
        labels_df, label_to_topic, ("all", "both"), "all_topic_id"
    )
    # IDs that exist only in the "all" model — these are the sub-labels that
    # would otherwise be zero if we only used the S2 model.
    all_only_ids: set[str] = {
        label_to_topic[str(r["analytic_label"]).lower()]["id"]
        for _, r in labels_df[labels_df["source"] == "all"].iterrows()
        if str(r["analytic_label"]).lower() in label_to_topic
    }
    log.info("all_only topic ids: %d", len(all_only_ids))

    log.info("Loading doc-topics_K25_S2.txt …")
    s2_index, s2_confidence = load_topic_index(DOC_TOPICS_S2_TXT, "S2")
    _sanity_check_mallet(s2_mallet_to_analytic, s2_index, df)

    log.info("Loading all_doc-topics_K25_S1.txt …")
    all_index, _ = load_topic_index(DOC_TOPICS_ALL_TXT, "all")

    group_to_s2, group_to_best_text = build_group_to_s2_topic(df, s2_index, s2_confidence)

    # ── Build features ────────────────────────────────────────────────────────
    log.info("Building GeoJSON features …")
    features = []
    tier_counts = Counter()
    source_counts = Counter()
    fallback_details = []
    missing_city_state: Counter = Counter()

    for _, row in df.iterrows():
        # Geo
        lat, lng, tier = locate(row, county_centroids, state_centroids)
        tier_counts[tier] += 1

        # Track Level-3 misses for reporting
        if tier == 3:
            pub_city = str(row["Pub_City"]).strip() if pd.notna(row["Pub_City"]) else ""
            pub_state = str(row["Pub_State"]).strip() if pd.notna(row["Pub_State"]) else ""
            hi = str(row["Pub_State"]).strip().lower() == "hawaii"
            if not hi:
                missing_city_state[(pub_city, pub_state)] += 1

        # Topic
        topic, src = resolve_topic(
            row, s2_index, all_index, group_to_s2,
            s2_mallet_to_analytic, all_mallet_to_analytic, all_only_ids,
            label_to_topic,
        )
        source_counts[src] += 1
        if src == "topic_tags_fallback":
            fallback_details.append(
                (row["doc_id"], row.get("topic_tags", ""), topic["label"], topic["category"])
            )

        # Coverage
        coverage = _parse_coverage_region(row.get("Coverage_Region"))

        # Excerpt: for records whose topic is inherited from the group's best S2
        # member, also inherit that member's model_text so the excerpt is
        # thematically consistent with the assigned topic.
        if src == "s2_inherited":
            grp = row.get("duplicate_group")
            grp_text = group_to_best_text.get(str(grp)) if pd.notna(grp) else None
            excerpt_text = grp_text if grp_text else row.get("model_text")
        else:
            excerpt_text = row.get("model_text")

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lng, lat],   # GeoJSON: lng, lat
            },
            "properties": {
                "doc_id": row["doc_id"],
                "date": str(row["Date"]) if pd.notna(row["Date"]) else None,
                "year_month": str(row["year_month"]) if pd.notna(row.get("year_month")) else None,
                "topic_id": topic["id"],
                "topic_label": topic["label"],
                "category": topic["category"],
                "category_color": topic["category_color"],
                "topic_color": topic["color"],
                "topic_source": src,
                "newspaper": str(row["Newspaper_Name"]) if pd.notna(row["Newspaper_Name"]) else None,
                "pub_city": str(row["Pub_City"]) if pd.notna(row["Pub_City"]) else None,
                "pub_state": str(row["Pub_State"]) if pd.notna(row["Pub_State"]) else None,
                "coverage_counties": coverage,
                "page_url": str(row["Page_URL"]) if pd.notna(row.get("Page_URL")) else None,
                "is_reprint": bool(row["is_reprint"]),
                "reprint_count": int(row["reprint_count"]) if pd.notna(row["reprint_count"]) else 0,
                "excerpt": _excerpt(excerpt_text),
                "location_tier": tier,
            },
        }
        features.append(feature)

    # ── Write output ──────────────────────────────────────────────────────────
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "records.json"
    geojson = {"type": "FeatureCollection", "features": features}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)

    size_mb = out_path.stat().st_size / 1024 / 1024
    total = len(features)

    # ── Stats ─────────────────────────────────────────────────────────────────
    log.info("── Output stats ──────────────────────────────────────────────")
    log.info("  records.json: %d features, %.2f MB", total, size_mb)
    log.info("── Location tier distribution ────────────────────────────────")
    for t in (1, 2, 3):
        n = tier_counts[t]
        log.info("  L%d: %4d  (%5.1f%%)", t, n, 100 * n / total)

    log.info("── Topic source distribution ──────────────────────────────────")
    for src in ("all_direct", "s2_direct", "s2_inherited", "topic_tags_fallback"):
        n = source_counts[src]
        log.info("  %-24s %4d  (%5.1f%%)", src, n, 100 * n / total)

    log.info("city_to_county_1882 entries: %d", len(city_to_county_1882))

    if tier_counts[3] / total > 0.30:
        log.warning("L3 > 30%% — top 20 unmapped (city, state) combos:")
        for (city, state), cnt in missing_city_state.most_common(20):
            log.warning("  %4d  %-30s %s", cnt, city, state)

    if len(fallback_details) > 20:
        log.warning("topic_tags_fallback > 20 — first 10 samples:")
        for doc_id, tags, label, cat in fallback_details[:10]:
            log.warning("  %s  tags=%-40r → %r / %r", doc_id, str(tags)[:40], label, cat)

    log.info("Done.")


if __name__ == "__main__":
    main()

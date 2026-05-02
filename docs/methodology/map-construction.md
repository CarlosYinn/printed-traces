---
title: Map Construction
---

# Map Construction

This document describes how the interactive spatial map is built from the cleaned corpus and topic model outputs. The pipeline produces four static data files that are loaded at runtime by the map frontend: `counties_1882.geojson`, `states_1882.geojson`, `topics.json`, `records.json`, and `events.json`.

Scripts are located in `scripts/build_map_data/`. They must be run in order: boundaries first, then topics, then records.


## Step 1: Historical Boundary Data (`build_boundaries.py`)

The map uses period-appropriate administrative boundaries rather than modern state and county outlines. This is essential for the 1880–1885 period, when several territories had not yet achieved statehood and county divisions differed substantially from today.

### Source

Boundaries are derived from the [Atlas of Historical County Boundaries](https://digital.newberry.org/ahcb/), published by the Newberry Library. The atlas provides shapefiles for all U.S. states and territories, with each feature carrying a start date and end date to record when each administrative unit came into existence or was dissolved.

### Snapshot date

A snapshot date of **1882-06-30** is used to represent the political geography of the study period. All features whose active date range includes this date are selected; all others are discarded.

:::info
The 1882 midpoint was chosen because it coincides with the passage of the Chinese Exclusion Act, making it both politically central to the project and a reasonable approximation of the corpus's geographic conditions across the full 1880–1885 window. It also aligns with the date of the Rand McNally basemap layer used in the interactive map.
:::

For date-range filtering, the script handles two column formats present in different Newberry shapefiles:

- `START_DATE` / `END_DATE` (timestamp columns)
- `START_N` / `END_N` (integer format `YYYYMMDD`)

### Dakota Territory handling

The Newberry Atlas assigns pre-statehood North Dakota and South Dakota counties to their respective future-state files (ND and SD shapefiles). These counties predate statehood (November 1889) and would duplicate Dakota Territory features already present in the DT shapefile. To prevent overlap, ND and SD features with a start date before 1889-11-02 are dropped. In practice this removes exactly 40 features.

### Geometry simplification

County boundaries are checked against a 5 MB file size threshold after initial export. If the file exceeds this limit, `shapely.simplify` is applied with a tolerance of 0.003 degrees to reduce vertex count while preserving topology.

### Outputs

| File | Contents |
|---|---|
| `docs/public/data/states_1882.geojson` | State and territory outlines as of 1882-06-30 |
| `docs/public/data/counties_1882.geojson` | County outlines as of 1882-06-30, with FIPS codes and state abbreviations |


## Step 2: Topic Taxonomy (`build_topics.py`)

`topics.json` provides the hierarchical topic structure used by the filter panel in the map frontend. It is derived from `data/merged_topic_labels.csv`, which consolidates topic assignments from both MALLET model runs.

### Aggregation

The merged CSV may contain multiple rows for the same (category, analytic label) pair due to partial matches between the two model runs. These are collapsed by grouping on (category, analytic label) and taking the maximum weight and the union of topic IDs from both runs.

### ID generation

Each topic is assigned a unique string ID for use in the frontend. The ID is constructed from:
1. A category prefix: initials of significant words in the category name (e.g., `Chinese Educational Mission` becomes `cem`)
2. A snake-cased version of the analytic label with any leading `ABBR:` prefix stripped

Example: category "Education & Schools", label "Public School Admission" produces ID `es_public_school_admission`.

### Exclusion

Topics in the NOISE category are unconditionally excluded. Other topics marked `exclude: yes` in the CSV are also excluded. Excluded topics appear in the output but are hidden from the map interface.

If a topic index is missing from the CSV, check its top words in `keys_K25_S2.txt` and either add an `analytic_label` or mark it `exclude: yes` before rerunning.

### Output structure

```json
{
  "categories": [
    {
      "name": "Chinese Educational Mission",
      "color": "#fe640b",
      "hue": "Peach",
      "topics": [
        {
          "id": "cem_government_policy_institutional_recall",
          "label": "CEM: Government Policy & Institutional Recall",
          "color": "#ef9f76",
          "deduped_topic_id": null,
          "all_topic_id": "topic_24",
          "weight": 0.1328,
          "exclude": false
        }
      ]
    }
  ]
}
```

The script validates that the output contains exactly 10 categories and 25 topics total. Warnings are emitted if these counts are not met.


## Step 3: Document Records (`build_records.py`)

`records.json` is the main data layer for the map. Each of the 1,535 corpus documents becomes a GeoJSON feature with geographic coordinates, topic assignment, and display metadata.

### Geographic resolution

Publication cities in the 1880s are not always present in modern geocoding databases, and many small towns no longer exist under the same name. A three-tier fallback system resolves coordinates for each record:

**Tier 1: City lookup (110 major cities)**
A hand-verified dictionary maps 110 major cities to their county centroid. Coordinates are deterministically jittered by 2–8 km (seed derived from `doc_id`) to prevent point stacking when many records originate from the same city.

**Tier 2: Coverage region county**
If the publication city is not in the Tier 1 dictionary, the script parses the `Coverage_Region` field (pipe-separated county/place names) and attempts to match against the counties GeoJSON. The matched county centroid is used with 2–8 km jitter.

**Tier 3: State centroid**
If neither Tier 1 nor Tier 2 resolves, the state centroid is used as a fallback with 20–50 km jitter to indicate lower location confidence. The `location_tier` field in the output records which tier was used, allowing map users to assess coordinate precision.

**Hawaii special case**
All records from Hawaiian newspapers are assigned fixed Honolulu coordinates (21.3099°N, 157.8581°W) without jitter, since the Kingdom of Hawaii is outside the U.S. boundary GeoJSON and county-level resolution is not available.

If Tier 3 geocoding exceeds 30% of records, the script prints the top 20 unresolved `(city, state)` pairs. Add them to the `city_to_county_1882` dictionary at the top of `build_records.py` and rerun. Current measured rates: L1 69.6% / L2 19.3% / L3 11.1%.

### Topic assignment

Each document may have topic weights from both MALLET model runs (deduped model K25_S2 and full-corpus model K25_S1). A single canonical topic is assigned for map display using a five-priority resolution:

| Priority | Rule |
|---|---|
| 1 | Full-corpus model fine-grained label for CEM and Diplomacy sub-topics |
| 2 | Deduped model direct assignment (highest-weight topic) |
| 3 | Full-corpus model direct assignment for documents absent from the deduped corpus |
| 4 | Inheritance: adopt the topic of the highest-confidence original in the same reprint group |
| 5 | Fallback: score the `topic_tags` field by keyword counting |

This ordering preserves the deduped model's finer sub-topic distinctions where available, while ensuring that reprint-only records and unmodeled documents still receive a displayable category.

### Record structure

Each GeoJSON feature includes the following properties:

| Property | Description |
|---|---|
| `doc_id` | Unique document identifier |
| `date` | Publication date (YYYY-MM-DD) |
| `year_month` | Publication year-month (YYYY-MM) |
| `topic_id` | Canonical topic ID (matches `topics.json`) |
| `topic_label` | Analytic topic label |
| `topic_category` | Parent category name |
| `topic_color` | Topic hex color |
| `category_color` | Category hex color |
| `newspaper` | Newspaper title |
| `pub_city` | Publication city |
| `pub_state` | Publication state |
| `region` | U.S. Census region |
| `page_url` | Persistent Chronicling America link |
| `is_reprint` | Boolean reprint flag |
| `reprint_count` | Total size of reprint chain |
| `chain_position` | Position within reprint chain |
| `excerpt` | First 300 characters of cleaned text |
| `location_tier` | Geographic resolution tier (1, 2, or 3) |


## Step 4: Historical Event Overlays (`build_events.py`)

`events.json` contains ten hardcoded historical events that serve as navigational anchors in the map interface. Each event can filter the record layer to its associated time window and highlight relevant counties on the boundary layer.

### Event structure

```json
{
  "id": "rock_springs_1885",
  "title": "Rock Springs Massacre",
  "date": "1885-09-02",
  "month_range": ["1885-08", "1885-11"],
  "description": "...",
  "highlight_level": "county",
  "highlight_fips": ["56037"],
  "related_topic_ids": ["violence_anti_chinese_violence"]
}
```

| Field | Description |
|---|---|
| `date` | Exact event date used to anchor the timeline |
| `month_range` | Start and end months for filtering records |
| `highlight_level` | `"county"` or `"state"` |
| `highlight_fips` | Array of FIPS codes to shade on the boundary layer |
| `related_topic_ids` | Topic IDs to pre-select in the topic filter panel |

### Events included

| Event | Date | Highlight |
|---|---|---|
| Angell Treaty Signed | 1880-11-17 | (national) |
| Chinese New Year Press Wave | 1881-01-30 | San Francisco, New York, Boston |
| CEM Recall Begins | 1881-06-08 | Hartford and Springfield area |
| Chinese Exclusion Act Signed | 1882-05-06 | San Francisco |
| First CEM Student Graduates from Yale | 1883-06-01 | New Haven, CT |
| *Tape v. Hurley* Case Filed | 1884-09-01 | San Francisco |
| Sino-French War, Battle of Fuzhou | 1884-08-23 | (international) |
| Rock Springs Massacre | 1885-09-02 | Sweetwater County, WY |
| Tacoma Expulsion | 1885-11-03 | Pierce County, WA |
| Seattle Expulsion Attempt | 1886-02-07 | King County, WA |

FIPS codes for county highlights were assigned manually after inspecting `counties_1882.geojson`.

## Build Order and Dependencies

`build_topics.py` and `build_events.py` are independent and can run in any order. `build_records.py` requires both `counties_1882.geojson` and `topics.json` to be present first.

```bash
python scripts/build_map_data/build_topics.py       # independent
python scripts/build_map_data/build_events.py       # independent
python scripts/build_map_data/build_boundaries.py   # requires Newberry raw data
python scripts/build_map_data/build_records.py      # requires boundaries + topics
```

:::tip
When iterating on topic labels, only `build_topics.py` and `build_records.py` need to be rerun. Boundary data is stable across the project lifetime, and `build_events.py` only needs updating if event definitions or FIPS codes change.
:::

| Script | Output | Size |
|---|---|---|
| `build_topics.py` | `docs/public/data/topics.json` | ~10 KB |
| `build_events.py` | `docs/public/data/events.json` | ~5 KB |
| `build_boundaries.py` | `docs/public/data/counties_1882.geojson` | 7.26 MB |
| | `docs/public/data/states_1882.geojson` | <500 KB |
| `build_records.py` | `docs/public/data/records.json` | 1.35 MB |

All output files are served as static assets by the VitePress build and fetched at runtime by the map frontend.

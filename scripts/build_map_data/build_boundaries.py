"""
Build 1882-06-30 boundary snapshots from Newberry Atlas data.

Usage:
    python scripts/build_map_data/build_boundaries.py

Outputs:
    docs/public/data/states_1882.geojson
    docs/public/data/counties_1882.geojson
"""

import glob
import logging
import os
import re
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SNAPSHOT_DATE = "1882-06-30"

ROOT = Path(__file__).resolve().parents[2]
STATE_SHP = (
    ROOT
    / "data/newberry/US_AtlasHCB_StateTerr_Gen001"
    / "US_HistStateTerr_Gen001_Shapefile"
    / "US_HistStateTerr_Gen001.shp"
)
COUNTY_GLOB = str(
    ROOT / "data/newberry/states/*_AtlasHCB/*_Historical_Counties/*_Historical_Counties.shp"
)
OUT_DIR = ROOT / "docs/public/data"

TARGET_CRS = "EPSG:4326"
SIMPLIFY_THRESHOLD_BYTES = 5 * 1024 * 1024  # 5 MB
SIMPLIFY_TOLERANCE = 0.003


# ── Helpers ───────────────────────────────────────────────────────────────────
def _filter_snapshot(gdf: gpd.GeoDataFrame, snap: str) -> gpd.GeoDataFrame:
    """Return rows active on snap date. Handles both datetime and integer columns."""
    cols = gdf.columns.tolist()

    if "START_DATE" in cols and "END_DATE" in cols:
        ts = pd.Timestamp(snap)
        return gdf[(gdf["START_DATE"] <= ts) & (gdf["END_DATE"] >= ts)].copy()

    if "START_N" in cols and "END_N" in cols:
        snap_n = int(snap.replace("-", ""))
        return gdf[(gdf["START_N"] <= snap_n) & (gdf["END_N"] >= snap_n)].copy()

    raise ValueError(f"Cannot find date columns in: {cols}")


# ── States / Territories ──────────────────────────────────────────────────────
def build_states(snap: str) -> gpd.GeoDataFrame:
    log.info("Reading state/territory shapefile: %s", STATE_SHP)
    gdf = gpd.read_file(STATE_SHP)
    log.info("State/terr columns: %s", gdf.columns.tolist())
    log.info("State/terr row count (all time): %d", len(gdf))

    filtered = _filter_snapshot(gdf, snap)
    log.info("State/terr features active on %s: %d", snap, len(filtered))

    filtered = filtered.to_crs(TARGET_CRS)
    filtered["geometry"] = filtered["geometry"].simplify(0.01, preserve_topology=True)

    keep = ["NAME", "TERR_TYPE", "geometry"]
    result = filtered[keep].reset_index(drop=True)

    log.info("States GeoDataFrame ready: %d features", len(result))
    return result


# ── Counties ──────────────────────────────────────────────────────────────────
def build_counties(snap: str) -> gpd.GeoDataFrame:
    shp_paths = sorted(glob.glob(COUNTY_GLOB))
    log.info("Found %d county shapefiles", len(shp_paths))

    chunks = []
    per_state: dict[str, int] = {}

    for shp in shp_paths:
        fname = os.path.basename(shp)
        m = re.match(r"^([A-Z]{2})_Historical_Counties\.shp$", fname)
        if not m:
            log.warning("Skipping unexpected filename: %s", fname)
            continue
        abbr = m.group(1)

        gdf = gpd.read_file(shp)
        filtered = _filter_snapshot(gdf, snap)
        filtered = filtered.to_crs(TARGET_CRS)
        filtered["state_abbr"] = abbr

        # Normalise to a consistent set of output columns
        col_map = {}
        if "STATE" in filtered.columns:
            col_map["STATE"] = "STATE_TERR"

        filtered = filtered.rename(columns=col_map)

        # Keep START_DATE temporarily for the post-concat ND/SD dedup step
        keep_cols = ["NAME", "STATE_TERR", "FIPS", "state_abbr", "START_DATE", "geometry"]
        out_cols = [c for c in keep_cols if c in filtered.columns]
        filtered = filtered[out_cols]

        count = len(filtered)
        per_state[abbr] = count
        log.info("  %s: %d county features", abbr, count)
        chunks.append(filtered)

    if not chunks:
        raise RuntimeError("No county data collected — check COUNTY_GLOB path")

    combined = pd.concat(chunks, ignore_index=True)
    combined = gpd.GeoDataFrame(combined, crs=TARGET_CRS)
    log.info("Combined county GeoDataFrame: %d total features", len(combined))

    # Drop ND/SD features that overlap with Dakota Territory in 1882.
    # The Newberry Atlas assigns pre-statehood counties to their future state
    # files; DT_Historical_Counties already covers that area, so we exclude
    # ND/SD rows whose START_DATE predates statehood (1889-11-02).
    POST_1889_STATES = {"ND", "SD"}
    statehood_cutoff = pd.Timestamp("1889-11-02")
    if "START_DATE" in combined.columns:
        mask_drop = combined["state_abbr"].isin(POST_1889_STATES) & (
            combined["START_DATE"] < statehood_cutoff
        )
    else:
        statehood_n = int("18891102")
        mask_drop = combined["state_abbr"].isin(POST_1889_STATES) & (
            combined["START_N"] < statehood_n
        )
    before = len(combined)
    combined = combined[~mask_drop].copy()
    dropped = before - len(combined)
    log.info("Dropped %d ND/SD features overlapping Dakota Territory (expected 40)", dropped)
    if dropped != 40:
        log.warning("Expected to drop 40 ND/SD features but dropped %d — review data", dropped)

    # Drop START_DATE now that dedup is done; keep final output columns only
    final_cols = ["NAME", "STATE_TERR", "FIPS", "state_abbr", "geometry"]
    combined = combined[[c for c in final_cols if c in combined.columns]]

    return combined, per_state


# ── Sanity checks ─────────────────────────────────────────────────────────────
def sanity_check(per_state: dict[str, int], counties_gdf: gpd.GeoDataFrame, snap: str) -> None:
    log.info("── Sanity check ──────────────────────────────────────")
    total = sum(per_state.values())
    log.info("Total county features: %d", total)

    if not (2000 <= total <= 3500):
        log.warning("Total county count %d is outside expected range 2000–3500", total)

    # ND and SD should be 0 (not states until 1889)
    for abbr in ("ND", "SD"):
        n = per_state.get(abbr, 0)
        if n != 0:
            log.warning(
                "%s: expected 0 features for %s but got %d — these are pre-statehood counties",
                abbr, snap, n
            )
            rows = counties_gdf[counties_gdf["state_abbr"] == abbr]
            # Load raw dates for inspection
            shp = glob.glob(str(ROOT / f"data/newberry/states/{abbr}_AtlasHCB/{abbr}_Historical_Counties/{abbr}_Historical_Counties.shp"))[0]
            raw = gpd.read_file(shp)
            filtered_raw = _filter_snapshot(raw, snap)
            log.warning(
                "  %s features START_DATE range: %s .. %s",
                abbr,
                filtered_raw["START_DATE"].min() if "START_DATE" in raw.columns else filtered_raw["START_N"].min(),
                filtered_raw["START_DATE"].max() if "START_DATE" in raw.columns else filtered_raw["START_N"].max(),
            )
        else:
            log.info("%s: 0 features on %s (expected)", abbr, snap)

    # DT should be > 0
    dt_n = per_state.get("DT", 0)
    if dt_n > 0:
        log.info("DT (Dakota Territory): %d features on %s (expected > 0)", dt_n, snap)
    else:
        log.warning("DT: 0 features on %s — check Dakota Territory shapefile", snap)

    # AK and HI informational
    ak_n = per_state.get("AK", 0)
    hi_n = per_state.get("HI", 0)
    log.info(
        "AK: %d features on %s (expect > 0 as territory; HI: %d, expect 0 — Kingdom of Hawaii in 1882s)",
        ak_n, snap, hi_n,
    )

    # Per-state summary
    log.info("── Per-state feature counts ──────────────────────────")
    for abbr, n in sorted(per_state.items()):
        log.info("  %-4s %d", abbr, n)


# ── Write output ──────────────────────────────────────────────────────────────
def write_geojson(gdf: gpd.GeoDataFrame, path: Path, label: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GeoJSON", COORDINATE_PRECISION=5)
    size = path.stat().st_size

    if label == "counties" and size > SIMPLIFY_THRESHOLD_BYTES:
        log.info(
            "%s initial size %.1f MB > 5 MB threshold — simplifying geometry",
            path.name, size / 1024 / 1024,
        )
        gdf = gdf.copy()
        gdf["geometry"] = gdf["geometry"].simplify(SIMPLIFY_TOLERANCE, preserve_topology=True)
        gdf.to_file(path, driver="GeoJSON", COORDINATE_PRECISION=5)
        size = path.stat().st_size

    log.info(
        "%s: %d features, %.2f MB (%s)",
        path.name, len(gdf), size / 1024 / 1024, path,
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    log.info("SNAPSHOT_DATE = %s", SNAPSHOT_DATE)

    states_gdf = build_states(SNAPSHOT_DATE)
    counties_gdf, per_state = build_counties(SNAPSHOT_DATE)

    sanity_check(per_state, counties_gdf, SNAPSHOT_DATE)

    write_geojson(states_gdf, OUT_DIR / "states_1882.geojson", "states")
    write_geojson(counties_gdf, OUT_DIR / "counties_1882.geojson", "counties")

    log.info("Done.")


if __name__ == "__main__":
    main()

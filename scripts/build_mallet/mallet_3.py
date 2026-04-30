import pandas as pd

# =========================
# Dataset pipeline: Step 7
# MALLET preprocessing: Step 3 of 3
#
# Takes mallet_2.xlsx and enriches each row with time and region metadata
# (year, month, time_bin, region_bin) needed for MALLET labels.
# =========================
INPUT_EXCEL  = "mallet_2.xlsx"
OUTPUT_EXCEL = "mallet_3.xlsx"     # enriched working file


# =========================
# REGION MAP
# =========================
REGION_MAP = {
    # Northeast
    "maine": "Northeast", "new hampshire": "Northeast", "vermont": "Northeast",
    "massachusetts": "Northeast", "rhode island": "Northeast",
    "connecticut": "Northeast", "new york": "Northeast",
    "new jersey": "Northeast", "pennsylvania": "Northeast",

    # Midwest
    "ohio": "Midwest", "indiana": "Midwest", "illinois": "Midwest",
    "michigan": "Midwest", "wisconsin": "Midwest", "minnesota": "Midwest",
    "iowa": "Midwest", "missouri": "Midwest", "north dakota": "Midwest",
    "south dakota": "Midwest", "nebraska": "Midwest", "kansas": "Midwest",

    # South
    "delaware": "South", "maryland": "South", "district of columbia": "South",
    "virginia": "South", "west virginia": "South", "north carolina": "South",
    "south carolina": "South", "georgia": "South", "florida": "South",
    "kentucky": "South", "tennessee": "South", "mississippi": "South",
    "alabama": "South", "oklahoma": "South", "texas": "South",
    "arkansas": "South", "louisiana": "South",

    # West
    "montana": "West", "wyoming": "West", "colorado": "West",
    "new mexico": "West", "arizona": "West", "utah": "West",
    "idaho": "West", "nevada": "West", "washington": "West",
    "oregon": "West", "california": "West", "alaska": "West",
    "hawaii": "West",

    # Historical territories (1880s)
    "dakota territory": "West", "new mexico territory": "West",
    "arizona territory": "West", "utah territory": "West",
    "idaho territory": "West", "montana territory": "West",
    "wyoming territory": "West", "washington territory": "West",
    "oklahoma territory": "South", "indian territory": "South",
}


# =========================
# HELPERS
# =========================
def parse_date_safe(series):
    return pd.to_datetime(series, errors="coerce")

def clean_state(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()

def build_region_bin(pub_state, coverage_region=""):
    """
    Assign a US census region based on Pub_State.
    Falls back to Coverage_Region only if Pub_State is missing.
    """
    state    = clean_state(pub_state)
    coverage = clean_state(coverage_region)

    if state in REGION_MAP:
        return REGION_MAP[state]
    if "national" in coverage or coverage in {"united states", "usa", "us"}:
        return "National"
    return "Unknown"

def build_time_bin(year_value):
    """Return the year as a string label for MALLET and QGIS grouping."""
    if pd.isna(year_value):
        return ""
    return str(int(year_value))


# =========================
# STEP 7A — enrich with time and region metadata
# =========================
def enrich_metadata(df):
    """
    Add year, month, year_month, time_bin, and region_bin columns.
    These are used as MALLET document labels and QGIS grouping keys.
    """
    df = df.copy()

    if "Coverage_Region" not in df.columns:
        df["Coverage_Region"] = ""

    df["Date_parsed"] = parse_date_safe(df["Date"])
    df["month"]      = df["Date_parsed"].dt.month.astype("Int64").astype(str).replace("<NA>", "")
    df["year_month"] = df["Date_parsed"].dt.strftime("%Y-%m").fillna("")

    year_numeric   = df["Date_parsed"].dt.year
    df["time_bin"] = year_numeric.apply(build_time_bin)

    df["region_bin"] = df.apply(
        lambda row: build_region_bin(row["Pub_State"], row["Coverage_Region"]),
        axis=1,
    )

    df = df.drop(columns=["Date_parsed"])
    return df


# =========================
# MAIN
# =========================
def main():
    print(f"Reading: {INPUT_EXCEL}")
    df = pd.read_excel(INPUT_EXCEL, dtype=str).fillna("")

    required = ["doc_id", "Date", "Pub_State", "Pub_City",
                "use_for_mallet", "mallet_ready_text", "token_count"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Source sheet is missing columns: {missing}")

    df = enrich_metadata(df)

    # Save enriched working file, dropping columns not needed at this stage
    out = df.drop(columns=["unique_word_count"], errors="ignore")
    out.to_excel(OUTPUT_EXCEL, index=False, engine="openpyxl")

    print("\nSummary")
    print("-------")
    print("Total rows:", len(df))

    print("\nYear breakdown:")
    print(df["time_bin"].value_counts().sort_index().to_string())

    print("\nRegion breakdown:")
    print(df["region_bin"].value_counts().to_string())

    print(f"\nSaved: {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()

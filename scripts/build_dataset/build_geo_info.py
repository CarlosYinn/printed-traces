import pandas as pd
import re
import ast

# =========================
# Dataset pipeline: Step 2
#
# Parses raw LOC data (Title + Location columns) into structured
# geographic and bibliographic fields:
#   Title    -> Newspaper_Name, Image_Number
#   Location -> Pub_City, Pub_County, Pub_State, Coverage_Region
# Then cleans and standardises all geo fields:
#   - State abbreviations and historical territory names
#   - County abbreviations (Co. -> County)
#   - Misplaced values (county in state field, city with commas, etc.)
#   - Admin_Type (State vs Territory)
# =========================
INPUT_FILE  = "input.csv"
OUTPUT_FILE = "output.csv"

FINAL_COLUMNS = [
    "Keyword", "Date", "Newspaper_Name", "Image_Number",
    "Pub_City", "Pub_County", "Pub_State", "Admin_Type",
    "Coverage_Region", "Page_URL", "OCR_Text",
]

# =========================
# REFERENCE DATA
# =========================
US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "district of columbia",
    # Historical territories
    "indian territory", "dakota territory", "washington territory",
    "utah territory", "new mexico territory", "arizona territory",
    "colorado territory", "montana territory", "idaho territory",
    "wyoming territory", "hawaii territory",
}

TERRITORIES_1880s = {
    "dakota", "washington", "idaho", "montana", "wyoming",
    "utah", "arizona", "new mexico", "indian",
}

STATE_ABBREV_MAP = {
    r"^D\.?T\.?$":               "Dakota Territory",
    r"^W\.?T\.?$":               "Washington",
    r"^A\.?T\.?$":               "Arizona",
    r"^Wash\.?\s?Terr\.?":       "Washington",
    r"^Ariz\.?\s?Territory":     "Arizona",
    r"^Va\.$":                   "Virginia",
    r"^Dak\.$":                  "Dakota Territory",
    r"^N\.?T\.?$":               "Nevada",
}

STOP_WORDS = {"united states", "town", "city", "village"}


# =========================
# STEP A — parse Title
# =========================
def parse_title(raw_title: str):
    """
    Extract Image_Number and Newspaper_Name from a LOC title string.
    e.g. "Image 4 of Baptist courier (Greenville, S.C.), May 28, 1885"
    """
    raw_title = str(raw_title)

    match = re.search(
        r"^(Image\s+\d+)\s+of\s+(.*?),\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}$",
        raw_title, re.IGNORECASE,
    )
    if match:
        image_num = match.group(1).strip()
        newspaper_raw = match.group(2).strip()
    elif " of " in raw_title:
        parts = raw_title.split(" of ", 1)
        image_num = parts[0].strip()
        rest = parts[1]
        newspaper_raw = rest.rsplit(",", 1)[0].strip() if "," in rest else rest.strip()
    else:
        return raw_title, "Unknown"

    # Strip trailing parenthesised location from newspaper name
    clean_newspaper = re.sub(r"\s*\([^)]+\)$", "", newspaper_raw).strip()
    return clean_newspaper, image_num


# =========================
# STEP B — parse Location list
# =========================
def parse_location(raw_title: str, loc_str):
    """
    Parse the LOC Location list and the parenthesised city/state in the
    Title to produce Pub_City, Pub_County, Pub_State, Coverage_Region.
    """
    # --- Extract city/state hint from Title parentheses ---
    title_city   = ""
    title_county = ""
    title_state  = ""

    loc_match = re.search(r"\(([^)]+)\)$", str(raw_title).rsplit(",", 1)[0])
    if loc_match:
        pub_loc = loc_match.group(1).strip()
        if "[" in pub_loc:
            parts = pub_loc.split("[")
            title_city  = parts[0].strip()
            title_state = parts[1].replace("]", "").strip()
        elif "," in pub_loc:
            parts = [p.strip() for p in pub_loc.split(",")]
            title_city = parts[0]
            if len(parts) >= 3:
                if "co." in parts[1].lower() or "county" in parts[1].lower():
                    title_county = parts[1]
                title_state = parts[-1]
            else:
                title_state = parts[1]
        else:
            title_city = pub_loc.strip()

    # --- Parse Location list ---
    loc_state  = ""
    loc_county = ""
    coverage_places = []

    try:
        if isinstance(loc_str, str) and loc_str.startswith("["):
            loc_list = ast.literal_eval(loc_str.lower())
        elif isinstance(loc_str, list):
            loc_list = [str(x).lower() for x in loc_str]
        else:
            loc_list = [str(loc_str).lower()]

        for item in loc_list:
            item = item.strip()
            if not item or item in STOP_WORDS:
                continue
            if item in US_STATES:
                loc_state = item.title()
            elif item.endswith(" county") or item.endswith(" parish"):
                loc_county = item.title()
            else:
                formatted = item.title()
                if not any(formatted in p or p in formatted for p in coverage_places):
                    coverage_places.append(formatted)
    except Exception:
        coverage_places.append(str(loc_str))

    pub_city     = title_city
    pub_county   = title_county if title_county else loc_county
    pub_state    = loc_state    if loc_state    else title_state
    coverage_str = " | ".join(coverage_places) if coverage_places else pub_city

    return pub_city, pub_county, pub_state, coverage_str


# =========================
# STEP C — clean state names
# =========================
def clean_state_name(state: str) -> str:
    """Expand abbreviations and strip bracketed corrections."""
    state = str(state).strip()
    if not state or state == "nan":
        return ""

    for pattern, replacement in STATE_ABBREV_MAP.items():
        if re.match(pattern, state, re.IGNORECASE):
            return replacement

    # Bracketed correction: "Dakota (South Dakota)" -> "South Dakota"
    bracket = re.search(r"\((.*?)\)", state)
    if bracket:
        content = bracket.group(1).replace("i.e. ", "").strip()
        return content

    if "Va. (" in state:
        return state.split("(")[1].replace(")", "").strip()

    return state.title()


# =========================
# STEP D — clean county names
# =========================
def clean_county_name(county: str) -> str:
    """Expand 'Co.' / 'Co' abbreviations to 'County'."""
    if pd.isna(county) or not str(county).strip():
        return ""
    result = re.sub(r"\bco\b\.?", "County", str(county), flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", result).strip()


# =========================
# STEP E — fix misplaced geo values and assign Admin_Type
# =========================
def fix_geo_and_admin(pub_city: str, pub_county: str, pub_state: str):
    """
    Fix common LOC data quirks:
      - County accidentally placed in the State field
      - Multiple values concatenated into Pub_City with commas
    Then derive Admin_Type (State / Territory).
    """
    city   = str(pub_city).strip()
    county = str(pub_county).strip()
    state  = str(pub_state).strip()

    # Clean noise from state field
    state = re.sub(r"i\.?e\.?\s*", "", state).replace("[", "").replace("]", "").strip()

    # County accidentally placed in state field
    if "county" in state.lower() or "co." in state.lower():
        county = state
        state  = ""

    # City field has been contaminated with county/state via commas
    if "," in city:
        parts = [p.strip() for p in city.split(",")]
        city  = parts[0]
        for part in parts[1:]:
            part_lower = part.lower()
            if "county" in part_lower or "co." in part_lower:
                county = f"{part} ({county})" if county and county != part else part
            else:
                if not state:
                    state = part
                elif state.lower() not in part.lower():
                    state = f"{part} ({state})"
                else:
                    state = part

    # Derive Admin_Type
    admin_type = ""
    if state:
        state_lower = state.lower()
        is_territory = "territory" in state_lower or any(
            re.search(rf"\b{t}\b", state_lower) for t in TERRITORIES_1880s
        )
        admin_type = "Territory" if is_territory else "State"

    return city, county, state, admin_type


# =========================
# MAIN
# =========================
def main():
    print(f"Reading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, dtype=str).fillna("")

    required = ["Title", "Location"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Input file is missing columns: {missing}")

    print("  Parsing Title -> Newspaper_Name, Image_Number...")
    parsed_titles = df["Title"].apply(parse_title)
    df["Newspaper_Name"] = [r[0] for r in parsed_titles]
    df["Image_Number"]   = [r[1] for r in parsed_titles]

    print("  Parsing Location -> Pub_City, Pub_County, Pub_State, Coverage_Region...")
    parsed_locs = df.apply(
        lambda row: parse_location(row["Title"], row["Location"]), axis=1
    )
    df["Pub_City"]        = [r[0] for r in parsed_locs]
    df["Pub_County"]      = [r[1] for r in parsed_locs]
    df["Pub_State"]       = [r[2] for r in parsed_locs]
    df["Coverage_Region"] = [r[3] for r in parsed_locs]

    print("  Cleaning state names...")
    df["Pub_State"] = df["Pub_State"].apply(clean_state_name)

    print("  Cleaning county names...")
    df["Pub_County"] = df["Pub_County"].apply(clean_county_name)

    print("  Fixing geo fields and assigning Admin_Type...")
    fixed = df.apply(
        lambda row: fix_geo_and_admin(row["Pub_City"], row["Pub_County"], row["Pub_State"]),
        axis=1,
    )
    df["Pub_City"]   = [r[0] for r in fixed]
    df["Pub_County"] = [r[1] for r in fixed]
    df["Pub_State"]  = [r[2] for r in fixed]
    df["Admin_Type"] = [r[3] for r in fixed]

    # Drop raw columns and reorder
    df = df.drop(columns=["Title", "Location"], errors="ignore")
    output_cols = [c for c in FINAL_COLUMNS if c in df.columns]
    extra_cols  = [c for c in df.columns if c not in output_cols]
    df = df[output_cols + extra_cols]

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\nSummary")
    print(f"-------")
    print(f"Total rows       : {len(df)}")
    print(f"Admin_Type breakdown:")
    print(df["Admin_Type"].value_counts().to_string())
    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

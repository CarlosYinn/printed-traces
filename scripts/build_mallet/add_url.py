import pandas as pd

INPUT_SOURCE = "input.xlsx"       # original dataset with Page_URL and Image_Number
INPUT_MALLET = "mallet_3.xlsx"          # enriched MALLET working file
OUTPUT_EXCEL = "mallet_final.xlsx"      # final dataset with URL and Image_Number added
OUTPUT_CSV   = "dataset.csv"            # same data as CSV

# Join key: combination of fields that uniquely identifies each article
JOIN_KEYS = ["Date", "Newspaper_Name", "Pub_City", "Pub_State"]


def normalise_keys(df):
    """Lowercase and strip all join key columns for consistent matching."""
    df = df.copy()
    for col in JOIN_KEYS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
    return df


def main():
    print(f"Reading: {INPUT_SOURCE}")
    src = pd.read_excel(INPUT_SOURCE, dtype=str).fillna("")

    print(f"Reading: {INPUT_MALLET}")
    mallet = pd.read_excel(INPUT_MALLET, dtype=str).fillna("")

    # Check all join keys exist in both files
    for col in JOIN_KEYS:
        if col not in src.columns:
            raise KeyError(f"input.xlsx is missing join key: {col}")
        if col not in mallet.columns:
            raise KeyError(f"mallet_3.xlsx is missing join key: {col}")

    # Deduplicate source to one URL+ImageNumber per unique article
    src_dedup = normalise_keys(src)[JOIN_KEYS + ["Page_URL", "Image_Number"]].drop_duplicates(subset=JOIN_KEYS)

    # Check for duplicate keys in source after dedup
    dupes = src_dedup[src_dedup.duplicated(subset=JOIN_KEYS, keep=False)]
    if not dupes.empty:
        print(f"  Warning: {len(dupes)} rows in input.xlsx share the same join key — "
              f"only the first occurrence will be used.")
        src_dedup = src_dedup.drop_duplicates(subset=JOIN_KEYS, keep="first")

    mallet_norm = normalise_keys(mallet)

    merged = mallet_norm.merge(
        src_dedup,
        on=JOIN_KEYS,
        how="left",
    )

    # Restore original (non-lowercased) values for join key columns from mallet
    for col in JOIN_KEYS:
        merged[col] = mallet[col].values

    # Report match quality
    matched   = merged["Page_URL"].notna() & (merged["Page_URL"] != "")
    unmatched = (~matched).sum()
    print(f"\nMatch summary")
    print(f"  Total rows in mallet_3   : {len(mallet)}")
    print(f"  Successfully matched     : {matched.sum()}")
    print(f"  Unmatched (no URL found) : {unmatched}")
    if unmatched > 0:
        print("\n  Unmatched rows (first 10):")
        print(merged.loc[~matched, ["doc_id"] + JOIN_KEYS].head(10).to_string(index=False))

    # Place Image_Number and Page_URL right after doc_id
    cols = merged.columns.tolist()
    for insert_col in ["Page_URL", "Image_Number"]:
        if insert_col in cols:
            cols.remove(insert_col)
    doc_id_pos = cols.index("doc_id") + 1
    cols = cols[:doc_id_pos] + ["Image_Number", "Page_URL"] + cols[doc_id_pos:]
    merged = merged[cols]

    merged.to_excel(OUTPUT_EXCEL, index=False, engine="openpyxl")
    merged.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nSaved: {OUTPUT_EXCEL}")
    print(f"Saved: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

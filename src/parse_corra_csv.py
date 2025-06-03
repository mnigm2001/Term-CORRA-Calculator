"""
parse_corra_csv.py

Read the Bank of Canada CORRA raw CSV (with metadata) and produce a filtered
Date,Rate CSV for our term-rate pipeline.
"""
import pandas as pd
import argparse
import os


def parse_corra_raw(
    raw_csv_path: str,
    output_csv_path: str,
    rate_column: str,
    start_date: str = None,
    end_date: str = None
) -> None:
    """
    Read the raw CORRA CSV (including metadata rows) and write a trimmed CSV
    with columns: Date (YYYY-MM-DD), Rate (decimal).

    - Skips all rows until the row that starts with "OBSERVATIONS".
    - The next row is treated as header (e.g., Date,AVG.INTWO,...).
    - Filters to the chosen rate_column and converts rate to decimal.
    - Optionally filters to a date range.
    """
    # 1) Read entire file to find the line index of "OBSERVATIONS"
    with open(raw_csv_path, 'r') as f:
        lines = f.readlines()

    observations_idx = None
    for idx, line in enumerate(lines):
        if line.strip().upper() == "\"OBSERVATIONS\"":
            observations_idx = idx
            break
    if observations_idx is None:
        raise ValueError("Could not find 'OBSERVATIONS' row in raw CSV.")

    header_row_idx = observations_idx + 1

    # 2) Use pandas to read from the header row_idx
    #    skiprows=header_row_idx to skip metadata up to header; header=0 uses first non-skipped as column names
    df = pd.read_csv(
        raw_csv_path,
        skiprows=header_row_idx,
        parse_dates=["date"],
        keep_default_na=False  # avoid treating empty strings as NaN except later
    )

    if rate_column not in df.columns:
        raise ValueError(f"Column '{rate_column}' not found in raw CSV.")

    # 3) Filter to Date + chosen rate column
    df = df[["date", rate_column]].copy()
    # Convert empty strings to NaN so dropna works
    df[rate_column] = pd.to_numeric(df[rate_column], errors='coerce')
    df = df.dropna(subset=[rate_column])

    # 4) Optional date range filtering
    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date)]

    # 5) Convert to decimal if > 1 (e.g., 4.50 -> 0.0450)
    def to_decimal(r):
        r = float(r)
        return (r / 100) if r > 1.0 else r
    df["Rate"] = df[rate_column].apply(to_decimal)

    # 6) Sort by Date and format as YYYY-MM-DD
    df = df.sort_values(by="date")
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    out_df = df[["date", "Rate"]]

    # 7) Write output CSV
    out_dir = os.path.dirname(output_csv_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    out_df.to_csv(output_csv_path, index=False)
    print(f"Filtered CORRA fixings written to: {output_csv_path}")


# -------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse raw CORRA CSV and produce date,rate CSV for pipeline."
    )
    parser.add_argument("raw_csv", help="Path to raw Bank of Canada CORRA CSV (e.g., data/corra_raw.csv)")
    parser.add_argument("output_csv", help="Output path for filtered date,rate CSV (e.g., data/corra_fixings.csv)")
    parser.add_argument("rate_column", help="Column name in raw CSV to use for rate (e.g., 'AVG.INTWO' or 'CORRA_WEIGHTED_MEAN_RATE')")
    parser.add_argument("--start_date", help="Optional start date 'YYYY-MM-DD'", default=None)
    parser.add_argument("--end_date", help="Optional end date 'YYYY-MM-DD'", default=None)
    args = parser.parse_args()

    parse_corra_raw(
        raw_csv_path=args.raw_csv,
        output_csv_path=args.output_csv,
        rate_column=args.rate_column,
        start_date=args.start_date,
        end_date=args.end_date
    )
"""
utils.py

Utility functions for:
- Converting CSV date strings → QuantLib.Date
- Transforming float rates → QuantLib.InterestRate
"""

import QuantLib as ql
import pandas as pd

# -------------------------------------------------------------------
def parse_date_to_ql(date_str: str) -> ql.Date:
    """
    Convert a date string 'YYYY-MM-DD' to a QuantLib.Date,
    adjusting for weekends and business-day conventions (Canada).
    """
    year, month, day = map(int, date_str.split('-'))
    ql_date = ql.Date(day, month, year)

    cal = ql.CanadianGovernmentBond()  # Canada business days
    bdc = ql.ModifiedFollowing
    return cal.adjust(ql_date, bdc)


# -------------------------------------------------------------------
def float_to_ql_rate(rate_float: float) -> ql.InterestRate:
    """
    Convert a decimal rate (e.g., 0.045) into a QuantLib.InterestRate
    with Actual365Fixed day count and Compounded annual compounding.
    """
    day_count = ql.Actual365Fixed()
    comp = ql.Compounded
    freq = ql.Annual
    return ql.InterestRate(rate_float, day_count, comp, freq)


# -------------------------------------------------------------------
def load_fixings(csv_path: str) -> pd.DataFrame:
    """
    Read a CSV of overnight CORRA fixings into a pandas DataFrame,
    parse dates into QuantLib.Date, and attach QL InterestRate objects.
    Expects columns: Date (str), Rate (float).
    Returns a DataFrame with extra columns: ql_date (QuantLib.Date), ql_rate (InterestRate).
    """
    df = pd.read_csv(csv_path, parse_dates=['Date'])
    df['Rate'] = df['Rate'].astype(float)

    df['ql_date'] = df['Date'].dt.strftime('%Y-%m-%d').apply(parse_date_to_ql)
    df['ql_rate'] = df['Rate'].apply(float_to_ql_rate)

    return df

# -------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python utils.py <path_to_fixings_csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    df = load_fixings(csv_path)
    print(df.head())
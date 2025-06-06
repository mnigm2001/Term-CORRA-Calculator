"""
utils.py

Utility functions for:
- Converting CSV date strings → QuantLib.Date
- Transforming float rates → QuantLib.InterestRate
"""
import QuantLib as ql
import pandas as pd

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

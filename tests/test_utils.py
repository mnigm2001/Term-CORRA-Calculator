import QuantLib as ql
import pytest
import pandas as pd
from src.utils import parse_date_to_ql, float_to_ql_rate, load_fixings


def test_parse_date_to_ql_weekday():
    ql_date = parse_date_to_ql("2025-01-15")  # Wednesday
    assert ql_date == ql.Date(15, 1, 2025)


def test_parse_date_to_ql_weekend_adjustment():
    adjusted = parse_date_to_ql("2025-01-18")  # Saturday → Monday 2025-01-20
    assert adjusted == ql.Date(20, 1, 2025)


def test_float_to_ql_rate_properties():
    ir = float_to_ql_rate(0.05)
    assert pytest.approx(ir.rate(), rel=1e-9) == 0.05
    assert ir.dayCounter() == ql.Actual365Fixed()
    assert ir.compounding() == ql.Compounded
    assert ir.frequency() == ql.Annual


def test_load_fixings_dataframe(tmp_path):
    csv_content = "Date,Rate\n2025-01-02,0.045\n2025-01-03,0.046\n"
    file_path = tmp_path / "temp_fixings.csv"
    file_path.write_text(csv_content)

    df = load_fixings(str(file_path))
    assert 'ql_date' in df.columns
    assert 'ql_rate' in df.columns
    assert df.iloc[0]['ql_date'] == ql.Date(2, 1, 2025)
    assert pytest.approx(df.iloc[0]['Rate'], rel=1e-9) == 0.045
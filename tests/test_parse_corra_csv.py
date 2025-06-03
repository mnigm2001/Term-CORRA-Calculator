import pandas as pd
import pytest
import os
from src.parse_corra_csv import parse_corra_raw


def create_raw_with_metadata(tmp_path):
    """
    Create a dummy raw CSV with 3 metadata rows + 'OBSERVATIONS' row, then header and data.
    """
    csv_path = tmp_path / "dummy_meta.csv"
    content = (
        "METADATA LINE 1\n"
        "METADATA LINE 2\n"
        "METADATA LINE 3\n"
        "OBSERVATIONS\n"
        "Date,AVG.INTWO,CORRA_WEIGHTED_MEAN_RATE\n"
        "2025-01-01,4.50,\n"
        "2025-01-02,4.60,4.55\n"
        "2025-01-03,,4.65\n"
        "2025-01-04,4.70,4.60\n"
    )
    csv_path.write_text(content)
    return str(csv_path)


def test_parse_avg_intwo(tmp_path):
    raw = create_raw_with_metadata(tmp_path)
    out = tmp_path / "filtered_avg.csv"
    parse_corra_raw(raw, str(out), rate_column="AVG.INTWO")
    df_out = pd.read_csv(str(out))
    assert list(df_out["Date"]) == ["2025-01-01", "2025-01-02", "2025-01-04"]
    assert pytest.approx(df_out.iloc[0]["Rate"], rel=1e-9) == 0.0450
    assert pytest.approx(df_out.iloc[1]["Rate"], rel=1e-9) == 0.0460
    assert pytest.approx(df_out.iloc[2]["Rate"], rel=1e-9) == 0.0470


def test_parse_weighted_mean(tmp_path):
    raw = create_raw_with_metadata(tmp_path)
    out = tmp_path / "filtered_wm.csv"
    parse_corra_raw(raw, str(out), rate_column="CORRA_WEIGHTED_MEAN_RATE")
    df_out = pd.read_csv(str(out))
    assert list(df_out["Date"]) == ["2025-01-02", "2025-01-03", "2025-01-04"]
    expected = [0.0455, 0.0465, 0.0460]
    for i, val in enumerate(df_out["Rate"]):
        assert pytest.approx(val, rel=1e-9) == expected[i]


def test_date_range_filter(tmp_path):
    raw = create_raw_with_metadata(tmp_path)
    out = tmp_path / "filtered_range.csv"
    parse_corra_raw(raw, str(out), rate_column="AVG.INTWO", start_date="2025-01-02", end_date="2025-01-03")
    df_out = pd.read_csv(str(out))
    assert list(df_out["Date"]) == ["2025-01-02"]
    assert pytest.approx(df_out.iloc[0]["Rate"], rel=1e-9) == 0.0460


def test_invalid_column(tmp_path):
    raw = create_raw_with_metadata(tmp_path)
    out = tmp_path / "filtered_bad.csv"
    with pytest.raises(ValueError):
        parse_corra_raw(raw, str(out), rate_column="NON_EXISTENT_COL")
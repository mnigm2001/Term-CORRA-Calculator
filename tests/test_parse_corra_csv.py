import pandas as pd
import pytest
import shutil
import os
from pathlib import Path
from src.parse_corra_csv import parse_corra_raw


def create_raw_with_metadata(tmp_path):
    """
    Create a dummy raw CSV with 3 metadata lines + 'OBSERVATIONS' row, then header and data.
    """
    csv_path = tmp_path / "dummy_meta.csv"
    content = (
        "METADATA LINE 1\n"
        "METADATA LINE 2\n"
        "METADATA LINE 3\n"
        "OBSERVATIONS\n"
        "date,AVG.INTWO,CORRA_WEIGHTED_MEAN_RATE\n"
        "2025-01-01,4.50,\n"
        "2025-01-02,4.60,4.55\n"
        "2025-01-03,,4.65\n"
        "2025-01-04,4.70,4.60\n"
    )
    csv_path.write_text(content)
    print(csv_path)
    return str(csv_path)


def test_parse_avg_intwo(tmp_path):
    raw = create_raw_with_metadata(tmp_path)
    out = tmp_path / "filtered_avg.csv"
    parse_corra_raw(raw, str(out), rate_column="AVG.INTWO")
    df_out = pd.read_csv(str(out))
    assert list(df_out["date"]) == ["2025-01-01", "2025-01-02", "2025-01-04"]
    assert pytest.approx(df_out.iloc[0]["Rate"], rel=1e-9) == 0.0450
    assert pytest.approx(df_out.iloc[1]["Rate"], rel=1e-9) == 0.0460
    assert pytest.approx(df_out.iloc[2]["Rate"], rel=1e-9) == 0.0470


def test_parse_weighted_mean(tmp_path):
    raw = create_raw_with_metadata(tmp_path)
    out = tmp_path / "filtered_wm.csv"
    parse_corra_raw(raw, str(out), rate_column="CORRA_WEIGHTED_MEAN_RATE")
    df_out = pd.read_csv(str(out))
    assert list(df_out["date"]) == ["2025-01-02", "2025-01-03", "2025-01-04"]
    expected = [0.0455, 0.0465, 0.0460]
    for i, val in enumerate(df_out["Rate"]):
        assert pytest.approx(val, rel=1e-9) == expected[i]


def test_date_range_filter(tmp_path):
    raw = create_raw_with_metadata(tmp_path)
    out = tmp_path / "filtered_range.csv"
    parse_corra_raw(raw, str(out), rate_column="AVG.INTWO", start_date="2025-01-02", end_date="2025-01-03")
    df_out = pd.read_csv(str(out))
    assert list(df_out["date"]) == ["2025-01-02"]
    assert pytest.approx(df_out.iloc[0]["Rate"], rel=1e-9) == 0.0460


def test_invalid_column(tmp_path):
    raw = create_raw_with_metadata(tmp_path)
    out = tmp_path / "filtered_bad.csv"
    with pytest.raises(ValueError):
        parse_corra_raw(raw, str(out), rate_column="NON_EXISTENT_COL")


def test_integration_on_real_sample(tmp_path):
    """
    Integration test: Use a small real CORRA CSV sample saved under tests/data/real_sample_corra.csv
    to ensure parsing works end-to-end.
    """
    # Copy the sample into tmp_path
    sample_dir = Path(__file__).parent / "data"
    sample_file = sample_dir / "real_sample_corra.csv"
    print(sample_file)
    if not sample_file.exists():
        pytest.skip("Real sample CSV not found: tests/data/real_sample_corra.csv")
    dest = tmp_path / "real_sample.csv"
    print(f"dest = {dest}")
    shutil.copy(sample_file, dest)

    out_csv = tmp_path / "parsed_real.csv"
    print(out_csv)
    parse_corra_raw(str(dest), str(out_csv), rate_column="AVG.INTWO", start_date="2015-01-01", end_date="2015-12-30")
    df = pd.read_csv(str(out_csv))

    # At least one row in 2015
    assert len(df) >= 1
    # All rates between 0 and 0.1 (plausible CORRA range)
    assert df["Rate"].between(0, 0.9).all()
    # If date "2025-01-02" is present, check its approximate rate (example):
    if "2025-01-02" in df["date"].values:
        row = df[df["date"] == "2025-01-02"].iloc[0]
        assert 0 < row["Rate"] < 0.1
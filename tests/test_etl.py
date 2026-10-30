"""Unit tests for the refine/load steps, run against a copy of sample_data/."""

import shutil
from pathlib import Path

import pandas as pd
import pytest

from treat_books import parse_book_file, refine_books
from treat_stocks import parse_stock_frame, refine_stocks
from utils import get_missing_stock_dates, to_naive_date
import load_warehouse

SAMPLE = Path(__file__).resolve().parents[1] / "sample_data" / "data_lake"


@pytest.fixture()
def lake(tmp_path):
    dst = tmp_path / "data_lake"
    shutil.copytree(SAMPLE, dst)
    return f"{dst}/"


def test_to_naive_date_handles_tz_and_strings():
    s = to_naive_date(pd.Series(["2026-10-29 00:00:00-04:00", "2026-10-28", None]))
    assert str(s.iloc[0].date()) == "2026-10-29"
    assert str(s.iloc[1].date()) == "2026-10-28"
    assert pd.isna(s.iloc[2])


def test_parse_book_file_flattens_lists():
    rec = parse_book_file("20250130_book_OL1M.json", {
        "title": "T", "publishers": ["A", "B"], "authors": [{"key": "/authors/X"}]})
    assert rec["id"] == "OL1M" and rec["publishers"] == "A|B"
    assert rec["authors_uri"] == "/authors/X" and rec["collect_date"] == "2025-01-30"
    assert parse_book_file("20250130_book_.json", {"title": "x"}) is None
    assert parse_book_file("20250130_book_OL1M.json", {}) is None


def test_parse_stock_frame_without_date_column_uses_previous_day():
    raw = pd.DataFrame([{"Open": 1, "High": 2, "Low": 0.5, "Close": 1.5, "Volume": 10}])
    out = parse_stock_frame("20250129_stock_AAPL.csv", raw)
    assert out.loc[0, "ticker_name"] == "AAPL"
    assert str(out.loc[0, "date"].date()) == "2025-01-28"


def test_refine_books_writes_parquet_with_real_dates(lake):
    rows = refine_books(lake)
    df = pd.read_parquet(f"{lake}refined/parquet/books/books.parquet")
    assert len(rows) > 0 and df["id"].str.match(r"^OL\d+M$").all()
    assert pd.api.types.is_datetime64_any_dtype(df["collect_date"])
    assert df["collect_date"].notna().all()  # regression: used to become all-NA


def test_refine_stocks_writes_parquet(lake):
    refine_stocks(lake)
    df = pd.read_parquet(f"{lake}refined/parquet/stocks/stocks.parquet")
    assert set(df["ticker_name"]) >= {"AAPL", "MSFT"}
    assert df["date"].notna().all()


def test_get_missing_stock_dates():
    df = pd.DataFrame({"ticker_name": ["AAPL"] * 2,
                       "date": pd.to_datetime(["2024-01-01", "2024-01-03"])})
    missing = get_missing_stock_dates(df, "AAPL", "date", "2024-01-01", "2024-01-03")
    assert missing == ["2024-01-02"]
    assert get_missing_stock_dates(df, "MSFT", "date", "2024-01-01", "2024-01-03") == []


def test_load_warehouse_into_sqlite(lake, tmp_path):
    refine_books(lake)
    refine_stocks(lake)
    url = f"sqlite:///{tmp_path}/wh.db"
    counts = load_warehouse.load(lake, url, run_id="test")
    assert counts["books"] > 0 and counts["stocks"] > 0
    audit = pd.read_sql("SELECT * FROM load_audit", url)
    assert audit.loc[0, "run_id"] == "test"

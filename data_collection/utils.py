"""
This module contains utility functions for data processing and storage.
"""

import json
import os
from typing import Dict, List, Union
import pandas as pd
from datetime import datetime, timedelta


def save_data(
    file_content: Union[List[Dict], Dict, List, str, pd.DataFrame],
    file_name: str,
    zone: str = "raw",
    context: str = "books",
    file_type: str = "csv",
    base_path="/opt/airflow/data_lake/",
) -> None:
    DATA_LAKE_BASE_PATH = f"{base_path}{zone}/{file_type}/{context}/"
    full_file_name = f"{DATA_LAKE_BASE_PATH}{file_name}"
    print(full_file_name)
    if zone == "raw":
        os.makedirs(DATA_LAKE_BASE_PATH, exist_ok=True)
    if file_type == "csv" and zone == "raw":
        if not isinstance(file_content, pd.DataFrame):
            df = pd.DataFrame(file_content)
        else:
            df = file_content
        df.to_csv(f"{full_file_name}.csv", index=False)
    elif file_type == "json" and zone == "raw":
        with open(f"{full_file_name}.json", "w", encoding="utf-8") as fp:
            json.dump(file_content, fp)
    elif file_type == "parquet" and zone == "refined":
        if not isinstance(file_content, pd.DataFrame):
            df = pd.DataFrame(file_content)
        else:
            df = file_content

        print(df.dtypes)
        # Store dates as real datetimes. The previous version ran pd.to_numeric over
        # "YYYY-MM-DD" strings, which silently turned every date into NA.
        for col in ("collect_date", "date"):
            if col in df.columns:
                df[col] = to_naive_date(df[col])
        print(df.dtypes)

        cols_except_dt = [col for col in df.columns.tolist() if col != "collect_date"]

        df =df.sort_values("collect_date", ascending=False).drop_duplicates(
            subset=cols_except_dt, keep="last"
            )
        os.makedirs(DATA_LAKE_BASE_PATH, exist_ok=True)
        df.to_parquet(f"{full_file_name}.parquet", index=False)
    else:
        print(
            "Specified file type not found or combination of Zone and File Type does not match"
        )

def to_naive_date(series: pd.Series) -> pd.Series:
    """Parse strings/timestamps (tz-aware or not) into tz-naive midnight datetimes."""
    parsed = pd.to_datetime(series, errors="coerce", utc=True, format="mixed")
    return parsed.dt.tz_localize(None).dt.normalize()


def get_missing_stock_dates(
    df: pd.DataFrame, ticker: str, date_col_name: str, start_date: str, end_date: str
) -> List[str]:
    print(f'ticker: {ticker}')
    # df_filtered = df.query("ticker_name == @ticker")
    df_filtered = df[df["ticker_name"] == ticker]
    dt_fmt = "%Y-%m-%d"

    if df_filtered.shape[0] == 0:
        print(f'ticker does not exist in the data for {ticker} between {start_date} and {end_date}')
        # raise ValueError("ticker does not exist in the data")
        return []

    existing_dates = (
        pd.to_datetime(df_filtered[date_col_name], errors="coerce")
        .dt.strftime("%Y-%m-%d").dropna().unique().tolist()
    )
    datetime_start_date = datetime.strptime(start_date, dt_fmt)
    datetime_end_date = datetime.strptime(end_date, dt_fmt)
    expected_dates = [
        (datetime_start_date + timedelta(days=x)).strftime(dt_fmt)
        for x in range((datetime_end_date - datetime_start_date).days)
    ] + [end_date]
    return list(set(expected_dates) - set(existing_dates))


# df = pd.read_parquet("./data_lake/refined/parquet/stocks/stocks.parquet")
# tickers_list = df["ticker_name"].unique().tolist()
# for ticker in tickers_list:
#     missing_dates = get_missing_stock_dates(df, ticker=ticker, date_col_name="date", start_date="2024-01-31", end_date="2024-02-17")
#     print(f"Missing dates for ticker {ticker}: {missing_dates}")
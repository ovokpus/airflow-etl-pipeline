"""Refine raw yfinance CSV files into refined/parquet/stocks/stocks.parquet."""

import os
import re
from argparse import ArgumentParser
from datetime import datetime

import numpy as np
import pandas as pd

from utils import save_data, to_naive_date

COLUMNS = ["date", "open", "high", "low", "close", "volume"]


def parse_stock_frame(file_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Normalise one raw CSV (one ticker, one collect date) into the refined schema."""
    collect_date = datetime.strptime(file_name.split("_")[0], "%Y%m%d").strftime("%Y-%m-%d")
    ticker = file_name.split("_")[2].split(".")[0]
    df = df.copy()
    df.columns = [re.sub(r"\s+", "_", x.lower()) for x in df.columns]
    if df.shape[0] == 0:
        return pd.DataFrame([{**{c: np.nan for c in COLUMNS}, "date": collect_date,
                              "ticker_name": ticker, "collect_date": collect_date}])
    if "date" not in df.columns:
        # Older yfinance exports dropped the index; the bar is the day before collection.
        df["date"] = (pd.Timestamp(collect_date) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    df = df[COLUMNS]
    df["date"] = to_naive_date(df["date"])
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(float)
    df["volume"] = df["volume"].astype("Int64")
    df["ticker_name"] = ticker
    df["collect_date"] = collect_date
    return df


def refine_stocks(data_lake_path: str) -> pd.DataFrame:
    raw_path = f"{data_lake_path}raw/csv/stocks/"
    dfs = []
    for file_name in sorted(os.listdir(raw_path)):
        if not file_name.endswith(".csv") or not file_name.split("_")[2].split(".")[0]:
            continue
        dfs.append(parse_stock_frame(file_name, pd.read_csv(f"{raw_path}{file_name}")))
    df = pd.concat(dfs, ignore_index=True)
    save_data(df, "stocks", zone="refined", context="stocks",
              file_type="parquet", base_path=data_lake_path)
    return df


if __name__ == "__main__":
    parser = ArgumentParser(description="Refine raw stock data")
    parser.add_argument("--data_lake_path", required=True, help="Airflow's data lake path in docker")
    args = parser.parse_args()
    out = refine_stocks(args.data_lake_path)
    print(f"Refined {len(out)} stock rows")

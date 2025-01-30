"""
This module contains functions and classes for processing stock data.
"""

import os
from datetime import datetime
import re
import pprint
from argparse import ArgumentParser
import numpy as np
import pandas as pd
from utils import save_data

pp = pprint.PrettyPrinter(indent=4)

BASE_RAW_CSV_STOCKS_PATH = "./data_lake/raw/csv/stocks/"

if __name__ == "__main__":
    parser = ArgumentParser(description="Parser of book collection")
    parser.add_argument(
        "--data_lake_path", required=True, help="Airflow's data lake path in docker"
    )
    args = parser.parse_args()
    BASE_RAW_CSV_STOCKS_PATH = f"{args.data_lake_path}raw/csv/stocks/"
    dfs = []
    for file_name in os.listdir(BASE_RAW_CSV_STOCKS_PATH):
        file_full = f"{BASE_RAW_CSV_STOCKS_PATH}{file_name}"
        file_creation_date = datetime.strptime(file_name.split("_")[0], "%Y%m%d").strftime(
            "%Y-%m-%d"
        )
        ticker_name = file_name.split("_")[2].split(".")[0]
        df = pd.read_csv(file_full)
        df.columns = [re.sub(r"\s+", "_", x.lower()) for x in df.columns]
        if 'date' not in df.columns:
            df["date"] = datetime.today().strftime("%Y-%m-%d")
        df = df[["date", "open", "high", "low", "close", "volume"]]

        if df.shape[0] > 0:
            df["date"] = pd.to_datetime(df["date"]).dt.date
            for item in ["open", "high", "low", "close"]:
                df[item] = df[item].astype(float)
            df["volume"] = df["volume"].astype(int)
            df["ticker_name"] = ticker_name
            df["collect_date"] = file_creation_date
            dfs.append(df)
        else:
            df = pd.DataFrame(
                [
                    {
                        "date": file_creation_date,
                        "open": np.nan,
                        "high": np.nan,
                        "low": np.nan,
                        "close": np.nan,
                        "volume": np.nan,
                        "ticker_name": ticker_name,
                        "collect_date": file_creation_date,
                    }
                ]
            )
            dfs.append(df)

    df = pd.concat(dfs)

    save_data(df, "stocks", zone="refined", context="stocks",
              file_type="parquet", base_path=args.data_lake_path)
    # df_parquet = pd.read_parquet(
    #     "./data_lake/refined/parquet/stocks/stocks.parquet"
    # )
    # pp.pprint(df_parquet)

"""
This module contains functions and classes for collecting stock data.
"""

from datetime import datetime, timedelta, date
import pprint
from datetime import date, timedelta, datetime
from yfinance import Ticker
import re
from argparse import ArgumentParser
import pandas as pd
from utils import save_data, get_missing_stock_dates

import requests_cache
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


pp = pprint.PrettyPrinter(indent=4)

# TICKERS_LIST = [
#     "AAPL",
#     "MSFT",
#     "AMZN",
#     "META",
#     "NFLX",
#     "GOOG"
# ]


def collect_stock_data(stock_ticker: str, start_date: str, end_date: str) -> dict:
    n_requests = 2
    interval = 6
    session = CachedLimiterSession(
        limiter=Limiter(
            RequestRate(n_requests, Duration.SECOND * interval)
        ),  # max X requests per Y seconds
        bucket_class=MemoryQueueBucket,
        backend=SQLiteCache("stock_etl.cache"),
    )

    ticker_data = Ticker(stock_ticker, session=session)
    df = ticker_data.history(start=start_date, end=end_date)
    return df


if __name__ == "__main__":
    parser = ArgumentParser(description="Parser of stock collection")
    parser.add_argument(
        "--data_lake_path", required=True, help="Airflow's data lake path in docker"
    )
    parser.add_argument(
        "--stock_tickers", required=True, help="List of stock tickers to be downloaded"
    )
    parser.add_argument(
        "--execution_date", required=True, help="Execution date of the Airflow DAG"
    )
    parser.add_argument(
        "--stock_collect_mode",
        required=True,
        help="Flag that defines in which mode this script will run",
        choices=["normal", "fill_missing"],
    )
    parser.add_argument(
        "--start_date_missing_values",
        required=False,
        help="If script is set to mode 'fill_missing', this date identify the initial search point ",
    )
    parser.add_argument(
        "--end_date_missing_values",
        required=False,
        help="If script is set to mode 'fill_missing', this date identify the final search point ",
    )

    args = parser.parse_args()
    print(args)

    # TICKER_LIST = args.stock_tickers.split(",")
    TICKER_LIST = [item for item in args.stock_tickers.split(
        ",") if isinstance(item, str) and re.search(r"^[A-Z]+$", item)]
    dt = datetime.strptime(args.execution_date, "%Y-%m-%d").strftime("%Y%m%d")

    if args.stock_collect_mode == "normal":
        yesterday = (
            datetime.strptime(args.execution_date,
                              "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        for ticker in TICKER_LIST:
            response = collect_stock_data(
                ticker, start_date=yesterday, end_date=args.execution_date
            )
            file_name = f"{dt}_stock_{ticker}"
            response = response.reset_index()

            save_data(
                response,
                file_name,
                context="stocks",
                file_type="csv",
                base_path=args.data_lake_path,
            )
    elif args.stock_collect_mode == "fill_missing":
        try:
            df = pd.read_parquet(
                f"{args.data_lake_path}refined/parquet/stocks/stocks.parquet")
            print(df.head())

            for ticker in TICKER_LIST:
                missing_dates = get_missing_stock_dates(
                    df,
                    ticker=ticker,
                    date_col_name="date",
                    start_date=args.start_date_missing_values,
                    end_date=args.end_date_missing_values,
                )
                dfs = []
                for missing_date in missing_dates:
                    tomorrow_dt = (
                        datetime.strptime(
                            missing_date, "%Y-%m-%d") + timedelta(days=1)
                    ).strftime("%Y-%m-%d")
                    response = collect_stock_data(
                        ticker, start_date=missing_date, end_date=tomorrow_dt
                    ).reset_index()
                    dfs.append(response)
                response = pd.concat(dfs)

                file_name = f"{dt}_stock_{ticker}_fill_missing_from_{args.start_date_missing_values}_to_{args.end_date_missing_values}"
                save_data(
                    response,
                    file_name,
                    context="stocks",
                    file_type="csv",
                    base_path=args.data_lake_path,
                )

        except FileNotFoundError:
            print("There is no stock.parquet file. Task not executed")
            pass

    else:
        raise Exception("Invalid stock_collect_mode")

"""
This module contains functions and classes for collecting stock data.
"""

import pprint
from datetime import date, timedelta, datetime
from yfinance import Ticker
from argparse import ArgumentParser
from utils import save_data

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
    ticker_data = Ticker(stock_ticker)
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

    args = parser.parse_args()
    print(args)

    TICKERS_LIST = args.stock_tickers.split(",")

    dt = datetime.strptime(args.execution_date, "%Y-%m-%d")
    yesterday = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
    for item in TICKERS_LIST:
        response = collect_stock_data(
            item, start_date=yesterday, end_date=args.execution_date
        )  # .reset_index()
        dt_fmt = dt.strftime("%Y%m%d")
        file_name = f"{dt_fmt}_stock_{item}"
        pp.pprint(response)
        response = response.reset_index()

        save_data(
            response,
            file_name,
            context="stocks",
            file_type="csv",
            base_path=args.data_lake_path,
        )

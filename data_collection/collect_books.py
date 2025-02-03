"""
This module contains functions for collecting book data from the Open Library API.
"""

from typing import Dict, Union
from datetime import date, datetime
from argparse import ArgumentParser
import requests
import re
from utils import save_data
import pandas as pd

BASE_API_URL = "https://openlibrary.org/works/"
FILE_FORMAT = ".json"

# IDS_LIST = [
#     "OL47317227M",
#     "OL38631342M",
#     "OL46057997M",
#     "OL26974419M",
#     "OL10737970M",
#     "OL25642803M",
#     "OL20541993M",
# ]


def collect_single_book_data(
    base_url: str, open_library_id: str, file_format: str
) -> Dict:
    """
    Collect data for a single book from the Open Library API.

    Args:
        base_url (str): The base URL of the Open Library API.
        open_library_id (str): The Open Library ID of the book.
        file_format (str): The file format to request (e.g., '.json').

    Raises:
        Exception: If the request fails or returns a non-200 status code.

    Returns:
        Dict: The JSON response from the API as a dictionary.
    """
    url = base_url + open_library_id + file_format
    print(url)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(url, timeout=20, headers=headers)
        if r.status_code == 200:
            return r.json()
        else:
            msg = (
                f"Error occurred in the request. It returned code: {r.status_code} \n {r.json()}"
            )
            raise requests.exceptions.HTTPError(msg)
    except requests.exceptions.RequestException as e:
        print(e)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Collect book data from the Open Library API.")
    parser.add_argument(
        "--data_lake_path",
        required=False,
        help="The Open Library IDs of the books to collect data for.",
        default='./data_lake/'
    )
    parser.add_argument(
        "--open_library_ids", required=False, help="List of books to be downloaded",
        default="OL47317227M,OL38631342M,OL46057997M,OL26974419M,OL10737970M,OL25642803M,OL20541993M"
    )
    parser.add_argument(
        "--execution_date", required=True, help="Execution date of the Airflow DAG"
    )
    args = parser.parse_args()
    # IDS_LIST = args.open_library_ids.split(",")
    IDS_LIST = [item for item in args.open_library_ids.split(
        ",") if isinstance(item, str) and re.search(r"^[A-Z0-9]+$", item)]
    blocklist = []

    try:
        df = pd.read_parquet(
            f"{args.data_lake_path}refined/parquet/books/books.parquet"
        )
        df["collect_date"] = pd.to_datetime(df["collect_date"])
        df["execution_date"] = args.execution_date
        df["execution_date"] = pd.to_datetime(df["execution_date"])
        df["diff_months"] = df["execution_date"].dt.to_period("M").astype(int) - df[
            "collect_date"
        ].dt.to_period("M").astype(int)

        blocklist = df.query("diff_months > 12")["id"].values.tolist()
    except FileNotFoundError:
        pass

    cleaned_ids_list = list(set(IDS_LIST) - set(blocklist))

    for item in cleaned_ids_list:
        item = item.strip()
        dt = datetime.strptime(args.execution_date,
                               "%Y-%m-%d").strftime("%Y%m%d")
        response_json = collect_single_book_data(
            BASE_API_URL, item, FILE_FORMAT)
        file_name = f"{dt}_book_{item}"
        save_data(
            response_json,
            file_name,
            context="books",
            file_type="json",
            base_path=args.data_lake_path,
        )
# for item in IDS_LIST:
#     response_json = collect_single_book_data(BASE_API_URL, item, FILE_FORMAT)
#     file_name = f"{date.today().strftime('%Y%m%d')}_book_{item}"
#     save_data(response_json, file_name, context="books", file_type="json")

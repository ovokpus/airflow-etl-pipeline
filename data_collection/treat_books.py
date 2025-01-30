import os
from datetime import datetime
import pprint
import json
from argparse import ArgumentParser
import pandas as pd
from utils import save_data

pp = pprint.PrettyPrinter(indent=4)

if __name__ == "__main__":
    parser = ArgumentParser(description="Parser of book collection")
    parser.add_argument(
        "--data_lake_path", required=True, help="Airflow's data lake path in docker", default="./data_lake/"
    )
    args = parser.parse_args()
    BASE_RAW_JSON_BOOKS_PATH = f"{args.data_lake_path}raw/json/books/"
    data = []

    for file_name in os.listdir(BASE_RAW_JSON_BOOKS_PATH):
        file_full = f"{BASE_RAW_JSON_BOOKS_PATH}{file_name}"
        file_creation_date = datetime.strptime(file_name.split("_")[0], "%Y%m%d").strftime(
            "%Y-%m-%d"
        )
        open_library_id = file_name.split("_")[-1].split(".")[0]
        with open(file_full, "r", encoding="utf-8") as fp:
            item = json.load(fp)
            if item:
                d = {
                    "id": open_library_id,
                    "title": item["title"] if "title" in item else None,
                    "subtitle": item["subtitle"] if "subtitle" in item else None,
                    "number_of_pages": item["number_of_pages"]
                    if "number_of_pages" in item
                    else None,
                    "publish_date": item["publish_date"] if "publish_date" in item else None,
                    "publish_country": item["publish_country"]
                    if "publish_country" in item
                    else None,
                    "by_statement": item["by_statement"] if "by_statement" in item else None,
                    "publish_places": "|".join(item["publish_places"])
                    if "publish_places" in item
                    else None,
                    "publishers": "|".join(item["publishers"])
                    if "publishers" in item
                    else None,
                    "authors_uri": "|".join(
                        [author_dict["key"] for author_dict in item["authors"]]
                    )
                    if "authors" in item
                    else None,
                    "collect_date": file_creation_date,
                }

                data.append(d)
            else:
                print("No item")
    # filename = f"books_{datetime.now().strftime('%d-%m-%Y_%H:%M:%S')}"
    filename = "books"
    save_data(data, filename, zone="refined", context="books", file_type="parquet")

    # df_parquet = pd.read_parquet(f"opt/airflow/data_lake/refined/parquet/books/{filename}.parquet")
    # pp.pprint(df_parquet)


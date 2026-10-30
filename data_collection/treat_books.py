"""Refine raw Open Library book JSON files into refined/parquet/books/books.parquet."""

import json
import os
from argparse import ArgumentParser
from datetime import datetime
from typing import Dict, List, Optional

from utils import save_data


def parse_book_file(file_name: str, item: Dict) -> Optional[Dict]:
    """Turn one raw book JSON payload into a flat record (None if empty or unnamed)."""
    open_library_id = file_name.split("_")[-1].split(".")[0]
    if not item or not open_library_id:
        return None
    collect_date = datetime.strptime(file_name.split("_")[0], "%Y%m%d").strftime("%Y-%m-%d")

    def joined(key: str) -> Optional[str]:
        return "|".join(item[key]) if key in item else None

    return {
        "id": open_library_id,
        "title": item.get("title"),
        "subtitle": item.get("subtitle"),
        "number_of_pages": item.get("number_of_pages"),
        "publish_date": item.get("publish_date"),
        "publish_country": item.get("publish_country"),
        "by_statement": item.get("by_statement"),
        "publish_places": joined("publish_places"),
        "publishers": joined("publishers"),
        "authors_uri": "|".join(a["key"] for a in item["authors"]) if "authors" in item else None,
        "collect_date": collect_date,
    }


def refine_books(data_lake_path: str) -> List[Dict]:
    raw_path = f"{data_lake_path}raw/json/books/"
    data = []
    for file_name in sorted(os.listdir(raw_path)):
        if not file_name.endswith(".json"):
            continue
        with open(f"{raw_path}{file_name}", "r", encoding="utf-8") as fp:
            record = parse_book_file(file_name, json.load(fp))
        if record:
            data.append(record)
        else:
            print(f"No item in {file_name}")
    save_data(data, "books", zone="refined", context="books",
              file_type="parquet", base_path=data_lake_path)
    return data


if __name__ == "__main__":
    parser = ArgumentParser(description="Refine raw book data")
    parser.add_argument("--data_lake_path", default="./data_lake/",
                        help="Airflow's data lake path in docker")
    args = parser.parse_args()
    rows = refine_books(args.data_lake_path)
    print(f"Refined {len(rows)} book records")

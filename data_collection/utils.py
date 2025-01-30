"""
This module contains utility functions for data processing and storage.
"""

import json
import os
from typing import Dict, List, Union
import pandas as pd
from datetime import datetime


def save_data(
    file_content: Union[List[Dict], Dict, List, str, pd.DataFrame],
    file_name: str,
    zone: str = "raw",
    context: str = "books",
    file_type: str = "csv",
    base_path="/opt/airflow/data_lake/",
) -> None:
    DATA_LAKE_BASE_PATH = f"{base_path}{zone}/{file_type}/"
    full_file_name = DATA_LAKE_BASE_PATH + file_name
    print(full_file_name)
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
        df['collect_date'] = pd.to_numeric(df['collect_date'], errors='coerce').astype('Int64')
        df['date'] = pd.to_numeric(df['date'], errors='coerce').astype('Int64')
        print(df.dtypes)
        cols_except_dt = [col for col in df.columns.tolist() if col != "collect_date"]

        df =df.sort_values("collect_date", ascending=False).drop_duplicates(
            subset=cols_except_dt, keep="last"
            )
        df.to_parquet(f"{full_file_name}.parquet")
    else:
        print(
            "Specified file type not found or combination of Zone and File Type does not match"
        )

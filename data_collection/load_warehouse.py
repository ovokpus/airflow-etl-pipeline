"""Load the refined parquet files into the Postgres warehouse (the "L" in ETL).

Tables: books, stocks (replaced on every run) and load_audit (appended).
"""

import os
from argparse import ArgumentParser
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import create_engine


def load(data_lake_path: str, warehouse_url: str, run_id: str = "manual") -> dict:
    engine = create_engine(warehouse_url)
    counts = {}
    for table in ("books", "stocks"):
        path = f"{data_lake_path}refined/parquet/{table}/{table}.parquet"
        if not os.path.exists(path):
            print(f"{path} missing, skipping {table}")
            continue
        df = pd.read_parquet(path)
        df.to_sql(table, engine, if_exists="replace", index=False)
        counts[table] = len(df)
    audit = pd.DataFrame([{
        "run_id": run_id,
        "loaded_at": datetime.now(timezone.utc),
        "books_rows": counts.get("books", 0),
        "stocks_rows": counts.get("stocks", 0),
    }])
    audit.to_sql("load_audit", engine, if_exists="append", index=False)
    return counts


if __name__ == "__main__":
    parser = ArgumentParser(description="Load refined data into the warehouse")
    parser.add_argument("--data_lake_path", required=True)
    parser.add_argument("--run_id", default="manual")
    args = parser.parse_args()
    url = os.environ["WAREHOUSE_URL"]
    print(load(args.data_lake_path, url, args.run_id))

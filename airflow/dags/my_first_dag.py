"""etl_dag: Open Library books + Yahoo Finance stocks -> data lake -> Postgres warehouse."""

import os
from datetime import datetime

from airflow import DAG
from airflow.models import Param
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator

# Read from the environment (set in docker-compose) instead of Variable.get at import
# time, so the DAG parses without a metadata DB (e.g. in CI import tests).
BASE_DATA_COLLECTION_PATH = os.getenv("BASE_DATA_COLLECTION_PATH", "/opt/airflow/data_collection/")
BASE_DATA_LAKE_PATH = os.getenv("BASE_DATA_LAKE_PATH", "/opt/airflow/data_lake/")

DEFAULT_BOOK_IDS = [
    "OL47317227M", "OL38631342M", "OL46057997M", "OL26974419M",
    "OL10737970M", "OL25642803M", "OL20541993M",
]
DEFAULT_TICKERS = ["AAPL", "MSFT", "AMZN", "META", "NFLX", "GOOG"]

with DAG(
    dag_id="etl_dag",
    description="Collect books and stocks, refine to parquet, load into Postgres",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,  # runs share one data lake + warehouse tables
    tags=["etl", "books", "stocks"],
    params={
        "open_library_ids": Param(DEFAULT_BOOK_IDS, type="array", items={"type": "string"}),
        "stock_tickers": Param(DEFAULT_TICKERS, type="array", items={"type": "string"}),
        "stock_collect_mode": Param("normal", type="string", enum=["normal", "fill_missing"]),
        "start_date_missing_values": Param(None, type=["string", "null"], format="date"),
        "end_date_missing_values": Param(None, type=["string", "null"], format="date"),
    },
    render_template_as_native_obj=True,
    is_paused_upon_creation=True,
) as dag:
    start = EmptyOperator(task_id="dummy_task")

    collect_books_task = BashOperator(
        task_id="collect_raw_books",
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}collect_books.py --data_lake_path $DATA_LAKE_PATH --open_library_ids $OPEN_LIBRARY_IDS --execution_date $EXECUTION_DATE",
        env={
            "DATA_LAKE_PATH": BASE_DATA_LAKE_PATH,
            "OPEN_LIBRARY_IDS": "{{ params.open_library_ids|join(',') }}",
            "EXECUTION_DATE": "{{ logical_date | ds }}",
        },
        append_env=True,
    )

    refine_books_task = BashOperator(
        task_id="refine_books",
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}treat_books.py --data_lake_path $DATA_LAKE_PATH",
        env={"DATA_LAKE_PATH": BASE_DATA_LAKE_PATH},
        append_env=True,
    )

    collect_stocks_task = BashOperator(
        task_id="collect_raw_stocks",
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}collect_stocks.py --data_lake_path $DATA_LAKE_PATH --stock_tickers $STOCK_TICKERS --execution_date $EXECUTION_DATE --stock_collect_mode $STOCK_COLLECT_MODE ${{START_DATE_MISSING_VALUES:+--start_date_missing_values $START_DATE_MISSING_VALUES}} ${{END_DATE_MISSING_VALUES:+--end_date_missing_values $END_DATE_MISSING_VALUES}}",
        env={
            "DATA_LAKE_PATH": BASE_DATA_LAKE_PATH,
            "STOCK_TICKERS": "{{ params.stock_tickers|join(',') }}",
            "EXECUTION_DATE": "{{ logical_date | ds }}",
            "STOCK_COLLECT_MODE": "{{ params.stock_collect_mode }}",
            "START_DATE_MISSING_VALUES": "{{ params.start_date_missing_values or '' }}",
            "END_DATE_MISSING_VALUES": "{{ params.end_date_missing_values or '' }}",
        },
        append_env=True,
    )

    refine_stocks_task = BashOperator(
        task_id="refine_stocks",
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}treat_stocks.py --data_lake_path $DATA_LAKE_PATH",
        env={"DATA_LAKE_PATH": BASE_DATA_LAKE_PATH},
        append_env=True,
    )

    load_warehouse_task = BashOperator(
        task_id="load_warehouse",
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}load_warehouse.py --data_lake_path $DATA_LAKE_PATH --run_id '{{{{ run_id }}}}'",
        env={"DATA_LAKE_PATH": BASE_DATA_LAKE_PATH},
        append_env=True,  # keeps WAREHOUSE_URL from the container environment
        trigger_rule="all_done",  # load whatever refined data exists even if one source failed
    )

    start >> collect_books_task >> refine_books_task
    start >> collect_stocks_task >> refine_stocks_task
    [refine_books_task, refine_stocks_task] >> load_warehouse_task

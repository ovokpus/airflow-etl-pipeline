from datetime import datetime, date

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Param, Variable

BASE_DATA_COLLECTION_PATH = Variable.get("BASE_DATA_COLLECTION_PATH")
BASE_DATA_LAKE_PATH = Variable.get("BASE_DATA_LAKE_PATH")

# A DAG represents a workflow, a collection of tasks
with DAG(
    dag_id="etl_dag",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    params={
        "open_library_ids": Param([], type="array", items={"type": "string"}),
        "stock_tickers": Param([], type="array", items={"type": "string"}),
        "stock_collect_mode": Param(
            "normal", type="string", enum=["normal", "fill_missing"]
        ),
        "start_date_missing_values": Param(None, type=["string", "null"], format="date"),
        "end_date_missing_values": Param(None, type=["string", "null"], format="date"),
    },
    render_template_as_native_obj=True,
    is_paused_upon_creation=True
) as dag:
    dummy_task = DummyOperator(task_id="dummy_task")

    # Task to execute the collect_open_library.py script
    collect_books_task = BashOperator(
        task_id="collect_raw_books",
        # Adjust the path accordingly
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}collect_books.py --data_lake_path $DATA_LAKE_PATH --open_library_ids $OPEN_LIBRARY_IDS --execution_date $EXECUTION_DATE",
        env={
            "DATA_LAKE_PATH": BASE_DATA_LAKE_PATH,
            "OPEN_LIBRARY_IDS": "{{ params.open_library_ids|join(',') }}",
            "EXECUTION_DATE": "{{ logical_date | ds }}"
        },
    )

    # Task to execute the treat_open_library.py script
    refine_books_task = BashOperator(
        task_id="refine_books",
        # Adjust the path accordingly
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}treat_books.py --data_lake_path $DATA_LAKE_PATH",
        env={"DATA_LAKE_PATH": BASE_DATA_LAKE_PATH}
    )

    collect_stocks_task = BashOperator(
        task_id="collect_raw_stocks",
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}collect_stocks.py --data_lake_path $DATA_LAKE_PATH --stock_tickers $STOCK_TICKERS --execution_date $EXECUTION_DATE --stock_collect_mode $STOCK_COLLECT_MODE --start_date_missing_values $START_DATE_MISSING_VALUES --end_date_missing_values $END_DATE_MISSING_VALUES",
        env={
            "DATA_LAKE_PATH": BASE_DATA_LAKE_PATH,
            "STOCK_TICKERS": "{{params.stock_tickers|join(',')}}",
            "EXECUTION_DATE": "{{ logical_date | ds }}",
            "STOCK_COLLECT_MODE": "{{ params.stock_collect_mode }}",
            "START_DATE_MISSING_VALUES": "{{ params.start_date_missing_values }}",
            "END_DATE_MISSING_VALUES": "{{ params.end_date_missing_values }}",
        },
    )

    # Task to execute the treat_stocks.py script
    refine_stocks_task = BashOperator(
        task_id="refine_stocks",
        # Adjust the path accordingly
        bash_command=f"python3 {BASE_DATA_COLLECTION_PATH}treat_stocks.py --data_lake_path $DATA_LAKE_PATH",
        env={"DATA_LAKE_PATH": BASE_DATA_LAKE_PATH},
    )

    # Set dependencies between tasks
    dummy_task >> collect_books_task >> refine_books_task
    dummy_task >> collect_stocks_task >> refine_stocks_task

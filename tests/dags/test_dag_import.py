"""DAG integrity tests. Run inside the Airflow image (see CI), not the uv env."""

from pathlib import Path

import pytest

airflow = pytest.importorskip("airflow")
from airflow.models import DagBag  # noqa: E402

DAGS = Path(__file__).resolve().parents[2] / "airflow" / "dags"


@pytest.fixture(scope="module")
def dagbag():
    return DagBag(dag_folder=str(DAGS), include_examples=False)


def test_no_import_errors(dagbag):
    assert dagbag.import_errors == {}


def test_etl_dag_structure(dagbag):
    dag = dagbag.dags.get("etl_dag")  # .get_dag() would query the metadata DB
    assert dag is not None
    assert set(dag.task_ids) == {"dummy_task", "collect_raw_books", "refine_books",
                                 "collect_raw_stocks", "refine_stocks", "load_warehouse"}
    assert dag.get_task("refine_books").upstream_task_ids == {"collect_raw_books"}
    assert dag.get_task("load_warehouse").upstream_task_ids == {"refine_books", "refine_stocks"}
    assert dag.params["stock_tickers"]  # scheduled runs get non-empty defaults

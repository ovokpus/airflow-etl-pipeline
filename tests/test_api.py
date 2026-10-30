"""API tests with Airflow mocked and the data lake pointed at sample_data/."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api.main as main

SAMPLE = Path(__file__).resolve().parents[1] / "sample_data" / "data_lake"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(main, "DATA_LAKE_PATH", SAMPLE)
    calls = []

    def fake_airflow(method, path, **kw):
        calls.append((method, path))
        if path.endswith("/dagRuns") and method == "GET":
            return {"dag_runs": [{"dag_run_id": "manual__1", "run_type": "manual", "state": "success",
                                  "logical_date": "2026-10-30T00:00:00+00:00",
                                  "start_date": "2026-10-30T00:00:00+00:00",
                                  "end_date": "2026-10-30T00:01:00+00:00"}]}
        if path.endswith("/taskInstances"):
            return {"task_instances": [{"task_id": "refine_books", "state": "success",
                                        "duration": 1.2, "try_number": 1}]}
        if method == "POST":
            return {"dag_run_id": "manual__2", "state": "queued"}
        return {}

    monkeypatch.setattr(main, "airflow", fake_airflow)
    c = TestClient(main.app)
    c.calls = calls
    return c


def test_lake_counts_sample_files(client):
    zones = {z["zone"]: z for z in client.get("/api/lake").json()}
    assert zones["raw/json/books"]["files"] > 0
    assert zones["raw/csv/stocks"]["files"] > 0


def test_runs_include_task_states(client):
    runs = client.get("/api/runs").json()
    assert runs[0]["state"] == "success"
    assert runs[0]["tasks"][0] == {"task_id": "refine_books", "state": "success", "duration": 1.2, "try_number": 1}


def test_trigger_unpauses_then_triggers(client):
    assert client.post("/api/runs").json()["run_id"] == "manual__2"
    assert [m for m, _ in client.calls] == ["PATCH", "POST"]

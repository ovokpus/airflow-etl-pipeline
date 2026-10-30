"""Pipeline viewer API: Airflow run history + warehouse outputs + data-lake stats."""

import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, inspect, text

AIRFLOW_URL = os.getenv("AIRFLOW_URL", "http://airflow-webserver:8080").rstrip("/")
AIRFLOW_AUTH = (os.getenv("AIRFLOW_USER", "admin"), os.getenv("AIRFLOW_PASSWORD", "admin"))
WAREHOUSE_URL = os.getenv("WAREHOUSE_URL", "postgresql+psycopg://airflow:airflow@postgres/warehouse")
DATA_LAKE_PATH = Path(os.getenv("DATA_LAKE_PATH", "/data_lake"))
DAG_ID = os.getenv("DAG_ID", "etl_dag")

app = FastAPI(title="Airflow ETL Pipeline Viewer", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_engine = None


def engine():
    global _engine
    if _engine is None:
        _engine = create_engine(WAREHOUSE_URL, pool_pre_ping=True)
    return _engine


def airflow(method: str, path: str, **kwargs) -> Any:
    try:
        r = httpx.request(method, f"{AIRFLOW_URL}/api/v1{path}", auth=AIRFLOW_AUTH, timeout=15, **kwargs)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Airflow unreachable: {e}") from e
    if r.status_code >= 400:
        raise HTTPException(r.status_code, r.text)
    return r.json()


def query(sql: str, **params) -> list[dict]:
    with engine().connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql), params)]


def table_exists(name: str) -> bool:
    return inspect(engine()).has_table(name)


@app.get("/health")
def health():
    status = {"api": "ok"}
    try:
        query("SELECT 1")
        status["warehouse"] = "ok"
    except Exception as e:  # noqa: BLE001
        status["warehouse"] = f"error: {type(e).__name__}"
    try:
        airflow("GET", "/health")
        status["airflow"] = "ok"
    except HTTPException as e:
        status["airflow"] = f"error: {e.status_code}"
    return status


@app.get("/api/dag")
def dag_info():
    dag = airflow("GET", f"/dags/{DAG_ID}")
    tasks = airflow("GET", f"/dags/{DAG_ID}/tasks")["tasks"]
    return {
        "dag_id": dag["dag_id"],
        "description": dag.get("description"),
        "is_paused": dag["is_paused"],
        "schedule": (dag.get("schedule_interval") or {}).get("value"),
        "next_run": dag.get("next_dagrun"),
        "tasks": [{"task_id": t["task_id"], "downstream": t["downstream_task_ids"]} for t in tasks],
    }


@app.get("/api/runs")
def runs(limit: int = 15):
    data = airflow("GET", f"/dags/{DAG_ID}/dagRuns", params={"order_by": "-execution_date", "limit": limit})
    out = []
    for run in data["dag_runs"]:
        tis = airflow("GET", f"/dags/{DAG_ID}/dagRuns/{run['dag_run_id']}/taskInstances")["task_instances"]
        out.append({
            "run_id": run["dag_run_id"],
            "run_type": run["run_type"],
            "state": run["state"],
            "logical_date": run["logical_date"],
            "start_date": run["start_date"],
            "end_date": run["end_date"],
            "tasks": sorted(
                [{"task_id": t["task_id"], "state": t["state"], "duration": t["duration"],
                  "try_number": t["try_number"]} for t in tis],
                key=lambda t: t["task_id"],
            ),
        })
    return out


@app.post("/api/runs")
def trigger_run():
    """Unpause the DAG (it is created paused) and trigger a manual run with default params."""
    airflow("PATCH", f"/dags/{DAG_ID}", params={"update_mask": "is_paused"}, json={"is_paused": False})
    run = airflow("POST", f"/dags/{DAG_ID}/dagRuns", json={"conf": {}})
    return {"run_id": run["dag_run_id"], "state": run["state"]}


@app.get("/api/summary")
def summary():
    out: dict[str, Any] = {"books": 0, "stocks_rows": 0, "tickers": 0, "last_load": None}
    if table_exists("books"):
        out["books"] = query("SELECT COUNT(DISTINCT id) AS n FROM books")[0]["n"]
    if table_exists("stocks"):
        r = query("SELECT COUNT(*) AS n, COUNT(DISTINCT ticker_name) AS t, MIN(date) AS lo, MAX(date) AS hi FROM stocks WHERE close IS NOT NULL")[0]
        out.update(stocks_rows=r["n"], tickers=r["t"], first_date=r["lo"], last_date=r["hi"])
    if table_exists("load_audit"):
        rows = query("SELECT * FROM load_audit ORDER BY loaded_at DESC LIMIT 1")
        out["last_load"] = rows[0] if rows else None
    return out


@app.get("/api/stocks")
def stocks():
    if not table_exists("stocks"):
        return []
    return query(
        """SELECT DISTINCT ON (ticker_name, date) ticker_name, date, open, high, low, close, volume
           FROM stocks WHERE close IS NOT NULL
           ORDER BY ticker_name, date, collect_date DESC"""
    )


@app.get("/api/books")
def books():
    if not table_exists("books"):
        return []
    return query(
        """SELECT DISTINCT ON (id) id, title, subtitle, number_of_pages, publish_date,
                  publishers, collect_date
           FROM books ORDER BY id, collect_date DESC"""
    )


@app.get("/api/lake")
def lake():
    """File counts per data-lake zone (raw json/csv, refined parquet)."""
    zones = []
    for sub in ["raw/json/books", "raw/csv/stocks", "refined/parquet/books", "refined/parquet/stocks"]:
        p = DATA_LAKE_PATH / sub
        files = sorted(p.glob("*")) if p.exists() else []
        zones.append({
            "zone": sub,
            "files": len(files),
            "bytes": sum(f.stat().st_size for f in files),
            "latest": files[-1].name if files else None,
        })
    return zones

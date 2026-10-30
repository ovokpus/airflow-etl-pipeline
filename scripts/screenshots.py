"""Capture README screenshots from the running stack (headless Chromium).

    uv run --with playwright python scripts/screenshots.py
Needs `docker compose up` and at least one finished etl_dag run.
"""

import os

from playwright.sync_api import sync_playwright

OUT = "docs/screenshots"
APP = os.getenv("APP_URL", "http://localhost:3000")
AIRFLOW = os.getenv("AIRFLOW_URL", "http://localhost:8080")
API = os.getenv("API_URL", "http://localhost:8000")
USER, PASSWORD = os.getenv("AIRFLOW_USER", "admin"), os.getenv("AIRFLOW_PASSWORD", "admin")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)

    page.goto(APP)
    page.wait_for_selector("text=Recent DAG runs")
    page.wait_for_selector("svg.spark")
    page.wait_for_timeout(800)
    page.screenshot(path=f"{OUT}/app-dashboard.png", full_page=True)

    page.goto(f"{AIRFLOW}/login/")
    page.fill("input#username", USER)
    page.fill("input#password", PASSWORD)
    page.click("input[type=submit]")
    page.wait_for_load_state("networkidle")

    page.goto(f"{AIRFLOW}/home")
    page.wait_for_selector("text=etl_dag")
    page.screenshot(path=f"{OUT}/airflow-dags.png")

    page.goto(f"{AIRFLOW}/dags/etl_dag/grid?tab=graph")
    page.wait_for_timeout(4000)
    page.screenshot(path=f"{OUT}/airflow-graph.png")

    page.goto(f"{AIRFLOW}/dags/etl_dag/grid")
    page.wait_for_timeout(3000)
    page.screenshot(path=f"{OUT}/airflow-grid.png")

    page.goto(f"{API}/docs")
    page.wait_for_selector(".opblock-summary-path")
    page.wait_for_timeout(500)
    page.screenshot(path=f"{OUT}/api-docs.png")
    browser.close()

# Business case: Airflow ETL Pipeline

**Scheduled pulls from public APIs into a data lake and a warehouse, with run history you can see.**

## Who buys this

The buyer is a data-engineering lead at a small company whose data team runs scripts by hand or with cron. The users are analysts who need fresh tables every morning and engineers who need to see what failed.

## The problem and what it costs

Cron scripts fail silently, retry badly and leave no record. Apache Airflow is the common open-source answer: schedules, retries, dependencies and a run history in one place ([Apache Airflow](https://airflow.apache.org/)). I found no reliable public figure for the cost of a failed scheduled job, so the model below uses assumptions.

## How the repo solves it

| Need | What in the repo does it |
|---|---|
| Collect | `collect_raw_books` (Open Library API) and `collect_raw_stocks` (Yahoo Finance) tasks in `etl_dag` |
| Refine | `refine_books` and `refine_stocks` write cleaned files to a file-based data lake |
| Load | `load_warehouse` writes to Postgres with `trigger_rule=all_done`, so one failed source doesn't block the other |
| Backfill | `stock_collect_mode=fill_missing` fills gaps in a date range |
| See runs | A FastAPI + React viewer reads Airflow's REST API and the warehouse: run history, task states, loaded data and file counts |

## Use-case scenarios

All of these organisations are fictional.

1. **A small investment newsletter** loads daily price bars for a watch list each morning, and sees at a glance if a source failed.
2. **A library-services company** refreshes book metadata from Open Library without re-fetching recent records.
3. **A data team moving off cron** uses this DAG as the template for its first three pipelines.

## ROI: a worked model (illustrative)

These figures are **illustrative assumptions** unless a source is linked.

| Input | Value | Basis |
|---|---|---|
| Pipeline failures a month needing manual investigation | 6 | Assumption |
| Engineer hours per failure without retries or run history | 3 | Assumption |
| Engineer hours per failure with Airflow | 1 | Assumption |
| Engineer hourly cost | US$83 | BLS May 2024 median for software developers, $63.98 an hour ([BLS OEWS](https://www.bls.gov/news.release/archives/ocwage_04022025.pdf)), multiplied by an assumed 1.3 for overhead |

Saving: 6 × 2 h × 12 = 144 hours, about **US$12,000 a year**, against the cost of running Airflow (a small VM or a managed service).

## Path to production

1. Swap the public sources for your own, and check each source's terms of use. Yahoo Finance data is unofficial and not licensed for redistribution.
2. Move to a managed Airflow or a production executor, with secrets in a secret store.
3. Add data-quality checks and alerting on failed tasks.

## Risks and limits

- Airflow adds operating overhead. For one or two jobs, a simpler scheduler may be enough.
- The data sources are demonstrations, so this repo proves the pattern, not a data product.

**Case strength:** **Moderate.** Orchestration has clear value, but the example sources are toy feeds.

## Sources

- Apache Airflow project home page: https://airflow.apache.org/
- U.S. Bureau of Labor Statistics, OEWS May 2024: https://www.bls.gov/news.release/archives/ocwage_04022025.pdf

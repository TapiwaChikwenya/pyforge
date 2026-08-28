"""
example_taxi_dag — your reference DAG for Project 8 (Orchestrate It).

Pipeline: generate a day's taxi data -> validate it -> aggregate it with
Spark on the cluster -> load results to SQLite. Every task is idempotent
and date-aware via the {{ ds }} template, so any day can be re-run safely.

Two ways to call Spark are shown:
  * BashOperator + spark-submit  (used below — transparent, easy to debug)
  * SparkSubmitOperator          (commented at the bottom — the 'proper' way)
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowSkipException

WORKSPACE = "/workspace"          # shared volume: same path on Spark workers

default_args = {
    "owner": "dataforged",
    "retries": 2,                                  # retried by the scheduler,
    "retry_delay": timedelta(minutes=1),           # so tasks MUST be idempotent
}


def _generate(ds, **_):
    """Generate synthetic trips for the logical date `ds` (idempotent:
    re-running a day overwrites that day's file, never appends)."""
    import csv
    import random

    random.seed(ds)  # same date -> same data: reruns are reproducible
    path = f"{WORKSPACE}/data/trips_{ds}.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pickup_time", "zone_id", "distance_km", "fare"])
        for _ in range(10_000):
            hour = random.randint(0, 23)
            zone = random.randint(1, 60)
            km = round(random.uniform(0.5, 25), 2)
            w.writerow([f"{ds}T{hour:02d}:00", zone, km, round(2.5 + km * 1.4, 2)])
    print(f"wrote {path}")


def _validate(ds, **_):
    """Skip downstream work if the day's file is missing or empty."""
    import os

    path = f"{WORKSPACE}/data/trips_{ds}.csv"
    if not os.path.exists(path) or os.path.getsize(path) < 100:
        raise AirflowSkipException(f"no usable data for {ds}")
    print(f"{path}: {os.path.getsize(path)} bytes — ok")


def _load(ds, **_):
    """Load Spark's parquet output into SQLite (upsert-by-replace = idempotent)."""
    import sqlite3
    import pandas as pd

    df = pd.read_parquet(f"{WORKSPACE}/data/agg_{ds}.parquet")
    with sqlite3.connect(f"{WORKSPACE}/data/results.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS revenue "
                     "(ds TEXT, zone_id INT, total_fare REAL, UNIQUE(ds, zone_id))")
        conn.execute("DELETE FROM revenue WHERE ds = ?", (ds,))  # replace the day
        df.to_sql("revenue", conn, if_exists="append", index=False)
    print(f"loaded {len(df)} rows for {ds}")


with DAG(
    dag_id="example_taxi_dag",
    description="Reference pipeline: generate -> validate -> spark -> load",
    start_date=datetime(2026, 7, 1),
    schedule="@daily",
    catchup=False,                 # don't backfill every day since start_date
    default_args=default_args,
    tags=["dataforged", "example"],
) as dag:

    generate = PythonOperator(task_id="generate", python_callable=_generate)
    validate = PythonOperator(task_id="validate", python_callable=_validate)

    # Airflow orchestrates; Spark computes. The job file lives in the shared
    # workspace, and the cluster reads/writes the same /workspace paths.
    transform = BashOperator(
        task_id="transform_with_spark",
        bash_command=(
            "spark-submit --master spark://spark-master:7077 "
            "{{ params.job }} {{ ds }}"
        ),
        params={"job": f"{WORKSPACE}/spark_jobs/aggregate_trips.py"},
    )

    load = PythonOperator(task_id="load", python_callable=_load)

    generate >> validate >> transform >> load

    # --- The provider-operator alternative (same effect as `transform`): ---
    # from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
    # transform = SparkSubmitOperator(
    #     task_id="transform_with_spark",
    #     application=f"{WORKSPACE}/spark_jobs/aggregate_trips.py",
    #     application_args=["{{ ds }}"],
    #     conn_id="spark_default",   # configure spark://spark-master:7077 in Admin > Connections
    # )

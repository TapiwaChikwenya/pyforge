"""
Curriculum aggregator v3: 34 projects across 10 stages.

Merges all stage modules, assigns project numbers by position, attaches
environment info and enrichment/interview content, and defines the stage
structure served to the dashboard.
"""

from curriculum_core import CORE_PROJECTS          # 1-4 (+ pandas powerplant)
from curriculum_bigdata import BIGDATA_PROJECTS    # first-spark, spark-at-scale, orchestrate-it
from curriculum_stage2 import STAGE2_PROJECTS      # algorithms
from curriculum_sql import STAGE3_PROJECTS         # relational SQL
from curriculum_nosql import STAGE4_PROJECTS       # NoSQL
from curriculum_wrangling import STAGE5_PROJECTS   # cleanroom, duckdb, features
from curriculum_etl import STAGE6_PROJECTS, STAGE78_PROJECTS
from curriculum_ai import STAGE9_PROJECTS, STAGE10_PROJECTS
from enrichment_core import ENRICHMENT_CORE
from enrichment_bigdata import ENRICHMENT_BIGDATA
from interviews_core import INTERVIEWS_CORE

# Enrichment layout (unified at assembly time):
#   - Stages 1 / 7–8 early projects: overlay dicts in enrichment_*.py
#   - Later stages: refresher/hints/objectives/interview embedded in the
#     curriculum_* module next to the exercise definition
# Both paths end up on the same exercise keys below (setdefault + update).
_ENRICHMENT = {**ENRICHMENT_CORE, **ENRICHMENT_BIGDATA}

# ----------------------------------------------------------------- lookups
_by_id = {}
for plist in (CORE_PROJECTS, BIGDATA_PROJECTS, STAGE2_PROJECTS, STAGE3_PROJECTS,
              STAGE4_PROJECTS, STAGE5_PROJECTS, STAGE6_PROJECTS, STAGE78_PROJECTS,
              STAGE9_PROJECTS, STAGE10_PROJECTS):
    for p in plist:
        _by_id[p["id"]] = p

# ------------------------------------------------------------------ stages
# The learning path: stage title + ordered project ids.
STAGES = [
    {"title": "Stage 1 · Python that ships",
     "projects": ["task-forge", "weather-watcher", "log-miner", "data-deck"]},
    {"title": "Stage 2 · Interview algorithms",
     "projects": ["structly", "algo-gym", "heap-stream"]},
    {"title": "Stage 3 · Relational databases & SQL mastery",
     "projects": ["sql-foundry", "window-works", "pg-warehouse", "star-schema", "migration-master"]},
    {"title": "Stage 4 · NoSQL & non-relational",
     "projects": ["doc-store", "cache-money", "polyglot"]},
    {"title": "Stage 5 · Data on one machine",
     "projects": ["pandas-powerplant", "cleanroom", "duckdb-turbo", "feature-foundry"]},
    {"title": "Stage 6 · ETL engineering",
     "projects": ["pipeline-blueprint", "cdc-lite", "quality-gate", "stream-sim"]},
    {"title": "Stage 7 · Distributed data — Spark",
     "projects": ["first-spark", "spark-at-scale", "lakehouse-lite"]},
    {"title": "Stage 8 · Orchestration — Airflow",
     "projects": ["orchestrate-it", "airflow-pro"]},
    {"title": "Stage 9 · AI & data science",
     "projects": ["ds-primer", "model-factory", "vector-vault", "llm-pipeline", "rag-works"]},
    {"title": "Stage 10 · Capstone",
     "projects": ["grand-central"]},
]

# ------------------------------------------------------------- environments
ENV_LIGHT = {
    "services": ["app (this app)", "jupyter (JupyterLab at localhost:8888)"],
    "command": "docker compose up -d",
    "note": "The base stack is all you need: code in-app or in JupyterLab. Your files live in the workspace/ folder.",
}
ENV_DB = {
    "services": ["base stack", "warehouse (Postgres+pgvector, localhost:5432, pyforge/pyforge)",
                 "mongo (localhost:27017)", "redis (localhost:6379)"],
    "command": "docker compose --profile db up -d",
    "note": "Adds the seeded databases: the Postgres warehouse (500 customers / 5000 orders, pgvector enabled), MongoDB (reviews + clickstream), and Redis. They persist in volumes and are reused across all later projects.",
}
ENV_SPARK = {
    "services": ["base + databases", "spark-master (UI at localhost:8080)", "spark-worker x2"],
    "command": "docker compose --profile db --profile spark up -d",
    "note": "Adds the 2-worker Spark cluster. JupyterLab reaches it at spark://spark-master:7077 and ships the Postgres JDBC driver for warehouse reads/writes. In-app Spark exercises run in local mode and need nothing extra.",
}
ENV_FULL = {
    "services": ["everything above", "airflow (UI at localhost:8085, admin/admin)"],
    "command": "docker compose --profile db --profile spark --profile airflow up -d",
    "note": "The full platform. airflow/dags is live-mounted — save a DAG file, refresh the UI. This is the stack the capstone runs on.",
}

_ENV_BY_PROJECT = {
    # Stage 1 + 2 + early 5: light
    "task-forge": ENV_LIGHT, "weather-watcher": ENV_LIGHT, "log-miner": ENV_LIGHT,
    "data-deck": ENV_LIGHT, "structly": ENV_LIGHT, "algo-gym": ENV_LIGHT,
    "heap-stream": ENV_LIGHT, "sql-foundry": ENV_DB, "window-works": ENV_DB,
    "pg-warehouse": ENV_DB, "star-schema": ENV_DB, "migration-master": ENV_DB,
    "doc-store": ENV_DB, "cache-money": ENV_DB, "polyglot": ENV_DB,
    "pandas-powerplant": ENV_LIGHT, "cleanroom": ENV_LIGHT, "duckdb-turbo": ENV_LIGHT,
    "feature-foundry": ENV_DB,
    "pipeline-blueprint": ENV_DB, "cdc-lite": ENV_DB, "quality-gate": ENV_DB,
    "stream-sim": ENV_DB,
    "first-spark": ENV_SPARK, "spark-at-scale": ENV_SPARK, "lakehouse-lite": ENV_SPARK,
    "orchestrate-it": ENV_FULL, "airflow-pro": ENV_FULL,
    "ds-primer": ENV_DB, "model-factory": ENV_DB, "vector-vault": ENV_DB,
    "llm-pipeline": ENV_DB, "rag-works": ENV_DB,
    "grand-central": ENV_FULL,
}

# ------------------------------------------------------------ final assembly
# ------------------------------------------------------- runtime capability
# Where each exercise can execute. Everything runs in the browser (Pyodide)
# except the two that boot a real JVM Spark session — verified by running all
# 85 exercises inside headless Chromium; see tests/PYODIDE_COMPAT.md.
_LOCAL_ONLY = {"fs-3", "ss-3"}

# Third-party packages Pyodide must download before an exercise runs. Used by
# the UI to warn about the one-off download (pandas is ~12 MB) — the runtime
# loads them automatically from the import statements either way.
_PKG_BY_IMPORT = {
    "numpy": "numpy", "pandas": "pandas", "sklearn": "scikit-learn",
    "scipy": "scipy", "pydantic": "pydantic", "fastapi": "fastapi",
    "duckdb": "duckdb",
}


def _packages_needed(exercise):
    """Scan starter + check code for imports of heavy third-party packages."""
    import re
    text = exercise["starter_code"] + "\n" + exercise["check_code"]
    found = set()
    for mod in re.findall(r"^\s*(?:from|import)\s+([a-zA-Z_][\w]*)", text, re.M):
        if mod in _PKG_BY_IMPORT:
            found.add(_PKG_BY_IMPORT[mod])
    return sorted(found)


PROJECTS = []
num = 0
for stage in STAGES:
    for pid in stage["projects"]:
        p = _by_id[pid]
        num += 1
        p["num"] = num                                # renumber by path position
        p["environment"] = _ENV_BY_PROJECT[pid]
        p.setdefault("interview", [])
        if pid in INTERVIEWS_CORE:
            p["interview"] = INTERVIEWS_CORE[pid]
        for ex in p["exercises"]:
            extra = _ENRICHMENT.get(ex["id"])
            if extra:
                ex.update(extra)
            ex.setdefault("refresher", "")
            ex.setdefault("objectives", [])
            ex.setdefault("hints", [])
            ex.setdefault("resources", [])
            ex["runtime"] = "local" if ex["id"] in _LOCAL_ONLY else "browser"
            ex["packages"] = _packages_needed(ex)
        PROJECTS.append(p)

PROJECTS_BY_ID = {p["id"]: p for p in PROJECTS}

# Stage payload for the dashboard API
STAGE_LAYOUT = [
    {"title": s["title"], "project_ids": s["projects"]} for s in STAGES
]

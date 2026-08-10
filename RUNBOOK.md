# PyForge Runbook

Everything you need to operate PyForge — 34 projects across 10 stages, from
Python fundamentals to Spark, Airflow, databases and AI. There are no manual
scripts to run and no per-project configuration: every service is fully wired
in `docker-compose.yml`, and every database seeds itself on first start.

> **Hosting it publicly instead?** This runbook covers the local stack, where
> exercises run server-side on your own machine. To put PyForge on the internet
> for other developers, see **DEPLOY.md** — the hosted mode runs learner code in
> the visitor's browser (Pyodide) and removes every code-execution endpoint from
> the server. For AWS specifically — instance sizing, secrets, costs, and what
> happens to the Spark projects — see **AWS.md**.

---

> **First time, or about to deploy?** Follow **TESTING.md** — a step-by-step
> rehearsal of the local stack and then the production stack on your laptop,
> with a go/no-go checklist.

---

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| Docker Desktop (or Docker Engine + Compose v2) | `docker compose version` should print v2.x |
| ~8 GB free RAM | Base+db stack is light (~2 GB); full stack with Spark+Airflow wants 8 GB |
| ~15 GB free disk | Images: app ~2.5 GB (JRE + pyspark + sklearn), Jupyter ~5 GB, Spark ~1 GB, Airflow ~2 GB, DBs ~1 GB |
| Free ports | 8000, 8888, 8080, 7077, 8085, 5432, 27017, 6379 (see §4 to change) |

---

## 2. Start / stop

Compose **profiles** mean you only run what your current project needs. The
app's *Environment* tab always shows the exact command for the project you're on.

| Stack | Projects | Command |
|---|---|---|
| Base (app + JupyterLab) | Stages 1–2, most of 5 | `docker compose up -d` |
| + databases (Postgres/pgvector, Mongo, Redis) | Stages 3, 4, 6, 9 | `docker compose --profile db up -d` |
| + Spark cluster | Stage 7 | `docker compose --profile db --profile spark up -d` |
| + Airflow (full platform) | Stages 8, 10 | `docker compose --profile db --profile spark --profile airflow up -d` |

First start builds three images (app, jupyter, airflow) and pulls the rest —
allow 10–20 minutes once; afterwards startup is seconds.

### Upgrading an existing install

Replace the folder contents, then rebuild — the app image changes with every
new version, so `--build` matters:

```
docker compose down                       # keeps all volumes
# ...replace the pyforge folder with the new one...
docker compose up -d --build              # add the profiles you use
```

The app container runs as uid `10001`. If an older root-owned `app-data` volume
blocks writes after upgrading, fix ownership once:
`docker compose run --user root app chown -R 10001:10001 /app/data`.

Your learning progress lives in the `app-data` volume and the seeded databases
in `warehouse-data` / `mongo-data`, so all three survive the upgrade. Only
`down -v` deletes them.

Stop everything (all data preserved):

```
docker compose --profile db --profile spark --profile airflow down
```

Full reset (**also deletes your progress, warehouse data, Mongo data and
Airflow history** — see §6 for backups first):

```
docker compose --profile db --profile spark --profile airflow down -v
```

---

## 3. URLs & credentials

| Service | URL / DSN | Credentials |
|---|---|---|
| PyForge learning app | http://localhost:8000 | none |
| App's own API docs | http://localhost:8000/api/docs | none |
| JupyterLab | http://localhost:8888 | none (token disabled — local use only) |
| Spark master UI | http://localhost:8080 | none |
| Spark cluster endpoint | `spark://spark-master:7077` | used from code |
| Airflow UI | http://localhost:8085 | `admin` / `admin` |
| Postgres warehouse | `localhost:5432` / from containers: host `warehouse` | db `warehouse`, user `pyforge`, pass `pyforge` |
| MongoDB | `localhost:27017` / from containers: host `mongo` | none, db `appdata` |
| Redis | `localhost:6379` / from containers: host `redis` | none |

> Security note: auth is intentionally minimal because everything binds to
> localhost for learning. Do not expose these ports to the internet as-is.
>
> The in-app runner (`app/runner.py`) scrubbs secrets from the child env,
> uses an isolated temp cwd, enforces timeouts, and applies POSIX resource
> limits. It is **not** a multi-tenant jail — learner code can still reach
> other compose services by design (SQL/Spark exercises). Never publish
> local-mode port 8000 to untrusted networks; use hosted mode for that.

Connection snippets (they work as-is inside JupyterLab):

```python
import psycopg2, pymongo, redis
pg    = psycopg2.connect(host='warehouse', dbname='warehouse', user='pyforge', password='pyforge')
mongo = pymongo.MongoClient('mongodb://mongo:27017').appdata
cache = redis.Redis(host='redis', decode_responses=True)
```

---

## 4. Configuration reference (all of it)

Every knob lives in `docker-compose.yml`. Defaults work; change only with reason.

| Setting | Where | Default | Why you'd change it |
|---|---|---|---|
| App / Jupyter / Spark UI / Airflow ports | `<service>.ports` | 8000 / 8888 / 8080 / 8085 | port clash — change the **left** side only |
| Postgres / Mongo / Redis ports | `<service>.ports` | 5432 / 27017 / 6379 | port clash with a local install |
| Warehouse credentials | `warehouse.environment` | pyforge / pyforge / warehouse | applied on **first** start only (volume init) |
| Spark worker resources | `SPARK_WORKER_CORES/MEMORY` | 2 cores / 2 GB each | bigger datasets in Stage 7 |
| Airflow admin login | `_AIRFLOW_ADMIN_USER/PASSWORD` | admin / admin | applied on first start only |
| Airflow executor | `AIRFLOW__CORE__EXECUTOR` | LocalExecutor | leave as is |
| Spark / PySpark version | image tags + both Dockerfiles + requirements | 3.5.x everywhere | keep in sync if you upgrade |
| Optional LLM key (Stage 9) | add `LLM_API_KEY=...` to `app.environment` | unset (mock client) | to run LLM projects against a real API |

Folder map (host → containers):

| Host folder | Mounted at | Used by |
|---|---|---|
| `workspace/` | `/workspace` (all), also `~/work` in Jupyter | your code & data — shared by Jupyter, Spark, Airflow |
| `airflow/dags/` | `/opt/airflow/dags` | save a `.py` DAG → appears in the UI within ~30 s |
| `databases/postgres-init/` | Postgres init dir | warehouse schema + seed (runs once, on empty volume) |
| `databases/mongo-init/` | Mongo init dir | reviews + events seed (runs once) |
| volume `app-data` | `/app/data` | your learning progress |
| volumes `warehouse-data`, `mongo-data` | DB data dirs | seeded databases persist here |

**The one rule that prevents 90% of Spark file errors:** always use
`/workspace/...` paths in Spark code — driver and executors mount the same
folder there.

**Re-seeding a database:** the init scripts run only on an empty volume. To
reload seeds: `docker compose --profile db down` then
`docker volume rm pyforge_warehouse-data` (or `pyforge_mongo-data`), then start
again. Your own tables go too — export first if you care.

---

## 5. Daily operations

```
docker compose ps                         # what's running
docker compose logs -f app                # follow app logs (or jupyter / airflow / warehouse)
docker compose restart app                # restart one service
docker compose up -d --build app          # rebuild after editing app code
docker compose exec warehouse psql -U pyforge -d warehouse   # SQL shell
docker compose exec mongo mongosh appdata                    # Mongo shell
docker compose exec redis redis-cli                          # Redis shell
```

Backups:

```
docker cp pyforge-app:/app/data/progress.json ./progress-backup.json     # learning progress
docker compose exec warehouse pg_dump -U pyforge warehouse > warehouse.sql
docker compose exec mongo mongodump --db appdata --archive > mongo.archive
```

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| A UI won't load right after `up` | services still starting | `docker compose ps` — wait for `running`; Airflow takes ~1–2 min on first boot |
| "port is already allocated" | another program owns the port | change the **left** side of the mapping, e.g. `5433:5432` |
| Postgres/Mongo has no seed data | volume already existed from an earlier run | see "Re-seeding a database" in §4 |
| `psycopg2.OperationalError` from Jupyter | db profile not started, or wrong host | `docker compose --profile db up -d`; use host `warehouse` (not `localhost`) from inside containers |
| Spark exercise in the app times out | local Spark cold start (JVM) | run it again — the 180 s timeout covers a warm start |
| Notebook can't reach `spark://spark-master:7077` | spark profile not started | `docker compose --profile db --profile spark up -d` |
| Spark job: "file not found" on workers | used `~/work/...` | use `/workspace/...` (§4, the one rule) |
| Spark can't write to Postgres (Lakehouse Lite) | JDBC driver download was skipped at build time | check the jupyter build log for the JDBC warning; re-run `docker compose build jupyter` on a working network, or drop `postgresql-42.7.3.jar` into the container's `$SPARK_HOME/jars/` |
| DAG not appearing in Airflow UI | parse error in the file | `docker compose logs airflow \| grep -i error`; check the UI banner |
| Airflow task stuck in `queued` | scheduler died | `docker compose restart airflow` |
| Airflow login rejected | user created in an earlier run | `docker compose exec airflow airflow users reset-password -u admin -p admin` |
| Jupyter "permission denied" writing files | host folder owned by root | `sudo chown -R 1000:100 workspace/` (Linux hosts only) |
| Spark/Airflow can't write `/workspace` | Linux host permissions | `chmod -R a+rwX workspace/` (Docker Desktop unaffected) |
| Out of memory with everything running | full stack on a small machine | run only the profile your project needs; lower `SPARK_WORKER_MEMORY` |

---

## 7. What's in the box

```
pyforge/
├── docker-compose.yml          # the whole stack; profiles: (base) / db / spark / airflow
├── RUNBOOK.md                  # this file
├── app/                        # the learning app (FastAPI + single-page UI)
│   ├── Dockerfile              # python + JRE (in-app PySpark) + db clients + sklearn/duckdb
│   ├── main.py                 # API: curriculum, sandboxed runner, linting, progress
│   ├── runner.py               # subprocess sandbox with timeouts
│   ├── curriculum*.py          # all 34 projects across 10 stages
│   ├── enrichment*.py          # per-exercise refreshers, hints, objectives, links
│   ├── interviews_core.py      # interview Q&A for the stage 1/7/8 projects
│   └── static/index.html       # the UI (dark, single file, CodeMirror + live lint)
├── jupyter/Dockerfile          # pyspark-notebook + psycopg2/pymongo/redis/duckdb/sklearn + JDBC
├── airflow/
│   ├── Dockerfile              # airflow + JRE + pyspark + spark provider
│   └── dags/example_taxi_dag.py
├── databases/
│   ├── postgres-init/01_warehouse.sql   # warehouse schema + seed (+ pgvector)
│   └── mongo-init/01_seed.js            # reviews + clickstream seed
├── tests/                      # reference solutions + exercise test harness
└── workspace/                  # YOUR files — shared with Jupyter/Spark/Airflow
    ├── notebooks/00_connect_to_spark.ipynb
    ├── spark_jobs/aggregate_trips.py
    └── data/
```

## 8. The learning path

**Stage 1 · Python that ships** — Task Forge (OOP/dataclasses) · Weather Watcher (first ETL) · LogMiner (generators) · DataDeck API (FastAPI)

**Stage 2 · Interview algorithms** — Structly (hashmaps) · Algo Gym (two pointers/windows/binary search) · Heap & Stream (heaps, top-K, reservoir sampling)

**Stage 3 · Relational databases & SQL mastery** — SQL Foundry (joins/aggregates) · Window Works (windows, gaps & islands) · PG Warehouse (indexes, EXPLAIN, transactions, COPY) · Star Schema Studio (dimensional modeling, SCD2) · Migration Master (zero-downtime schema evolution)

**Stage 4 · NoSQL & non-relational** — DocStore (MongoDB) · Cache Money (Redis) · Polyglot Persistence (CAP, quorums, consistent hashing)

**Stage 5 · Data on one machine** — Pandas PowerPlant · Cleanroom (messy data) · DuckDB Turbo · Feature Foundry (features without leakage)

**Stage 6 · ETL engineering** — Pipeline Blueprint (your reusable framework) · CDC Lite (watermarks, late data) · Quality Gate (data quality as code) · Stream Simulator (offsets, windows, exactly-once)

**Stage 7 · Distributed data — Spark** — First Spark · Spark at Scale (shuffles, skew, Catalyst) · Lakehouse Lite (medallion architecture)

**Stage 8 · Orchestration — Airflow** — Orchestrate It · Airflow Pro (dynamic mapping, sensors, backfills, SLAs)

**Stage 9 · AI & data science** — DS Primer (statistics) · Model Factory (scikit-learn end to end) · Vector Vault (embeddings + pgvector) · LLM Pipeline (LLMs as data workers) · RAG Works (retrieval, measured)

**Stage 10 · Capstone** — Grand Central: the whole platform, wired and broken on purpose.

Each project has six tabs: **Brief · Milestones · Exercises** (run code in-app
with instant checks, live linting, progressive hints) **· Under the Hood ·
Interview Q&A** (LeetCode-standard questions with worked answers and
explanations) **· Environment** (the one command it needs).

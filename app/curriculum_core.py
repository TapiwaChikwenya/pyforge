"""
Curriculum part 1: the Python ladder (projects 1-5).

Each project is a dict with:
  id, title, tagline, level, tech, est_hours
  brief          - what you're building and why it matters
  milestones     - ordered build steps you do in the workspace/ folder
  under_the_hood - how the underlying machinery actually works
  exercises      - runnable in-app: starter_code is shown in the editor,
                   check_code is appended and run after the user's code;
                   it uses asserts, so a clean exit means "passed".
"""

CORE_PROJECTS = [
    # ------------------------------------------------------------------ 1
    {
        "id": "task-forge",
        "num": 1,
        "title": "Task Forge",
        "tagline": "A CLI task manager — real OOP, files, and packaging",
        "level": "Intermediate",
        "tech": ["Python OOP", "dataclasses", "argparse", "JSON", "pytest"],
        "est_hours": 4,
        "brief": (
            "Build a command-line task manager you will actually use: add tasks, "
            "list them, mark them done, tag them, and persist everything to a JSON "
            "file. This project locks in the intermediate skills everything else "
            "builds on: clean OOP design, dataclasses, error handling, and a "
            "proper project layout with tests. You'll work in workspace/task_forge/ "
            "(create it in the Jupyter file browser or a terminal there)."
        ),
        "milestones": [
            "Model it: create a Task dataclass (id, title, tags, done, created_at) and a TaskStore class that holds a list of tasks in memory.",
            "Persist it: give TaskStore .save(path) and .load(path) using json — handle the file-not-found case gracefully on first run.",
            "Wire the CLI: use argparse subcommands (add / list / done / rm) so `python -m task_forge add \"learn spark\" --tag learning` works.",
            "Harden it: raise and catch a custom TaskNotFoundError; print friendly messages instead of tracebacks.",
            "Prove it: write pytest tests for TaskStore (add, complete, round-trip save/load) and get them green.",
        ],
        "under_the_hood": (
            "**What Python is really doing.** When you write `@dataclass`, Python "
            "generates `__init__`, `__repr__` and `__eq__` for you at class-creation "
            "time — decorators are just functions that receive your class and return "
            "a modified one. Your objects live in heap memory as dicts of attributes "
            "(`obj.__dict__`), which is why attribute access is flexible but slower "
            "than a C struct — a fact that matters later when pandas and Spark avoid "
            "Python objects entirely for speed.\n\n"
            "**Imports & `python -m`.** Running `python -m task_forge` makes Python "
            "find the package on sys.path and execute its `__main__.py`. Understanding "
            "sys.path now saves you hours of pain later when Spark ships your code to "
            "executor processes that must import it the same way.\n\n"
            "**JSON persistence** is serialization: turning live objects into bytes. "
            "Every data system you'll touch — Spark shuffles, Airflow XComs, Kafka "
            "messages — is serialization + deserialization at industrial scale."
        ),
        "exercises": [
            {
                "id": "tf-1",
                "title": "Dataclass + behavior",
                "instructions": (
                    "Create a dataclass `Task` with fields `title: str`, `done: bool = False`, "
                    "and `tags: list` defaulting to an empty list (careful: mutable default!). "
                    "Add a method `complete()` that sets done to True and returns the task itself "
                    "so calls can chain."
                ),
                "starter_code": (
                    "from dataclasses import dataclass, field\n\n"
                    "# Your Task dataclass here\n"
                ),
                "check_code": (
                    "t = Task('learn spark')\n"
                    "assert t.done is False and t.tags == []\n"
                    "t2 = Task('other')\n"
                    "t.tags.append('x')\n"
                    "assert t2.tags == [], 'Mutable default shared between instances! Use field(default_factory=list)'\n"
                    "assert t.complete() is t and t.done is True\n"
                    "print('PASS: Task dataclass works, mutable-default trap avoided')\n"
                ),
            },
            {
                "id": "tf-2",
                "title": "A store with a custom exception",
                "instructions": (
                    "Write a class `TaskStore` with an internal list. Methods: `add(title)` returns "
                    "a new task id (0, 1, 2, ...); `complete(task_id)` marks that task done; "
                    "if the id doesn't exist, raise a custom exception `TaskNotFoundError`."
                ),
                "starter_code": (
                    "class TaskNotFoundError(Exception):\n"
                    "    pass\n\n"
                    "class TaskStore:\n"
                    "    def __init__(self):\n"
                    "        self.tasks = []\n\n"
                    "    # add() and complete() here\n"
                ),
                "check_code": (
                    "s = TaskStore()\n"
                    "i = s.add('a'); j = s.add('b')\n"
                    "assert (i, j) == (0, 1)\n"
                    "s.complete(1)\n"
                    "try:\n"
                    "    s.complete(99)\n"
                    "    raise AssertionError('complete(99) should raise TaskNotFoundError')\n"
                    "except TaskNotFoundError:\n"
                    "    pass\n"
                    "print('PASS: TaskStore with custom exception works')\n"
                ),
            },
            {
                "id": "tf-3",
                "title": "JSON round-trip",
                "instructions": (
                    "Write `to_json(tasks)` that turns a list of dicts into a JSON string, and "
                    "`from_json(text)` that turns it back. A round trip must preserve the data "
                    "exactly. Use the `json` module."
                ),
                "starter_code": (
                    "import json\n\n"
                    "def to_json(tasks):\n"
                    "    ...\n\n"
                    "def from_json(text):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "data = [{'title': 'x', 'done': False, 'tags': ['a', 'b']}]\n"
                    "s = to_json(data)\n"
                    "assert isinstance(s, str)\n"
                    "assert from_json(s) == data\n"
                    "print('PASS: serialization round-trip preserved the data')\n"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ 2
    {
        "id": "weather-watcher",
        "num": 2,
        "title": "Weather Watcher",
        "tagline": "Your first ETL: pull an API, clean it, land it in SQLite",
        "level": "Intermediate",
        "tech": ["requests", "HTTP/JSON", "retries", "sqlite3", "context managers"],
        "est_hours": 5,
        "brief": (
            "Extract-Transform-Load is the core loop of all data engineering. Build a "
            "pipeline that fetches weather for a list of cities from the free "
            "Open-Meteo API (no key needed), normalizes the JSON into rows, and "
            "upserts them into SQLite. This is exactly what your future Airflow DAGs "
            "will orchestrate — you're building the E, T, and L by hand first so the "
            "orchestration later isn't magic."
        ),
        "milestones": [
            "Extract: write fetch_weather(lat, lon) using requests against api.open-meteo.com; inspect the raw JSON in a notebook.",
            "Be resilient: add a timeout and a retry-with-backoff loop for transient failures; treat HTTP != 200 as an error.",
            "Transform: flatten the nested JSON into rows of (city, timestamp, temperature, windspeed) — pure functions, easy to test.",
            "Load: create the SQLite table with a UNIQUE constraint and upsert with INSERT ... ON CONFLICT so re-runs don't duplicate (idempotency!).",
            "Compose: a run_pipeline(cities) function that does E→T→L and logs counts — then run it twice and prove row counts don't double.",
        ],
        "under_the_hood": (
            "**What happens when requests.get runs.** DNS lookup → TCP handshake → "
            "TLS negotiation → an HTTP GET with headers → the server streams back "
            "bytes → requests decodes them per the Content-Type header. `.json()` is "
            "just `json.loads` on the body. Timeouts exist because every one of those "
            "steps can hang forever.\n\n"
            "**Idempotency is the most important word in this project.** A pipeline "
            "you can safely re-run is the difference between a 2am page and rolling "
            "over in bed. Airflow *retries tasks by design*, so every task you ever "
            "write must tolerate running twice. UPSERT (insert-or-update on a unique "
            "key) is the classic trick.\n\n"
            "**Context managers** (`with sqlite3.connect(...) as conn`) are how Python "
            "guarantees cleanup: `__enter__` on the way in, `__exit__` on the way out "
            "— even when an exception flies. Files, DB connections, Spark sessions: "
            "all managed this way."
        ),
        "exercises": [
            {
                "id": "ww-1",
                "title": "Flatten nested JSON",
                "instructions": (
                    "APIs return nested JSON; databases want flat rows. Write "
                    "`flatten(payload, city)` that takes a dict shaped like Open-Meteo's "
                    "response and returns a flat dict with keys: city, time, temperature, "
                    "windspeed."
                ),
                "starter_code": (
                    "payload = {\n"
                    "    'latitude': -17.83,\n"
                    "    'current_weather': {\n"
                    "        'time': '2026-07-27T09:00',\n"
                    "        'temperature': 18.4,\n"
                    "        'windspeed': 11.2,\n"
                    "    },\n"
                    "}\n\n"
                    "def flatten(payload, city):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "row = flatten(payload, 'Harare')\n"
                    "assert row == {'city': 'Harare', 'time': '2026-07-27T09:00',\n"
                    "               'temperature': 18.4, 'windspeed': 11.2}\n"
                    "print('PASS: nested JSON flattened into a clean row')\n"
                ),
            },
            {
                "id": "ww-2",
                "title": "Retry with backoff",
                "instructions": (
                    "Write `with_retry(fn, attempts=3)` that calls fn(); if it raises, try again "
                    "up to `attempts` total times, then re-raise the last error. Count calls to "
                    "prove it. (In real life you'd also sleep between tries — skip sleeping here.)"
                ),
                "starter_code": (
                    "def with_retry(fn, attempts=3):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "calls = {'n': 0}\n"
                    "def flaky():\n"
                    "    calls['n'] += 1\n"
                    "    if calls['n'] < 3:\n"
                    "        raise ConnectionError('boom')\n"
                    "    return 'ok'\n"
                    "assert with_retry(flaky) == 'ok' and calls['n'] == 3\n"
                    "calls['n'] = 0\n"
                    "def always_fails():\n"
                    "    calls['n'] += 1\n"
                    "    raise ConnectionError('boom')\n"
                    "try:\n"
                    "    with_retry(always_fails, attempts=2)\n"
                    "    raise AssertionError('should have re-raised after 2 attempts')\n"
                    "except ConnectionError:\n"
                    "    assert calls['n'] == 2\n"
                    "print('PASS: retry logic behaves like a real HTTP client')\n"
                ),
            },
            {
                "id": "ww-3",
                "title": "Idempotent upsert",
                "instructions": (
                    "Using sqlite3 in memory, create table readings(city TEXT, time TEXT, temp REAL, "
                    "UNIQUE(city, time)) and write `upsert(conn, rows)` using INSERT ... ON CONFLICT(city, time) "
                    "DO UPDATE SET temp=excluded.temp. Running it twice must not duplicate rows."
                ),
                "starter_code": (
                    "import sqlite3\n\n"
                    "conn = sqlite3.connect(':memory:')\n"
                    "conn.execute('CREATE TABLE readings(city TEXT, time TEXT, temp REAL, UNIQUE(city, time))')\n\n"
                    "def upsert(conn, rows):\n"
                    "    # rows: list of (city, time, temp) tuples\n"
                    "    ...\n"
                ),
                "check_code": (
                    "rows = [('Harare', 't1', 18.0), ('Cape Town', 't1', 15.5)]\n"
                    "upsert(conn, rows)\n"
                    "upsert(conn, [('Harare', 't1', 19.0)])  # re-run with updated temp\n"
                    "got = conn.execute('SELECT COUNT(*) FROM readings').fetchone()[0]\n"
                    "assert got == 2, f'expected 2 rows, found {got} — re-runs must not duplicate'\n"
                    "temp = conn.execute(\"SELECT temp FROM readings WHERE city='Harare'\").fetchone()[0]\n"
                    "assert temp == 19.0\n"
                    "print('PASS: pipeline is idempotent — safe to re-run')\n"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ 3
    {
        "id": "log-miner",
        "num": 3,
        "title": "LogMiner",
        "tagline": "Stream a 1GB log file without 1GB of RAM — think like Spark",
        "level": "Intermediate+",
        "tech": ["generators", "itertools", "regex", "lazy evaluation"],
        "est_hours": 5,
        "brief": (
            "Analyze web-server logs that are too big to load into memory. You'll "
            "build a streaming analytics tool with generators: parse lines lazily, "
            "filter, aggregate top IPs and error rates — constant memory no matter "
            "the file size. This project is secretly Spark training: lazy pipelines "
            "of transformations that only do work when a result is demanded is "
            "*exactly* Spark's execution model."
        ),
        "milestones": [
            "Generate data: write a script that produces a synthetic access.log with ~1M lines (ip, timestamp, path, status, bytes).",
            "Parse lazily: a generator parse_lines(path) that yields one dict per line using a compiled regex — never .readlines().",
            "Build pipeline stages: filter_status(rows, code), and a top_n(rows, key, n) using collections.Counter.",
            "Chain them: errors-per-hour and top-10 IPs computed in one pass; watch memory stay flat (check with tracemalloc).",
            "Compare: load the same file with .read() and measure memory both ways — write down the difference you observe.",
        ],
        "under_the_hood": (
            "**Generators are paused functions.** `yield` freezes the function's "
            "frame (locals, instruction pointer) and hands a value out; `next()` "
            "resumes it. Chaining generators builds a *pull pipeline*: nothing "
            "computes until the final consumer asks. That's lazy evaluation.\n\n"
            "**This is Spark's soul.** In Spark, `df.filter(...).groupBy(...)` builds "
            "a plan and does nothing — only an *action* (count, write) triggers "
            "execution, and Spark then streams partitions through the pipeline just "
            "like your generators stream lines. When you get to Project 6, you will "
            "recognize everything.\n\n"
            "**Why constant memory matters.** An 8GB log on a 4GB machine is fine if "
            "you stream. Big data is not 'more RAM' — it's *never needing the whole "
            "dataset in memory at once*, on one machine (generators) or a hundred "
            "(Spark partitions)."
        ),
        "exercises": [
            {
                "id": "lm-1",
                "title": "Write a real generator",
                "instructions": (
                    "Write `numbers(path_lines)` — a generator that takes an iterable of raw "
                    "strings, skips blank lines and lines starting with '#', and yields each "
                    "remaining line as an int. It must be lazy: consuming one value must not "
                    "read the rest."
                ),
                "starter_code": (
                    "def numbers(lines):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "import types\n"
                    "consumed = []\n"
                    "def tracking():\n"
                    "    for x in ['1', '', '# comment', '2', '3']:\n"
                    "        consumed.append(x)\n"
                    "        yield x\n"
                    "g = numbers(tracking())\n"
                    "assert isinstance(g, types.GeneratorType), 'use yield, not a list'\n"
                    "assert next(g) == 1\n"
                    "assert len(consumed) <= 2, 'not lazy: you consumed the whole input for one value'\n"
                    "assert list(g) == [2, 3]\n"
                    "print('PASS: lazy generator — this is how Spark streams partitions')\n"
                ),
            },
            {
                "id": "lm-2",
                "title": "Parse log lines with regex",
                "instructions": (
                    "Write `parse(line)` using the `re` module to extract ip, status (int) and "
                    "bytes (int) from lines like:\n"
                    "  203.0.113.7 - - [27/Jul/2026:10:01:22] \"GET /api/x HTTP/1.1\" 200 512\n"
                    "Return a dict {'ip':..., 'status':..., 'bytes':...} or None if the line "
                    "doesn't match."
                ),
                "starter_code": (
                    "import re\n\n"
                    "def parse(line):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "line = '203.0.113.7 - - [27/Jul/2026:10:01:22] \"GET /api/x HTTP/1.1\" 200 512'\n"
                    "row = parse(line)\n"
                    "assert row == {'ip': '203.0.113.7', 'status': 200, 'bytes': 512}\n"
                    "assert parse('garbage line') is None\n"
                    "print('PASS: regex parser handles good and bad lines')\n"
                ),
            },
            {
                "id": "lm-3",
                "title": "One-pass aggregation (map/reduce by hand)",
                "instructions": (
                    "Write `top_ips(rows, n)` that consumes an iterable of {'ip':...} dicts ONCE "
                    "and returns the n most common IPs as a list of (ip, count) tuples, most "
                    "frequent first. Use collections.Counter. This is a reduce — the same "
                    "operation Spark runs per-partition and then merges."
                ),
                "starter_code": (
                    "from collections import Counter\n\n"
                    "def top_ips(rows, n):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "def one_shot():\n"
                    "    for ip in ['a', 'b', 'a', 'c', 'a', 'b']:\n"
                    "        yield {'ip': ip}\n"
                    "assert top_ips(one_shot(), 2) == [('a', 3), ('b', 2)]\n"
                    "print('PASS: single-pass aggregation — a hand-rolled reduce')\n"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ 4
    {
        "id": "data-deck",
        "num": 4,
        "title": "DataDeck API",
        "tagline": "Serve your data: a FastAPI service with tests",
        "level": "Intermediate+",
        "tech": ["FastAPI", "pydantic", "async/await", "pytest", "uvicorn"],
        "est_hours": 6,
        "brief": (
            "Data that nobody can reach is dead data. Wrap the SQLite database from "
            "Weather Watcher in a FastAPI service: list readings, filter by city, "
            "add readings via POST with validation, and ship it with tests. Fun "
            "fact: the very learning app you're using right now is FastAPI — by the "
            "end of this project you can read its source (app/main.py) and "
            "understand every line."
        ),
        "milestones": [
            "Hello service: a FastAPI app with GET /health returning {'status':'ok'}; run it with uvicorn and open the auto-docs at /docs.",
            "Read endpoints: GET /readings and GET /readings/{city} pulling from your Weather Watcher SQLite db.",
            "Validated writes: a pydantic model Reading(city, time, temperature); POST /readings rejects bad payloads automatically — try it in /docs.",
            "Async awareness: add an async endpoint that calls asyncio.sleep and understand why blocking calls would freeze the event loop.",
            "Test it: use fastapi.testclient to test the endpoints without running a server; get pytest green.",
        ],
        "under_the_hood": (
            "**ASGI and the event loop.** Uvicorn holds a single-threaded event loop. "
            "Every request is a coroutine; `await` yields control back to the loop so "
            "thousands of connections interleave on one thread. Async is cooperative "
            "multitasking — one blocking call (time.sleep, heavy CPU) starves "
            "everyone. That's why data-heavy work belongs in workers (or Spark), not "
            "in request handlers.\n\n"
            "**Pydantic = parse, don't validate.** Your type hints become runtime "
            "schema enforcement at the boundary; inside the app, data is *known* "
            "clean. Schema-at-the-boundary is the same discipline as Spark's "
            "DataFrame schemas and Airflow's typed connections.\n\n"
            "**Dependency injection** (FastAPI's `Depends`) is how the framework "
            "builds per-request resources (like DB connections) and cleans them up — "
            "a factory + context manager pattern you already know."
        ),
        "exercises": [
            {
                "id": "dd-1",
                "title": "Validation at the boundary",
                "instructions": (
                    "Using pydantic, define `Reading` with fields city (str, min length 1), "
                    "temperature (float, must be between -90 and 60), and time (str). "
                    "Invalid data must raise a ValidationError on construction."
                ),
                "starter_code": (
                    "from pydantic import BaseModel, Field, ValidationError\n\n"
                    "class Reading(BaseModel):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "r = Reading(city='Harare', temperature=18.4, time='t1')\n"
                    "assert r.temperature == 18.4\n"
                    "ok = False\n"
                    "try:\n"
                    "    Reading(city='X', temperature=200.0, time='t1')\n"
                    "except ValidationError:\n"
                    "    ok = True\n"
                    "assert ok, 'temperature=200 should fail validation'\n"
                    "try:\n"
                    "    Reading(city='', temperature=10.0, time='t1')\n"
                    "    raise AssertionError('empty city should fail')\n"
                    "except ValidationError:\n"
                    "    pass\n"
                    "print('PASS: schema enforced at the boundary')\n"
                ),
            },
            {
                "id": "dd-2",
                "title": "A real endpoint, tested",
                "instructions": (
                    "Build a FastAPI app with GET /cities/{name} that returns "
                    "{'city': name, 'len': len(name)}. Then test it with TestClient — no "
                    "server needed. (This whole exercise runs right here in the app.)"
                ),
                "starter_code": (
                    "from fastapi import FastAPI\n"
                    "from fastapi.testclient import TestClient\n\n"
                    "app = FastAPI()\n\n"
                    "# your endpoint here\n"
                ),
                "check_code": (
                    "# The checker sends a real request through your app. TestClient is the\n"
                    "# normal local tool, but it needs a threadpool — when threads aren't\n"
                    "# available (Python running in the browser) we call the ASGI app\n"
                    "# directly instead. Same request, same response, no threads.\n"
                    "def _get(app, path):\n"
                    "    try:\n"
                    "        from fastapi.testclient import TestClient\n"
                    "        r = TestClient(app).get(path)\n"
                    "        return r.status_code, r.json()\n"
                    "    except Exception:\n"
                    "        import asyncio, json as _json\n"
                    "        async def _call():\n"
                    "            msgs = []\n"
                    "            scope = {'type': 'http', 'asgi': {'version': '3.0'},\n"
                    "                     'http_version': '1.1', 'method': 'GET', 'scheme': 'http',\n"
                    "                     'path': path, 'raw_path': path.encode(), 'query_string': b'',\n"
                    "                     'root_path': '', 'headers': [], 'client': ('test', 1),\n"
                    "                     'server': ('test', 80)}\n"
                    "            async def receive():\n"
                    "                return {'type': 'http.request', 'body': b'', 'more_body': False}\n"
                    "            async def send(m):\n"
                    "                msgs.append(m)\n"
                    "            await app(scope, receive, send)\n"
                    "            status = next(m['status'] for m in msgs\n"
                    "                          if m['type'] == 'http.response.start')\n"
                    "            body = b''.join(m.get('body', b'') for m in msgs\n"
                    "                            if m['type'] == 'http.response.body')\n"
                    "            return status, _json.loads(body)\n"
                    "        return asyncio.run(_call())\n"
                    "\n"
                    "status, payload = _get(app, '/cities/Harare')\n"
                    "assert status == 200, status\n"
                    "assert payload == {'city': 'Harare', 'len': 6}, payload\n"
                    "print('PASS: endpoint served and tested in-process')\n"
                ),
            },
            {
                "id": "dd-3",
                "title": "Feel the event loop",
                "instructions": (
                    "Write async function `gather_all(coros)` that runs a list of coroutines "
                    "CONCURRENTLY (asyncio.gather) and returns their results in order. "
                    "The check runs three 0.1s sleepers — concurrent execution must finish in "
                    "well under 0.3s."
                ),
                "starter_code": (
                    "import asyncio\n\n"
                    "async def gather_all(coros):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "import time\n"
                    "async def sleeper(x):\n"
                    "    await asyncio.sleep(0.1)\n"
                    "    return x\n"
                    "async def main():\n"
                    "    t0 = time.perf_counter()\n"
                    "    out = await gather_all([sleeper(1), sleeper(2), sleeper(3)])\n"
                    "    dt = time.perf_counter() - t0\n"
                    "    assert out == [1, 2, 3]\n"
                    "    assert dt < 0.25, f'{dt:.2f}s — they ran sequentially, not concurrently'\n"
                    "asyncio.run(main())\n"
                    "print('PASS: three sleeps overlapped on one thread — that is the event loop')\n"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ 5
    {
        "id": "pandas-powerplant",
        "num": 5,
        "title": "Pandas PowerPlant",
        "tagline": "Columnar analytics on a million rows — the bridge to Spark",
        "level": "Intermediate+",
        "tech": ["pandas", "numpy", "parquet", "vectorization", "groupby"],
        "est_hours": 6,
        "brief": (
            "Analyze a million-row NYC-taxi-style trips dataset with pandas: load, "
            "clean, join with a zones lookup, aggregate revenue by zone and hour, "
            "and write results to Parquet. You'll generate the dataset yourself "
            "(the generator script is milestone 1), then learn why vectorized "
            "columnar operations crush Python loops — which is precisely why Spark "
            "DataFrames exist. Same API shape, one machine; Spark is next and it "
            "will feel familiar."
        ),
        "milestones": [
            "Generate the data: write make_trips.py producing trips.csv (~1M rows: pickup_time, zone_id, distance_km, fare) plus zones.csv (zone_id, borough).",
            "Load & inspect: read with dtypes specified, parse dates, check .info() memory usage; try category dtype for zone and compare.",
            "Clean: drop impossible rows (negative fares, 0km trips over $50) — count what you dropped and log it.",
            "Join & aggregate: merge zones, then revenue by borough by hour with groupby; find the top-earning zone per borough (groupby + idxmax).",
            "Benchmark & land: compute fare-per-km with a Python loop vs vectorized division, time both; write final aggregates to Parquet and note the file size vs CSV.",
        ],
        "under_the_hood": (
            "**Why vectorization wins.** A pandas column is a numpy array: one "
            "contiguous block of typed memory. `df.fare / df.distance` runs a C loop "
            "over raw doubles — no Python objects, no interpreter dispatch per "
            "element, CPU cache lines fully used. A Python for-loop pays ~100ns of "
            "interpreter overhead *per element*; the C loop pays ~1ns. That's your "
            "100x.\n\n"
            "**Columnar beats row-wise for analytics.** Summing one column touches "
            "only that column's memory. Row storage (like SQLite) drags every field "
            "of every row through the CPU cache. Parquet stores data columnar *on "
            "disk*, with per-column compression — which is why it's the lingua "
            "franca of Spark pipelines.\n\n"
            "**The limit.** Pandas is single-machine, mostly single-core, and wants "
            "your data in RAM. When the data outgrows the box, you keep the "
            "DataFrame mental model and distribute the columns across machines: "
            "that's Spark, next project."
        ),
        "exercises": [
            {
                "id": "pp-1",
                "title": "Vectorize it",
                "instructions": (
                    "You're given arrays fare and km. Compute fare_per_km WITHOUT any Python "
                    "loop (no for/while/comprehension over elements) — pure numpy. Where km is "
                    "0, the result must be 0 (hint: np.where or divide with where=)."
                ),
                "starter_code": (
                    "import numpy as np\n\n"
                    "fare = np.array([10.0, 20.0, 5.0, 8.0])\n"
                    "km = np.array([2.0, 4.0, 0.0, 2.0])\n\n"
                    "fare_per_km = ...  # your one-liner (or two)\n"
                ),
                "check_code": (
                    "import numpy as _np\n"
                    "assert isinstance(fare_per_km, _np.ndarray)\n"
                    "assert _np.allclose(fare_per_km, [5.0, 5.0, 0.0, 4.0])\n"
                    "import inspect\n"
                    "src = _USER_SOURCE\n"
                    "assert 'for ' not in src and 'while ' not in src, 'no loops — vectorize!'\n"
                    "print('PASS: vectorized, zero-division handled')\n"
                ),
            },
            {
                "id": "pp-2",
                "title": "Groupby like you mean it",
                "instructions": (
                    "Given the small trips DataFrame, compute `result`: a DataFrame (or Series) "
                    "of total fare per borough, sorted descending. Use groupby — then peek at "
                    "what it returns before you aggregate to see the split-apply-combine steps."
                ),
                "starter_code": (
                    "import pandas as pd\n\n"
                    "trips = pd.DataFrame({\n"
                    "    'borough': ['Manhattan', 'Brooklyn', 'Manhattan', 'Queens', 'Brooklyn'],\n"
                    "    'fare':    [12.0,        8.0,        20.0,       5.0,      7.0],\n"
                    "})\n\n"
                    "result = ...\n"
                ),
                "check_code": (
                    "vals = result.squeeze()\n"
                    "assert list(vals.index) == ['Manhattan', 'Brooklyn', 'Queens']\n"
                    "assert list(vals.values) == [32.0, 15.0, 5.0]\n"
                    "print('PASS: split-apply-combine — the same thing Spark distributes')\n"
                ),
            },
            {
                "id": "pp-3",
                "title": "Join + find the winner",
                "instructions": (
                    "Merge trips (zone_id, fare) with zones (zone_id, borough), then produce "
                    "`winner`: the zone_id with the highest total fare overall. Two joins ideas "
                    "matter here: merge keys and what happens to rows with no match (try "
                    "how='left' vs 'inner' mentally)."
                ),
                "starter_code": (
                    "import pandas as pd\n\n"
                    "trips = pd.DataFrame({'zone_id': [1, 2, 1, 3, 2, 1],\n"
                    "                      'fare': [10.0, 6.0, 4.0, 9.0, 3.0, 2.0]})\n"
                    "zones = pd.DataFrame({'zone_id': [1, 2, 3],\n"
                    "                      'borough': ['Manhattan', 'Brooklyn', 'Queens']})\n\n"
                    "winner = ...\n"
                ),
                "check_code": (
                    "assert winner == 1, f'zone 1 has 16.0 total — got {winner!r}'\n"
                    "print('PASS: join + aggregate + argmax, the everyday analytics combo')\n"
                ),
            },
        ],
    },
]

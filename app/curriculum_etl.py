"""
Stage 6 — ETL Engineering (4 projects). Real extract-transform-load across
the stack's open-source databases: Mongo (source) -> Postgres warehouse
(target), with Redis in supporting roles. The pipeline library built in
Pipeline Blueprint is REUSED by CDC, Quality Gate, Stream Simulator, Airflow
Pro and the capstone.
"""

STAGE6_PROJECTS = [
    # ------------------------------------------------------------------
    {
        "id": "pipeline-blueprint",
        "title": "Pipeline Blueprint",
        "tagline": "Build a config-driven ETL framework — your reusable pipeline library",
        "level": "Advanced",
        "tech": ["ETL architecture", "connectors", "config-driven design", "Mongo→Postgres"],
        "est_hours": 9,
        "brief": (
            "Stop writing one-off scripts; build the small framework you'll reuse "
            "for the rest of the course: pyforge_etl — extractors (Mongo "
            "collections, REST APIs, CSV files), pure transform functions, "
            "loaders (Postgres upsert, parquet), wired together by a YAML/dict "
            "config instead of code changes. Then use it for real: reviews and "
            "events flow from Mongo into warehouse tables nightly. This is the "
            "architecture question 'design an ETL system' answered in code."
        ),
        "milestones": [
            "Design the interfaces: Extractor.extract() -> iterator of dicts; transform(record) -> record|None; Loader.load(records) -> count. Write them as small ABCs in workspace/pyforge_etl/.",
            "Implement MongoExtractor (collection, query, batch cursor), CsvExtractor, and ApiExtractor (with ww-2 retries) — each yielding plain dicts.",
            "Implement PostgresUpsertLoader (executemany + ON CONFLICT, pw-3 batching) and ParquetLoader; both idempotent by construction.",
            "Build the Pipeline class: config dict {source, transforms, sink, batch_size} -> wired pipeline; run() streams extract→transform→load in batches and returns a run report (counts in/out/errors).",
            "Ship reviews: Mongo reviews → flatten (aspects to columns) → warehouse.fact_reviews. Run twice, prove idempotency with row counts.",
            "Ship events: Mongo events → filter bots/nulls → warehouse.raw_events (JSONB payload). Add a --since parameter (preview of CDC).",
        ],
        "under_the_hood": (
            "**Why config-driven beats script-per-pipeline:** twenty pipelines "
            "as twenty scripts = twenty copies of retry/batch/logging logic "
            "drifting apart. Factoring the *invariant machinery* (extract-"
            "transform-load loop, batching, error handling, reporting) from the "
            "*varying specifics* (which collection, which transforms, which "
            "table) is the framework instinct — and configs are data, so "
            "pipelines become reviewable, diffable, generatable. This is "
            "exactly the design of Airbyte/Meltano/Singer (connectors + "
            "catalog) and dbt (SQL + YAML).\n\n"
            "**Streaming through batches:** extract yields records lazily "
            "(LogMiner!), transforms are pure per-record functions (ww-1!), "
            "the loader buffers into batches (pw-3!) — memory stays flat at "
            "batch_size regardless of table size. Failure granularity = one "
            "batch; paired with idempotent loads, rerun-after-crash is safe. "
            "Every piece of this you've already built — the project is "
            "*composition*.\n\n"
            "**The run report is not optional:** counts in/out/skipped/errored "
            "per run, persisted (the ledger pattern, mm-1) — it's how you "
            "answer 'did last night work?' without grepping logs, and it "
            "becomes the raw material for Quality Gate's automated checks."
        ),
        "exercises": [
            {
                "id": "pb-1",
                "title": "The ETL engine loop",
                "instructions": (
"The heart of every ETL tool, in 20 lines.\n\n**Your task**\n\nImplement "
"`run_pipeline(extract, transforms, load, batch_size)`: `extract` is an "
"iterable of dicts; `transforms` a list of functions record→record|None "
"(None = filter out, applied in order, short-circuiting); `load(batch)` "
"consumes lists of ≤ batch_size records. Stream — never materialize the "
"full dataset — and return a report dict: {'read': n, 'filtered': n, "
"'loaded': n, 'batches': n}. Flush the final partial batch!"
                ),
                "starter_code": (
                    "def run_pipeline(extract, transforms, load, batch_size=2):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "loads = []\n"
                    "def loader(batch):\n"
                    "    loads.append(list(batch))\n"
                    "def gen():\n"
                    "    for i in range(7):\n"
                    "        yield {'n': i}\n"
                    "report = run_pipeline(\n"
                    "    gen(),\n"
                    "    [lambda r: r if r['n'] % 2 == 0 else None,   # drop odds\n"
                    "     lambda r: {'n': r['n'] * 10}],\n"
                    "    loader, batch_size=2)\n"
                    "assert report == {'read': 7, 'filtered': 3, 'loaded': 4, 'batches': 2}, report\n"
                    "assert loads == [[{'n': 0}, {'n': 20}], [{'n': 40}, {'n': 60}]]\n"
                    "print('PASS: the streaming ETL engine — everything else is connectors')\n"
                ),
                "refresher": (
"**Composition of everything you've built:**\n\n"
"```python\nbatch, report = [], {'read': 0, 'filtered': 0, 'loaded': 0, 'batches': 0}\nfor record in extract:                    # lazy stream (lm-1)\n    report['read'] += 1\n    for t in transforms:                  # pure transforms (ww-1)\n        record = t(record)\n        if record is None:\n            report['filtered'] += 1\n            break\n    else:                                  # for/else: no break happened\n        batch.append(record)\n        if len(batch) >= batch_size:      # batching (pw-3)\n            load(batch); report['loaded'] += len(batch)\n            report['batches'] += 1; batch = []\nif batch:                                  # THE classic bug: flush the tail\n    load(batch); ...\n```\n\n"
"Two Python teachables hiding here: the rarely-seen **for/else** (else "
"runs when the loop completed without break — precisely 'record survived "
"all transforms'), and the final-partial-batch flush that every batching "
"implementation forgets once. Design notes that scale up: transforms "
"returning None as the filter contract keeps the interface to ONE "
"function shape; short-circuiting saves work; and because the loop never "
"holds more than batch_size records, this same code shape handles 7 rows "
"or 7 billion — which is the honest answer to 'how would you build an "
"ETL framework?'"
                ),
                "objectives": [
                    "Compose stream + transform-chain + batching into the ETL loop",
                    "Use for/else and short-circuit filtering idiomatically",
                    "Never forget the final partial-batch flush again",
                ],
                "hints": [
                    "Loop transforms inside the record loop; break on None; use for/else to detect survival.",
                    "Flush when len(batch) >= batch_size; reset the list.",
                    "After the main loop: if batch is non-empty, load it and count it.",
                ],
                "resources": [
                    {"title": "for/else — the forgotten Python feature", "url": "https://docs.python.org/3/tutorial/controlflow.html#break-and-continue-statements-and-else-clauses-on-loops"},
                    {"title": "Singer spec (taps & targets — this pattern, standardized)", "url": "https://github.com/singer-io/getting-started"},
                ],
            },
            {
                "id": "pb-2",
                "title": "Dead-letter queue (errors are data)",
                "instructions": (
"Production pipelines don't crash on bad records — they quarantine "
"them.\n\n**Your task**\n\nImplement `run_with_dlq(records, transform, "
"load, dead_letter)`: apply transform to each record; on ANY exception, "
"append {'record': original, 'error': str(exception)} to dead_letter (a "
"list) and continue; survivors go to load (all at once is fine here). "
"Return {'ok': n, 'dead': n}. The pipeline must survive a transform that "
"raises on 2 of 5 records — and the DLQ must preserve enough to replay "
"later."
                ),
                "starter_code": (
                    "def run_with_dlq(records, transform, load, dead_letter):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "def t(r):\n"
                    "    if r.get('amount') is None:\n"
                    "        raise ValueError('null amount')\n"
                    "    if r['amount'] < 0:\n"
                    "        raise ValueError('negative amount')\n"
                    "    return {'amount': r['amount'] * 2}\n"
                    "loaded, dlq = [], []\n"
                    "report = run_with_dlq(\n"
                    "    [{'amount': 1}, {'amount': None}, {'amount': 3}, {'amount': -5}, {'amount': 4}],\n"
                    "    t, loaded.extend, dlq)\n"
                    "assert report == {'ok': 3, 'dead': 2}, report\n"
                    "assert loaded == [{'amount': 2}, {'amount': 6}, {'amount': 8}]\n"
                    "assert dlq[0]['record'] == {'amount': None} and 'null amount' in dlq[0]['error']\n"
                    "assert dlq[1]['record'] == {'amount': -5} and 'negative' in dlq[1]['error']\n"
                    "print('PASS: dead-letter queue — bad records quarantined, pipeline lives')\n"
                ),
                "refresher": (
"**The error-handling ladder for pipelines:** crash-on-first-error "
"(loses the night's run to one bad row), skip-silently (data quietly "
"vanishes — worse), or **dead-letter**: divert failures WITH their "
"errors to a side channel, keep flowing, alert on DLQ volume:\n\n"
"```python\nfor r in records:\n    try:\n        ok.append(transform(r))\n    except Exception as e:\n        dead_letter.append({'record': r, 'error': str(e)})\n```\n\n"
"The DLQ entry preserves the ORIGINAL record (not the half-transformed "
"one) plus the error — the two things replay needs: fix the transform "
"(or the data), re-run the DLQ through the same pipeline, done. In real "
"stacks the DLQ is a table (your raw_events pattern), a Kafka topic, or "
"S3 prefix; the replay-ability requirement is why it must capture "
"records verbatim.\n\n"
"Judgment call worth stating in interviews: DLQ rate is a *metric with "
"a threshold* — 0.01% is weather, 5% is an incident (cr-1's parse-"
"failure lesson). And some errors SHOULD crash the run: a missing "
"table or bad credentials isn't a record problem — distinguish "
"record-level (quarantine) from run-level (fail fast) errors; catching "
"Exception at the record level while letting infrastructure errors "
"propagate from extract/load is the standard cut."
                ),
                "objectives": [
                    "Quarantine per-record failures with replayable DLQ entries",
                    "Distinguish record-level from run-level errors",
                    "Treat DLQ rate as an alertable pipeline metric",
                ],
                "hints": [
                    "try/except around ONLY the transform call; append survivors to a local list.",
                    "DLQ entries: the ORIGINAL record + str(e).",
                    "Call load once with all survivors; return the counts dict.",
                ],
                "resources": [
                    {"title": "Dead letter queues (AWS primer)", "url": "https://aws.amazon.com/what-is/dead-letter-queue/"},
                    {"title": "Kafka DLQ patterns", "url": "https://www.confluent.io/blog/error-handling-patterns-in-kafka/"},
                ],
            },
            {
                "id": "pb-3",
                "title": "Config → pipeline wiring",
                "instructions": (
"The 'framework' part: declarative pipelines.\n\n**Your task**\n\nImplement "
"`build_pipeline(config, registry)`: config is "
"{'source': {'type': ..., **params}, 'transforms': [name, ...], 'sink': "
"{'type': ..., **params}}; registry maps type/name strings to factory "
"functions (for source/sink: factory(**params) → object; for transforms: "
"the function itself). Return {'source': obj, 'transforms': [fns], "
"'sink': obj}. Unknown names must raise ValueError naming the missing "
"key — config errors should fail loudly at BUILD time, not at 2am."
                ),
                "starter_code": (
                    "def build_pipeline(config, registry):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "made = []\n"
                    "registry = {\n"
                    "    'mongo': lambda collection: f'MongoExtractor({collection})',\n"
                    "    'postgres': lambda table, batch=100: f'PgLoader({table},{batch})',\n"
                    "    'drop_nulls': lambda r: r,\n"
                    "    'flatten': lambda r: r,\n"
                    "}\n"
                    "cfg = {'source': {'type': 'mongo', 'collection': 'reviews'},\n"
                    "       'transforms': ['drop_nulls', 'flatten'],\n"
                    "       'sink': {'type': 'postgres', 'table': 'fact_reviews', 'batch': 500}}\n"
                    "p = build_pipeline(cfg, registry)\n"
                    "assert p['source'] == 'MongoExtractor(reviews)'\n"
                    "assert p['sink'] == 'PgLoader(fact_reviews,500)'\n"
                    "assert p['transforms'] == [registry['drop_nulls'], registry['flatten']]\n"
                    "try:\n"
                    "    build_pipeline({'source': {'type': 'kafka'}, 'transforms': [], 'sink': cfg['sink']}, registry)\n"
                    "    raise AssertionError('unknown source type must raise')\n"
                    "except ValueError as e:\n"
                    "    assert 'kafka' in str(e)\n"
                    "print('PASS: declarative pipelines — config in, wired objects out')\n"
                ),
                "refresher": (
"**The registry pattern** is how plugin systems work everywhere "
"(Airflow operators, Airbyte connectors, pytest plugins): a dict from "
"names to factories, so *data can select code*:\n\n"
"```python\ndef build_pipeline(config, registry):\n    src = dict(config['source']); kind = src.pop('type')\n    if kind not in registry:\n        raise ValueError(f'unknown source type: {kind}')\n    source = registry[kind](**src)          # params become kwargs\n    ...\n```\n\n"
"`dict.pop('type')` + `**kwargs` is the idiom: the type selects the "
"factory, the remaining keys ARE its arguments — adding a new connector "
"param requires zero framework changes. Fail-at-build-time is the "
"design principle carrying the exercise: validating every name before "
"anything runs converts 2am NameErrors into deploy-time config "
"rejections (pydantic-validating the whole config schema is the "
"industrial version — dd-1's boundary lesson applied to your own "
"tool).\n\n"
"Zoom out: config-as-data is why dbt/Airbyte/Kubernetes won their "
"categories — declarative artifacts can be diffed in PRs, generated by "
"tools, validated statically, and understood without reading engine "
"code. When an interviewer asks you to 'design a system where analysts "
"can add pipelines without engineers', this exercise IS the answer's "
"core."
                ),
                "objectives": [
                    "Implement registry + factory dispatch with pop/kwargs",
                    "Fail loudly at build time on config errors",
                    "Argue the declarative-config design in system-design terms",
                ],
                "hints": [
                    "Copy the source/sink dicts before pop('type') — don't mutate the caller's config.",
                    "Transforms: look each name up, ValueError (naming it!) if absent.",
                    "registry[kind](**remaining_params) builds the object.",
                ],
                "resources": [
                    {"title": "Airflow provider/operator registry (the pattern at scale)", "url": "https://airflow.apache.org/docs/apache-airflow-providers/"},
                    {"title": "pydantic settings/config validation", "url": "https://docs.pydantic.dev/latest/concepts/pydantic_settings/"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Design an ETL system that syncs 200 heterogeneous sources (APIs, "
"databases, files) into a warehouse, maintained by a 4-person team. What "
"are the core abstractions and operational features?"
                ),
                "difficulty": "Hard",
                "topics": ["ETL architecture", "system design"],
                "answer": (
"Core abstractions: **connector interface** (extract → iterator of "
"typed records; load → idempotent batch writes) so each source is a "
"small plugin, not a bespoke pipeline; **declarative configs** per "
"pipeline (source, schedule, transforms, destination, owners) validated "
"at deploy; **shared engine** owning batching, retries, rate limits, "
"checkpointing/watermarks, DLQ, and run reports — written once. "
"Operational features that make 200 sources survivable for 4 people: "
"per-pipeline run ledger + freshness SLAs with alerting (not 200 "
"dashboards — alert on breach), DLQ with replay tooling, schema-drift "
"detection (new/removed columns → quarantine + notify, don't crash), "
"backfill as a first-class parameterized run, and incremental sync via "
"per-source watermarks. Buy-vs-build honesty: this IS Airbyte/Meltano's "
"architecture — adopt one and spend the team on the 20 connectors that "
"are genuinely custom."
                ),
                "explanation": (
"The question scores architecture *economics*: 200 sources × bespoke "
"scripts is unmaintainable at any team size, so the answer must factor "
"invariants into an engine and reduce each source to config + minimal "
"code (exactly your pb-1/pb-3 build, scaled). The 4-person constraint "
"rewards operational leverage: SLAs-and-alerts over dashboards, replay "
"over firefighting, drift-quarantine over crash. Closing with the "
"buy-vs-build assessment — and knowing WHERE custom effort goes — "
"demonstrates the judgment layer above coding that senior interviews "
"actually price."
                ),
            },
            {
                "question": (
"Your nightly Mongo→Postgres pipeline ran twice due to a scheduler bug "
"and some rows now appear twice in the warehouse. Whose fault is it "
"architecturally, and how do you make this class of bug impossible?"
                ),
                "difficulty": "Medium",
                "topics": ["idempotency", "exactly-once"],
                "answer": (
"Architecturally the *loader's* fault: schedulers, networks and humans "
"WILL cause duplicate runs — at-least-once execution is the only "
"realistic contract (Airflow retries by design), so any load that isn't "
"idempotent is a latent bug regardless of who triggered it. Fixes, in "
"order of robustness: **natural-key upserts** (INSERT ... ON CONFLICT "
"(review_id) DO UPDATE — reruns converge, ww-3); **delete-and-reload "
"the partition** (per day/source in one transaction — full-refresh "
"semantics); **run-scoped staging + swap** (load to temp, atomically "
"replace). Plus a **run ledger** keyed by (pipeline, logical_date) "
"letting the engine detect 'already completed' and no-op the duplicate "
"trigger entirely. Cleanup of the current mess: dedup with ROW_NUMBER "
"OVER (PARTITION BY natural_key) keeping rn=1 (wf-milestone's idiom)."
                ),
                "explanation": (
"The framing — 'whose fault architecturally' — is the interview's real "
"question: blaming the scheduler is the junior answer; designing loads "
"that survive hostile schedulers is the senior one. Reciting the "
"exactly-once-doesn't-exist catechism (at-least-once delivery + "
"idempotent processing = effective exactly-once) with three concrete "
"mechanisms shows applied depth, and the run-ledger addition shows "
"defense-in-depth thinking. The ROW_NUMBER cleanup earns practical "
"points — interviewers like candidates who also mop the floor, not "
"just fix the pipe."
                ),
            },
            {
                "question": (
"ETL vs ELT: define both, explain what shifted the industry toward ELT, "
"and give a case where classic ETL is still the right choice."
                ),
                "difficulty": "Easy",
                "topics": ["ETL vs ELT"],
                "answer": (
"ETL transforms *before* loading (transform on pipeline infrastructure, "
"load clean results); ELT loads raw data first and transforms *inside* "
"the warehouse (SQL, dbt) — raw + staged + modeled layers. The shift's "
"drivers: cloud warehouses made storage cheap and compute elastic (the "
"warehouse became the biggest computer you own), SQL-based transform "
"tooling (dbt) brought software practices to in-warehouse transforms, "
"and keeping raw data means transforms are *replayable* — fix logic, "
"rebuild history, impossible if you only stored transformed output. "
"Classic ETL still wins when: PII/compliance requires "
"masking/tokenizing BEFORE data lands anywhere queryable; heavy "
"unstructured processing (parsing PDFs, image features) that SQL can't "
"express; source-side data reduction for bandwidth (IoT edge "
"aggregation); or the target is an operational store, not an analytical "
"warehouse."
                ),
                "explanation": (
"A vocabulary question, but the follow-ups separate levels: replay-"
"ability of raw data is the deepest argument for ELT (transforms become "
"stateless functions over an immutable log — the functional-programming "
"instinct at architecture scale), while the PII carve-out shows you've "
"met a compliance officer. Worth name-dropping the medallion "
"(bronze/silver/gold) framing since it's the same idea — you'll build "
"it literally in the Lakehouse project — and noting that YOUR pipeline "
"library does ETL for shaping into the warehouse, after which SQL "
"transforms take over: real stacks are hybrids, and saying so "
"gracefully beats picking a side."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "cdc-lite",
        "title": "Incremental Loader (CDC Lite)",
        "tagline": "Watermarks, change capture, and never syncing the same row twice",
        "level": "Advanced",
        "tech": ["incremental loads", "watermarks", "CDC concepts", "late data"],
        "est_hours": 7,
        "brief": (
            "Full reloads die as data grows — production pipelines move only "
            "what changed. Upgrade your Pipeline Blueprint extractors with "
            "watermark-based incremental sync (timestamp cursors persisted in a "
            "state table), handle the gnarly edge cases (late-arriving data, "
            "clock skew, deletes that timestamps can't see), and study how real "
            "CDC (Debezium-style log tailing) solves what cursors can't."
        ),
        "milestones": [
            "Add a state table to the warehouse (pipeline_state: pipeline, watermark, updated_at) and a StateStore class over it — the mm-1 ledger, evolved.",
            "Make MongoExtractor incremental: query {ts: {$gt: watermark}}, ORDER BY ts, and advance the watermark ONLY after the load commits — crash between = safe re-extract (at-least-once).",
            "Prove it: run the events pipeline, insert new Mongo events, rerun — only deltas move; kill it mid-run and verify no data loss on resume.",
            "Late data lab: insert an event with ts BEFORE the current watermark (backdated); show it's missed; fix with an overlap window (watermark - 5min) + upsert dedup — measure the redundancy cost.",
            "Deletes: demonstrate that cursor-based sync never sees Mongo deletions; implement one remediation (soft-delete flags in source, or periodic full-key reconciliation) and document the trade.",
        ],
        "under_the_hood": (
            "**A watermark is a promise:** 'everything with ts <= W has been "
            "processed.' Query-based CDC keeps that promise only if (1) ts is "
            "monotonic and indexed, (2) you order by it and advance W to the "
            "max ts actually loaded, (3) W persists transactionally with (or "
            "after) the load — advance-before-load turns crashes into data "
            "loss; advance-after turns them into harmless re-delivery "
            "(at-least-once + your idempotent loader = converged state. The "
            "trinity completes.).\n\n"
            "**Why the promise leaks:** writers commit out of ts order (clock "
            "skew, long transactions) → rows appear 'in the past' behind W — "
            "the overlap-window rescan is the pragmatic patch, sized to your "
            "source's commit-lag tail. And deletions never update a timestamp "
            "— cursors are blind to them by construction.\n\n"
            "**Log-based CDC** (Debezium tailing Postgres WAL / Mongo change "
            "streams / MySQL binlog) fixes all three leaks at once: the "
            "replication log is ordered by *commit*, includes deletes, and "
            "captures every intermediate state — the database's own "
            "authoritative diary (the WAL you met in pw-2), streamed. Cost: "
            "infrastructure (connector cluster, schema registry, snapshot "
            "handling). The professional decision — cursor CDC for friendly "
            "sources and modest freshness, log CDC for correctness-critical "
            "or delete-heavy sync — is a standard interview fork."
        ),
        "exercises": [
            {
                "id": "cl-1",
                "title": "Watermark sync engine",
                "instructions": (
"The incremental core, with crash-safety semantics.\n\n**Your task**\n\n"
"Implement `sync(source_rows, state, load)`: source_rows is a list of "
"dicts with 'ts' (int) in ARBITRARY order; state is a dict like "
"{'watermark': 5} (missing key = first run = everything). Extract rows "
"with ts strictly > watermark, sort by ts, call load(rows) ONCE (may "
"raise!), and only on success advance state['watermark'] to the max "
"loaded ts. Return the number loaded (0 loads nothing and touches "
"nothing). A failing load must leave the watermark untouched."
                ),
                "starter_code": (
                    "def sync(source_rows, state, load):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "rows = [{'ts': 3, 'v': 'c'}, {'ts': 1, 'v': 'a'}, {'ts': 2, 'v': 'b'}]\n"
                    "loaded = []\n"
                    "state = {}\n"
                    "assert sync(rows, state, loaded.extend) == 3\n"
                    "assert [r['ts'] for r in loaded] == [1, 2, 3] and state['watermark'] == 3\n"
                    "rows.append({'ts': 5, 'v': 'e'}); rows.append({'ts': 4, 'v': 'd'})\n"
                    "assert sync(rows, state, loaded.extend) == 2\n"
                    "assert state['watermark'] == 5 and len(loaded) == 5\n"
                    "assert sync(rows, state, loaded.extend) == 0, 'no new rows -> no-op'\n"
                    "def boom(batch):\n"
                    "    raise IOError('warehouse down')\n"
                    "rows.append({'ts': 6, 'v': 'f'})\n"
                    "try:\n"
                    "    sync(rows, state, boom)\n"
                    "except IOError:\n"
                    "    pass\n"
                    "assert state['watermark'] == 5, 'failed load must NOT advance the watermark'\n"
                    "assert sync(rows, state, loaded.extend) == 1, 'retry picks the row up again'\n"
                    "print('PASS: watermark discipline — crash-safe incremental sync')\n"
                ),
                "refresher": (
"**Order of operations IS the correctness:**\n\n"
"```python\nwm = state.get('watermark', float('-inf'))\nnew = sorted((r for r in source_rows if r['ts'] > wm),\n             key=lambda r: r['ts'])\nif not new:\n    return 0\nload(new)                                  # may raise — fine!\nstate['watermark'] = new[-1]['ts']         # ONLY after success\nreturn len(new)\n```\n\n"
"Walk the failure: load raises → the exception propagates *before* the "
"watermark line → next run re-extracts the same rows → your idempotent "
"loader converges. Flip those two lines and a crash after advance "
"loses the batch forever, silently — the single most consequential "
"line-ordering in data engineering. (In production, 'advance after' "
"means the state write shares the load's transaction or strictly "
"follows its commit.)\n\n"
"Details that earn their keep: **strictly greater** (>) — with >= "
"you'd reprocess the boundary row every run forever (harmless-looking, "
"but with ts-collisions plus > you can *miss* rows sharing the "
"watermark ts — which is why real systems use (ts, id) compound "
"cursors, worth mentioning); `state.get(..., -inf)` makes first-run "
"bootstrap fall out of the same code path; and sorting means the "
"watermark equals the LAST loaded row — the invariant auditors (and "
"your 3am self) can check."
                ),
                "objectives": [
                    "Implement extract-load-then-advance watermark ordering",
                    "Explain why the ordering converts crashes into safe redelivery",
                    "Know the boundary subtleties: > vs >=, compound cursors, bootstrap",
                ],
                "hints": [
                    "Filter ts > watermark (strict), sort ascending, early-return on empty.",
                    "Call load BEFORE touching state — let exceptions fly through.",
                    "Advance to new[-1]['ts'] (the max, thanks to sorting).",
                ],
                "resources": [
                    {"title": "Airbyte: incremental sync modes", "url": "https://docs.airbyte.com/understanding-airbyte/connections/incremental-append"},
                    {"title": "Debezium (log-based CDC)", "url": "https://debezium.io/documentation/reference/stable/tutorial.html"},
                ],
            },
            {
                "id": "cl-2",
                "title": "Late data: the overlap window",
                "instructions": (
"Reality: rows arrive with timestamps in the past.\n\n**Your task**\n\n"
"Implement `sync_with_overlap(source_rows, state, load, overlap)`: like "
"cl-1 but extract rows with `ts > watermark - overlap` — re-scanning a "
"safety margin — and deduplicate against `state['seen_ids']` (a set of "
"already-loaded row 'id's you maintain; keep only ids within the "
"current overlap window to bound memory... simplified here: keep all). "
"Advance watermark to max ts as before. Return loaded count. The "
"checker backdates a row inside the window (caught) and outside it "
"(documented loss)."
                ),
                "starter_code": (
                    "def sync_with_overlap(source_rows, state, load, overlap):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "state = {}\n"
                    "loaded = []\n"
                    "rows = [{'id': 'a', 'ts': 10}, {'id': 'b', 'ts': 20}, {'id': 'c', 'ts': 30}]\n"
                    "assert sync_with_overlap(rows, state, loaded.extend, overlap=15) == 3\n"
                    "assert state['watermark'] == 30\n"
                    "rows.append({'id': 'late', 'ts': 22})   # backdated but within 30-15\n"
                    "rows.append({'id': 'd', 'ts': 40})\n"
                    "n = sync_with_overlap(rows, state, loaded.extend, overlap=15)\n"
                    "assert n == 2, f'late (ts=22 > 15) and d must load, NOT a/b/c again: {n}'\n"
                    "assert {r['id'] for r in loaded} == {'a', 'b', 'c', 'late', 'd'}\n"
                    "rows.append({'id': 'too_late', 'ts': 5})  # outside any window\n"
                    "assert sync_with_overlap(rows, state, loaded.extend, overlap=15) == 0\n"
                    "assert 'too_late' not in {r['id'] for r in loaded}, 'documented loss: beyond the window'\n"
                    "print('PASS: overlap window + dedup — late data handled, loss bounded and known')\n"
                ),
                "refresher": (
"**Overlap + dedup = redundancy you control.** Re-scanning `watermark - "
"overlap` catches stragglers whose commit lagged their timestamp; the "
"seen-ids set (or, equivalently, an idempotent keyed upsert at the "
"sink) cancels the intentional re-reads:\n\n"
"```python\nwm = state.get('watermark', float('-inf'))\nseen = state.setdefault('seen_ids', set())\ncandidates = [r for r in source_rows\n              if r['ts'] > wm - overlap and r['id'] not in seen]\n...\nload(new); seen.update(r['id'] for r in new)\nstate['watermark'] = max(watermark, max ts loaded)\n```\n\n"
"Sizing the window is an SLO conversation, not a constant: measure your "
"source's commit-lag distribution (p99.9 of ts-to-visibility delay) and "
"add margin; the checker's 'too_late' row demonstrates the honest "
"residual — beyond the window, loss is by design, so *say so* in the "
"pipeline's contract and let periodic reconciliation (count/checksum "
"comparisons over closed periods) catch the tail. This exact triad — "
"window, dedup, reconciliation — is how streaming systems frame "
"watermarks/allowed-lateness (Flink, Beam), which you'll meet in Stream "
"Simulator: batch and streaming are the same problem at different "
"granularities."
                ),
                "objectives": [
                    "Combine overlap rescans with dedup for late-data tolerance",
                    "Size windows from commit-lag distributions, not vibes",
                    "Pair windows with reconciliation and state the loss contract",
                ],
                "hints": [
                    "Candidates: ts > watermark - overlap AND id not in seen_ids.",
                    "Update BOTH seen_ids and watermark only after load succeeds.",
                    "Watermark should never move backwards: max(current, new max).",
                ],
                "resources": [
                    {"title": "Streaming watermarks & allowed lateness (Beam model)", "url": "https://beam.apache.org/documentation/programming-guide/#watermarks-and-late-data"},
                    {"title": "Data reconciliation patterns", "url": "https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Compare query-based CDC (timestamp cursors) with log-based CDC "
"(Debezium/WAL tailing) across: completeness, source load, latency, "
"deletes, and operational cost. When do you pick each?"
                ),
                "difficulty": "Hard",
                "topics": ["CDC", "architecture"],
                "answer": (
"**Completeness:** cursors see only the latest state at poll time (miss "
"intermediate updates, miss deletes, leak late commits); log CDC sees "
"every committed change in commit order, including deletes — it reads "
"the database's own WAL. **Source load:** cursor polls run real queries "
"(need an indexed ts column; heavy on hot tables); log tailing reads "
"the replication stream — near-zero query load. **Latency:** polling "
"interval vs sub-second streaming. **Deletes:** cursors structurally "
"blind (workarounds: soft deletes, reconciliation); log CDC emits them "
"natively. **Operational cost:** cursors are ~free (your cl-1 code); "
"log CDC needs connectors (Kafka Connect/Debezium), slot management "
"(an abandoned replication slot can fill the source's disk!), initial "
"snapshots, schema evolution handling. **Pick:** cursors for "
"append-mostly sources, relaxed freshness, small teams; log CDC when "
"deletes/every-change/low-latency matter — billing, inventory, "
"replicating to search indexes — and you can afford the platform."
                ),
                "explanation": (
"A structured-comparison question: the rubric wants the dimensions "
"named crisply and a decision rule, not a winner. Depth signals: the "
"replication-slot disk-fill footgun (real Debezium operators all have "
"this scar), intermediate-states mattering for audit/event-sourcing "
"use cases, and the observation that cursor CDC + idempotent upsert + "
"periodic reconciliation is an honest 90% solution most mid-size "
"shops should run first. Tie-back that lands: log CDC is the outbox "
"pattern's cousin — both piggyback on the transaction log's atomicity "
"to escape dual-write hell (your Polyglot interview answer, "
"resurfacing — interviewers notice coherent worldviews)."
                ),
            },
            {
                "question": (
"Your incremental pipeline's watermark advanced to yesterday 23:59, "
"but finance reports today that ~400 of yesterday's orders are missing "
"from the warehouse. List plausible causes and your systematic fix."
                ),
                "difficulty": "Medium",
                "topics": ["watermarks", "late data", "debugging"],
                "answer": (
"Plausible causes, ordered: **(1) late commits** — rows with "
"yesterday-timestamps committed after the run read past them (long "
"transactions, retried app writes) — the classic cursor leak; **(2) "
"clock skew** — an app server writing ts a few minutes behind DB time; "
"**(3) advance-before-load bug** — a partially failed load that still "
"advanced the watermark (check run logs vs state history); **(4) "
"boundary logic** — >= vs > dropping ties at the watermark, or "
"timezone mismatch making 'yesterday' ambiguous; **(5) filtered "
"casualties** — DLQ'd rows nobody alerted on. Systematic fix: add an "
"overlap window sized to measured commit lag with keyed upserts "
"(redundancy-safe); make watermark advancement transactional with the "
"load; switch the cursor to (ts, id) compound; alert on DLQ volume; "
"and — the structural answer — nightly reconciliation comparing source "
"vs warehouse counts/sums per closed hour, so this class of silent "
"gap pages you instead of finance."
                ),
                "explanation": (
"This is cl-1/cl-2 as a war story, and the interviewer wants both the "
"taxonomy (cursor leaks come from exactly a handful of mechanisms — "
"naming them shows mastery) and the operational instinct that "
"*finance should never be your data-quality monitoring*. "
"Reconciliation as a permanent control, watermark state history as an "
"audit trail, and measuring commit-lag before sizing the window "
"(evidence over guessing) are the senior beats. Quietly impressive "
"closer: backfill the 400 via a bounded re-sync of yesterday's window "
"— and verify with the same reconciliation query that now guards the "
"future."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "quality-gate",
        "title": "Quality Gate",
        "tagline": "Data quality as code: expectations, anomaly checks, and circuit breakers",
        "level": "Advanced",
        "tech": ["data quality", "expectations", "anomaly detection", "data contracts"],
        "est_hours": 7,
        "brief": (
            "Bad data is worse than no data — it looks like truth. Build a "
            "mini Great Expectations: declarative checks (not-null, unique, "
            "ranges, referential integrity, freshness) that run against "
            "warehouse tables after every pipeline run, plus statistical "
            "anomaly detection on row counts and sums, wired into your "
            "Pipeline Blueprint as a gate: green → publish, red → quarantine "
            "and alert. Every check you write here is one Cleanroom lesson, "
            "automated forever."
        ),
        "milestones": [
            "Design the check spec: {'table', 'checks': [{'type': 'not_null', 'column': ...}, {'type': 'unique', ...}, {'type': 'range', ...}, {'type': 'fk', ...}, {'type': 'freshness', ...}]} — declarative, reviewable, pb-3 style.",
            "Implement the runner against Postgres: each check compiles to ONE SQL query (COUNT of violations) — run the suite on fact_reviews and raw_events.",
            "Seed violations deliberately (a null review_id, an orphan product_id) and watch the gate catch them; route violating rows to a quarantine table with the check name attached.",
            "Anomaly layer: store per-run row counts in a history table; flag runs beyond 3 sigma of the trailing 14-run window (your hs-2 stats instincts) — catch a simulated half-empty file.",
            "Wire the gate into the pipeline: staging table → checks → swap-to-final on green / halt-and-alert on red. The mm 'create-and-swap' trick becomes your publish mechanism.",
        ],
        "under_the_hood": (
            "**Checks are assertions about distributions, not just rows.** "
            "Row-level checks (null, range, format) catch corrupt records; "
            "*dataset-level* checks (row count vs history, sum drift, "
            "distinct-count stability) catch the systemic failures — "
            "half-delivered files, doubled loads, upstream filter changes — "
            "that row checks sail past. You need both layers; the second is "
            "where your cr-2 'report' dict grows into monitoring.\n\n"
            "**The staging-gate-swap pattern** is the architectural heart: "
            "load into staging, validate there, publish atomically only on "
            "green. Consumers never see intermediate or invalid states — "
            "it's MVCC's isolation idea rebuilt at the pipeline level, using "
            "the transactional rename you learned in Migration Master.\n\n"
            "**Data contracts** move checks upstream: producer and consumer "
            "agree on schema + semantics + SLAs (freshness, null rates) as "
            "a versioned artifact, validated on BOTH sides — the "
            "'validate at the boundary' principle (dd-1) drawn between "
            "teams. Alert fatigue is the failure mode of naive quality "
            "systems: every check needs an owner, a severity, and a "
            "documented response, or the channel gets muted and the whole "
            "apparatus becomes theater."
        ),
        "exercises": [
            {
                "id": "qg-1",
                "title": "Declarative check runner",
                "instructions": (
"Great Expectations' core in one function.\n\n**Your task**\n\nImplement "
"`run_checks(rows, checks)`: rows are dicts; checks are specs — "
"{'type': 'not_null', 'column': c}, {'type': 'unique', 'column': c}, "
"{'type': 'range', 'column': c, 'min': lo, 'max': hi} (violation if "
"outside [lo, hi] or non-numeric; nulls are ignored here — not_null's "
"job). Return a list of result dicts {'check': spec, 'passed': bool, "
"'violations': count}. Every check runs (no short-circuit) — a report, "
"not a crash."
                ),
                "starter_code": (
                    "def run_checks(rows, checks):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "rows = [\n"
                    "    {'id': 1, 'amount': 50.0},\n"
                    "    {'id': 2, 'amount': -10.0},\n"
                    "    {'id': 2, 'amount': None},\n"
                    "    {'id': None, 'amount': 3000.0},\n"
                    "]\n"
                    "out = run_checks(rows, [\n"
                    "    {'type': 'not_null', 'column': 'id'},\n"
                    "    {'type': 'unique', 'column': 'id'},\n"
                    "    {'type': 'range', 'column': 'amount', 'min': 0, 'max': 1000},\n"
                    "])\n"
                    "assert out[0]['passed'] is False and out[0]['violations'] == 1\n"
                    "assert out[1]['passed'] is False and out[1]['violations'] == 1, 'id=2 duplicated once'\n"
                    "assert out[2]['passed'] is False and out[2]['violations'] == 2, '-10 and 3000; None ignored'\n"
                    "clean = run_checks([{'id': 1, 'amount': 5.0}], [{'type': 'not_null', 'column': 'id'}])\n"
                    "assert clean[0]['passed'] is True and clean[0]['violations'] == 0\n"
                    "print('PASS: declarative quality checks — assertions that outlive the notebook')\n"
                ),
                "refresher": (
"**Dispatch + count, that's the whole engine:**\n\n"
"```python\nfor spec in checks:\n    t, col = spec['type'], spec['column']\n    if t == 'not_null':\n        v = sum(1 for r in rows if r.get(col) is None)\n    elif t == 'unique':\n        counts = Counter(r.get(col) for r in rows\n                         if r.get(col) is not None)\n        v = sum(c - 1 for c in counts.values() if c > 1)\n    elif t == 'range':\n        v = sum(1 for r in rows\n                if r.get(col) is not None\n                and not (isinstance(r[col], (int, float))\n                         and spec['min'] <= r[col] <= spec['max']))\n    results.append({'check': spec, 'passed': v == 0, 'violations': v})\n```\n\n"
"Design decisions doing quiet heavy lifting: *violations as counts* "
"(not booleans) because '3 nulls' and '3 million nulls' demand "
"different responses — thresholds attach later; *unique counts "
"extras* (c-1 per duplicated value) so the number means 'rows to "
"delete'; *nulls ignored by range* keeps each check single-"
"responsibility — compose not_null + range instead of entangling "
"them (the Unix philosophy for data checks); and *no short-circuit* "
"because a quality report with one failure hiding nine others "
"triggers serial redeploys. In SQL these same checks compile to "
"COUNT queries — which is your milestone — and in interviews, "
"sketching this engine is the strong answer to 'how would you build "
"data quality tooling?'"
                ),
                "objectives": [
                    "Implement single-responsibility, count-based quality checks",
                    "Compose checks instead of entangling them",
                    "Explain counts-over-booleans and no-short-circuit reporting",
                ],
                "hints": [
                    "not_null: count rows where .get(col) is None.",
                    "unique: Counter over non-null values; violations = sum of (count-1) for dupes.",
                    "range: skip None; non-numeric OR outside [min, max] counts as a violation.",
                ],
                "resources": [
                    {"title": "Great Expectations concepts", "url": "https://docs.greatexpectations.io/docs/core/introduction/"},
                    {"title": "dbt tests (the SQL-compiled version)", "url": "https://docs.getdbt.com/docs/build/data-tests"},
                ],
            },
            {
                "id": "qg-2",
                "title": "Anomaly detection on run metrics",
                "instructions": (
"Catch the half-empty file no row check can see.\n\n**Your task**\n\n"
"Implement `is_anomalous(history, current, sigmas=3.0)`: history is a "
"list of past run metrics (floats, may be short); current the new "
"value. Return True if |current - mean(history)| > sigmas * "
"std(history) (population std). Edge rules: fewer than 3 history "
"points → False (not enough evidence); std == 0 → anomalous iff "
"current != mean. Then `check_run(history, current)` returning "
"{'anomalous': bool, 'mean': m, 'std': s} (None stats when history "
"< 3)."
                ),
                "starter_code": (
                    "import math\n\n"
                    "def is_anomalous(history, current, sigmas=3.0):\n"
                    "    ...\n\n"
                    "def check_run(history, current):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "hist = [1000, 1020, 980, 1010, 990]\n"
                    "assert is_anomalous(hist, 1005) is False\n"
                    "assert is_anomalous(hist, 500) is True, 'half-empty file must flag'\n"
                    "assert is_anomalous(hist, 2000) is True, 'doubled load must flag'\n"
                    "assert is_anomalous([1000], 5) is False, 'too little history'\n"
                    "assert is_anomalous([50, 50, 50], 50) is False\n"
                    "assert is_anomalous([50, 50, 50], 51) is True, 'zero variance: any deviation flags'\n"
                    "r = check_run(hist, 500)\n"
                    "assert r['anomalous'] is True and abs(r['mean'] - 1000) < 1e-9\n"
                    "assert check_run([10], 99) == {'anomalous': False, 'mean': None, 'std': None}\n"
                    "print('PASS: statistical gates — systemic failures caught by numbers')\n"
                ),
                "refresher": (
"**Row checks see trees; metric checks see the forest.** A file "
"delivered half-empty contains zero *invalid* rows — only the COUNT "
"is wrong, and only history makes 'wrong' definable:\n\n"
"```python\nm = sum(history) / len(history)\ns = math.sqrt(sum((x - m) ** 2 for x in history) / len(history))\nif s == 0:\n    return current != m\nreturn abs(current - m) > sigmas * s\n```\n\n"
"Three-sigma on a trailing window is the honest 80% solution: simple, "
"explainable ('today is 12σ below normal'), tunable via the window "
"and threshold. Its known blind spots — and the upgrades interviews "
"like hearing: weekly *seasonality* (Mondays differ from Sundays — "
"compare same-weekday windows), *trend* (growing tables drift the "
"mean — model the delta or use robust median/MAD), and *slow leaks* "
"(a 1%/day decline never trips 3σ — pair with week-over-week "
"checks). The min-history guard matters operationally: day-2 "
"pipelines alert on everything otherwise, and alert fatigue kills "
"quality systems faster than missing checks do. Same math monitors "
"sums, distinct counts, null rates, DLQ volume, latencies — one "
"function, your entire metric-health layer."
                ),
                "objectives": [
                    "Implement sigma-based anomaly gates with edge guards",
                    "Name the blind spots: seasonality, trend, slow leaks",
                    "Prioritize alert quality over check quantity",
                ],
                "hints": [
                    "len(history) < 3 → False immediately (and None stats in check_run).",
                    "Population std: divide by len, not len-1.",
                    "Zero std: any difference from the mean is anomalous.",
                ],
                "resources": [
                    {"title": "Monte Carlo: data observability pillars", "url": "https://www.montecarlodata.com/blog-what-is-data-observability/"},
                    {"title": "Statistical process control (the 3σ tradition)", "url": "https://en.wikipedia.org/wiki/Control_chart"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Design the data-quality strategy for a warehouse feeding both executive "
"dashboards and an ML feature store. What do you check, where, and what "
"happens on failure?"
                ),
                "difficulty": "Hard",
                "topics": ["data quality architecture", "SLAs"],
                "answer": (
"Layered checks at every boundary: **ingestion** — schema conformance, "
"parse-failure rates, file-level counts vs manifest (fail fast, "
"quarantine raw); **staging** — row-level suites (nulls, uniques, "
"ranges, FK integrity) plus metric anomalies (counts/sums vs history) "
"before the atomic swap to published tables; **transformation** — "
"grain assertions and reconciliation between layers (revenue in marts "
"== staging within tolerance); **serving** — freshness SLAs per table "
"and, for the feature store, distribution drift (PSI) between training "
"and serving features. Failure handling is *tiered by severity and "
"consumer*: blocking checks halt publication (dashboards prefer stale-"
"but-correct data — show yesterday with a banner); warning checks page "
"the owning team without halting; ML features degrade explicitly "
"(models fall back to defaults or hold last-known-good, never silently "
"train on breached data). Every check carries an owner, severity, and "
"runbook link — unowned alerts are noise generators."
                ),
                "explanation": (
"The design question rewards *boundary thinking* (checks at every "
"hand-off, validating both sides — the data-contract idea) and "
"*consumer-aware failure policy*: the insight that dashboards and "
"models want different degradation (stale-correct vs explicit-"
"fallback) elevates the answer above 'run Great Expectations'. "
"Stale-over-wrong as the default for human consumers is a strong, "
"defensible stance. Mentioning alert economics — owners, severities, "
"runbooks, and the mute-spiral of unowned checks — signals you've "
"operated one of these systems, which is precisely what the "
"interviewer is probing."
                ),
            },
            {
                "question": (
"Row counts passed, null checks passed — yet a bug shipped: every "
"order's amount was silently multiplied by 100 (cents vs dollars) for "
"three days. Which class of check catches this, and how do you design "
"it without drowning in false positives?"
                ),
                "difficulty": "Medium",
                "topics": ["anomaly detection", "unit errors"],
                "answer": (
"Distribution-level checks on *values*, not just presence: mean/median "
"order amount vs trailing history (a 100x shift is unmissable at even "
"loose thresholds), sum-of-amounts vs history, and cross-source "
"reconciliation (warehouse revenue vs the payment processor's "
"settlement totals — the strongest control, since it's an independent "
"system). Design against false positives: robust statistics (median/"
"MAD over mean/std — immune to a few whale orders), same-weekday "
"seasonal windows, warn-then-block thresholds (3σ warns, 6σ blocks "
"publication), and require N consecutive breaches before blocking on "
"noisy metrics. The cents-vs-dollars bug specifically argues for "
"*unit contracts* in the schema (amount_cents INT, never ambiguous "
"'amount') — naming conventions as a quality control, enforced at "
"code review."
                ),
                "explanation": (
"The scenario is a classic because it defeats every structural check — "
"the data is present, typed, unique, and in-range-ish; only its "
"*distribution* betrays it. Cross-system reconciliation is the "
"heavyweight answer (independent ground truth beats any statistical "
"cleverness) and payment data always has one. The unit-contract coda "
"— fixing the bug class at the schema level rather than detecting it "
"forever — is the kind of prevention-over-detection instinct that "
"closes interviews well. Robust stats and warn/block tiering show "
"you've tuned real alerting, not just read about it."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "stream-sim",
        "title": "Stream Simulator",
        "tagline": "Streaming concepts without Kafka: micro-batches, windows, exactly-once",
        "level": "Advanced",
        "tech": ["streaming", "micro-batching", "windowing", "consumer groups", "offsets"],
        "est_hours": 7,
        "brief": (
            "Streaming interviews test concepts, not Kafka trivia — so build "
            "the concepts. Using Redis lists as your 'topic' and Python "
            "consumers, implement the streaming canon: producers and consumer "
            "groups with offsets, micro-batch processing with checkpointing, "
            "tumbling/sliding window aggregations with watermarks (cl-2's "
            "ideas at second-granularity), and the at-least-once + idempotency "
            "dance that fakes exactly-once. Results land in the warehouse; "
            "lag lands on a dashboard."
        ),
        "milestones": [
            "Producer: a script emitting synthetic click events to a Redis list at a controllable rate (with occasional out-of-order timestamps — reality included).",
            "Consumer with offsets: BRPOP loop processing events, persisting its offset/checkpoint to Redis every batch; kill and restart it mid-stream — no loss, some redelivery (measure it).",
            "Micro-batch aggregator: tumbling 10-second windows of events-per-type written to warehouse upserts keyed by (window_start, type) — rerun-safe by construction.",
            "Watermark + allowed lateness: hold windows open for late events up to L seconds; count events dropped beyond L; tune L against your producer's disorder.",
            "Consumer lag monitoring: track produced-offset minus consumed-offset over time; throttle the producer up and watch lag grow, then scale to two consumers (a second list = partition) and watch it drain.",
        ],
        "under_the_hood": (
            "**A log, not a queue:** Kafka-style streaming is an append-only, "
            "offset-addressed log per partition. Consumers own their read "
            "position (offset) and commit it as a checkpoint — deleting "
            "nothing (retention handles that). Everything follows from this: "
            "replay = rewind the offset; consumer groups = partitions divided "
            "among members; ordering = guaranteed per partition only (key "
            "choice = ordering domain, ss-1's hash partitioning yet again).\n\n"
            "**Delivery semantics are offset-commit timing:** commit-then-"
            "process = at-most-once (crash loses the in-flight batch); "
            "process-then-commit = at-least-once (crash redelivers — cl-1's "
            "watermark ordering, identically). 'Exactly-once' in practice = "
            "at-least-once + idempotent/transactional sinks (upserts keyed "
            "by (window, key), or Kafka's transactional offset+output "
            "commit). Say those words in an interview and watch faces "
            "relax.\n\n"
            "**Windows + watermarks tame unbounded time:** tumbling/sliding/"
            "session windows bucket the infinite stream; the watermark "
            "('no events older than T expected') decides when a window can "
            "*close* and emit. Allowed lateness trades completeness against "
            "latency — the same overlap-window economics as batch CDC, "
            "compressed from hours to seconds. Batch is streaming with big "
            "windows; internalize that and both worlds share one theory."
        ),
        "exercises": [
            {
                "id": "sm-1",
                "title": "Offset semantics: pick your guarantee",
                "instructions": (
"The commit-timing decision, made tangible.\n\n**Your task**\n\nImplement "
"`consume(log, state, process, commit_first)`: log is a list (the "
"topic); state = {'offset': n} (start 0 if missing); process(record) "
"handles one record (may raise!). Loop from the offset: if "
"commit_first, advance state['offset'] BEFORE process(record); else "
"after. On any exception stop and return {'processed': n_ok, "
"'offset': current}. The checker crashes processing at record 2 under "
"both modes and verifies: commit_first loses the record; process-first "
"redelivers it on resume."
                ),
                "starter_code": (
                    "def consume(log, state, process, commit_first):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "def crashing(rec):\n"
                    "    if rec == 'c':\n"
                    "        raise RuntimeError('boom')\n"
                    "    done.append(rec)\n"
                    "log = ['a', 'b', 'c', 'd']\n"
                    "done, state = [], {}\n"
                    "r = consume(log, state, crashing, commit_first=True)\n"
                    "assert done == ['a', 'b'] and state['offset'] == 3, 'offset committed past the crash!'\n"
                    "done2 = []\n"
                    "def ok(rec): done2.append(rec)\n"
                    "consume(log, state, ok, commit_first=True)\n"
                    "assert done2 == ['d'], 'at-most-once: c is LOST forever'\n"
                    "done, state = [], {}\n"
                    "consume(log, state, crashing, commit_first=False)\n"
                    "assert state['offset'] == 2, 'offset must NOT pass the failed record'\n"
                    "done3 = []\n"
                    "consume(log, state, lambda r: done3.append(r), commit_first=False)\n"
                    "assert done3 == ['c', 'd'], 'at-least-once: c is redelivered'\n"
                    "print('PASS: at-most-once vs at-least-once — one line of ordering apart')\n"
                ),
                "refresher": (
"**The whole distributed-delivery debate is two lines swapped:**\n\n"
"```python\nwhile offset < len(log):\n    if commit_first:\n        state['offset'] = offset + 1   # commit... \n        process(log[offset])            # ...then process = AT-MOST-ONCE\n    else:\n        process(log[offset])            # process...\n        state['offset'] = offset + 1   # ...then commit = AT-LEAST-ONCE\n    offset += 1\n```\n\n"
"Crash between the two lines and the difference materializes: "
"committed-but-unprocessed = a hole (acceptable for metrics ticks, "
"fatal for orders); processed-but-uncommitted = a rerun (harmless IF "
"processing is idempotent — the ww-3/cl-1/oi-2 chorus, now at "
"per-record granularity). There is no third ordering: 'exactly-once "
"delivery' over a network is impossible (the Two Generals problem); "
"what vendors sell as exactly-once is at-least-once delivery + "
"deduplicating/transactional *processing* — Kafka commits offsets and "
"outputs in one transaction, your warehouse upsert dedups by key. In "
"interviews, deriving the semantics from commit ordering (rather than "
"reciting definitions) and then naming the idempotency escape hatch "
"is the complete answer, every time."
                ),
                "objectives": [
                    "Derive delivery semantics from offset-commit ordering",
                    "Stop the loop cleanly on failure with honest state",
                    "Explain why exactly-once = at-least-once + idempotent sinks",
                ],
                "hints": [
                    "Read the current offset with state.get('offset', 0); loop while it's < len(log).",
                    "The ONLY difference between modes is whether the offset write precedes process().",
                    "except around process: return immediately with counts; don't advance past a failure in process-first mode.",
                ],
                "resources": [
                    {"title": "Kafka: consumer offsets & delivery semantics", "url": "https://kafka.apache.org/documentation/#semantics"},
                    {"title": "You Cannot Have Exactly-Once Delivery (classic essay)", "url": "https://bravenewgeek.com/you-cannot-have-exactly-once-delivery/"},
                ],
            },
            {
                "id": "sm-2",
                "title": "Tumbling windows with allowed lateness",
                "instructions": (
"The streaming aggregation core.\n\n**Your task**\n\nImplement "
"`window_count(events, size, lateness)`: events are (ts, key) tuples "
"in arrival order (ts may be out of order!). Tumbling windows: "
"window_start = (ts // size) * size. Maintain a watermark = max ts "
"seen so far; an arriving event is **dropped** if its window has "
"closed — i.e. if `watermark >= window_end + lateness` at arrival "
"time (using the watermark BEFORE updating it with this event). "
"Return ({(window_start, key): count}, dropped_count)."
                ),
                "starter_code": (
                    "def window_count(events, size, lateness):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "events = [(1, 'a'), (3, 'a'), (12, 'b'), (5, 'a'), (23, 'b'), (2, 'a')]\n"
                    "counts, dropped = window_count(events, size=10, lateness=5)\n"
                    "# ts=5 arrives with watermark 12 < 10+5 -> accepted into [0,10)\n"
                    "# ts=2 arrives with watermark 23 >= 10+5 -> DROPPED\n"
                    "assert counts == {(0, 'a'): 3, (10, 'b'): 1, (20, 'b'): 1}, counts\n"
                    "assert dropped == 1\n"
                    "c2, d2 = window_count([(1, 'x'), (2, 'x')], size=10, lateness=0)\n"
                    "assert c2 == {(0, 'x'): 2} and d2 == 0\n"
                    "print('PASS: windows + watermark + lateness — the streaming triangle')\n"
                ),
                "refresher": (
"**Event time vs processing time is THE streaming distinction:** "
"events carry when they *happened* (ts); they arrive when networks "
"deign to deliver them. Windows bucket by event time; the watermark — "
"here the simple max-ts heuristic — tracks how far event time has "
"provably progressed:\n\n"
"```python\nwatermark = float('-inf')\nfor ts, key in events:\n    start = (ts // size) * size\n    if watermark >= start + size + lateness:\n        dropped += 1                      # window closed: too late\n    else:\n        counts[(start, key)] = counts.get((start, key), 0) + 1\n    watermark = max(watermark, ts)        # AFTER the check\n```\n\n"
"The check-before-update ordering is the subtle beat (an event can't "
"close its own window), and `(ts // size) * size` is the tumbling-"
"window bucketing one-liner worth memorizing. The triangle of tensions "
"this encodes — **latency** (close windows fast) vs **completeness** "
"(wait for stragglers) vs **state size** (open windows cost memory) — "
"is the entire design space of streaming systems; lateness is the "
"dial. Real engines (Flink/Beam) add per-partition watermarks, "
"idle-source handling, and side-outputs for the dropped (your DLQ, "
"again) — but this loop IS their semantic core, and being able to "
"write it cold is a streaming-interview trump card."
                ),
                "objectives": [
                    "Bucket by event time with floor-division windowing",
                    "Maintain watermarks and enforce lateness on arrival",
                    "Articulate the latency/completeness/state triangle",
                ],
                "hints": [
                    "window_start = (ts // size) * size; closed when watermark >= start + size + lateness.",
                    "Check with the OLD watermark, then update it with max().",
                    "Dropped events increment the counter and touch nothing else.",
                ],
                "resources": [
                    {"title": "Streaming 101 & 102 (Akidau — the canonical essays)", "url": "https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/"},
                    {"title": "Flink: event time & watermarks", "url": "https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Kafka fundamentals rapid-fire: why are partitions the unit of "
"parallelism, what does message key choice control, and what happens "
"when a consumer group rebalances?"
                ),
                "difficulty": "Medium",
                "topics": ["Kafka", "partitioning", "consumer groups"],
                "answer": (
"**Partitions** are independent append-only logs; each is consumed by "
"exactly one member of a consumer group, so max useful consumers = "
"partition count — parallelism is fixed at topic design time (resizing "
"later breaks key→partition mapping for existing data). **Key choice** "
"controls two things at once: ordering (guaranteed only within a "
"partition, so all events for user X sharing a key preserve X's "
"order) and load distribution (hash(key) % partitions — a hot key = a "
"hot partition = a capped consumer, ss-1's skew in streaming "
"clothes). **Rebalance**: membership change (join/leave/crash/"
"slow-heartbeat) triggers partition reassignment; classic eager "
"rebalancing stops the world (all consumers pause, offsets commit, "
"partitions reassign — a latency spike), cooperative/incremental "
"protocols move only the necessary partitions. Frequent rebalances "
"from slow processing (max.poll exceeded) are the most common "
"production pathology — fix batch sizes, not heartbeats."
                ),
                "explanation": (
"Three questions that together test whether Kafka is a mental model "
"or a logo on a resume. The connecting insight to voice: partition = "
"ordering domain = parallelism unit = failure domain — one concept "
"wearing four hats, and key choice is where you spend it. Skew "
"transfer from batch knowledge (hot keys stall stages ⇄ hot "
"partitions stall consumers) demonstrates the transferable-theory "
"thinking this curriculum builds. On rebalances, naming the "
"slow-consumer→rebalance death spiral and its real fix shows "
"operations scar tissue interviewers trust."
                ),
            },
            {
                "question": (
"Design a real-time 'orders per minute per region' dashboard fed by an "
"order event stream, end to end. Address late events, exactly-once "
"display, and what happens during a 10-minute pipeline outage."
                ),
                "difficulty": "Hard",
                "topics": ["streaming design", "windows", "recovery"],
                "answer": (
"Pipeline: orders topic (keyed by region for per-region ordering) → "
"stream processor computing 1-minute tumbling windows per region "
"(event-time, watermark = max-ts minus observed disorder, allowed "
"lateness ~2min with *window re-emission on late updates*) → sink "
"upserts to a serving table keyed by (window_start, region) — "
"at-least-once processing + keyed upsert = correct display regardless "
"of retries (effective exactly-once). Dashboard reads the table; "
"late-updated windows simply overwrite. Outage story: the topic "
"retains events (a log, not a queue), consumer offsets froze at the "
"crash point; on restart the processor replays from committed offsets "
"— windows recompute identically, upserts converge, the dashboard "
"backfills the gap in seconds; only *display latency* suffered, never "
"correctness. Monitoring: consumer lag (the outage's live signature), "
"watermark lag, and late-drop counts."
                ),
                "explanation": (
"A synthesis question — every piece is one you've built: keyed "
"partitioning (ordering per region), sm-2's windows/watermark/"
"lateness, sm-1's semantics resolved by the idempotent keyed sink, "
"cl-1's replay-safety. The outage answer is where candidates separate: "
"log retention + offset replay + convergent upserts means the system "
"*heals by re-running its normal path* — no special recovery code — "
"and articulating that 'correctness was never at risk, only "
"freshness' is the exact sentence interviewers hope to hear. "
"Re-emission of late windows (update-in-place dashboards) vs "
"append-only emission is a subtle fork worth raising unprompted."
                ),
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Stage 7 addition: Lakehouse Lite  +  Stage 8 addition: Airflow Pro
# ---------------------------------------------------------------------------

STAGE78_PROJECTS = [
    {
        "id": "lakehouse-lite",
        "title": "Lakehouse Lite",
        "tagline": "Medallion architecture: Spark + Parquet lake + warehouse serving",
        "level": "Advanced",
        "tech": ["medallion (bronze/silver/gold)", "partitioned Parquet", "Spark JDBC", "incremental merges"],
        "est_hours": 9,
        "brief": (
            "Assemble the modern default architecture: raw events land in a "
            "bronze Parquet lake (partitioned by date), Spark curates them "
            "into deduplicated, validated silver tables, gold aggregates "
            "serve business questions — and the gold layer syncs to your "
            "Postgres warehouse over JDBC for dashboards. You'll implement "
            "incremental merge logic by hand (what Delta/Iceberg automate) "
            "and feel exactly which problems those table formats exist to "
            "solve."
        ),
        "milestones": [
            "Bronze: your Stream Simulator / pipeline events written as-is to workspace/lake/bronze/events/date=YYYY-MM-DD/*.parquet — append-only, schema-on-read, hive-partitioned.",
            "Silver: a Spark job reading bronze partitions, deduplicating by event_id (wf dedup idiom), validating (qg checks as Spark filters), writing partitioned silver — rerunnable per-partition (overwrite that date only: dynamic partition overwrite).",
            "Gold: daily revenue/activity aggregates from silver; write parquet AND to warehouse.gold_daily via spark.write.jdbc (the driver jar is preinstalled in your Jupyter image).",
            "Incremental: process only bronze partitions newer than the silver watermark (cl-1 at partition granularity); prove a late-arriving bronze file for an old date triggers exactly that date's silver rebuild.",
            "Break concurrent writes: run two silver jobs on the same date simultaneously, observe the mess (partial files, double data), then write up how Delta/Iceberg's transaction log prevents it — the 'why table formats exist' essay, from experience.",
        ],
        "under_the_hood": (
            "**Medallion is refinement with receipts:** bronze = the "
            "immutable, replayable log of what arrived (ELT's 'keep raw' "
            "argument as a layer); silver = cleaned, deduplicated, "
            "conformed entities (your quality gates as code); gold = "
            "consumption-shaped aggregates (star-schema thinking). Fix a "
            "silver bug → rebuild from bronze; every layer is a pure "
            "function of the one below — functional programming at "
            "architecture scale.\n\n"
            "**Partition-as-unit-of-work** is the operational key: "
            "date-partitioned data makes 'reprocess 2026-07-25' a targeted, "
            "idempotent, parallelizable operation (overwrite one directory) "
            "— mm-2's batched backfill philosophy with directories as "
            "batches. Partition pruning (dt-2) makes reads cheap for the "
            "same reason writes are safe.\n\n"
            "**What plain Parquet can't do** — and you'll experience each: "
            "no atomic multi-file commits (concurrent writers corrupt), no "
            "row-level updates/deletes (rewrite whole partitions), no "
            "schema evolution safety, no time travel. Delta Lake and "
            "Iceberg add a transaction log over the files (versioned "
            "manifests, optimistic concurrency, snapshot isolation) — "
            "MVCC's ideas (pw-2) rebuilt on object storage. You'll have "
            "earned exactly why they exist, which beats knowing their "
            "APIs."
        ),
        "exercises": [
            {
                "id": "ll-1",
                "title": "Partition planner (incremental at the file level)",
                "instructions": (
"The lakehouse scheduling core.\n\n**Your task**\n\nImplement "
"`plan_work(bronze_partitions, silver_state)`: bronze_partitions maps "
"date-string → latest_file_ts (int, when its newest file landed); "
"silver_state maps date-string → processed_ts (when silver last built "
"it; missing = never). Return the sorted list of dates needing "
"(re)processing: never-processed dates, plus dates where "
"latest_file_ts > processed_ts (late files landed after the build). "
"This one function is 'incremental lakehouse' in miniature."
                ),
                "starter_code": (
                    "def plan_work(bronze_partitions, silver_state):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "bronze = {'2026-07-25': 100, '2026-07-26': 200, '2026-07-27': 300}\n"
                    "silver = {'2026-07-25': 150, '2026-07-26': 150}\n"
                    "work = plan_work(bronze, silver)\n"
                    "assert work == ['2026-07-26', '2026-07-27'], work\n"
                    "# late file for the 25th arrives:\n"
                    "bronze['2026-07-25'] = 400\n"
                    "assert plan_work(bronze, silver) == ['2026-07-25', '2026-07-26', '2026-07-27']\n"
                    "assert plan_work({}, {}) == []\n"
                    "assert plan_work({'d': 5}, {'d': 5}) == [], 'equal ts = already processed'\n"
                    "print('PASS: partition-level incremental planning — the lakehouse scheduler')\n"
                ),
                "refresher": (
"**Watermarks per partition, not per stream:** cl-1 tracked one "
"cursor; a lake tracks one per partition, and 'needs work' is a "
"comparison join between two dicts:\n\n"
"```python\nreturn sorted(\n    d for d, file_ts in bronze_partitions.items()\n    if d not in silver_state or file_ts > silver_state[d]\n)\n```\n\n"
"The elegance: late data STOPS being a special case. A file landing "
"in an old date's directory bumps that partition's latest_file_ts → "
"the planner flags exactly that date → the silver job rebuilds one "
"directory (idempotent overwrite). Compare with the stream version's "
"anxiety about windows and lateness bounds — at batch granularity, "
"late data is just... Tuesday. This is why lakehouse + daily/hourly "
"partitions remains the sane default for most analytics, with true "
"streaming reserved for genuinely low-latency needs.\n\n"
"Production notes: real systems get latest_file_ts from object-store "
"listings or manifest logs (Delta/Iceberg make it transactional); "
"processed_ts must be written AFTER the silver commit (cl-1's "
"ordering, always); and the sorted() output is your Airflow dynamic "
"task list — each date fans out as an independent, parallel, "
"retryable task (oi-3's scheduler, meeting real work)."
                ),
                "objectives": [
                    "Implement per-partition watermark comparison",
                    "Explain why partitioning turns late data into routine rebuilds",
                    "Feed work plans into orchestrators as dynamic parallel tasks",
                ],
                "hints": [
                    "A date needs work if absent from silver_state OR bronze ts strictly greater.",
                    "One comprehension + sorted() — resist overengineering.",
                ],
                "resources": [
                    {"title": "Delta Lake: how transaction logs work", "url": "https://docs.delta.io/latest/delta-intro.html"},
                    {"title": "Spark: dynamic partition overwrite", "url": "https://spark.apache.org/docs/latest/sql-data-sources-parquet.html"},
                ],
            },
            {
                "id": "ll-2",
                "title": "Merge-into, by hand",
                "instructions": (
"The operation Delta/Iceberg made famous — implement its semantics.\n\n"
"**Your task**\n\nImplement `merge_into(target, updates, key)`: both are "
"lists of dicts. For each update: matching target row (same key value) "
"→ replace it IN PLACE (position preserved); no match → append. Multiple "
"updates to the same key apply in order (last wins). Return (updated_count, "
"inserted_count). This is UPSERT at the dataset level — what "
"`MERGE INTO silver USING updates ON ...` compiles to."
                ),
                "starter_code": (
                    "def merge_into(target, updates, key):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "target = [{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'b'}, {'id': 3, 'v': 'c'}]\n"
                    "u, i = merge_into(target, [{'id': 2, 'v': 'B'}, {'id': 4, 'v': 'd'}, {'id': 2, 'v': 'B2'}], 'id')\n"
                    "assert (u, i) == (2, 1), (u, i)\n"
                    "assert target == [{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'B2'}, {'id': 3, 'v': 'c'}, {'id': 4, 'v': 'd'}]\n"
                    "u2, i2 = merge_into([], [{'id': 9, 'v': 'x'}], 'id')\n"
                    "assert (u2, i2) == (0, 1)\n"
                    "print('PASS: MERGE semantics — the heart of every table format')\n"
                ),
                "refresher": (
"**Index-then-merge** (ss-2's broadcast join, mutating edition):\n\n"
"```python\npos = {row[key]: idx for idx, row in enumerate(target)}\nupdated = inserted = 0\nfor u in updates:\n    if u[key] in pos:\n        target[pos[u[key]]] = u\n        updated += 1\n    else:\n        pos[u[key]] = len(target)     # future updates hit the new row!\n        target.append(u)\n        inserted += 1\n```\n\n"
"The subtle line is registering appended rows in the index — the "
"checker's double-update-same-key case ('id 2 twice', and would-be "
"'insert then update id 4') breaks naive versions. Counting updated "
"vs inserted mirrors real MERGE output metrics, which ops teams "
"watch (a suddenly-all-inserts merge means your join key broke).\n\n"
"Now the punchline this project builds to: on plain Parquet, this "
"cheap in-memory operation is *impossible in place* — files are "
"immutable, so merging means rewrite-the-partition (your milestone "
"experience). Delta/Iceberg's MERGE INTO does copy-on-write (rewrite "
"only affected files) or merge-on-read (log deltas, reconcile at "
"query time) with an atomic manifest swap — and choosing between "
"those modes IS the modern lakehouse performance interview. You've "
"implemented the semantics; the formats implement the durability."
                ),
                "objectives": [
                    "Implement MERGE semantics with a live position index",
                    "Handle sequential updates hitting freshly-inserted keys",
                    "Map hand-rolled merge onto copy-on-write vs merge-on-read",
                ],
                "hints": [
                    "Build {key_value: position} first; enumerate(target).",
                    "On insert: append AND add to the index at the new position.",
                    "Replace the whole row on update (assignment, not .update()).",
                ],
                "resources": [
                    {"title": "Delta Lake MERGE INTO", "url": "https://docs.delta.io/latest/delta-update.html#merge-into"},
                    {"title": "Iceberg: copy-on-write vs merge-on-read", "url": "https://iceberg.apache.org/docs/latest/configuration/#write-properties"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Why did table formats (Delta Lake, Iceberg, Hudi) become the center "
"of the modern data platform? Answer from the failure modes of a plain "
"Parquet lake."
                ),
                "difficulty": "Medium",
                "topics": ["table formats", "lakehouse"],
                "answer": (
"Plain Parquet-on-object-storage fails at: **atomicity** — a job "
"writing 200 files that dies at 120 leaves readers seeing a torn "
"state, and two concurrent writers to one partition interleave "
"corruptly (no rename-based commit on S3); **mutations** — GDPR "
"deletes or CDC upserts require rewriting whole partitions manually; "
"**consistent reads** — a query listing files mid-write reads a "
"moving target; **schema evolution** — nothing stops a producer "
"writing incompatible files into the same directory; **performance "
"metadata** — listing millions of files for planning is itself slow. "
"Table formats fix all five with one move: a transaction log of "
"versioned manifests over immutable files — writers commit a new "
"manifest atomically (optimistic concurrency), readers pin a "
"snapshot (isolation + time travel), MERGE/DELETE become logged file "
"rewrites, schema lives in the log and evolves with rules, and "
"planning reads manifests instead of listing storage."
                ),
                "explanation": (
"The question rewards deriving the solution from felt pain rather "
"than listing features — which is literally this project's milestone "
"5. The unifying insight to state: it's MVCC and WAL (pw-2!) "
"rebuilt over object storage — databases and lakes converged on the "
"same concurrency answers because the problems are the same. Time "
"travel falls out free (old manifests = old snapshots), which also "
"gives reproducible ML training sets — a cross-stage connection "
"worth making. If asked to choose between formats: Iceberg's "
"engine-neutral spec vs Delta's Spark-native maturity; the honest "
"answer is 'whichever your platform's engines support best' — "
"they're converging fast."
                ),
            },
            {
                "question": (
"Your silver-layer Spark job reprocesses a full day's partition on "
"every late file, and late files arrive for ~10 old dates daily — "
"burning 4 hours of cluster time on mostly-unchanged data. Options?"
                ),
                "difficulty": "Hard",
                "topics": ["incremental processing", "optimization"],
                "answer": (
"Escalating options: **(1) Shrink the unit** — partition silver by "
"hour instead of day: late files trigger 1/24th the rebuild (works "
"if late files cluster in recent hours — measure first). **(2) True "
"merge instead of rebuild** — adopt a table format and MERGE only "
"the late file's rows into silver (copy-on-write rewrites just "
"affected files); requires stable dedup keys, which you have "
"(event_id). **(3) Change-aware skipping** — if late files are "
"often duplicate redeliveries, hash file contents and skip "
"already-seen files before scheduling any rebuild (mm-1's ledger "
"on file checksums). **(4) Lateness budget** — hold bronze→silver "
"for high-churn recent dates (process D-1 at noon instead of "
"midnight), converting straggler storms into one planned pass — the "
"cl-2 window trade at scheduling granularity. Usually the winning "
"combo is 2+3: merge semantics for genuine late data, dedup "
"skipping for redeliveries."
                ),
                "explanation": (
"A cost-optimization scenario testing whether 'idempotent partition "
"rebuild' (correct and simple) can be refined when its economics "
"break. Each option trades along a different axis — granularity, "
"machinery, dedup, latency — and the interviewer wants axes named "
"before tools. The measure-first instinct (are late files new data "
"or redelivery? do they cluster?) separates engineers from "
"pattern-appliers, and connecting the lateness budget to your "
"streaming/CDC windows shows the unified theory this curriculum "
"keeps building: it's all watermarks and overlap, at every "
"timescale."
                ),
            },
        ],
    },
    {
        "id": "airflow-pro",
        "title": "Airflow Pro",
        "tagline": "Production orchestration: dynamic DAGs, sensors, backfills, SLAs",
        "level": "Advanced",
        "tech": ["dynamic task mapping", "sensors", "XCom", "backfills", "SLAs", "pools"],
        "est_hours": 9,
        "brief": (
            "Beyond the capstone's first DAG: run Airflow like a platform. "
            "Orchestrate your REAL stack — the Mongo→Postgres pipeline "
            "library, quality gates, lakehouse partition planner — with "
            "dynamic task mapping (one task per partition, ll-1's plan as "
            "the input!), sensors that wait for data instead of guessing, "
            "cross-DAG dependencies, controlled backfills, and the "
            "operational controls (pools, SLAs, retries with backoff) that "
            "keep 200-DAG installations sane."
        ),
        "milestones": [
            "Dynamic task mapping: a DAG that calls your ll-1 plan_work, then .expand()s a process_partition task over the result — 0 late dates = 0 tasks, 10 = 10 parallel, watch the Grid view morph per run.",
            "Sensors done right: replace a schedule-guess with a deferrable-style sensor polling for the day's Mongo data (or bronze file) before the pipeline runs; set a timeout + on-timeout alert instead of infinite waiting.",
            "XCom hygiene: pass the run's watermark and row counts between tasks via XCom; then deliberately try passing a DataFrame and read the serialization error — metadata through XCom, data through storage. Write the rule on a sticky note.",
            "Backfill a schema change: after adding a column to fact_reviews, run `airflow dags backfill -s ... -e ...` for 30 logical dates; use pools to cap warehouse-hitting concurrency at 4 while backfill and daily runs coexist.",
            "Platform hygiene: add SLAs (silver by 06:00), retries with exponential backoff + jitter on flaky tasks, an on_failure_callback posting to a (file-based) alert log, and a cross-DAG dependency (gold waits on silver's dataset) — the full production seasoning.",
        ],
        "under_the_hood": (
            "**Dynamic task mapping** is oi-3's insight industrialized: the "
            "DAG *structure* can depend on runtime data. expand() creates "
            "task instances per input element at scheduling time — your "
            "partition planner literally becomes the task list, each "
            "retryable and parallelizable independently. (Pre-2.3 Airflow "
            "generated tasks by writing loops in DAG files — parse-time "
            "dynamism, brittle and slow; knowing the difference is an "
            "interview marker.)\n\n"
            "**Sensors vs schedules** is data-awareness vs clock-guessing: "
            "'run at 3am and hope the file landed' fails monthly; 'wait "
            "for the file, timeout at 6am, page on timeout' states the "
            "actual dependency. Deferrable operators solve the cost "
            "problem — a waiting sensor yields its worker slot to the "
            "triggerer's event loop (dd-3's async, running your "
            "orchestrator) instead of burning a process on sleep().\n\n"
            "**XCom discipline:** XComs live in the metadata DB, serialized "
            "— they're for watermarks, counts, file paths, run decisions "
            "(kilobytes), never datasets. Data flows through storage; "
            "*references* flow through XCom. Violating this is the most "
            "common Airflow anti-pattern in the wild. **Pools/priorities** "
            "are the multi-tenant controls: cap concurrent warehouse "
            "connections across ALL dags (the pw deadlock lesson as "
            "config), and let the backfill and the daily run share "
            "politely. Datasets (data-aware scheduling) replace fragile "
            "cross-DAG ExternalTaskSensors with producer-consumer edges — "
            "small graphs composed, not monoliths grown."
        ),
        "exercises": [
            {
                "id": "ap-1",
                "title": "Dynamic mapping executor",
                "instructions": (
"expand() semantics, implemented.\n\n**Your task**\n\nImplement "
"`run_mapped(items, task_fn, max_active)`: execute task_fn(item) for "
"each item with at most max_active 'concurrently' — simulate with "
"waves: process items in chunks of max_active, collecting results "
"per wave (call order within a wave follows item order). Any item "
"raising → record ('failed', str(e)) for it, others in the wave "
"continue. Return list of ('ok', result) / ('failed', error) tuples "
"in item order. Empty items → empty list (the zero-tasks case that "
"makes mapping elegant)."
                ),
                "starter_code": (
                    "def run_mapped(items, task_fn, max_active=4):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "calls = []\n"
                    "def work(d):\n"
                    "    calls.append(d)\n"
                    "    if d == '2026-07-26':\n"
                    "        raise ValueError('bad partition')\n"
                    "    return f'built {d}'\n"
                    "out = run_mapped(['2026-07-25', '2026-07-26', '2026-07-27'], work, max_active=2)\n"
                    "assert out[0] == ('ok', 'built 2026-07-25')\n"
                    "assert out[1][0] == 'failed' and 'bad partition' in out[1][1]\n"
                    "assert out[2] == ('ok', 'built 2026-07-27'), 'one failure must not sink the wave'\n"
                    "assert calls == ['2026-07-25', '2026-07-26', '2026-07-27']\n"
                    "assert run_mapped([], work) == []\n"
                    "print('PASS: expand() semantics — per-item isolation, bounded concurrency')\n"
                ),
                "refresher": (
"**Waves = a poor engineer's semaphore:**\n\n"
"```python\nresults = []\nfor start in range(0, len(items), max_active):\n    for item in items[start:start + max_active]:\n        try:\n            results.append(('ok', task_fn(item)))\n        except Exception as e:\n            results.append(('failed', str(e)))\nreturn results\n```\n\n"
"The two properties this models — and why mapped tasks beat a loop "
"inside ONE task (the anti-pattern this exercise retires): "
"**per-item isolation** (partition 26 failing doesn't abort 27; in "
"real Airflow each mapped instance retries independently, and "
"'retry only the failed ones' is exactly what a monolithic loop "
"task can't do) and **bounded concurrency** (max_active_tis_per_dag "
"/ pools protect the warehouse from 30 simultaneous backfill "
"connections — the resource governance that separates platforms "
"from scripts). The zero-item case returning [] cleanly is mapping's "
"quiet elegance: 'no late partitions' needs no special-case code "
"anywhere.\n\n"
"In real Airflow this is `process.expand(date=plan_work_task)` — "
"the planner task's XCom (a small list — proper XCom hygiene) "
"becomes the mapping input, and the Grid view shows N instances. "
"Your simulation is the semantic contract that API keeps."
                ),
                "objectives": [
                    "Implement per-item isolation with bounded concurrency waves",
                    "Argue mapped-tasks vs loop-in-one-task for retries and visibility",
                    "Keep mapping inputs XCom-small (references, not data)",
                ],
                "hints": [
                    "Chunk with range(0, len, max_active); slice items per wave.",
                    "try/except INSIDE the inner loop — around one item only.",
                    "Failures record str(e); order is just item order.",
                ],
                "resources": [
                    {"title": "Airflow: dynamic task mapping", "url": "https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/dynamic-task-mapping.html"},
                    {"title": "Airflow pools", "url": "https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/pools.html"},
                ],
            },
            {
                "id": "ap-2",
                "title": "Sensor with timeout and backoff",
                "instructions": (
"Wait for data like a grown-up.\n\n**Your task**\n\nImplement "
"`sensor_wait(check_fn, timeout, poke_interval, clock)`: poll "
"check_fn() at t=0, then every poke_interval, using the provided "
"`clock` dict {'t': 0} as simulated time (advance clock['t'] += "
"poke_interval after each failed poke). Success → return {'found': "
"True, 'pokes': n, 'waited': clock['t']}. If the NEXT poke would "
"occur at t > timeout → return {'found': False, ...} instead of "
"poking forever. check_fn exceptions count as failed pokes (sensors "
"survive flaky checks)."
                ),
                "starter_code": (
                    "def sensor_wait(check_fn, timeout, poke_interval, clock):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "attempts = {'n': 0}\n"
                    "def ready_on_third():\n"
                    "    attempts['n'] += 1\n"
                    "    if attempts['n'] == 3:\n"
                    "        return True\n"
                    "    raise IOError('not yet')   # flaky check: exception = not ready\n"
                    "clock = {'t': 0}\n"
                    "r = sensor_wait(ready_on_third, timeout=100, poke_interval=10, clock=clock)\n"
                    "assert r == {'found': True, 'pokes': 3, 'waited': 20}, r\n"
                    "clock2 = {'t': 0}\n"
                    "r2 = sensor_wait(lambda: False, timeout=25, poke_interval=10, clock=clock2)\n"
                    "assert r2['found'] is False and r2['pokes'] == 3, r2   # pokes at 0,10,20; next would be 30>25\n"
                    "print('PASS: bounded waiting — sensors that page instead of hanging')\n"
                ),
                "refresher": (
"**A sensor is a retry loop wearing a scheduler costume** (ww-2, "
"third appearance):\n\n"
"```python\npokes = 0\nwhile True:\n    pokes += 1\n    try:\n        ok = check_fn()\n    except Exception:\n        ok = False                      # flaky check ≠ ready\n    if ok:\n        return {'found': True, 'pokes': pokes, 'waited': clock['t']}\n    if clock['t'] + poke_interval > timeout:\n        return {'found': False, 'pokes': pokes, 'waited': clock['t']}\n    clock['t'] += poke_interval\n```\n\n"
"The timeout check *before* advancing (would the next poke overrun?) "
"is the loop's precision point — the checker's 0/10/20-then-stop "
"case. Clock injection (cm-1's lesson) makes a time-based component "
"testable in microseconds.\n\n"
"Why bounded waiting is a *reliability* feature, not politeness: an "
"infinite sensor converts 'upstream is late' into 'downstream "
"silently never ran' — invisible until someone misses the data. "
"Timeout + on-timeout alert converts it into a page with a name "
"attached ('partner file 4 hours late'), which is an SLA "
"conversation. Real Airflow adds mode='reschedule' (release the "
"worker slot between pokes) and deferrable sensors (async event "
"loop, thousands of waits per triggerer process) — the resource "
"story behind the same loop. Exceptions-as-not-ready keeps S3 "
"blips from failing the sensor task — but count them; a 100%-"
"exception sensor is a permissions bug wearing a lateness mask."
                ),
                "objectives": [
                    "Implement poke loops with precise timeout boundaries",
                    "Treat check exceptions as not-ready while staying observable",
                    "Explain reschedule/deferrable modes as worker-economics",
                ],
                "hints": [
                    "Poke first (at t=0), then decide whether the next poke fits within timeout.",
                    "try/except around check_fn; exception = failed poke, not failed sensor.",
                    "Only advance clock['t'] after a failed poke that will retry.",
                ],
                "resources": [
                    {"title": "Airflow: sensors & deferrable operators", "url": "https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/deferring.html"},
                    {"title": "Airflow: sensor modes (poke vs reschedule)", "url": "https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/sensors/base/index.html"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"An Airflow installation has 300 DAGs and the scheduler is 'slow': "
"tasks sit queued for minutes, the UI lags, and one team's backfill "
"starved everyone yesterday. Diagnose and fix like a platform owner."
                ),
                "difficulty": "Hard",
                "topics": ["Airflow operations", "scheduling", "multi-tenancy"],
                "answer": (
"Separate the three symptoms: **(1) Parse latency** — 300 DAG files "
"re-parsed continuously; top-level code doing imports/DB "
"calls/config fetches multiplies it (the classic killer). Fix: audit "
"top-level code (nothing heavy outside task functions), raise "
"min_file_process_interval, shard files across DAG processors. "
"**(2) Task queuing** — check executor saturation: parallelism, "
"max_active_tasks_per_dag, pool limits, and executor slots "
"(Celery workers / K8s quota); queued-but-unpicked tasks with idle "
"workers usually means pool exhaustion or a priority inversion. "
"**(3) The starving backfill** — multi-tenancy controls: per-team "
"pools capping shared-resource concurrency (warehouse connections!), "
"priority_weight favoring SLA-bound dailies over backfills, and "
"backfill-specific max_active_runs. Structural fixes beyond tuning: "
"datasets over ExternalTaskSensors (sensors burn slots), deferrable "
"operators for all waits, and metadata-DB health (it's a Postgres — "
"pw-2's VACUUM story applies to Airflow itself)."
                ),
                "explanation": (
"Platform questions grade decomposition: three distinct subsystems "
"(parser, executor, resource governance) produce superficially "
"similar 'slowness', and the fix lists differ entirely. The "
"top-level-code parse trap is THE Airflow-at-scale war story — "
"naming it first signals real operation. The multi-tenancy framing "
"(pools as quotas, priorities as QoS, backfills as batch citizens) "
"maps onto every scheduler ever built, and closing with 'the "
"metadata DB is itself a database you must operate' ties the whole "
"curriculum's Postgres knowledge back into the orchestrator — "
"coherence interviewers reward."
                ),
            },
            {
                "question": (
"Your daily DAG has a bug fixed today; the last 60 days of gold-layer "
"output are wrong. Design the remediation: what do you re-run, in "
"what order, with what safeguards — without disturbing today's "
"production runs?"
                ),
                "difficulty": "Medium",
                "topics": ["backfills", "idempotency", "operations"],
                "answer": (
"Preconditions first: confirm tasks are idempotent per logical date "
"(they are — keyed upserts/partition overwrites; if not, fix THAT "
"first) and that the bug is in transform logic, not source data — "
"bronze/raw is intact, so rebuild is a pure function replay. Then: "
"backfill only the affected layer forward (silver→gold if silver "
"was wrong, gold-only if just gold), `airflow dags backfill -s -e` "
"with max_active_runs capped (3-5) and a dedicated pool so the "
"backfill can't exhaust warehouse connections against the daily "
"runs; run oldest→newest (some aggregates read prior days). "
"Safeguards: quality gates run per backfilled date exactly as in "
"daily runs (qg suite validates each rebuilt partition), "
"reconciliation totals compared before/after over a sample of "
"dates, dashboards flagged during the window ('historical revision "
"in progress'), and downstream consumers notified — revised "
"history is a *product* event, not just an ops event."
                ),
                "explanation": (
"This scenario is the payoff of the entire curriculum's idempotency "
"drumbeat: because every layer was built as 'pure function of "
"logical date over immutable raw', remediation is *re-execution, "
"not surgery* — no hand-written UPDATE against production. The "
"resource-isolation details (pools, capped active runs) reuse the "
"multi-tenancy answer; oldest-first ordering shows you thought "
"about inter-date dependencies; and the consumer-notification beat "
"reflects that data teams ship a product — silently rewriting 60 "
"days of executive dashboards erodes exactly the trust quality "
"systems exist to build. If asked 'what if tasks WEREN'T "
"idempotent?' — that's the real answer: you fix idempotency first, "
"because un-rerunnable pipelines make every bug permanent."
                ),
            },
        ],
    },
]

"""
Enrichment for projects 6-8 (Spark & Airflow exercises): expanded instructions,
concept refreshers tying back to earlier projects, objectives, hints, links.
"""

ENRICHMENT_BIGDATA = {
    # ================================================== First Spark
    "fs-1": {
        "instructions": (
"Before running Spark, build its engine in 25 lines — you'll never find shuffles "
"mysterious again.\n\n"
"**Your task**\n\n"
"Implement `mini_spark(partitions, key_fn, agg_fn)` in three labeled phases:\n\n"
"1. **MAP** — for each partition independently (this would run on different "
"machines), build `{key: [records]}` using `key_fn` on each record.\n"
"2. **SHUFFLE** — merge those per-partition dicts into one, so each key ends up "
"with ALL its records. This merge is what crosses the network in real Spark.\n"
"3. **REDUCE** — apply `agg_fn` to each key's record list, giving `{key: value}`.\n\n"
"The checker aggregates fares per borough across three partitions and expects "
"`{'M': 30, 'B': 15, 'Q': 5}`. Keep the three phases as separate blocks — the "
"structure is the lesson."
        ),
        "refresher": (
"**From basics to this exercise.** Everything here is Python you already own from "
"earlier projects: dict-of-lists grouping (LogMiner's Counter, pandas' split "
"phase) plus loops. What's new is the *distribution shape*.\n\n"
"The grouping primitive, per partition:\n\n"
"```python\ngroups = {}\nfor rec in partition:\n    groups.setdefault(key_fn(rec), []).append(rec)\n```\n\n"
"`setdefault(k, [])` returns the existing list or inserts an empty one — the "
"one-line dict-of-lists builder. The shuffle phase is the same trick again, one "
"level up: merge many `{key: [..]}` dicts by extending lists.\n\n"
"**Why Spark is shaped exactly like this:** partitions live on different machines, "
"so phase 1 is *embarrassingly parallel* (no coordination). But to total borough "
"'M', every M record must reach one place — that key-based regrouping across "
"machines is the **shuffle**: each mapper writes output bucketed by key, each "
"reducer fetches its bucket from every mapper. Disk + network + serialization "
"(remember tf-3!) makes it the expensive step — Spark performance tuning (Project "
"7) is mostly the art of shuffling less.\n\n"
"Real Spark adds one optimization you can see in your own code: if `agg_fn` is "
"something like sum, you can pre-aggregate *within* each partition before "
"shuffling — moving `{'M': 30}` across the network instead of all M records. "
"That's a combiner (`reduceByKey` vs `groupByKey`).\n\n"
"**Practice beyond the exercise:** refactor your mini_spark to pre-aggregate in "
"the map phase and confirm identical results — you've just discovered why "
"reduceByKey exists."
        ),
        "objectives": [
            "Build dict-of-lists groupings with setdefault",
            "Explain map / shuffle / reduce and which phase crosses the network",
            "Explain why pre-aggregation (combiners) shrinks shuffles",
        ],
        "hints": [
            "Phase 1: loop over partitions; for each, build a groups dict; collect them in a list.",
            "Phase 2: one empty dict; for each per-partition dict, for each (k, vals), merged.setdefault(k, []).extend(vals).",
            "Phase 3 is a dict comprehension: {k: agg_fn(vs) for k, vs in merged.items()}.",
        ],
        "resources": [
            {"title": "MapReduce — the original Google paper (readable!)", "url": "https://research.google/pubs/mapreduce-simplified-data-processing-on-large-clusters/"},
            {"title": "Spark RDD programming guide (see shuffle section)", "url": "https://spark.apache.org/docs/latest/rdd-programming-guide.html#shuffle-operations"},
            {"title": "dict.setdefault docs", "url": "https://docs.python.org/3/library/stdtypes.html#dict.setdefault"},
        ],
    },
    "fs-2": {
        "instructions": (
"Build lazy evaluation itself — the trick behind Spark's transformations-vs-actions "
"split.\n\n"
"**Your task**\n\n"
"Implement `LazyFrame` so that:\n\n"
"- `.filter(pred)` and `.map(fn)` are **transformations**: each returns a NEW "
"LazyFrame with the step appended to `self.steps` — and touches zero data. "
"(Don't mutate self — return `LazyFrame(self.data, self.steps + [...])`.)\n"
"- `.collect()` is the **action**: it streams the data through all recorded steps "
"in order and returns a list.\n\n"
"The checker plants a spy function and fails you if it runs before `collect()`, "
"or if `map` ran on rows the preceding `filter` should have removed — so collect "
"must *stream* each element through the pipeline, not apply steps list-by-list."
        ),
        "refresher": (
"**From basics to this exercise.** Three ingredients, all familiar:\n\n"
"*Functions are values* (Weather Watcher's with_retry) — so a step is just a "
"tuple `('filter', pred)` stored in a list.\n\n"
"*Immutable chaining* (Task Forge's return self, evolved): returning a NEW object "
"per transformation is how Spark makes plans safe to reuse — `base.filter(a)` and "
"`base.filter(b)` share nothing.\n\n"
"*Generator chaining* (LogMiner): the streaming pipeline. Builtins make it clean:\n\n"
"```python\nit = iter(data)\nit = filter(pred, it)   # lazy — nothing runs yet\nit = map(fn, it)        # still nothing\nlist(it)                # NOW elements flow through both\n```\n\n"
"**A trap worth meeting on purpose:** if you build the chain in a loop with "
"generator *expressions* — `it = (x for x in it if fn(x))` — all the genexps "
"capture the loop variable `fn` by reference and, because they run lazily *after* "
"the loop finished, they all see its final value. The builtins `filter(fn, it)` / "
"`map(fn, it)` bind `fn` immediately as an argument, dodging the bug. This "
"late-binding closure trap is a classic Python interview question — now you've "
"built the fix.\n\n"
"**The Spark payoff:** `df.filter(...).select(...)` records steps; `.count()` / "
"`.write()` executes them. Laziness lets Catalyst *see the whole plan* before "
"running it — reorder filters below joins, prune unread columns, fuse steps into "
"one pass. Your LazyFrame is the toy version of a query optimizer's input.\n\n"
"**Practice beyond the exercise:** add `.take(n)` that stops pulling after n "
"results — notice how laziness makes early-exit free, exactly like Spark's "
"`limit`."
        ),
        "objectives": [
            "Implement transformations that record work and an action that executes it",
            "Stream elements through chained filter/map without materializing intermediates",
            "Explain the late-binding closure trap and why builtins avoid it",
        ],
        "hints": [
            "filter/map are one-liners: return LazyFrame(self.data, self.steps + [('filter', pred)]).",
            "collect: start with it = iter(self.data); loop steps; use builtins filter()/map() to wrap it; finish with list(it).",
            "Spy ran during .map()? You applied fn eagerly — steps must only run inside collect().",
        ],
        "resources": [
            {"title": "Spark: transformations vs actions", "url": "https://spark.apache.org/docs/latest/rdd-programming-guide.html#transformations"},
            {"title": "filter/map builtins", "url": "https://docs.python.org/3/library/functions.html#filter"},
            {"title": "The late-binding closure gotcha", "url": "https://docs.python-guide.org/writing/gotchas/#late-binding-closures"},
        ],
    },
    "fs-3": {
        "instructions": (
"The real engine. This boots an actual Spark driver + executors inside the app "
"container (local mode) — first run takes ~30–60s, that's the JVM starting.\n\n"
"**Your task**\n\n"
"From the provided 5-row trips DataFrame, compute `result` as a plain Python dict "
"`{'M': 30.0, 'B': 15.0, 'Q': 5.0}` using **Spark operations only** (no pandas):\n\n"
"1. `groupBy('borough')` then `.agg(F.sum('fare'))` — this is your mini_spark from "
"fs-1, industrialized.\n"
"2. `.collect()` the result — the action that triggers execution — giving a list "
"of `Row` objects.\n"
"3. Convert rows to the dict. A Row supports `row['borough']` access; the sum "
"column's name depends on whether you `.alias(...)` it (do — it's cleaner).\n\n"
"Compare what you wrote in fs-1 and here: same three phases, but now a real "
"driver planned it and executor threads ran it."
        ),
        "refresher": (
"**From basics to this exercise.** Map your last two exercises onto the real "
"API:\n\n"
"- mini_spark's phases ⇒ `groupBy` (declares the shuffle) + `agg` (the reduce)\n"
"- LazyFrame ⇒ DataFrame: `groupBy`/`agg` are transformations (instant, lazy); "
"`collect()` is the action\n\n"
"The session and functions module are boilerplate you'll type forever:\n\n"
"```python\nfrom pyspark.sql import SparkSession\nfrom pyspark.sql import functions as F\nspark = SparkSession.builder.master('local[2]').appName('x').getOrCreate()\n```\n\n"
"`local[2]` = run executors as 2 threads in this process — same engine and same "
"plans as a 100-node cluster, which is why local development transfers. "
"`F.sum('fare')` builds an *expression object* (not a number!) that Catalyst "
"compiles to JVM code — your Python never touches rows, which is why PySpark "
"DataFrames are fast (pp-1's lesson at cluster scale).\n\n"
"`.alias('total')` names the output column; without it you get the ugly "
"`sum(fare)`. `.collect()` returns `Row` objects — dict-like: `row['borough']`. "
"Only collect small results: it funnels everything to the driver; a big collect "
"is the classic out-of-memory. For real outputs, `.write.parquet(...)` instead "
"(your cluster milestones do this).\n\n"
"**Watch it happen:** while this exercise runs in-app, your cluster milestones "
"run the same code against spark://spark-master:7077 — with the Spark UI at "
"localhost:8080 showing the job, its one shuffle (caused by groupBy), and the "
"stage boundary. Find it.\n\n"
"**Practice beyond the exercise:** in your notebook, run `.explain()` on the "
"aggregation before collecting — read the plan bottom-up and spot the Exchange "
"(shuffle) node."
        ),
        "objectives": [
            "Create sessions/DataFrames and aggregate with groupBy + F.sum",
            "Map transformations/actions onto your LazyFrame mental model",
            "Convert collected Rows to Python structures and know when NOT to collect",
        ],
        "hints": [
            "rows = trips.groupBy('borough').agg(F.sum('fare').alias('total')).collect()",
            "Then: result = {row['borough']: row['total'] for row in rows}.",
            "Slow first run is normal (JVM boot). If it times out once, just run again.",
        ],
        "resources": [
            {"title": "PySpark: Getting started (official quickstart)", "url": "https://spark.apache.org/docs/latest/api/python/getting_started/quickstart_df.html"},
            {"title": "GroupedData.agg reference", "url": "https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.GroupedData.agg.html"},
            {"title": "Spark SQL programming guide", "url": "https://spark.apache.org/docs/latest/sql-programming-guide.html"},
        ],
    },
    # ================================================== Spark at Scale
    "ss-1": {
        "instructions": (
"Build the two diagnostic tools of a Spark performance engineer: a partitioner and "
"a skew meter.\n\n"
"**Your task**\n\n"
"1. `partition_keys(keys, n)` — assign each key to partition `hash(key) % n`, "
"returning n lists. This must be *deterministic*: the same key always lands in the "
"same partition (the checker verifies — it's the property that makes distributed "
"groupBy possible at all).\n"
"2. `skew_ratio(partitions)` — max partition size ÷ mean partition size. Balanced "
"= 1.0; the checker's `[90, 5, 5, 0]` case scores 3.6.\n\n"
"That ratio is a real metric: it predicts your stage time, because a stage "
"finishes when its SLOWEST task does."
        ),
        "refresher": (
"**From basics to this exercise.** `hash(x)` maps any immutable value to an int; "
"`% n` folds it into buckets 0..n-1 — the same trick behind dicts and sets. Two "
"properties matter here: *determinism within a run* (same key → same bucket, "
"which is what lets every mapper independently agree where borough 'M' belongs) "
"and *roughly uniform spread* for typical keys.\n\n"
"```python\nparts = [[] for _ in range(n)]   # NOT [[]] * n — that's n refs to ONE list!\nfor k in keys:\n    parts[hash(k) % n].append(k)\n```\n\n"
"(That `[[]] * n` trap is tf-1's shared-mutable lesson in new clothes.)\n\n"
"**Skew: the silent stage-killer.** Hash partitioning spreads *keys* evenly — "
"but not *rows*, when one key dominates. If 60% of trips are airport-zone, one "
"partition holds 60% of the data; 199 tasks finish in seconds while task 200 "
"grinds for an hour, and the whole stage waits. In the Spark UI this looks like "
"a stage stuck at 199/200 — now you know what you're looking at, and "
"`max/mean` task input size is exactly the number to check.\n\n"
"The fix you'll apply on the cluster: **salting** — split the hot key into "
"`key_0 .. key_9` sub-keys (spread the work), aggregate, then merge the "
"sub-results. Cost: a second small aggregation. Benefit: 10x on the straggler.\n\n"
"**Practice beyond the exercise:** feed partition_keys a hot-key distribution "
"(90% one key), read its skew_ratio, then salt it (append random 0-9 suffix) and "
"watch the ratio drop toward 1.0."
        ),
        "objectives": [
            "Explain hash partitioning and why determinism enables distributed groupBy",
            "Quantify skew as max/mean and connect it to straggler tasks in the Spark UI",
            "Describe salting as the standard skew fix and its cost",
        ],
        "hints": [
            "Initialize with a list comprehension of empty lists — [[]]*n is the shared-list trap.",
            "skew_ratio: sizes = [len(p) for p in partitions]; return max(sizes) / (sum(sizes)/len(sizes)).",
        ],
        "resources": [
            {"title": "Spark tuning guide (partitions & parallelism)", "url": "https://spark.apache.org/docs/latest/tuning.html"},
            {"title": "hash() docs", "url": "https://docs.python.org/3/library/functions.html#hash"},
            {"title": "Spark AQE — automatic skew handling in 3.x", "url": "https://spark.apache.org/docs/latest/sql-performance-tuning.html#adaptive-query-execution"},
        ],
    },
    "ss-2": {
        "instructions": (
"Implement the optimization that removes shuffles entirely: the broadcast (map-side) "
"join.\n\n"
"**Your task**\n\n"
"`broadcast_join(big_rows, small_table, key)`:\n\n"
"1. **Index the small side ONCE**: build `{row[key]: row}` from small_table — this "
"dict is what Spark 'broadcasts' (copies) to every executor.\n"
"2. **Stream the big side**: for each big row (it's an iterator — one pass only!), "
"look up its key in the index. Match → emit the merged dict (all big-row fields + "
"the small row's other fields). No match → drop the row (inner join).\n\n"
"Preserve big-row order. The checker joins 3 trips to a 2-zone lookup and expects "
"exactly the 2 matched, enriched rows. Notice what you did NOT do: sort anything, "
"or move the big data at all — that's the entire point."
        ),
        "refresher": (
"**From basics to this exercise.** This is pp-3's join, but now you build the "
"machinery — and it's just a dict:\n\n"
"```python\nindex = {z['zone']: z for z in zones}       # build once: O(small)\nfor trip in trips:                          # stream: O(big), one pass\n    z = index.get(trip['zone'])             # O(1) lookup\n    if z is not None:\n        yield {**trip, **z}                 # merge dicts (or dict(trip) + update)\n```\n\n"
"`index.get(k)` returning None for a miss (basic-Python dicts!) is your "
"inner-join filter. Merging: `{**a, **b}` copies a then lays b's keys over it — "
"take care not to let the small side's key field clobber anything; excluding the "
"join key from the merge keeps it clean.\n\n"
"**Why this beats a shuffle join:** the default join must get matching keys onto "
"the same machine — BOTH sides get hashed, written to disk, and pulled across "
"the network (two full shuffles). If one side fits in memory (a zones lookup, a "
"country table — the common case!), ship *it* everywhere instead and stream the "
"big side untouched: zero shuffles, one pass. In Spark: "
"`big.join(F.broadcast(small), 'key')` — and your cluster milestone compares "
"both physical plans with .explain() to see the BroadcastHashJoin vs "
"SortMergeJoin difference in black and white.\n\n"
"**The limit:** broadcast the BIG side by mistake and you copy gigabytes to "
"every executor — instant memory pressure. Spark auto-broadcasts under a "
"threshold (spark.sql.autoBroadcastJoinThreshold, default 10MB); above it, you "
"decide.\n\n"
"**Practice beyond the exercise:** make your version a generator (yield instead "
"of building the list) — now it composes with lm-1-style streaming pipelines."
        ),
        "objectives": [
            "Implement hash-index + stream: the map-side join pattern",
            "Explain when broadcast beats shuffle join and its memory limit",
            "Merge dicts cleanly and handle misses as the join filter",
        ],
        "hints": [
            "Build the index with a dict comprehension over small_table keyed by row[key].",
            "For each big row: match = index.get(row[key]); skip if None; else merged = dict(row) then add match's non-key fields.",
            "The checker expects a list — collect merged rows in order.",
        ],
        "resources": [
            {"title": "Spark join hints incl. broadcast", "url": "https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-hints.html"},
            {"title": "Spark performance tuning (joins section)", "url": "https://spark.apache.org/docs/latest/sql-performance-tuning.html"},
            {"title": "Dict merging (** unpacking)", "url": "https://docs.python.org/3/library/stdtypes.html#dict"},
        ],
    },
    "ss-3": {
        "instructions": (
"Read the optimizer's homework. Catalyst rewrites your query before running it — "
"prove it and read the evidence. (Boots local Spark: ~30–60s.)\n\n"
"**Your task**\n\n"
"The query selects two columns and THEN filters. A naive engine would scan → "
"project → filter. Catalyst won't.\n\n"
"1. Capture the physical plan as a string into `plan`:\n"
"```python\nplan = q._jdf.queryExecution().executedPlan().toString()\n```\n"
"(That's reaching through PySpark into the JVM — `.explain()` prints the same "
"thing, but we need the string to assert on.)\n"
"2. Set `pushed = True` after confirming a `Filter` node in the plan (it sits "
"at/near the scan, *below* the projection — read bottom-up).\n"
"3. Leave the `print(plan)` so you actually look at it: find Scan, Filter, "
"Project, and any WholeStageCodegen markers.\n\n"
"The checker also verifies the query returns 49 rows — optimization never changes "
"results, only work."
        ),
        "refresher": (
"**From basics to this exercise.** Because transformations are lazy (fs-2), Spark "
"holds your *whole* query as a tree before executing — and **Catalyst** rewrites "
"that tree like a compiler:\n\n"
"- **Predicate pushdown** — filters sink toward the data source so fewer rows "
"flow upward (with Parquet, a filter can skip entire row-groups on disk).\n"
"- **Column pruning** — unread columns are never materialized (columnar formats "
"make this nearly free — pp-1's memory lesson again).\n"
"- Then **Tungsten** generates fused JVM bytecode for pipelined stages — the "
"`WholeStageCodegen` markers in your plan.\n\n"
"Reading plans is a daily skill. `df.explain()` prints the physical plan; "
"`explain('extended')` shows all four phases (parsed → analyzed → optimized → "
"physical). **Read bottom-up**: the bottom line touches the data; each line "
"feeds the one above. What you're checking in practice: Is the filter near the "
"scan? Is the join Broadcast or SortMerge? How many Exchange (shuffle) nodes?\n\n"
"That last habit ties this project together: an Exchange node in the plan IS "
"the shuffle you built in fs-1, the thing broadcast joins (ss-2) delete, and "
"the place skew (ss-1) hurts.\n\n"
"**The UDF warning, one more time with feeling:** Catalyst can only optimize "
"what it can see. `F.col('fare') > 50` is a transparent expression tree; a "
"Python `udf(lambda ...)` is an opaque box — no pushdown through it, plus "
"per-row serialization to a Python worker. Stay in `F.` functions unless you "
"truly can't.\n\n"
"**Practice beyond the exercise:** run `explain('extended')` on your Project-7 "
"broadcast-join milestone and find where the optimized plan diverges from what "
"you wrote."
        ),
        "objectives": [
            "Capture and read physical plans bottom-up",
            "Explain predicate pushdown and column pruning",
            "Spot Exchange/Broadcast/Codegen nodes and know what each implies",
        ],
        "hints": [
            "plan line is given verbatim in the instructions — assign it, then pushed = 'Filter' in plan.",
            "Read the printed plan bottom-up: Scan should be at the bottom, with Filter right above/at it, Project higher.",
        ],
        "resources": [
            {"title": "Deep dive into Catalyst (Databricks engineering post)", "url": "https://www.databricks.com/blog/2015/04/13/deep-dive-into-spark-sqls-catalyst-optimizer.html"},
            {"title": "explain() reference", "url": "https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.explain.html"},
            {"title": "Spark SQL performance tuning", "url": "https://spark.apache.org/docs/latest/sql-performance-tuning.html"},
        ],
    },
    # ================================================== Orchestrate It
    "oi-1": {
        "instructions": (
"Airflow's core, part 1: turning 'this depends on that' into a runnable order.\n\n"
"**Your task**\n\n"
"Implement `topo_order(deps)` where `deps` maps each task to the list of tasks it "
"depends on (its *upstreams*):\n\n"
"```python\n{'load': ['transform'], 'transform': ['ingest'], 'ingest': []}\n```\n\n"
"Return any valid execution order — every task strictly after all its upstreams. "
"There are often several valid orders (the checker accepts any; it verifies the "
"ordering constraints, not one fixed list). If the graph has a cycle "
"(`a` needs `b` needs `a`), raise `ValueError` — Airflow refuses cyclic DAGs at "
"parse time for exactly this reason; that's the A (acyclic) in DAG.\n\n"
"Two classic algorithms: DFS with visit states, or Kahn's (repeatedly take a "
"task with no unprocessed upstreams). Pick either; the refresher sketches both."
        ),
        "refresher": (
"**From basics to this exercise.** A graph is just a dict — you've been building "
"them since basic Python. **Topological sort** = 'flatten a dependency graph "
"into a to-do list', and it powers Airflow, make, pip resolvers, and every "
"build system.\n\n"
"*DFS with three states* (the elegant one):\n\n"
"```python\n# state: unvisited / IN-PROGRESS / done\ndef visit(t):\n    if state[t] == IN_PROGRESS: raise ValueError('cycle!')\n    if state[t] == DONE: return\n    state[t] = IN_PROGRESS\n    for up in deps[t]: visit(up)\n    state[t] = DONE\n    order.append(t)      # appended AFTER upstreams -> valid order\n```\n\n"
"The IN_PROGRESS state is the cycle detector: revisiting a node you're still "
"inside means you looped back into your own ancestry.\n\n"
"*Kahn's* (the iterative one): count unprocessed upstreams per task; repeatedly "
"pop any task at zero, append it, decrement its dependents. If you finish with "
"tasks still unpopped — cycle.\n\n"
"**How Airflow actually uses this:** when the scheduler parses your DAG file, "
"`t1 >> t2` builds exactly this dict (as task metadata), cycles are rejected "
"immediately, and at run time a task becomes *schedulable* precisely when all "
"its upstreams reached a terminal success state — Kahn's algorithm running "
"continuously against a database. Your capstone DAG's "
"`ingest >> validate >> transform >> load` line is sugar for the dict in this "
"exercise.\n\n"
"**Practice beyond the exercise:** add a diamond (two parallel branches merging) "
"to your test dict and print your order — see how independent branches can "
"interleave freely; that freedom is what lets Airflow run them in parallel."
        ),
        "objectives": [
            "Represent dependency graphs as dicts and traverse them",
            "Implement topological sort with cycle detection",
            "Explain how DAG parsing and task scheduling use this algorithm",
        ],
        "hints": [
            "Use a state dict: missing=unvisited, 1=in-progress, 2=done; recurse into deps.get(t, []) before appending t.",
            "Kick it off with `for t in deps: visit(t)` — visit() ignores already-done tasks.",
            "Cycle = visiting a node whose state is in-progress. That's the ValueError site.",
        ],
        "resources": [
            {"title": "Airflow: DAGs (core concepts)", "url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html"},
            {"title": "Topological sorting", "url": "https://en.wikipedia.org/wiki/Topological_sorting"},
            {"title": "graphlib.TopologicalSorter — stdlib does this too!", "url": "https://docs.python.org/3/library/graphlib.html"},
        ],
    },
    "oi-2": {
        "instructions": (
"Airflow's core, part 2: the task lifecycle state machine.\n\n"
"**Your task**\n\n"
"Implement `run_task(fn, retries=2)` returning the list of states the task walks "
"through — mirroring real Airflow TaskInstance states:\n\n"
"- immediate success → `['running', 'success']`\n"
"- fail once, then succeed → `['running', 'up_for_retry', 'running', 'success']`\n"
"- `retries=1`, always failing → `['running', 'up_for_retry', 'running', 'failed']`\n\n"
"The rules: `retries=N` allows N+1 total attempts; every attempt appends "
"'running' first; a failure appends 'up_for_retry' if attempts remain, else "
"'failed'; success appends 'success' and stops. This is ww-2's retry loop "
"wearing a state-machine jacket — the difference is that Airflow persists each "
"transition to its database, which is what makes retries survive scheduler "
"restarts."
        ),
        "refresher": (
"**From basics to this exercise.** A state machine is just 'a variable plus rules "
"for changing it' — here the variable is the task's lifecycle stage, and the "
"log of transitions is what you return. The skeleton is ww-2's try/except-in-a-"
"loop with bookkeeping:\n\n"
"```python\nfor attempt in range(retries + 1):        # N retries = N+1 attempts\n    states.append('running')\n    try:\n        fn(); states.append('success'); return states\n    except Exception:\n        last = attempt == retries\n        states.append('failed' if last else 'up_for_retry')\nreturn states\n```\n\n"
"Off-by-one alert: `retries=2` means **3** attempts. Airflow's own parameter "
"works the same way, and misreading it in production means a task retries more "
"(or less) than you budgeted.\n\n"
"**What real Airflow adds around this loop:** each transition is a row update "
"in the metadata DB (state, try_number, timestamps). 'up_for_retry' isn't a "
"sleep() — the scheduler simply won't queue the task again until "
"`retry_delay` (optionally with exponential backoff) has elapsed; the process "
"that failed is *gone*, and a fresh worker process runs the next try. That "
"design — state in the DB, workers disposable — is why you can kill the Spark "
"master mid-run in your capstone and watch the pipeline heal itself on retry.\n\n"
"And the operational punchline you already know from ww-3: because retries "
"re-run your task function from scratch, every task must be idempotent.\n\n"
"**Practice beyond the exercise:** add a `retry_delay` list argument that "
"records simulated waits (e.g. [1, 2, 4] seconds) between attempts — "
"exponential backoff in one line."
        ),
        "objectives": [
            "Model lifecycles as explicit state transitions",
            "Get retries-vs-attempts off-by-ones right (N retries = N+1 tries)",
            "Explain how DB-persisted state makes Airflow retries crash-proof",
        ],
        "hints": [
            "Loop range(retries + 1); append 'running' at the top of every iteration.",
            "On success: append and RETURN immediately — don't let the loop continue.",
            "On the final attempt's failure (attempt == retries) append 'failed', else 'up_for_retry'.",
        ],
        "resources": [
            {"title": "Airflow: task lifecycle & states", "url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html#task-instances"},
            {"title": "Airflow: retries & retry_delay (see default args)", "url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html"},
        ],
    },
    "oi-3": {
        "instructions": (
"The capstone's capstone: combine ordering (oi-1) and lifecycle (oi-2) into a "
"working scheduler.\n\n"
"**Your task**\n\n"
"Implement `run_dag(deps, fns)`:\n\n"
"1. Order tasks topologically (paste in your oi-1 solution as a helper).\n"
"2. Walk the order; for each task check its upstreams' states FIRST:\n"
"   - any upstream 'failed' **or** 'upstream_failed' → mark this task "
"'upstream_failed' and DO NOT run its function (transitive: a failure poisons "
"its entire downstream subtree)\n"
"   - otherwise run `fns[task]()` → 'success', or on exception → 'failed'\n"
"3. Return `{task: state}`.\n\n"
"The checker fails `validate` in an ingest→validate→transform→load chain and "
"requires: transform AND load marked 'upstream_failed' with their functions "
"never called (it logs side effects to prove it). Congratulations — after this "
"you have written the essential 20% of an orchestrator."
        ),
        "refresher": (
"**From basics to this exercise.** Pure composition — no new primitives, just "
"your last two solutions plus a dict of states:\n\n"
"```python\nstates = {}\nfor task in topo_order(deps):\n    if any(states.get(u) in ('failed', 'upstream_failed')\n           for u in deps.get(task, [])):\n        states[task] = 'upstream_failed'\n        continue                      # skip = never call the function\n    try:\n        fns[task](); states[task] = 'success'\n    except Exception:\n        states[task] = 'failed'\n```\n\n"
"The subtle requirement is **transitivity**: `load` is downstream of the failed "
"`validate` only *through* `transform` — that's why 'upstream_failed' must "
"itself count as a blocking state, so the poison propagates hop by hop. Miss "
"that and only direct children get marked (a bug the checker catches).\n\n"
"**What you've now built vs what Airflow adds:** your loop is the essence — "
"Airflow's scheduler is 'this, continuously': it re-evaluates readiness against "
"DB state every few seconds, runs ready tasks in *parallel* through an executor "
"(your sequential walk is the one big simplification), retries per oi-2 before "
"declaring 'failed', supports trigger rules other than all-success (e.g. "
"`all_done`, `one_failed` — your `any(...)` check is the default rule "
"`all_success`), and persists everything so a crashed scheduler resumes where "
"it left off. When you open Graph view in your capstone DAG and see green/red/"
"orange boxes — those are exactly your states dict, rendered.\n\n"
"**Practice beyond the exercise:** add retries by calling an oi-2-style "
"run_task inside the try, and a `trigger_rule='one_failed'` option for a "
"cleanup task that runs *only* when something broke — you'll then recognize "
"both features in the Airflow docs as old friends."
        ),
        "objectives": [
            "Compose ordering + lifecycle + state tracking into a scheduler",
            "Propagate failure transitively through downstream tasks",
            "Map your mini-scheduler onto real Airflow features (executors, trigger rules)",
        ],
        "hints": [
            "Reuse your oi-1 topo_order verbatim as an inner helper.",
            "The upstream check must treat BOTH 'failed' and 'upstream_failed' as blocking — that's what makes it transitive.",
            "continue after marking upstream_failed — the function must never run.",
        ],
        "resources": [
            {"title": "Airflow: scheduler concepts", "url": "https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/scheduler.html"},
            {"title": "Airflow: trigger rules", "url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#trigger-rules"},
            {"title": "Airflow: executors", "url": "https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/executor/index.html"},
        ],
    },
}

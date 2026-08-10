"""
Curriculum part 2: big data (projects 6-8) — Spark and Airflow.

Exercises marked heavy=True start a real local PySpark session inside the app
container (Java is installed in the image), so they get a longer timeout.
The other exercises are "build-it-yourself internals": you implement a tiny
version of the machinery (a mini-Spark, a mini-scheduler) in pure Python,
which is the fastest way to truly understand what the real engine is doing.
"""

BIGDATA_PROJECTS = [
    # ------------------------------------------------------------------ 6
    {
        "id": "first-spark",
        "num": 6,
        "title": "First Spark",
        "tagline": "Distributed DataFrames: lazy plans, partitions, and the Spark UI",
        "level": "Advanced",
        "tech": ["PySpark", "DataFrames", "lazy evaluation", "partitions", "Spark UI"],
        "est_hours": 8,
        "brief": (
            "Take the taxi dataset from Project 5 and process it with PySpark. "
            "Same analytics, new engine: a driver that builds lazy plans and "
            "executors that crunch partitions in parallel. You'll run it two ways — "
            "in-app exercises use Spark local mode, and the real thing runs on the "
            "Spark cluster in your Docker stack (start it with the command shown in "
            "the Environment panel; JupyterLab is pre-wired to the cluster). "
            "Keep the Spark UI at localhost:8080 open the whole time — watching "
            "jobs, stages and tasks appear is where the understanding happens."
        ),
        "milestones": [
            "Start the big-data stack (see Environment panel) and open JupyterLab at localhost:8888 — the notebooks folder has a starter that connects to spark://spark-master:7077.",
            "Load trips.csv into a Spark DataFrame with an explicit schema; run .rdd.getNumPartitions() and explain the number you see.",
            "Rebuild Project 5's analytics in Spark: filter bad rows, join zones, revenue per borough per hour — then call .explain() and read the plan bottom-up.",
            "Trigger vs build: note that nothing runs until .count()/.write — find your job in the Spark UI, count its stages, and identify which operation caused the shuffle boundary.",
            "Write the results partitioned: output.write.partitionBy('borough').parquet(...) — inspect the folder structure it creates and read one borough back.",
            "Break it on purpose: .repartition(200) on this small data, watch the UI fill with tiny tasks, and write one sentence on why more parallelism made it slower.",
        ],
        "under_the_hood": (
            "**The cast.** Your Python script is the *driver*: it builds a logical "
            "plan, nothing more. The *cluster manager* (your compose stack's "
            "standalone master) hands it *executors* — JVM processes on workers. "
            "Executors run *tasks*: one task = one partition of data through one "
            "stage of the plan. `getNumPartitions()` is literally 'how many parallel "
            "tasks would a pass over this data be'.\n\n"
            "**Transformations vs actions.** filter/join/groupBy are recorded, not "
            "executed — exactly like the generator pipelines you built in LogMiner. "
            "An action (count, collect, write) makes Spark compile the plan into "
            "*stages*. Stage boundaries appear where data must move between "
            "machines: the *shuffle*. groupBy('borough') must get all Manhattan "
            "rows to the same place — so every executor writes shuffle files "
            "bucketed by key, and the next stage fetches its bucket from everyone. "
            "Shuffles are the expensive thing in Spark; you tune jobs mostly by "
            "shuffling less.\n\n"
            "**Why Python is fast here.** PySpark DataFrames compile to JVM "
            "bytecode via Catalyst (the query optimizer) — your Python never "
            "touches the rows. Use built-in functions and this holds; write a "
            "Python UDF and rows must be serialized out to Python workers and "
            "back (slow — the pandas-loop lesson all over again, at cluster scale)."
        ),
        "exercises": [
            {
                "id": "fs-1",
                "title": "Build a mini-Spark (map + shuffle + reduce)",
                "instructions": (
                    "Understand the engine by building one. Implement `mini_spark(partitions, key_fn, agg_fn)`:\n"
                    "1) MAP: per partition, build a dict of key -> list of values (local pre-grouping)\n"
                    "2) SHUFFLE: merge the per-partition dicts so each key has ALL its values\n"
                    "3) REDUCE: apply agg_fn to each key's values.\n"
                    "Return {key: aggregated}. This is what groupBy().agg() does across machines."
                ),
                "starter_code": (
                    "def mini_spark(partitions, key_fn, agg_fn):\n"
                    "    \"\"\"partitions: list of lists of records.\n"
                    "    key_fn: record -> key. agg_fn: list_of_records -> value.\"\"\"\n"
                    "    # 1) map side: group within each partition\n"
                    "    # 2) shuffle: merge groups across partitions\n"
                    "    # 3) reduce: aggregate each key\n"
                    "    ...\n"
                ),
                "check_code": (
                    "parts = [\n"
                    "    [{'b': 'M', 'fare': 10}, {'b': 'B', 'fare': 8}],\n"
                    "    [{'b': 'M', 'fare': 20}, {'b': 'Q', 'fare': 5}],\n"
                    "    [{'b': 'B', 'fare': 7}],\n"
                    "]\n"
                    "out = mini_spark(parts, key_fn=lambda r: r['b'],\n"
                    "                 agg_fn=lambda rs: sum(r['fare'] for r in rs))\n"
                    "assert out == {'M': 30, 'B': 15, 'Q': 5}\n"
                    "print('PASS: you just implemented map -> shuffle -> reduce.')\n"
                    "print('Every Spark groupBy does exactly this across machines.')\n"
                ),
            },
            {
                "id": "fs-2",
                "title": "Lazy plans, by hand",
                "instructions": (
                    "Implement class `LazyFrame` wrapping an iterable. `.filter(pred)` and "
                    "`.map(fn)` must return a NEW LazyFrame recording the step WITHOUT touching "
                    "data (transformations). `.collect()` (action) applies all recorded steps "
                    "in order, streaming through generators. A counter proves nothing runs "
                    "before collect()."
                ),
                "starter_code": (
                    "class LazyFrame:\n"
                    "    def __init__(self, data, steps=None):\n"
                    "        self.data = data\n"
                    "        self.steps = steps or []   # list of ('filter'|'map', fn)\n\n"
                    "    def filter(self, pred):\n"
                    "        ...\n\n"
                    "    def map(self, fn):\n"
                    "        ...\n\n"
                    "    def collect(self):\n"
                    "        ...\n"
                ),
                "check_code": (
                    "calls = {'n': 0}\n"
                    "def spy(x):\n"
                    "    calls['n'] += 1\n"
                    "    return x * 10\n"
                    "lf = LazyFrame(range(6)).filter(lambda x: x % 2 == 0).map(spy)\n"
                    "assert calls['n'] == 0, 'transformations must be lazy — no work before an action'\n"
                    "assert lf.collect() == [0, 20, 40]\n"
                    "assert calls['n'] == 3, 'map must run only on rows that survived the filter'\n"
                    "print('PASS: transformations recorded, action executed — Spark in 20 lines')\n"
                ),
            },
            {
                "id": "fs-3",
                "title": "Real PySpark, local mode",
                "heavy": True,
                "instructions": (
                    "Now the real engine (this spins up Spark locally — allow ~30-60s). Create a "
                    "DataFrame from the trips data, then compute `result`: a dict mapping borough "
                    "-> total fare, using groupBy + sum. Convert with .collect() at the end. "
                    "No pandas — stay in Spark."
                ),
                "starter_code": (
                    "from pyspark.sql import SparkSession\n"
                    "from pyspark.sql import functions as F\n\n"
                    "spark = (SparkSession.builder.master('local[2]')\n"
                    "         .appName('exercise').getOrCreate())\n\n"
                    "trips = spark.createDataFrame(\n"
                    "    [('M', 10.0), ('B', 8.0), ('M', 20.0), ('Q', 5.0), ('B', 7.0)],\n"
                    "    ['borough', 'fare'])\n\n"
                    "result = ...  # {'M': 30.0, 'B': 15.0, 'Q': 5.0}\n"
                ),
                "check_code": (
                    "assert result == {'M': 30.0, 'B': 15.0, 'Q': 5.0}\n"
                    "spark.stop()\n"
                    "print('PASS: a real Spark job — driver built the plan, executors ran it')\n"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ 7
    {
        "id": "spark-at-scale",
        "num": 7,
        "title": "Spark at Scale",
        "tagline": "Shuffles, skew, caching and the Catalyst optimizer",
        "level": "Advanced",
        "tech": ["PySpark tuning", "shuffles", "broadcast joins", "caching", "Parquet"],
        "est_hours": 8,
        "brief": (
            "Scale the pipeline up and make it fast. You'll generate a 10M-row "
            "dataset, run real joins and window functions on the cluster, then "
            "learn performance the honest way: cause problems (skew, tiny files, "
            "fat shuffles) and fix them (broadcast joins, sensible partitioning, "
            "caching). The Spark UI stops being decoration and becomes your "
            "debugger."
        ),
        "milestones": [
            "Scale the generator to 10M rows written directly to Parquet; compare load time vs CSV and check partition counts on read.",
            "Join two ways: join trips to the small zones table normally, then with F.broadcast() — compare the physical plans (.explain) and the stage/shuffle counts in the UI.",
            "Window functions: rank each borough's zones by revenue per day (Window.partitionBy('borough','day').orderBy(...)) — check where the shuffle happens.",
            "Cache wisely: run three different aggregations off one cleaned DataFrame with and without .cache(); measure and explain the difference (check the Storage tab).",
            "Create skew: make 60% of trips belong to one zone, watch one task run forever in the UI, then fix it with salting (add a random suffix key, aggregate twice).",
            "Tune spark.sql.shuffle.partitions for this data size, and write a paragraph in your notebook: what did the default 200 cost you?",
        ],
        "under_the_hood": (
            "**Anatomy of a shuffle.** Map-side tasks write their output sorted "
            "into per-reducer buckets on local disk (shuffle write). Reduce-side "
            "tasks fetch their bucket from *every* mapper over the network "
            "(shuffle read), merge, and proceed. Disk + network + serialization: "
            "that's why one shuffle can dominate a job. A broadcast join removes "
            "the shuffle entirely by shipping the small table to every executor "
            "once — a hash map lookup instead of a cluster-wide re-sort.\n\n"
            "**Skew** is when one key (one partition) has most of the data: 199 "
            "tasks finish in seconds, task 200 runs for an hour, and the stage "
            "waits for the straggler. Salting splits the hot key into K sub-keys "
            "so the work spreads, at the cost of a second aggregation pass.\n\n"
            "**Catalyst & Tungsten.** Your DataFrame code becomes a logical plan; "
            "Catalyst rewrites it (pushes filters below joins, prunes unread "
            "columns — visible in .explain()), then Tungsten generates JVM "
            "bytecode operating on off-heap binary rows. This is why DataFrames "
            "beat RDD code and why .explain() is worth reading: you're reviewing "
            "the optimizer's work, not your own."
        ),
        "exercises": [
            {
                "id": "ss-1",
                "title": "Hash partitioner + skew detector",
                "instructions": (
                    "Implement `partition_keys(keys, n)`: assign each key to partition "
                    "hash(key) % n (use Python's hash), returning a list of n lists. Then "
                    "implement `skew_ratio(partitions)`: size of the biggest partition divided "
                    "by the average size (a perfectly balanced job scores 1.0)."
                ),
                "starter_code": (
                    "def partition_keys(keys, n):\n"
                    "    ...\n\n"
                    "def skew_ratio(partitions):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "parts = partition_keys(['a', 'b', 'c', 'd'] * 5, 4)\n"
                    "assert sum(len(p) for p in parts) == 20\n"
                    "for k in ['a', 'b', 'c', 'd']:\n"
                    "    homes = {i for i, p in enumerate(parts) if k in p}\n"
                    "    assert len(homes) == 1, 'same key must always land in the same partition'\n"
                    "assert abs(skew_ratio([[1]*90, [1]*5, [1]*5, []]) - 3.6) < 0.01\n"
                    "assert skew_ratio([[1]*10, [1]*10]) == 1.0\n"
                    "print('PASS: you can see why one hot key stalls a whole stage')\n"
                ),
            },
            {
                "id": "ss-2",
                "title": "Broadcast join by hand",
                "instructions": (
                    "Implement `broadcast_join(big_rows, small_table, key)`: build a dict index "
                    "of the small table ONCE, then stream the big rows and enrich each with the "
                    "matching small-table fields (inner join: drop rows with no match). "
                    "One pass over big_rows, no sorting — that's the whole trick."
                ),
                "starter_code": (
                    "def broadcast_join(big_rows, small_table, key):\n"
                    "    \"\"\"big_rows: iterable of dicts. small_table: list of dicts.\n"
                    "    Returns list of merged dicts (small fields added to big rows).\"\"\"\n"
                    "    ...\n"
                ),
                "check_code": (
                    "big = iter([{'zone': 1, 'fare': 10}, {'zone': 2, 'fare': 6}, {'zone': 9, 'fare': 1}])\n"
                    "small = [{'zone': 1, 'borough': 'M'}, {'zone': 2, 'borough': 'B'}]\n"
                    "out = broadcast_join(big, small, 'zone')\n"
                    "assert out == [{'zone': 1, 'fare': 10, 'borough': 'M'},\n"
                    "               {'zone': 2, 'fare': 6, 'borough': 'B'}]\n"
                    "print('PASS: index the small side, stream the big side — no shuffle needed')\n"
                ),
            },
            {
                "id": "ss-3",
                "title": "Read the optimizer's mind",
                "heavy": True,
                "instructions": (
                    "Catalyst pushes filters down below projections. Prove it: build the "
                    "DataFrame, select two columns THEN filter, capture the physical plan "
                    "string via df._jdf.queryExecution().executedPlan().toString() into "
                    "`plan`, and set `pushed = True` if the plan shows the Filter applied "
                    "at/near the scan (look for 'Filter' in the plan). Read the plan "
                    "bottom-up in the output."
                ),
                "starter_code": (
                    "from pyspark.sql import SparkSession\n"
                    "from pyspark.sql import functions as F\n\n"
                    "spark = (SparkSession.builder.master('local[2]')\n"
                    "         .appName('catalyst').getOrCreate())\n\n"
                    "df = spark.createDataFrame(\n"
                    "    [(i, 'M' if i % 2 else 'B', float(i)) for i in range(100)],\n"
                    "    ['id', 'borough', 'fare'])\n\n"
                    "q = df.select('borough', 'fare').filter(F.col('fare') > 50)\n\n"
                    "plan = ...   # the physical plan as a string\n"
                    "pushed = ...\n"
                    "print(plan)\n"
                ),
            "check_code": (
                    "assert isinstance(plan, str) and 'Filter' in plan\n"
                    "assert pushed is True\n"
                    "assert q.count() == 49\n"
                    "spark.stop()\n"
                    "print('PASS: you read a Catalyst physical plan — .explain() is your friend')\n"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------ 8
    {
        "id": "orchestrate-it",
        "num": 8,
        "title": "Orchestrate It (Capstone)",
        "tagline": "Airflow DAGs running your Spark pipeline, end to end",
        "level": "Advanced",
        "tech": ["Airflow", "DAGs", "scheduling", "idempotent tasks", "spark-submit"],
        "est_hours": 10,
        "brief": (
            "The capstone: your ETL becomes a scheduled, monitored, retryable "
            "production pipeline. Airflow (already in your Docker stack — start it "
            "with the command in the Environment panel, UI at localhost:8085, "
            "login admin/admin) will run a daily DAG: generate/ingest trips data, "
            "validate it, submit the Spark aggregation job to the cluster, load "
            "results to SQLite, and alert on failure. The project's airflow/dags "
            "folder is live-mounted into Airflow — save a file, refresh the UI, "
            "it's there."
        ),
        "milestones": [
            "Tour the included example: open dags/example_taxi_dag.py in the Airflow UI, read the graph view, trigger it manually, and read one task's logs.",
            "Author your DAG: taxi_daily with schedule '@daily', catchup=False, default retries=2 — tasks: ingest >> validate >> transform >> load.",
            "Make ingest date-aware: use the {{ ds }} template / context so each run processes ITS logical date's data — rerunning yesterday must not touch today (idempotency, again).",
            "Branch on quality: a validate task that raises AirflowSkipException (or branches) when the day's file is empty; watch downstream tasks skip in the UI.",
            "Go distributed: swap transform's local pandas for a spark-submit against spark://spark-master:7077 running your Project 7 job (BashOperator or SparkSubmitOperator — both shown in the example DAG).",
            "Operate it: set retries with exponential backoff, add an on_failure_callback that writes to a log file, then kill the Spark master mid-run and watch Airflow retry and recover.",
        ],
        "under_the_hood": (
            "**Airflow is a metadata machine.** Your DAG file is just Python that "
            "*declares* structure; the *scheduler* re-parses dag files every few "
            "seconds, computes which DagRuns are due, and flips TaskInstance rows "
            "in the metadata DB through a state machine: none → scheduled → queued "
            "→ running → success/failed/up_for_retry. The *executor* (LocalExecutor "
            "in your stack) forks worker processes that actually run task code. "
            "The webserver just renders the DB. When a task 'retries', nothing "
            "reruns your function magically — the scheduler simply sees "
            "up_for_retry + retry_delay elapsed and queues a fresh TaskInstance "
            "try.\n\n"
            "**The logical date.** A run with logical date 2026-07-26 executes "
            "*after* that day ends — it processes yesterday's data. {{ ds }} exists "
            "so a task is a pure function of its date: rerun any historical day "
            "and get the same result. That's why every task must be idempotent "
            "(Weather Watcher's lesson, now load-bearing).\n\n"
            "**Airflow orchestrates, Spark computes.** The DAG says *when* and "
            "*in what order*; heavy lifting happens elsewhere (spark-submit to "
            "the cluster). Keeping workers thin is what lets one small Airflow "
            "box coordinate terabyte pipelines."
        ),
        "exercises": [
            {
                "id": "oi-1",
                "title": "Build a mini-DAG resolver",
                "instructions": (
                    "Airflow's core in 25 lines. Implement `topo_order(deps)` where deps maps "
                    "task -> list of upstream tasks it depends on. Return a valid execution "
                    "order (every task after all its upstreams). Raise ValueError on a cycle. "
                    "Kahn's algorithm or DFS — your choice."
                ),
                "starter_code": (
                    "def topo_order(deps):\n"
                    "    \"\"\"deps: {'load': ['transform'], 'transform': ['ingest'], 'ingest': []}\"\"\"\n"
                    "    ...\n"
                ),
                "check_code": (
                    "order = topo_order({'load': ['transform', 'validate'],\n"
                    "                    'transform': ['ingest'], 'validate': ['ingest'], 'ingest': []})\n"
                    "assert set(order) == {'ingest', 'validate', 'transform', 'load'}\n"
                    "pos = {t: i for i, t in enumerate(order)}\n"
                    "assert pos['ingest'] < pos['transform'] < pos['load']\n"
                    "assert pos['ingest'] < pos['validate'] < pos['load']\n"
                    "try:\n"
                    "    topo_order({'a': ['b'], 'b': ['a']})\n"
                    "    raise AssertionError('cycle should raise ValueError')\n"
                    "except ValueError:\n"
                    "    pass\n"
                    "print('PASS: dependency resolution — the heart of every scheduler')\n"
                ),
            },
            {
                "id": "oi-2",
                "title": "Task state machine with retries",
                "instructions": (
                    "Implement `run_task(fn, retries)`: call fn() and return the list of states "
                    "the task passed through. Success on first try: ['running', 'success']. "
                    "Each failure appends 'up_for_retry' then 'running' again; after the final "
                    "allowed attempt fails, end with 'failed'. (retries=2 means up to 3 attempts.)"
                ),
                "starter_code": (
                    "def run_task(fn, retries=2):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert run_task(lambda: 'ok') == ['running', 'success']\n"
                    "n = {'v': 0}\n"
                    "def flaky():\n"
                    "    n['v'] += 1\n"
                    "    if n['v'] < 2: raise RuntimeError()\n"
                    "assert run_task(flaky) == ['running', 'up_for_retry', 'running', 'success']\n"
                    "def dead(): raise RuntimeError()\n"
                    "states = run_task(dead, retries=1)\n"
                    "assert states == ['running', 'up_for_retry', 'running', 'failed']\n"
                    "print('PASS: exactly how the scheduler walks TaskInstance states')\n"
                ),
            },
            {
                "id": "oi-3",
                "title": "Mini-scheduler: run a whole DAG",
                "instructions": (
                    "Combine both: implement `run_dag(deps, fns)` that executes tasks in "
                    "dependency order; if a task raises, mark it 'failed' and every downstream "
                    "task (direct or transitive) 'upstream_failed' without running it. Return "
                    "{task: state}. You've now written the essence of Airflow."
                ),
                "starter_code": (
                    "def run_dag(deps, fns):\n"
                    "    \"\"\"deps: task -> list of upstreams. fns: task -> callable.\n"
                    "    Returns task -> 'success' | 'failed' | 'upstream_failed'.\"\"\"\n"
                    "    ...\n"
                ),
                "check_code": (
                    "log = []\n"
                    "deps = {'ingest': [], 'validate': ['ingest'], 'transform': ['validate'], 'load': ['transform']}\n"
                    "fns = {'ingest': lambda: log.append('i'),\n"
                    "       'validate': lambda: (_ for _ in ()).throw(RuntimeError('bad data')),\n"
                    "       'transform': lambda: log.append('t'),\n"
                    "       'load': lambda: log.append('l')}\n"
                    "states = run_dag(deps, fns)\n"
                    "assert states == {'ingest': 'success', 'validate': 'failed',\n"
                    "                  'transform': 'upstream_failed', 'load': 'upstream_failed'}\n"
                    "assert log == ['i'], 'downstream tasks must not run after a failure'\n"
                    "print('PASS: capstone internals complete — you built a working mini-Airflow')\n"
                ),
            },
        ],
    },
]

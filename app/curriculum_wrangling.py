"""
Stage 5 additions — Data on One Machine (3 new projects joining Pandas
PowerPlant): real-world cleaning, DuckDB analytics, and feature engineering
(the bridge into the AI stage).
"""

STAGE5_PROJECTS = [
    # ------------------------------------------------------------------
    {
        "id": "cleanroom",
        "title": "Cleanroom",
        "tagline": "Messy real-world data: nulls, dupes, outliers, and lying dates",
        "level": "Intermediate+",
        "tech": ["pandas cleaning", "missing data", "outliers", "dtypes", "datetime"],
        "est_hours": 6,
        "brief": (
            "Production data is filthy — 80% of data work is cleaning, and "
            "interviews increasingly test it directly. Generate a deliberately "
            "corrupted customer/orders dataset (the generator script injects "
            "nulls, duplicate rows, '$1,234.56' strings, mixed date formats, "
            "impossible ages, trailing whitespace), then build a documented, "
            "rerunnable cleaning pipeline that turns it into typed, validated "
            "tables — logging every decision it makes."
        ),
        "milestones": [
            "Write make_mess.py: generate 50k clean rows then inject each corruption type at known rates — so you can verify your cleaning catches ~all of them.",
            "Profile before touching: df.info(), .describe(), .isna().sum(), duplicated().sum(), value_counts on suspicious columns — write a 10-line data-profile summary.",
            "Fix types: money strings → float (strip $ and commas), mixed dates → datetime with pd.to_datetime(format='mixed' / errors='coerce'), categoricals → category dtype; count coercion casualties.",
            "Handle missing data three ways on three columns — drop (when MCAR and rare), impute median (numeric), impute 'unknown' category — and justify each choice in comments.",
            "Dedup with intent: exact dupes via drop_duplicates, then near-dupes (same email, different case/whitespace) via normalized keys — st-2's canonical keys on real data.",
            "Outliers: flag ages outside [0, 120] and order amounts beyond 3 IQRs; decide flag-vs-drop-vs-cap per column and log counts of each action taken.",
        ],
        "under_the_hood": (
            "**Missingness has *mechanisms*.** MCAR (missing completely at "
            "random — a sensor blinked) is safe to drop or impute. MAR/MNAR "
            "(missing *because of* the value — rich people hide income) means "
            "imputation biases everything downstream; sometimes 'is_missing' "
            "itself is the most predictive feature you'll build in Feature "
            "Foundry. Diagnose before treating.\n\n"
            "**NaN mechanics that bite:** np.nan is a float — an int column with "
            "one null silently becomes float64 (pandas' nullable Int64 dtype "
            "fixes it); NaN != NaN (use isna(), never == np.nan); NaN sorts "
            "last-ish; groupby drops NaN keys by default (dropna=False to keep "
            "— a silent data-loss trap in reports).\n\n"
            "**The professional posture is a *pipeline*, not a session:** every "
            "cleaning decision as code, ordered, logged, rerunnable on next "
            "month's file (idempotency again). 'I fixed it in a notebook' is how "
            "the same mess returns forever; your Quality Gate project (Stage 6) "
            "turns today's assertions into automated contracts."
        ),
        "exercises": [
            {
                "id": "cr-1",
                "title": "Parse money and dates that lie",
                "instructions": (
"The two universal corruptions, handled robustly.\n\n**Your task**\n\n(1) "
"`parse_money(s)`: turn '$1,234.56', ' 1234.56 ', '1,234', or numbers into "
"float; None/empty/garbage → None (never raise). (2) `parse_date_any(s)`: "
"accept 'YYYY-MM-DD', 'DD/MM/YYYY', 'MM-DD-YYYY' and return ISO 'YYYY-MM-DD' "
"string or None. For the ambiguous '03/04/2026' the spec says day-first for "
"the slash format — real pipelines document exactly such contracts."
                ),
                "starter_code": (
                    "from datetime import datetime\n\n"
                    "def parse_money(s):\n"
                    "    ...\n\n"
                    "def parse_date_any(s):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "assert parse_money('$1,234.56') == 1234.56\n"
                    "assert parse_money(' 1234.56 ') == 1234.56\n"
                    "assert parse_money('1,234') == 1234.0\n"
                    "assert parse_money(99) == 99.0\n"
                    "assert parse_money('') is None and parse_money(None) is None\n"
                    "assert parse_money('N/A') is None\n"
                    "assert parse_date_any('2026-07-27') == '2026-07-27'\n"
                    "assert parse_date_any('27/07/2026') == '2026-07-27'\n"
                    "assert parse_date_any('03/04/2026') == '2026-04-03'   # day-first per spec\n"
                    "assert parse_date_any('07-27-2026') == '2026-07-27'\n"
                    "assert parse_date_any('garbage') is None\n"
                    "print('PASS: robust parsers — the unglamorous heart of every pipeline')\n"
                ),
                "refresher": (
"**Parsers must be total functions:** every input maps to value-or-None; "
"exceptions are for *your* bugs, not *their* data (lm-2's philosophy). The "
"money recipe: reject None/non-strings early, strip whitespace and '$', "
"remove ',', then try float() in a try/except:\n\n"
"```python\ndef parse_money(s):\n    if s is None: return None\n    if isinstance(s, (int, float)): return float(s)\n    s = str(s).strip().lstrip('$').replace(',', '')\n    try:\n        return float(s) if s else None\n    except ValueError:\n        return None\n```\n\n"
"Dates: try formats in a documented priority order with "
"`datetime.strptime`, catching ValueError per attempt — first success wins:\n\n"
"```python\nfor fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y'):\n    try: return datetime.strptime(s, fmt).strftime('%Y-%m-%d')\n    except (ValueError, TypeError): pass\nreturn None\n```\n\n"
"The deep lesson is the *ambiguity contract*: 03/04 is unparseable without "
"a declared convention — good pipelines write the convention down (and "
"reject at the source when possible). Count your Nones: a 0.1% parse-fail "
"rate is data noise; 40% means the format changed upstream — that "
"distinction is monitoring gold (Quality Gate will automate it)."
                ),
                "objectives": [
                    "Write total (never-raising) parsers with None as the failure value",
                    "Order date formats explicitly and document ambiguity contracts",
                    "Treat parse-failure rates as pipeline health signals",
                ],
                "hints": [
                    "Money: handle None → numeric passthrough → strip/replace → try float.",
                    "Dates: loop the three formats with strptime; return strftime('%Y-%m-%d') of the first hit.",
                    "'%d/%m/%Y' must come before any month-first slash format — the spec says day-first.",
                ],
                "resources": [
                    {"title": "strptime format codes", "url": "https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes"},
                    {"title": "pandas.to_datetime (the vectorized version)", "url": "https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html"},
                ],
            },
            {
                "id": "cr-2",
                "title": "Impute with judgment",
                "instructions": (
"Missing-data strategy as code.\n\n**Your task**\n\nWrite "
"`clean_missing(df)` for a DataFrame with columns `age` (numeric, some NaN), "
"`country` (strings, some NaN), `email` (some NaN): fill age NaNs with the "
"**median** age; fill country NaNs with `'unknown'`; **drop** rows missing "
"email (it's the entity key — an unkeyed row is unusable). Return "
"(cleaned_df, report) where report is "
"`{'age_filled': n, 'country_filled': n, 'rows_dropped': n}` — cleaning "
"without a report is cleaning you can't trust."
                ),
                "starter_code": (
                    "import pandas as pd\n"
                    "import numpy as np\n\n"
                    "def clean_missing(df):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "df = pd.DataFrame({\n"
                    "    'age': [20, np.nan, 40, np.nan, 30],\n"
                    "    'country': ['ZW', None, 'ZA', 'KE', None],\n"
                    "    'email': ['a@x.com', 'b@x.com', None, 'd@x.com', 'e@x.com'],\n"
                    "})\n"
                    "out, report = clean_missing(df)\n"
                    "assert report == {'age_filled': 2, 'country_filled': 2, 'rows_dropped': 1}, report\n"
                    "assert len(out) == 4 and out['email'].notna().all()\n"
                    "# drop-first, then impute: surviving ages are [20, nan, nan, 30] -> median 25\n"
                    "assert out['age'].tolist() == [20.0, 25.0, 25.0, 30.0], out['age'].tolist()\n"
                    "assert out['country'].tolist() == ['ZW', 'unknown', 'KE', 'unknown']\n"
                    "print('PASS: strategy-per-column imputation with an audit trail')\n"
                ),
                "refresher": (
"**Order of operations matters and must be declared.** Here: drop unkeyed "
"rows FIRST, then impute — otherwise dropped rows pollute the median and "
"your counts (the checker's expected ages only work drop-first: median of "
"the surviving [20, NaN, NaN, 30] candidates... work it through — that "
"kind of trace-by-hand is exactly how you debug cleaning code).\n\n"
"```python\nreport = {}\nkeyed = df[df['email'].notna()].copy()\nreport['rows_dropped'] = len(df) - len(keyed)\nmed = keyed['age'].median()\nreport['age_filled'] = int(keyed['age'].isna().sum())\nkeyed['age'] = keyed['age'].fillna(med)\n...\n```\n\n"
"Why median not mean: robust to the outliers you haven't cleaned yet "
"(one age=999 drags the mean, barely moves the median). Why 'unknown' not "
"mode for country: fabricating the most common country *biases* "
"downstream aggregates; an honest 'unknown' bucket keeps the uncertainty "
"visible. And the report dict is the difference between a script and a "
"pipeline — those counts become your monitoring time-series (sudden jump "
"in rows_dropped = upstream breakage), and in ML contexts the fill "
"decisions must be *fit on training data only* (Feature Foundry's leakage "
"lesson, incoming)."
                ),
                "objectives": [
                    "Sequence drop-then-impute deliberately and defend the order",
                    "Choose median/sentinel/drop per column with stated reasons",
                    "Emit cleaning reports as future monitoring signals",
                ],
                "hints": [
                    "Filter email-notna FIRST (copy!), count dropped as the length difference.",
                    "age: compute median on the kept frame, count isna before filling.",
                    "Return the report with exact keys: age_filled, country_filled, rows_dropped.",
                ],
                "resources": [
                    {"title": "pandas: working with missing data", "url": "https://pandas.pydata.org/docs/user_guide/missing_data.html"},
                    {"title": "Missingness mechanisms (MCAR/MAR/MNAR)", "url": "https://en.wikipedia.org/wiki/Missing_data"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"You receive a daily CSV of transactions from a partner. One day revenue "
"drops 30% in your dashboard. Walk through your debugging process — data "
"engineering's most common fire."
                ),
                "difficulty": "Medium",
                "topics": ["data debugging", "pipelines"],
                "answer": (
"Work the pipeline backwards with row counts and checksums at each stage: "
"(1) Dashboard/query layer — did logic or filters change? (2) Warehouse "
"tables — row count and SUM(amount) per day vs history; is the drop in "
"rows, in amounts, or in a segment? (3) Load stage — parse-failure/"
"coercion counts (a format change silently nulling amounts?), dedup "
"suddenly dropping more (partner started resending?), timezone shift "
"moving rows across the day boundary. (4) The raw file itself — size, "
"line count, checksum vs yesterday; open the actual bytes (delimiter "
"change? truncated upload? headers moved?). (5) The partner — schema "
"change announcement buried in email. Then: add the checks that would "
"have caught it automatically (file-size/row-count/sum anomaly alerts, "
"parse-failure-rate thresholds) — the fire drill becomes a monitor."
                ),
                "explanation": (
"Interviewers want a *systematic bisection*, not guesses: localize the "
"loss between stages using conserved quantities (counts, sums) — the "
"same invariant thinking as validate_grain. The strongest closers state "
"the base rates: it's the source file the majority of the time (partners "
"change formats without notice), timezone/day-boundary second, silent "
"coercion third. Converting the incident into permanent automated checks "
"(and a data contract with the partner) is the answer's mic-drop — "
"that's the Quality Gate mindset and precisely what 'senior' means "
"operationally."
                ),
            },
            {
                "question": (
"A junior teammate ran df.dropna() on the whole customer table 'to clean "
"it' before an LTV analysis and lost 60% of rows. Explain everything wrong "
"with that, and the professional alternative."
                ),
                "difficulty": "Easy",
                "topics": ["missing data", "bias"],
                "answer": (
"Problems: (1) blanket dropna removes rows missing ANY column — including "
"columns irrelevant to LTV (a missing fax number deletes a customer); "
"(2) it silently biases the sample if missingness correlates with the "
"target (newer customers lack history → analysis skews to veterans — MAR/"
"MNAR); (3) it's undocumented and unreproducible — no report of what died "
"and why. Professional alternative: per-column strategy driven by the "
"analysis's needs — subset dropna only on columns the LTV computation "
"actually requires (`dropna(subset=['signup_date', 'revenue'])`), impute "
"where defensible (median/sentinel with the choice logged), consider "
"missingness-as-signal (an 'is_missing' flag), and always report counts "
"per action so reviewers see the data's shape change."
                ),
                "explanation": (
"An easy question that efficiently separates practitioners from "
"course-completers: the subset argument, the bias mechanism, and the "
"audit trail are all things you only internalize by having been burned. "
"Bonus points for asking WHY the values are missing before choosing "
"treatment (mechanism first — MCAR tolerates deletion, MNAR doesn't), "
"and for noting that in an ML setting imputation parameters are fit on "
"train only. The one-line summary interviewers remember: 'dropna is a "
"per-question decision, never a per-table one.'"
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "duckdb-turbo",
        "title": "DuckDB Turbo",
        "tagline": "SQL directly on files: the embedded analytics engine",
        "level": "Intermediate+",
        "tech": ["DuckDB", "SQL on Parquet/CSV", "columnar execution", "pandas interop"],
        "est_hours": 5,
        "brief": (
            "DuckDB is 'SQLite for analytics' — a zero-server columnar engine "
            "that queries CSV/Parquet files directly at astonishing speed, and "
            "it's taking over the small-to-medium data world. Re-run your Pandas "
            "PowerPlant analytics as SQL over the same files, benchmark the "
            "difference, and learn the query-the-files-where-they-lie pattern "
            "that previews the lakehouse (Stage 7). It's installed in the app "
            "and Jupyter already."
        ),
        "milestones": [
            "duckdb.sql(\"SELECT * FROM 'trips.csv' LIMIT 5\") — no server, no load step; then query the parquet version and compare cold-start times.",
            "Port three Pandas PowerPlant analyses to DuckDB SQL (joins, groupbys, a window function) — verify identical results against pandas.",
            "Benchmark honestly: pandas vs DuckDB on the 1M-row groupby, cold and warm; then try 10M rows and note where pandas hits memory walls while DuckDB streams.",
            "Interop: duckdb.sql(...).df() → pandas for plotting; query an existing pandas DataFrame FROM duckdb (it reads the object in-place, zero-copy) — mix freely by strength.",
            "Query a *folder* of parquet files with a glob ('data/2026-*.parquet') and use hive partitioning — the lakehouse read pattern, one machine early.",
        ],
        "under_the_hood": (
            "**Vectorized columnar execution:** DuckDB processes data in ~2048-row "
            "column vectors flowing through operators — small enough for CPU "
            "cache, big enough to amortize dispatch (pandas' pp-1 lesson, "
            "engine-ified). Morsel-driven parallelism spreads vectors across "
            "cores automatically — pandas mostly single-cores unless you bring "
            "extra machinery.\n\n"
            "**Out-of-core:** operators spill to disk when memory runs short, so "
            "10GB files on an 8GB laptop *work* — slow beats crash. Pandas wants "
            "everything resident (plus copies during operations — the real "
            "killer). DuckDB also pushes filters and projections INTO file "
            "readers: parquet row-group min/max stats let it skip chunks "
            "entirely (your ag-3 binary-search instinct as I/O pruning).\n\n"
            "**Why this matters strategically:** the 'small data' majority of "
            "real workloads (<100GB) fits one beefy machine now — DuckDB-class "
            "tools often beat a Spark cluster on cost, latency, and simplicity "
            "there. The professional skill is knowing WHERE the crossover to "
            "distributed genuinely lives, and not paying cluster tax below it."
        ),
        "exercises": [
            {
                "id": "dt-1",
                "title": "SQL on a DataFrame, zero copies",
                "instructions": (
"The interop superpower.\n\n**Your task**\n\nUsing duckdb, query the pandas "
"DataFrame `trips` (defined in starter) **directly by name** in SQL — no "
"loading, no conversion. Produce `result` (a pandas DataFrame via .df()) "
"with columns `(borough, total)` = total fare per borough, ordered total "
"descending. DuckDB resolves the name `trips` from your Python scope — "
"replacement scans read the DataFrame's columns in place."
                ),
                "starter_code": (
                    "import duckdb\n"
                    "import pandas as pd\n\n"
                    "trips = pd.DataFrame({\n"
                    "    'borough': ['M', 'B', 'M', 'Q', 'B', 'M'],\n"
                    "    'fare':    [10.0, 8.0, 20.0, 5.0, 7.0, 2.0],\n"
                    "})\n\n"
                    "result = ...  # duckdb.sql(...).df()\n"
                ),
                "check_code": (
                    "assert list(result.columns) == ['borough', 'total']\n"
                    "assert result['borough'].tolist() == ['M', 'B', 'Q']\n"
                    "assert result['total'].tolist() == [32.0, 15.0, 5.0]\n"
                    "print('PASS: SQL over a live DataFrame — two tools, one workflow')\n"
                ),
                "refresher": (
"**Replacement scans:** when DuckDB meets an unknown table name, it checks "
"the calling Python frame for a matching DataFrame/Arrow object and reads "
"its columns *in place* (columnar → columnar, near-zero copy):\n\n"
"```python\nresult = duckdb.sql('''\n    SELECT borough, SUM(fare) AS total\n    FROM trips\n    GROUP BY borough\n    ORDER BY total DESC\n''').df()\n```\n\n"
"The workflow this unlocks — and why it's spreading through data teams: "
"pandas for what it's best at (I/O quirks, quick column surgery, "
"plotting), SQL for what IT'S best at (joins, windows, aggregations that "
"read like the business question), switching per-operation with no "
"serialization tax. Your entire Stage-3 SQL arsenal now applies to any "
"DataFrame in memory.\n\n"
"Same trick works on files — `FROM 'data/*.parquet'` — and across: join "
"a DataFrame to a parquet file to a Postgres table (duckdb's postgres "
"extension) in ONE query. That federated-query instinct previews the "
"lakehouse and is a genuinely modern answer to 'how would you explore "
"this data?' in interviews."
                ),
                "objectives": [
                    "Query in-memory DataFrames via replacement scans",
                    "Choose pandas vs SQL per operation, not per project",
                    "Recognize federated file/DataFrame/DB queries as an exploration pattern",
                ],
                "hints": [
                    "duckdb.sql(query_string).df() — the string references trips by name.",
                    "Alias the SUM as total and ORDER BY total DESC to match the checker.",
                ],
                "resources": [
                    {"title": "DuckDB Python API", "url": "https://duckdb.org/docs/api/python/overview"},
                    {"title": "DuckDB + pandas guide", "url": "https://duckdb.org/docs/guides/python/sql_on_pandas"},
                ],
            },
            {
                "id": "dt-2",
                "title": "Predicate pushdown you can measure",
                "instructions": (
"Prove the engine skips work.\n\n**Your task**\n\nImplement "
"`rows_scanned_estimate(row_groups, predicate_min, predicate_max)`: "
"row_groups is a list of dicts {'rows': n, 'min': lo, 'max': hi} (parquet "
"row-group stats on some column). Return how many rows a smart reader must "
"actually scan for `WHERE col BETWEEN predicate_min AND predicate_max` — "
"skipping groups whose [min, max] range doesn't overlap the predicate "
"range. Also return (as a tuple) the naive full-scan count. This is "
"EXACTLY the arithmetic DuckDB/Spark do before touching disk."
                ),
                "starter_code": (
                    "def rows_scanned_estimate(row_groups, predicate_min, predicate_max):\n"
                    "    \"\"\"Return (scanned_rows, total_rows).\"\"\"\n"
                    "    ...\n"
                ),
                "check_code": (
                    "groups = [\n"
                    "    {'rows': 1000, 'min': 0,   'max': 99},\n"
                    "    {'rows': 1000, 'min': 100, 'max': 199},\n"
                    "    {'rows': 1000, 'min': 200, 'max': 299},\n"
                    "    {'rows': 1000, 'min': 150, 'max': 250},   # overlapping ranges happen!\n"
                    "]\n"
                    "assert rows_scanned_estimate(groups, 120, 180) == (2000, 4000)\n"
                    "assert rows_scanned_estimate(groups, 0, 300) == (4000, 4000)\n"
                    "assert rows_scanned_estimate(groups, 500, 600) == (0, 4000)\n"
                    "assert rows_scanned_estimate(groups, 199, 200) == (3000, 4000)\n"
                    "print('PASS: min/max pruning — why sorted/partitioned data is fast data')\n"
                ),
                "refresher": (
"**Interval overlap, the one-liner worth memorizing:** ranges [a,b] and "
"[c,d] overlap iff `a <= d and c <= b`:\n\n"
"```python\nscanned = sum(g['rows'] for g in row_groups\n              if g['min'] <= predicate_max\n              and predicate_min <= g['max'])\ntotal = sum(g['rows'] for g in row_groups)\n```\n\n"
"Parquet writes min/max (plus null counts) per row group (~100k rows) in "
"the file footer; engines read footers first and skip non-overlapping "
"groups — zero I/O for excluded data. Two design consequences that make "
"this a *practitioner's* topic, not trivia: (1) pruning power depends on "
"**data layout** — if the column is randomly scattered, every group's "
"range is [global_min, global_max] and nothing prunes (your 4th test "
"group!); sorting or partitioning by common filter columns (usually "
"date) is what turns stats into skipped terabytes. (2) The same math "
"runs everywhere: Postgres BRIN indexes, Iceberg/Delta file stats, "
"ClickHouse marks. 'Sort your data by how you query it' — now you know "
"the mechanism behind the slogan."
                ),
                "objectives": [
                    "Apply interval-overlap logic to row-group pruning",
                    "Explain why data layout (sorting/partitioning) determines pruning power",
                    "Name the pruning family: parquet stats, BRIN, Iceberg/Delta manifests",
                ],
                "hints": [
                    "Overlap test: g['min'] <= predicate_max AND predicate_min <= g['max'].",
                    "Sum rows of overlapping groups; total is the sum over all groups; return the tuple.",
                ],
                "resources": [
                    {"title": "Parquet file format (row groups & stats)", "url": "https://parquet.apache.org/docs/file-format/"},
                    {"title": "DuckDB: parquet filter pushdown", "url": "https://duckdb.org/docs/data/parquet/overview"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"Your team runs a nightly Spark job on a 3-node cluster to aggregate 20GB "
"of daily parquet into reports; it takes 25 minutes and fails weekly. A "
"colleague suggests replacing it with DuckDB on one large VM. Evaluate."
                ),
                "difficulty": "Medium",
                "topics": ["right-sizing", "DuckDB vs Spark"],
                "answer": (
"Almost certainly a good trade. 20GB is comfortably single-node: DuckDB "
"will likely finish in low single-digit minutes (no cluster startup, no "
"shuffle over network, vectorized + out-of-core), operational surface "
"shrinks from cluster+scheduler-integration to one process, and weekly "
"failure modes (executor OOMs, shuffle fetch failures) vanish. Checklist "
"before committing: peak intermediate memory (joins/windows may exceed "
"20GB — DuckDB spills, but measure), growth trajectory (at 10x yearly "
"growth the cluster returns — keep the SQL portable), concurrent "
"downstream needs (DuckDB is in-process, not a multi-tenant server), and "
"integration (Airflow runs it as easily as spark-submit). Migration risk "
"is low because both speak SQL — port, run both in parallel for a week, "
"diff outputs."
                ),
                "explanation": (
"This question tests whether you size solutions to data, not resumes. "
"The numbers matter: modern single machines (100+ GB RAM, dozens of "
"cores, NVMe) cover the substantial majority of real-world batch jobs, "
"and distributed overhead (shuffles, serialization, coordination, "
"failure surface) is a real cost paid every night. The strong answer "
"keeps Spark for what clusters are FOR (data that truly exceeds one "
"machine, or wide-shuffle workloads) and names the parallel-run "
"validation as the professional migration pattern. Bonus: 'keep the SQL "
"dialect portable' shows you plan for reversal — engineering humility "
"interviewers notice."
                ),
            },
            {
                "question": (
"Why is the same GROUP BY query often 10-50x faster in DuckDB than in "
"pandas on identical data? Be specific about the engine differences."
                ),
                "difficulty": "Medium",
                "topics": ["execution engines", "vectorization"],
                "answer": (
"Four compounding reasons: **(1) Parallelism** — DuckDB's morsel-driven "
"scheduler uses all cores; pandas groupby is largely single-threaded. "
"**(2) Pipelined vectorized execution** — 2048-row vectors flow through "
"fused operators staying in L1/L2 cache; pandas materializes full "
"intermediate arrays per step (filter → whole boolean mask → whole "
"copied frame), churning memory bandwidth. **(3) No copies** — pandas "
"operations frequently copy columns (and its groupby builds Python-level "
"machinery per group in some paths); DuckDB's hash aggregate is one "
"tight loop over vectors. **(4) Smarter aggregation** — a proper "
"cost-based hash-aggregate with perfect-hash optimizations for "
"low-cardinality keys, plus spilling when groups exceed memory instead "
"of dying."
                ),
                "explanation": (
"The question rewards mechanism-level answers over 'DuckDB is "
"optimized'. Connect it to fundamentals you can defend: pp-1's "
"vectorization argument (interpreter dispatch amortization) applies to "
"BOTH — but pandas vectorizes per-operation while DuckDB vectorizes the "
"whole *pipeline*, avoiding intermediate materialization (the "
"generator-vs-list lesson from LogMiner at the engine level!). Honest "
"caveats show depth: pandas wins at many small operations (no query "
"startup), string-heavy custom Python logic, and API ergonomics for "
"exploration — which is why the answer to 'pandas or DuckDB' is 'both, "
"per operation' (dt-1)."
                ),
            },
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "feature-foundry",
        "title": "Feature Foundry",
        "tagline": "Feature engineering: turning raw data into model food — without leakage",
        "level": "Intermediate+",
        "tech": ["feature engineering", "encoding", "scaling", "leakage", "train/test discipline"],
        "est_hours": 6,
        "brief": (
            "The bridge from data engineering to machine learning — and where "
            "most real-world ML failures are born. From the warehouse's "
            "customers/orders, engineer features to predict churn-like labels: "
            "recency/frequency/monetary aggregates, categorical encodings, "
            "scaling — with the train/test discipline that prevents leakage, "
            "the silent killer that makes models ace offline tests and flop in "
            "production. Everything here feeds Model Factory (Stage 9)."
        ),
        "milestones": [
            "Build the label + snapshot date: define 'churned = no completed order in the 90 days after 2026-01-01' — and internalize why every feature may only use data BEFORE that date.",
            "RFM features with pure SQL/pandas as-of the snapshot: days-since-last-order, order count, total/avg spend, distinct categories bought.",
            "Encode categoricals: one-hot country (pd.get_dummies), and target-encode product-category-preference the SAFE way (fit on train only) — demonstrate the leak by doing it wrong first and comparing scores.",
            "Scale numerics with StandardScaler FIT ON TRAIN ONLY, transform both splits; show what fitting on all data changes (peeking at test distribution).",
            "Package it: a build_features(customers, orders, snapshot_date) function returning (X_train, X_test, y_train, y_test) with a fixed random_state — your Model Factory input.",
        ],
        "under_the_hood": (
            "**Leakage = information from the future (or the label) reaching "
            "features.** The three classic vectors: *temporal* (aggregates "
            "computed over data after the snapshot date — 'days since last "
            "order' accidentally including post-label orders), *preprocessing* "
            "(fitting scalers/encoders/imputers on ALL data — test-set "
            "statistics leak into training via the transform), and *target* "
            "(features derived from the label — target encoding without "
            "cross-fitting memorizes labels). Offline metrics soar; production "
            "craters. The discipline: a hard snapshot date, fit-on-train-only "
            "for every fitted transform, and sklearn Pipelines to make the "
            "discipline structural rather than willpower.\n\n"
            "**Why encodings exist:** models eat numbers. One-hot keeps "
            "categories orthogonal but explodes width on high cardinality; "
            "target encoding compresses to one informative column but is "
            "leakage-prone (cross-fold fitting mitigates); embeddings (Stage 9) "
            "learn the geometry. Scaling matters for distance/gradient-based "
            "models (kNN, SVM, neural nets, regularized linear) and not for "
            "trees — knowing WHICH is interview table stakes.\n\n"
            "**Point-in-time correctness** is where DE meets ML: production "
            "feature stores exist to answer 'what did we know about entity X "
            "at time T?' — your SCD2 valid_from/valid_to machinery (Star "
            "Schema Studio) is exactly how they do it. Features are pipelines; "
            "everything you've learned about idempotency and grain applies."
        ),
        "exercises": [
            {
                "id": "ff-1",
                "title": "RFM features, point-in-time correct",
                "instructions": (
"The bread-and-butter customer features, with the temporal discipline that "
"makes them honest.\n\n**Your task**\n\nImplement `rfm_features(orders, "
"snapshot)`: orders is a list of dicts {customer_id, order_date "
"('YYYY-MM-DD'), amount}; snapshot is a date string. Using ONLY orders "
"strictly before the snapshot, return {customer_id: {'recency_days': days "
"from last order to snapshot, 'frequency': count, 'monetary': total "
"amount}}. Customers with no pre-snapshot orders are absent. The checker "
"plants a post-snapshot order that MUST NOT leak in."
                ),
                "starter_code": (
                    "from datetime import date\n\n"
                    "def rfm_features(orders, snapshot):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "orders = [\n"
                    "    {'customer_id': 1, 'order_date': '2025-12-01', 'amount': 100.0},\n"
                    "    {'customer_id': 1, 'order_date': '2025-12-21', 'amount': 50.0},\n"
                    "    {'customer_id': 2, 'order_date': '2025-06-01', 'amount': 20.0},\n"
                    "    {'customer_id': 1, 'order_date': '2026-01-15', 'amount': 999.0},  # AFTER snapshot!\n"
                    "    {'customer_id': 3, 'order_date': '2026-02-01', 'amount': 10.0},   # entirely after\n"
                    "]\n"
                    "out = rfm_features(orders, '2026-01-01')\n"
                    "assert out[1] == {'recency_days': 11, 'frequency': 2, 'monetary': 150.0}, out.get(1)\n"
                    "assert out[2] == {'recency_days': 214, 'frequency': 1, 'monetary': 20.0}\n"
                    "assert 3 not in out, 'future customer leaked in!'\n"
                    "print('PASS: point-in-time features — the leak, prevented at the source')\n"
                ),
                "refresher": (
"**The snapshot is a wall.** Every feature answers 'what did we know at "
"time T?' — one filter, applied first, before any aggregation:\n\n"
"```python\nsnap = date.fromisoformat(snapshot)\npast = [o for o in orders\n        if date.fromisoformat(o['order_date']) < snap]\n```\n\n"
"Then plain grouping (your eternal dict-of-accumulators) computes R, F, M "
"per customer; recency is `(snap - last_order_date).days`. `date.fromiso"
"format` + date subtraction giving `.days` is the stdlib datemath you'll "
"use forever.\n\n"
"Why the checker's trap matters more than it looks: in real projects the "
"orders table *keeps growing after you define the label*, so any code "
"that computes features from 'the table' rather than 'the table as-of T' "
"silently improves as time passes — your model learns from the future it "
"is supposed to predict, validation looks great, production doesn't. "
"This bug has shipped at every company you've heard of. The fix is "
"structural, not vigilant: snapshot parameters on every feature "
"function, and (at scale) a feature store keyed by (entity, as_of_time) "
"— SCD2's question again. When an interviewer asks 'how do you prevent "
"leakage?', 'point-in-time joins with an explicit snapshot' is the "
"answer they're fishing for."
                ),
                "objectives": [
                    "Enforce as-of-time filtering before any feature computation",
                    "Compute RFM with stdlib date arithmetic",
                    "Explain temporal leakage's mechanism and its structural fix",
                ],
                "hints": [
                    "Parse and filter FIRST: keep orders with date < snapshot (strictly).",
                    "Group by customer: track last_date (max), count, sum.",
                    "recency_days = (snapshot_date - last_date).days after the loop.",
                ],
                "resources": [
                    {"title": "datetime.date docs", "url": "https://docs.python.org/3/library/datetime.html#date-objects"},
                    {"title": "Data leakage (sklearn's guide)", "url": "https://scikit-learn.org/stable/common_pitfalls.html#data-leakage"},
                ],
            },
            {
                "id": "ff-2",
                "title": "Fit-on-train-only scaler",
                "instructions": (
"Preprocessing leakage, built and prevented by hand.\n\n**Your task**\n\n"
"Implement `Scaler` with `.fit(values)` (learn mean and std — population "
"std, ddof=0) and `.transform(values)` (return [(x-mean)/std]; std of 0 → "
"return zeros; transform before fit → raise RuntimeError). Then "
"`safe_split_scale(train, test)` returning (train_scaled, test_scaled) "
"where the scaler is fitted ON TRAIN ONLY and applied to both. The checker "
"verifies test scaling uses TRAIN statistics — the whole point."
                ),
                "starter_code": (
                    "import math\n\n"
                    "class Scaler:\n"
                    "    def __init__(self):\n"
                    "        self.mean = None\n"
                    "        self.std = None\n\n"
                    "    def fit(self, values):\n"
                    "        ...\n\n"
                    "    def transform(self, values):\n"
                    "        ...\n\n"
                    "def safe_split_scale(train, test):\n"
                    "    ...\n"
                ),
                "check_code": (
                    "s = Scaler()\n"
                    "try:\n"
                    "    s.transform([1.0])\n"
                    "    raise AssertionError('transform before fit must raise')\n"
                    "except RuntimeError:\n"
                    "    pass\n"
                    "train = [10.0, 20.0, 30.0]        # mean 20, std ~8.165\n"
                    "test = [20.0, 40.0]\n"
                    "tr, te = safe_split_scale(train, test)\n"
                    "assert abs(tr[0] + 1.2247) < 0.001 and abs(tr[1]) < 1e-9\n"
                    "assert abs(te[0]) < 1e-9, 'test 20.0 must scale with TRAIN mean (20), giving 0'\n"
                    "assert abs(te[1] - 2.4495) < 0.001, 'test 40.0 with train stats: (40-20)/8.165'\n"
                    "s2 = Scaler(); s2.fit([5.0, 5.0])\n"
                    "assert s2.transform([5.0, 7.0]) == [0.0, 0.0], 'zero std -> zeros'\n"
                    "print('PASS: train statistics only — preprocessing leakage, structurally impossible')\n"
                ),
                "refresher": (
"**Why fitting on everything is cheating:** the scaler's mean/std are "
"*learned parameters*. Fit them on train+test and your training pipeline "
"has numerically absorbed the test distribution — a subtle peek that "
"inflates validation scores, worst on small data and drifting "
"distributions (exactly when honest evaluation matters most). The rule "
"generalizes to every fitted transform: imputers (cr-2's medians!), "
"encoders, PCA, vocabulary building.\n\n"
"```python\ndef safe_split_scale(train, test):\n    s = Scaler()\n    s.fit(train)                       # learn from train ONLY\n    return s.transform(train), s.transform(test)\n```\n\n"
"The fit/transform split is sklearn's core API design — and the reason "
"`Pipeline` exists: bundle scaler+model so cross-validation re-fits the "
"scaler *inside each fold* automatically (fitting once outside the CV "
"loop leaks across folds — the subtler variant that catches "
"intermediates). The RuntimeError-before-fit and zero-std guards mirror "
"sklearn's NotFittedError and variance floor: production feature code "
"is mostly these edge cases. Interview sound bite that lands: 'anything "
"with .fit() sees only training data, and Pipelines enforce it inside "
"CV' — that one sentence covers the majority of leakage questions."
                ),
                "objectives": [
                    "Implement the fit/transform contract with guards",
                    "Apply train-only fitting and articulate why",
                    "Explain Pipelines' role in fold-safe preprocessing",
                ],
                "hints": [
                    "fit: mean = sum/n; std = sqrt(sum((x-mean)^2)/n) — population (ddof=0).",
                    "transform: raise RuntimeError if mean is None; if std == 0 return [0.0]*len.",
                    "safe_split_scale: ONE scaler, fitted on train, transforming both.",
                ],
                "resources": [
                    {"title": "sklearn: common pitfalls & leakage", "url": "https://scikit-learn.org/stable/common_pitfalls.html"},
                    {"title": "sklearn Pipeline", "url": "https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html"},
                ],
            },
        ],
        "interview": [
            {
                "question": (
"A model predicting loan defaults achieved 0.94 AUC offline but performs "
"barely better than random in production. List the most likely causes in "
"priority order and how you'd confirm each."
                ),
                "difficulty": "Hard",
                "topics": ["leakage", "evaluation", "drift"],
                "answer": (
"Priority order: **(1) Temporal leakage** — features computed over data "
"unavailable at prediction time (post-application payment behavior, "
"account status fields that get backfilled after default). Confirm: audit "
"every feature's availability timestamp vs prediction time; retrain with "
"strict point-in-time joins and watch AUC fall to honest levels. **(2) "
"Target leakage** — a feature that's a proxy for the label (e.g. "
"'collections_flag'). Confirm: feature importance — leaky features "
"dominate suspiciously; drop-and-retrain. **(3) Evaluation mismatch** — "
"random train/test split on temporal data lets the model interpolate "
"within time; production extrapolates forward. Confirm: re-evaluate with "
"a time-based split (train past → test future). **(4) Serving skew** — "
"training features computed in SQL, serving features in app code, with "
"drifting definitions. Confirm: log served features, diff against "
"pipeline recomputation. **(5) Genuine drift** — population changed. "
"Confirm: feature distribution monitoring (PSI) between training and "
"live data."
                ),
                "explanation": (
"The 0.94-offline/random-online signature is leakage's fingerprint until "
"proven otherwise — genuine drift degrades gradually, leakage collapses "
"instantly because the 'information from the future' simply doesn't "
"exist at serving time. The confirm-steps matter as much as the causes: "
"each is a cheap, decisive experiment, and 'time-based split' is the "
"single highest-value habit change (random splits on temporal data are "
"the root of most inflated offline metrics). Mentioning feature-"
"availability audits and training/serving feature logging shows you've "
"operated models, not just fitted them — that's what the question is "
"really testing in a data-engineering loop."
                ),
            },
            {
                "question": (
"You have a categorical feature 'merchant_id' with 500k distinct values "
"in a fraud model. One-hot is impossible. Compare your realistic options "
"and their failure modes."
                ),
                "difficulty": "Medium",
                "topics": ["high-cardinality encoding"],
                "answer": (
"**Frequency/count encoding** — replace id with occurrence count: cheap, "
"leakage-safe-ish (fit on train), loses identity (two different merchants "
"with equal counts collide); good baseline. **Target encoding** — "
"replace with smoothed mean fraud rate per merchant: powerful, but "
"leakage-prone (must cross-fit: encode each fold using other folds' "
"stats, plus smoothing toward the global mean for rare merchants — a "
"merchant seen 3 times with 1 fraud would otherwise get an extreme, "
"memorized value). **Hashing trick** — hash ids into ~2^18 buckets: "
"bounded width, handles unseen merchants natively, collisions add noise "
"(usually tolerable, undebuggable when not). **Learned embeddings** — an "
"embedding layer if using neural nets, or pretrained entity embeddings: "
"most expressive, needs volume per merchant and MLOps maturity. "
"Realistic answer: frequency + cross-fitted smoothed target encoding for "
"trees; hashing for linear/online models; and always an 'unseen "
"merchant' strategy, since production WILL send new ids on day one."
                ),
                "explanation": (
"This is the applied-ML question data engineers actually get, because "
"the encodings are *pipelines* — the DE owns the cross-fitting "
"machinery, the smoothing parameters, and the unseen-value handling. "
"Interviewers listen for: the leakage story on target encoding told "
"precisely (rare-category memorization + the cross-fit fix), collisions "
"as the hashing trade, and the unseen-id contingency (the deployment "
"detail course-work forgets). The meta-point worth saying: "
"high-cardinality encoding choices interact with the model family — "
"trees split on target-encoded values beautifully, linear models like "
"hashed sparse features — 'it depends' with mechanisms is the senior "
"answer."
                ),
            },
        ],
    },
]

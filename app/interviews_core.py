"""
Interview Q&A for the original 8 projects — LeetCode-standard questions with
worked answers and explanations, merged into projects by curriculum.py.
"""

INTERVIEWS_CORE = {
    "task-forge": [
        {
            "question": (
"**Valid Parentheses-style state tracking** (Easy): implement `undo_stack(ops)` — "
"given operations like ('do', x) and ('undo',), return the final list of applied "
"values. More broadly: why is a stack the right structure for undo/redo, matched "
"brackets, and call frames?"
            ),
            "difficulty": "Easy",
            "topics": ["stacks", "LIFO"],
            "answer": (
"```python\ndef undo_stack(ops):\n    applied = []\n    for op in ops:\n        if op[0] == 'do':\n            applied.append(op[1])\n        elif op[0] == 'undo' and applied:\n            applied.pop()\n    return applied\n```"
            ),
            "explanation": (
"Undo must reverse the MOST RECENT action — last-in, first-out — and a Python "
"list's append/pop at the tail are both O(1), making it the canonical stack. The "
"same LIFO logic verifies matched brackets (push openers, pop on closers, valid "
"iff empty at end) and models the call stack (each function call pushes a frame; "
"return pops it — which is why infinite recursion gives a stack *overflow*). "
"The guard on empty-undo is the edge interviewers watch for. In Task Forge, an "
"undo feature for task operations is exactly this pattern — try adding it."
            ),
        },
        {
            "question": (
"Explain `__eq__`, `__hash__` and their contract: your teammate made Task a "
"dataclass with `eq=True` and put tasks in a set, then mutated one's title and "
"can't find it anymore. What happened?"
            ),
            "difficulty": "Medium",
            "topics": ["hashing", "object model"],
            "answer": (
"The contract: objects that compare equal MUST have equal hashes, and an "
"object's hash must never change while it lives in a hash-based container. A "
"dataclass with eq=True and no frozen=True sets `__hash__ = None` (unhashable) "
"precisely to prevent this bug — unless someone forces hashability "
"(`unsafe_hash=True` or a manual __hash__). With a hash derived from mutable "
"fields, the set filed the task under its ORIGINAL hash bucket; after mutating "
"the title, lookups compute the NEW hash, probe a different bucket, and find "
"nothing — the object is still in the set but unreachable (a 'ghost'). Fixes: "
"frozen=True dataclasses for set/dict members, hash by an immutable identity "
"field only (id), or don't use mutable objects as keys."
            ),
            "explanation": (
"This tests whether you understand hashing as *bucket addressing* (st-1's "
"lesson) rather than magic: mutate the fields feeding the hash and you break "
"the address, not the object. The dataclass design detail — eq=True silently "
"killing hashability to protect you — is the kind of language-lawyer knowledge "
"that signals real Python depth, and 'hash by immutable identity' is the "
"production pattern (it's why databases use surrogate keys — the Star Schema "
"echo). Bonus: this is also why lists/dicts can't be dict keys but tuples can."
            ),
        },
        {
            "question": (
"Design question (Medium): your CLI tool needs to support plugins — third-party "
"packages adding new subcommands without modifying your code. Sketch the "
"mechanism."
            ),
            "difficulty": "Medium",
            "topics": ["design", "registries", "entry points"],
            "answer": (
"Two layers: **(1) a command registry** — a dict name → handler that core "
"commands register into at import time (decorator sugar: `@register('add')`); "
"argparse subparsers are built by iterating the registry, so dispatch is "
"data-driven (pb-3's registry pattern). **(2) discovery** — third-party "
"packages declare an entry point group (e.g. `[project.entry-points."
"'taskforge.commands']` in their pyproject.toml); at startup you iterate "
"`importlib.metadata.entry_points(group='taskforge.commands')`, load each, and "
"let it register itself. Plugins install with pip; your tool discovers them "
"automatically; a broken plugin is caught with try/except around its load and "
"reported, not fatal."
            ),
            "explanation": (
"The registry-plus-entry-points combo is how pytest, Airflow providers, and "
"most extensible Python tools actually work — naming importlib.metadata entry "
"points marks practical experience over theory. Design points worth "
"volunteering: version the plugin API contract, isolate plugin failures "
"(one bad plugin must not kill the CLI), and consider a capability/permission "
"model if plugins run in sensitive contexts. The deeper pattern — behavior "
"selected by data, registered not hardcoded — recurs in your ETL framework "
"and in every 'make it extensible' interview question."
            ),
        },
    ],
    "weather-watcher": [
        {
            "question": (
"You call a third-party API for 10k cities daily. It rate-limits at 10 req/s, "
"fails ~1% of calls transiently, and occasionally hangs. Design the client. "
"(The everyday DE interview question.)"
            ),
            "difficulty": "Medium",
            "topics": ["HTTP clients", "resilience"],
            "answer": (
"Layers: **timeouts always** (connect ~3s, read ~10s — an unset timeout is an "
"eventual outage); **retry with exponential backoff + jitter** on transient "
"classes only (connection errors, 429, 5xx — never on 4xx like 400/404, which "
"retry into the same wall), honoring Retry-After headers; **client-side rate "
"limiting** at 10 req/s (token bucket / cm-2 sliding window) so you never "
"provoke 429 storms; **bounded concurrency** (a worker pool or asyncio "
"semaphore ~ the rate limit); **circuit breaker** — if error rate spikes, stop "
"hammering, alert, resume with probes; and **checkpointing** — record "
"per-city success (the ledger!) so a crash at city 7,000 resumes, not "
"restarts. Failed cities land in a DLQ for a sweep-up pass; the run report "
"counts everything."
            ),
            "explanation": (
"Interviewers use this to see production instincts stacked in the right "
"order: timeouts before retries (retrying a hang multiplies hangs), "
"retry-class discrimination (the 4xx/5xx split), and jitter (synchronized "
"retries from many workers create self-inflicted DDoS waves — the thundering "
"herd again). The checkpoint/DLQ layer converts a client question into a "
"*pipeline* answer, which is the point of asking it in a data loop. "
"Mentioning honor-the-Retry-After and negotiate-a-bulk-endpoint shows the "
"diplomacy of someone who has actually run partner integrations."
            ),
        },
        {
            "question": (
"Idempotency rapid-fire: which of these operations are idempotent, and how "
"would you fix the ones that aren't? (a) INSERT INTO t VALUES (...); "
"(b) UPDATE t SET count = count + 1 WHERE id = 5; (c) UPDATE t SET status = "
"'done' WHERE id = 5; (d) DELETE FROM t WHERE id = 5; (e) POST /charge "
"{amount: 50}."
            ),
            "difficulty": "Medium",
            "topics": ["idempotency"],
            "answer": (
"(a) **Not idempotent** — re-run duplicates the row. Fix: unique key + ON "
"CONFLICT DO NOTHING/UPDATE. (b) **Not idempotent** — increments compound "
"per retry. Fix: set an absolute value computed elsewhere, or make it "
"conditional on a version/run-id (count = 5 WHERE version = 3). (c) "
"**Idempotent** — absolute-state writes converge; rerunning changes nothing. "
"(d) **Idempotent** in effect — the row stays gone (return value differs, "
"state doesn't). (e) **Dangerously not** — retrying a charge bills twice. "
"Fix: idempotency keys — client sends a unique key per logical charge; the "
"server stores processed keys (the ledger pattern) and returns the original "
"result for duplicates. Stripe et al. work exactly this way."
            ),
            "explanation": (
"The pattern behind the answers: *absolute-state* operations (set X to V, "
"delete X) are naturally idempotent; *relative* operations (append, "
"increment, charge) are not — and every fix converts relative to absolute "
"(upsert by key, versioned writes, dedup ledgers). That one sentence is the "
"portable insight interviewers hope you'll say. The payments case matters "
"because it shows idempotency isn't a data-pipeline nicety but a "
"correctness requirement wherever retries exist — which, per ww-2 and every "
"scheduler ever, is everywhere."
            ),
        },
        {
            "question": (
"Your daily ETL truncates and reloads a table that dashboards read. Users "
"report the dashboard is empty for ~4 minutes every morning. Why, and what "
"are two fixes with different trade-offs?"
            ),
            "difficulty": "Easy",
            "topics": ["loading patterns", "atomicity"],
            "answer": (
"TRUNCATE commits the emptiness immediately (or the load runs across "
"multiple transactions), so readers between truncate and reload-complete "
"see an empty/partial table — the load isn't atomic from the consumer's "
"view. Fix 1: **wrap truncate+load in one transaction** — readers see old "
"data until commit flips them to new (Postgres MVCC handles this "
"beautifully); trade-off: long transaction, table lock contention on some "
"databases, WAL bloat for huge loads. Fix 2: **staging + atomic swap** — "
"load into table_new, then in one transaction rename/swap (or use a view "
"pointing at the current version); trade-off: 2x storage transiently, "
"slightly more machinery, but zero reader disruption at any size — the "
"blue-green deploy of tables."
            ),
            "explanation": (
"A gentle question that checks whether you think about *consumers* of data, "
"not just producers. The staging-swap answer is the professional default "
"(it's your Quality Gate publish mechanism and mm's create-and-swap, "
"unified) because it also enables validation-before-publish: check the new "
"table, THEN swap — bad loads never go live. Extending unprompted to "
"'and this is how you publish validated data generally' converts a "
"debugging question into an architecture answer."
            ),
        },
    ],
    "log-miner": [
        {
            "question": (
"Classic (Medium): find the top 10 most frequent words in a 100GB file on a "
"machine with 4GB RAM. Walk through the full solution."
            ),
            "difficulty": "Medium",
            "topics": ["external algorithms", "hashing", "top-K"],
            "answer": (
"Two-phase: **(1) Partition by hash** — stream the file (generators — never "
"load it), hash each word, append to one of ~200 bucket files by "
"hash(word) % 200. Same word always lands in the same bucket (st-parallel), "
"and each bucket is ~500MB — fits RAM. **(2) Count per bucket, keep a "
"global top-10 min-heap** — for each bucket file: Counter it in memory, "
"then push its (count, word) pairs through a size-10 min-heap (hs-1). The "
"heap merges bucket-local answers into the global top-10 because each "
"word's TOTAL count lives entirely in one bucket. O(N) I/O twice, O(RAM) "
"bounded by the largest bucket, and it parallelizes trivially — which is "
"exactly MapReduce/Spark's word-count execution."
            ),
            "explanation": (
"THE classic external-algorithm question. The key correctness insight — "
"hash partitioning makes per-bucket counts globally complete — is the same "
"property powering distributed GROUP BY (fs-1), and saying that connection "
"aloud upgrades the answer from algorithm recall to systems understanding. "
"Skew probe to preempt: a pathological bucket (one mega-word) still fits "
"because a Counter of ONE word is tiny — skew hurts when *distinct* keys "
"cluster, so a second hash level fixes it. Mention sampling first to "
"estimate distribution — measure, then engineer."
            ),
        },
        {
            "question": (
"What's the difference between a generator and a list comprehension in "
"memory and evaluation terms — and when is the LIST actually the right "
"choice? Give a concrete example of each."
            ),
            "difficulty": "Easy",
            "topics": ["generators", "memory"],
            "answer": (
"`[f(x) for x in xs]` computes everything NOW and holds all results in "
"memory (O(n)); `(f(x) for x in xs)` builds a paused computation yielding "
"one item on demand (O(1) memory) that can be consumed exactly once. "
"Generator wins: streaming a 10GB log through a filter-parse-aggregate "
"chain (lm-1) — constant memory, and early termination is free "
"(next(g) / islice stops upstream work). List wins when you need: multiple "
"passes (a generator is exhausted after one), random access/indexing/len, "
"sorting (sorted() must materialize anyway), or small data where the "
"clarity of a concrete list beats laziness ceremony. The trap worth "
"naming: returning a generator that closes over a resource (an open file) "
"which the caller consumes after the file closed — laziness moves "
"*when* code runs, which moves *when* bugs bite."
            ),
            "explanation": (
"An easy question with a discriminator hidden in 'when is the list "
"right' — candidates who can only cheer for laziness haven't been bitten "
"by one-shot exhaustion (looping a generator twice silently processes "
"zero items the second time — a real bug class) or by deferred-execution "
"surprises. The resource-lifetime trap shows scars. Tie-in worth making: "
"Spark inherits ALL of this — DataFrames are lazy and 'recompute on "
"every action' is the cluster version of re-iterating a generator, which "
"is why .cache() exists (ss milestone 4)."
            ),
        },
        {
            "question": (
"You must parse 500M log lines daily. Your regex-based parser (lm-2 style) "
"benchmarks at 40k lines/sec/core — that's 3.5 hours single-core. Get it "
"under 30 minutes. Options, in order?"
            ),
            "difficulty": "Hard",
            "topics": ["performance", "parallelism"],
            "answer": (
"In leverage order: **(1) make the regex cheaper** — anchor it (^), avoid "
"catastrophic backtracking (no nested quantifiers), compile once, and "
"consider splitting on delimiters via str.split for fixed formats (often "
"3-5x — string methods beat regex when structure is rigid); try re2-style "
"engines for guaranteed linear time. **(2) Skip work** — if only 2 fields "
"matter, extract just those; if only error lines matter, cheap substring "
"pre-filter ('\" 5' for 5xx) before the full parse — filter-early, the "
"eternal rule. **(3) Parallelize** — the file splits by line offsets: "
"multiprocessing over chunks (regex releases the GIL poorly; processes, "
"not threads) — 8 cores ≈ 8x, landing ~26 min. **(4) Change the game** — "
"columnarize: convert logs to parquet at ingestion (once) and query with "
"DuckDB/Spark thereafter; or push structure upstream — emit JSON/"
"structured logs and stop parsing free text entirely, which is the actual "
"correct long-term answer."
            ),
            "explanation": (
"Performance questions grade the ORDER of options: algorithmic waste "
"first (regex quality, work-skipping), parallelism second (it multiplies "
"whatever efficiency you have — parallelizing waste is buying eight "
"shovels to dig a hole in the wrong place), architecture third "
"(stop-parsing-at-read-time), and the org-level fix last (structured "
"logging upstream — the cheapest engineering is deleting the problem). "
"GIL awareness (processes for CPU-bound parsing) is the Python-specific "
"checkpoint. This laddered answer shape — micro, skip, parallel, "
"re-architect — transfers to every 'make it faster' interview."
            ),
        },
    ],
    "data-deck": [
        {
            "question": (
"Your FastAPI endpoint does `results = expensive_query(); return results` "
"and under load the whole service stops responding — even /health. The "
"query takes 30s. Explain precisely why, and give three fixes with "
"trade-offs."
            ),
            "difficulty": "Medium",
            "topics": ["async", "event loop", "blocking"],
            "answer": (
"If the endpoint is `async def` and expensive_query() is a *synchronous* "
"blocking call (psycopg2, requests), it runs ON the event loop thread — "
"for 30 seconds nothing else on that loop runs: no other requests, no "
"/health, nothing (dd-3's one-blocking-call-starves-everyone). Fixes: "
"**(1) make it truly async** — an async driver (asyncpg/httpx): the "
"await yields the loop during I/O; best throughput, requires async-"
"compatible libraries throughout. **(2) declare the endpoint plain "
"`def`** — FastAPI then runs it in its threadpool automatically; "
"simplest change, bounded by threadpool size (~40 default), fine for "
"moderate concurrency. **(3) don't do 30s work in requests at all** — "
"enqueue a job (or precompute/cache the result — cm-1), return 202 + "
"status endpoint; the architectural answer for genuinely slow work. "
"Bonus hygiene: statement timeouts so no query CAN hold a worker 30s."
            ),
            "explanation": (
"The precision demanded — 'async def + sync call = loop starvation, "
"plain def = threadpool' — is FastAPI's most misunderstood behavior and "
"a razor-sharp screen for whether someone has run async Python in "
"production. The three fixes ladder from tactical to architectural, and "
"option 3's 'slow work doesn't belong in request handlers' echoes the "
"course's serving philosophy (precompute in pipelines, serve from "
"fast stores). Knowing that /health dying is the *diagnostic tell* of "
"loop blockage (vs. worker exhaustion, where health usually survives) "
"is operational gold."
            ),
        },
        {
            "question": (
"Design pagination for GET /readings with millions of rows. Compare "
"offset-based and cursor-based; which do you ship and why?"
            ),
            "difficulty": "Medium",
            "topics": ["API design", "pagination"],
            "answer": (
"**Offset** (`?page=500&size=100` → OFFSET 50000 LIMIT 100): simple, "
"jumpable-to-page-N, but the database must scan and DISCARD 50k rows "
"per request (O(offset) — deep pages get slower and hammer the DB), and "
"it's unstable under writes: rows inserted while paging shift "
"everything, causing skips/duplicates. **Cursor/keyset** "
"(`?after=2026-07-27T10:00:00,12345&size=100` → WHERE (ts, id) > "
"(:ts, :id) ORDER BY ts, id LIMIT 100): O(log n) per page via the "
"index regardless of depth, stable under concurrent inserts, "
"opaque-token friendly; costs: no jump-to-page-7, requires a unique "
"sort key (hence the id tiebreaker), slightly more client logic. "
"**Ship cursor-based** for any API that machines page through (ETL "
"consumers! — your own extractors are the client), keep offset only "
"for shallow human-facing pages. Return the next-cursor in the "
"response; make the token opaque so you can change the sort scheme "
"later."
            ),
            "explanation": (
"A bread-and-butter API design question whose data-engineering twist "
"is that YOU are usually the consumer: extractors paging an API at "
"depth (cl milestones) feel offset degradation directly. The "
"(ts, id) compound cursor is ag-3's binary search + cl-1's compound "
"watermark wearing an API costume — one more instance of the "
"course's 'same idea, new layer' design. Mentioning the stability-"
"under-writes bug (page 3 shifts while you read it) shows you've "
"debugged a real paginated sync."
            ),
        },
        {
            "question": (
"How do you version a REST API that pipeline consumers depend on, and "
"how does this relate to schema evolution in data systems?"
            ),
            "difficulty": "Medium",
            "topics": ["API versioning", "contracts"],
            "answer": (
"Compatibility rules first: **additive changes are safe** (new "
"optional fields, new endpoints — consumers ignoring unknowns keep "
"working); **breaking changes** (rename/remove/retype fields, change "
"semantics) require a new version — path (/v2/) or header-based — run "
"in parallel with v1 through a deprecation window with usage "
"monitoring, migrating consumers before sunset. Enforce with contract "
"tests (pydantic response models ARE the contract; dd-1) in CI so "
"breaks are caught at build, not by consumers. The data-systems "
"parallel is exact: additive-only is Avro/Protobuf's "
"backward-compatibility discipline, /v2-in-parallel is "
"expand-migrate-contract (mm interview!) for endpoints, and the "
"deprecation window with usage metrics mirrors dropping a column "
"only after query logs show zero readers. One principle everywhere: "
"**never break a consumer you can't see — make contracts explicit, "
"changes additive, and migrations parallel-run**."
            ),
            "explanation": (
"The question looks like web-dev trivia but is really about the "
"contract discipline data platforms live or die by — schema "
"registries, data contracts (qg's under-the-hood), and warehouse "
"column deprecation are the same problem at different layers, and "
"the answer's power move is unifying them. Interviewers reward the "
"operational specifics: parallel-run windows, usage-monitoring-"
"before-sunset, contract tests in CI. 'Postel's law plus explicit "
"versioning' as a closer shows you know both the classical wisdom "
"and its modern hardening."
            ),
        },
    ],
    "pandas-powerplant": [
        {
            "question": (
"Your pandas job OOMs loading a 12GB CSV on a 16GB machine. List "
"five fixes in the order you'd try them, with the mechanism behind "
"each."
            ),
            "difficulty": "Medium",
            "topics": ["pandas memory", "out-of-core"],
            "answer": (
"**(1) dtypes at read** — pd.read_csv(dtype={...}, "
"parse_dates=[...]): default object/int64/float64 inflate memory "
"3-10x; category for low-cardinality strings is the single biggest "
"win. **(2) usecols** — load only needed columns (columnar thinking "
"at the reader: pp's lesson). **(3) chunked processing** — "
"read_csv(chunksize=1e6) + per-chunk aggregation, combining partials "
"(mergeable aggregates — ds-3's sums-and-counts); works when the "
"ANSWER is small even if data is big. **(4) switch the engine** — "
"DuckDB over the CSV directly (out-of-core, parallel, spills), or "
"polars' streaming; often the 5-line fix that ends the pain "
"(dt-project). **(5) convert the source** — CSV→parquet once "
"(typed, compressed, column-prunable), then every later read is "
"5-20x lighter. And the meta-fix: question whether pandas-on-one-"
"box is the right tool at this size at all."
            ),
            "explanation": (
"Graded on mechanism-awareness: WHY dtypes help (object columns "
"are pointers to Python objects — pp-1's boxing tax), why chunking "
"needs mergeable aggregates (you can't chunk a median naively — "
"the distributed-statistics lesson again), and why parquet "
"membership in the list matters (fixing the file beats fixing the "
"reader). The escalation order itself — cheap flags → less data → "
"streaming → different engine → different format — is the "
"transferable answer shape for every 'it doesn't fit' problem, "
"and interviewers recognize candidates who have actually watched "
"htop while a DataFrame doubled during a merge."
            ),
        },
        {
            "question": (
"Explain the SettingWithCopyWarning: `df[df.x > 0]['y'] = 1` — what "
"does the user think happens, what actually happens, and what's the "
"correct idiom?"
            ),
            "difficulty": "Easy",
            "topics": ["pandas semantics", "views vs copies"],
            "answer": (
"User's belief: 'set y to 1 where x > 0 in df'. Reality: it's TWO "
"operations — `df[df.x > 0]` builds a (usually) COPY of the "
"filtered rows; `['y'] = 1` then mutates that temporary copy, which "
"is immediately garbage-collected. df is untouched; the warning is "
"pandas admitting it can't always tell whether you got a view or a "
"copy (chained indexing makes it ambiguous — hence 'maybe' "
"semantics, the worst kind). Correct idiom: one operation with "
".loc — `df.loc[df.x > 0, 'y'] = 1` — a single indexer that pandas "
"guarantees mutates df. (pandas 3.0's copy-on-write semantics "
"finally make chained assignment consistently a no-op with a hard "
"error, killing the ambiguity.)"
            ),
            "explanation": (
"The most common pandas bug in the wild — silent no-op assignments "
"corrupting analyses without any exception. The answer's key is "
"'two operations vs one': chained indexing decomposes into "
"getitem-then-setitem on an intermediate, and .loc fuses "
"selection+assignment atomically. Knowing the copy-on-write "
"future shows currency. This is ALSO a soft probe of mutation "
"discipline generally — the same reasoning (which object am I "
"actually mutating?) that fs-2's immutable transformations and "
"functional pipelines sidestep entirely, a connection worth "
"making aloud."
            ),
        },
        {
            "question": (
"groupby().apply(custom_python_fn) on 10M rows is 100x slower than "
"the built-in .sum(). Why, and what's the escalation path when the "
"built-ins don't cover your logic?"
            ),
            "difficulty": "Medium",
            "topics": ["vectorization", "apply", "performance"],
            "answer": (
"Built-in aggregations (.sum/.mean/.max) run as compiled C over "
"contiguous arrays — one call per group at native speed. "
".apply(python_fn) crosses the C↔Python boundary PER GROUP (or "
"per row for Series.apply): each call boxes data into Python "
"objects, dispatches the interpreter, and un-boxes results — "
"pp-1's 100x tax, resurrected. Escalation when built-ins don't "
"suffice: (1) **decompose** the custom logic into vectorized "
"primitives (most 'custom' aggregations are algebra over "
"sums/counts/cumsums — e.g. weighted mean = (x*w).sum()/w.sum() "
"via two built-ins); (2) **.agg with multiple built-ins** then "
"combine columns; (3) **transform/window tricks** for "
"within-group normalization; (4) **numba/Cython** for genuinely "
"iterative per-group algorithms (compile the Python); (5) "
"**push to SQL/DuckDB** — window functions cover a shocking "
"share of 'custom' logic (wf-project). The interview-grade "
"instinct: .apply is the LAST resort, not the first reach."
            ),
            "explanation": (
"The decomposition move — rewriting custom logic as algebra over "
"built-in aggregates — is the highest-value pandas skill nobody "
"teaches: it's the same 'mergeable partials' math that makes "
"distributed aggregation work (avg = sum/count per partition, "
"combined), so practicing it doubles as Spark training. "
"Interviewers often follow with 'what CAN'T be decomposed?' — "
"answer: order-dependent iterative logic (e.g., path-dependent "
"state machines per group), which is where numba or explicit "
"loops in a faster engine genuinely belong. Knowing where the "
"boundary sits is the difference between cargo-cult "
"'vectorize everything' and engineering."
            ),
        },
    ],
    "first-spark": [
        {
            "question": (
"Explain what happens — in full — when you run "
"df.groupBy('country').count().show() on a 3-node cluster. From "
"your Python line to rows on your screen."
            ),
            "difficulty": "Medium",
            "topics": ["Spark execution", "shuffles"],
            "answer": (
"(1) Python builds a *logical plan* via py4j calls into the JVM "
"driver — no data moves. (2) .show() is an action: Catalyst "
"analyzes → optimizes (pushdowns, pruning) → compiles a physical "
"plan with a shuffle boundary at the groupBy, splitting execution "
"into two *stages*. (3) Stage 1: tasks (one per input partition) "
"scan their partition, pre-aggregate counts per country locally "
"(partial aggregation — the combiner), and write shuffle files "
"bucketed by hash(country) % 200 (spark.sql.shuffle.partitions). "
"(4) Stage 2: each reduce task fetches its bucket from EVERY "
"stage-1 task over the network, merges the partial counts, and "
"produces final rows. (5) show() collects a small sample of "
"result rows to the driver, which formats them to your terminal. "
"The scheduler retried any failed task from its lineage; you "
"watched none of it — that's the product."
            ),
            "explanation": (
"THE Spark interview question, and the grading rubric is "
"specificity: lazy-until-action, Catalyst's phases, the stage "
"split AT the shuffle, partial aggregation before the wire "
"(fs-1's combiner — why groupBy().count() ships tiny data while "
"groupByKey ships everything), and hash-partitioned shuffle "
"files. Bonus points: 200 default shuffle partitions as a "
"tunable (ss milestone), AQE coalescing them dynamically in "
"modern Spark, and show()'s implicit limit making it cheap "
"while .collect() on big data kills drivers. If you built "
"mini-spark (fs-1), narrate from it — 'I've implemented this' "
"beats 'I've read this' in every loop."
            ),
        },
        {
            "question": (
"Why are Python UDFs slow in PySpark, what are the faster "
"alternatives in order, and when is a UDF genuinely justified?"
            ),
            "difficulty": "Medium",
            "topics": ["UDFs", "Arrow", "Catalyst"],
            "answer": (
"A plain Python UDF forces each row out of the JVM's optimized "
"binary format (Tungsten), through serialization, into a Python "
"worker process, through your function, and back — per row, with "
"pickling. It's also an optimization black box: Catalyst can't "
"push filters through it, prune columns it uses, or reorder "
"around it. Faster alternatives, in order: **(1) built-in "
"F.* functions** — compile to JVM codegen, fully optimizable "
"(covers ~90% of 'I need a UDF' cases: F.when, F.regexp_extract, "
"F.transform for arrays...); **(2) pandas UDFs (Arrow-"
"vectorized)** — batches cross the boundary as Arrow columns, "
"amortizing serialization and running vectorized numpy/pandas "
"inside (10-100x over row UDFs); **(3) native/Scala UDF** if "
"the team can hold it. Genuinely justified: complex Python-only "
"library logic (a specialized parser, an ML model's .predict) "
"where reimplementation cost exceeds the performance tax — "
"then prefer pandas-UDF form and filter rows BEFORE the UDF "
"so it sees the minimum data."
            ),
            "explanation": (
"Tests two mechanisms at once: the serialization boundary "
"(pp-1's boxing tax at cluster scale — the course's most "
"recurring villain) and the optimizer-opacity cost (ss-3: "
"Catalyst optimizes what it can SEE). The Arrow answer shows "
"currency; 'filter before the UDF because pushdown can't "
"cross it' shows you understand WHY, not just THAT. The "
"model-scoring case is the honest carve-out — and even "
"there, batch-scoring via pandas UDFs on pre-filtered data "
"is the professional shape."
            ),
        },
        {
            "question": (
"A 200-partition Spark job shows 199 tasks done in ~1 min and one "
"task running for an hour. Diagnose and give the fix toolbox."
            ),
            "difficulty": "Hard",
            "topics": ["skew", "partitioning"],
            "answer": (
"Classic **data skew**: one partition holds a disproportionate "
"key's data (ss-1's hot key — a null-heavy join key, a "
"mega-customer, a default value). Confirm in the UI: task input "
"sizes/record counts for the straggler vs peers; find the key "
"with a quick groupBy().count().orderBy(desc) sample. Toolbox by "
"cause: **skewed join** — enable AQE skew-join handling (Spark "
"3.x splits oversized partitions automatically); broadcast the "
"small side if it fits (kills the shuffle entirely — ss-2); "
"**salt** the hot key (append random 1..K suffix, aggregate "
"twice) for aggregations; **isolate** — filter the mega-key, "
"process it separately (maybe broadcast-side), union results; "
"**null keys** — filter or coalesce nulls to a scattered "
"surrogate before joining (nulls all hash identically — the "
"sneakiest common cause). And the prevention layer: know your "
"key distributions BEFORE joining (profile, qg-style) — skew "
"is a data property you can see coming."
            ),
            "explanation": (
"The 199/200 pattern is the most recognizable Spark pathology "
"and a near-guaranteed interview scenario. Strong answers move "
"diagnose→confirm→fix-by-mechanism rather than reciting "
"'salting' as an incantation — AQE-first shows modern Spark "
"fluency (much manual salting is now obsolete), and the "
"null-key callout separates people who've debugged real joins "
"from tutorial graduates (log/event data is FULL of null join "
"keys, and they all land in one partition). The 'stage "
"finishes when its slowest task does' framing connects back "
"to ss-1's skew_ratio: max/mean IS your wall-clock "
"multiplier."
            ),
        },
    ],
    "spark-at-scale": [
        {
            "question": (
"You must join a 2TB fact table with a 40GB dimension table daily. "
"Broadcast is too big, sort-merge is slow. What are your options? "
"(A real staff-level scenario.)"
            ),
            "difficulty": "Hard",
            "topics": ["big joins", "bucketing", "storage layout"],
            "answer": (
"Options ladder: **(1) shrink the 40GB first** — column-prune and "
"pre-filter the dimension to only keys/columns the join needs "
"(often 40GB → 2GB → broadcastable after all; the most-skipped "
"easy win); semi-join reduction: broadcast the fact's DISTINCT "
"join keys to pre-filter the dimension. **(2) Bucketing** — "
"pre-partition BOTH tables by join key into the same bucket "
"count at write time; joins then match bucket-to-bucket with NO "
"shuffle of either side at read time — the amortize-the-shuffle "
"answer when this join runs daily (pay the layout cost once, "
"save it every run). **(3) Partition-wise strategy** — if the "
"dimension is slowly changing, capture its daily DELTA (CDC!) "
"and merge incrementally instead of re-joining everything. "
"**(4) Tune the sort-merge you keep** — AQE on, sensible "
"shuffle partitions, storage sorted by join key so shuffles "
"read pre-clustered data. The meta-answer: recurring big joins "
"are a *data layout* problem, not a per-job tuning problem."
            ),
            "explanation": (
"Staff-level because every option trades one-time layout cost "
"against recurring compute — the economic reasoning matters "
"more than the specific trick. Bucketing is the headline "
"(chronically underused; it's consistent hashing applied to "
"storage — pg-1 again), and the shrink-first move tests "
"whether you question requirements before scaling machinery "
"('do we even need 40GB of that dimension?'). The CDC option "
"connects joins to incrementality: most 'big join' pain is "
"actually 'we re-join unchanged data nightly' — the "
"cl-project's whole thesis, at TB scale."
            ),
        },
        {
            "question": (
"When should you call .cache()/.persist() in Spark, when is it "
"actively harmful, and why does 'cache everything' fail?"
            ),
            "difficulty": "Medium",
            "topics": ["caching", "lineage", "memory"],
            "answer": (
"Cache when a DataFrame is (a) reused by MULTIPLE actions and "
"(b) expensive to recompute: without caching, each action "
"replays the full lineage (lazy evaluation's dark side — your "
"three aggregations off one cleaned frame recompute the cleaning "
"three times; ss milestone 4 measures exactly this). Harmful "
"when: used once (pure overhead — materialization + memory "
"pressure); when it evicts something more valuable (executor "
"memory is shared with shuffles and execution — caching a huge "
"frame can make JOINS spill to disk, a net loss); or when "
"cheap-to-recompute data hogs storage that lineage would have "
"regenerated in seconds. 'Cache everything' fails because "
"storage memory is finite and LRU-evicted: over-caching causes "
"partial caching (some partitions evicted → mixed "
"recompute+read paths, unpredictable perf) and starves "
"execution memory. Discipline: cache deliberately, .unpersist() "
"when done, check the Storage tab (fraction cached!), and "
"prefer persist(DISK_ONLY)/checkpointing for huge reused "
"intermediates."
            ),
            "explanation": (
"Caching questions expose whether someone understands Spark's "
"unified memory model — storage and execution share a pool, so "
"a cache isn't free even when 'memory is available'. The "
"partial-caching failure mode (evicted partitions silently "
"recomputing) explains many 'caching made it slower??' "
"mysteries. Bonus depth: checkpointing vs caching (checkpoint "
"truncates lineage — vital for iterative algorithms whose "
"plans grow unboundedly), and noting that AQE + good layout "
"often beats caching by making recomputation cheap in the "
"first place."
            ),
        },
        {
            "question": (
"spark.sql.shuffle.partitions defaults to 200. Your job shuffles "
"2TB. What goes wrong at 200, how do you size it properly, and "
"what does AQE change?"
            ),
            "difficulty": "Medium",
            "topics": ["shuffle tuning", "AQE"],
            "answer": (
"At 200 partitions, 2TB / 200 = ~10GB per reduce task: tasks "
"spill to disk repeatedly (execution memory per task is far "
"smaller), GC thrashes, stragglers dominate, and a single task "
"failure re-does 10GB of work — possibly OOM-killing executors "
"outright. Classical sizing: target ~128-200MB per shuffle "
"partition → 2TB / 150MB ≈ 13,000+ partitions; also respect "
"cores (partitions ≥ 2-3x total cores for scheduling slack) "
"and beware the opposite failure — tiny data over many "
"partitions = per-task overhead and tiny-file output (ll's "
"small-files problem). **AQE (Spark 3.x) largely automates "
"this**: set shuffle partitions HIGH as a ceiling and AQE "
"*coalesces* small post-shuffle partitions to sensible sizes "
"at runtime using real statistics, plus splits skewed "
"partitions (the ss-1 problem) and switches join strategies "
"dynamically. Modern posture: enable AQE, set the ceiling "
"generously, and tune only when the UI shows it wrong — "
"measured, not memorized."
            ),
            "explanation": (
"The arithmetic IS the answer: bytes-per-task math (2TB/200) "
"turns an abstract config into a concrete pathology, and "
"interviewers listen for exactly that calculation. The "
"both-directions failure (too few = spills, too many = "
"overhead + small files) shows systems maturity, and AQE "
"fluency separates 2020-Spark knowledge from current "
"practice — many classic tuning interviews are now really "
"'do you know AQE does this for you' checks. Closing with "
"'read the UI, then tune' reinforces the "
"measurement-before-optimization theme the whole course "
"drills."
            ),
        },
    ],
    "orchestrate-it": [
        {
            "question": (
"Airflow's execution_date/logical_date confuses everyone: a DAG "
"scheduled '@daily' with start_date 2026-07-01 — when does the run "
"with logical_date 2026-07-01 actually execute, and why did "
"Airflow choose this model? What bug does misunderstanding it "
"cause?"
            ),
            "difficulty": "Medium",
            "topics": ["Airflow semantics", "logical date"],
            "answer": (
"It executes AFTER the interval ends: at 2026-07-02 00:00 (the "
"first moment all of July 1's data can exist). logical_date "
"labels the *data interval being processed* "
"(data_interval_start), not the wall-clock run time — a run is "
"'the job FOR July 1', executed July 2. Airflow chose this "
"because batch jobs process closed periods: {{ ds }} templates "
"then make each task a pure function of its interval "
"(idempotent, backfillable — rerun 'July 1' anytime and it "
"means the same thing). The classic bug: a task using "
"datetime.now() (or 'yesterday' relative to now) instead of the "
"templated interval — it works in daily operation, then a "
"backfill of 60 historical days processes TODAY's data 60 "
"times (oi/ff's leakage cousin). Modern Airflow's renaming "
"(logical_date, data_interval_start/end) exists precisely "
"because 'execution_date' misled a decade of engineers."
            ),
            "explanation": (
"The single most confusing thing in Airflow and therefore a "
"beloved interview filter. The seniority tell is connecting "
"semantics to *purpose*: interval-labeling is what makes "
"backfills meaningful and tasks idempotent-by-construction — "
"the now()-vs-{{ds}} bug is the practical cash-out, and "
"having a story about catching one ('backfill produced 60 "
"identical days') is instant credibility. Tie-back worth "
"making: this is ff-1's snapshot discipline enforced by the "
"scheduler — 'what did we know as of interval end' — the "
"same temporal honesty, orchestrated."
            ),
        },
        {
            "question": (
"Your DAG's tasks pass a 2GB DataFrame between them via XCom "
"'because it worked in dev'. Production melted. Explain why, and "
"design the correct data-passing architecture for multi-task "
"pipelines."
            ),
            "difficulty": "Easy",
            "topics": ["XCom", "task boundaries"],
            "answer": (
"XComs are rows in Airflow's metadata database, "
"serialized/deserialized per access: 2GB per task-pair bloats "
"Postgres (the scheduler's OWN database — now scheduling "
"latency, UI, and every other DAG suffer), hits serialization "
"limits, and multiplies across mapped tasks/retries. Correct "
"architecture: **data flows through storage, references flow "
"through XCom** — task A writes parquet/table to the "
"lake/warehouse at a deterministic, interval-templated path "
"(s3://.../{{ ds }}/cleaned.parquet), XCom carries the "
"path/table-name/row-count (kilobytes); task B reads the path. "
"Bonus rigor: paths keyed by logical_date make the handoff "
"idempotent and backfill-safe; row-count/checksum in XCom "
"enables cheap sanity checks (qg!); and custom XCom backends "
"(object-storage-backed) exist when you want the ergonomics "
"without the DB damage — but explicit storage contracts stay "
"clearer at scale."
            ),
            "explanation": (
"An easy question that maps a hard principle: orchestrators "
"coordinate work; they are not data planes. 'Metadata through "
"the control plane, data through the data plane' is the "
"sentence to say — it generalizes to every orchestration "
"system (Step Functions, Prefect, Dagster) and echoes the "
"platform design the course builds (Airflow never touches "
"rows; Spark/Postgres do). The deterministic-path detail "
"quietly re-invokes idempotency: same interval → same path → "
"reruns overwrite instead of duplicate — ww-3, eternally."
            ),
        },
        {
            "question": (
"Design the alerting for 150 production DAGs so that real "
"incidents page within minutes but the team isn't drowning in "
"noise. What do you alert on, and what do you deliberately NOT "
"alert on?"
            ),
            "difficulty": "Hard",
            "topics": ["alerting", "SLAs", "operations"],
            "answer": (
"Alert on **consumer-facing symptoms, tiered**: (P1, page) — "
"data freshness SLA breaches on business-critical tables "
"('gold_revenue stale > 2h past SLA'), platform-wide "
"failures (scheduler down, >N% of DAGs failing — systemic "
"signal), and quality-gate blocks on critical pipelines. "
"(P2, ticket/channel) — individual DAG final-failures after "
"retries exhausted, DLQ volume thresholds, anomaly flags "
"(qg-2), SLA warnings at 50% of budget. **Deliberately NOT "
"alerted**: individual task retries (retries are the system "
"WORKING — alerting on them trains people to ignore "
"everything; oi-2's design), transient sensor timeouts that "
"self-recover, per-task duration noise (track trends in "
"dashboards instead), and anything without a documented "
"response — if the runbook page is empty, it's a metric, "
"not an alert. Structural hygiene: alerts route to OWNING "
"teams (tagged per DAG), deduplicate storms (one incident, "
"not 40 task-failure messages), and every page links its "
"runbook. Review alert volume monthly: pages-per-week is "
"itself an SLO."
            ),
            "explanation": (
"Alert design is where operational maturity is most visible: "
"the symptom-over-cause principle (freshness SLAs summarize "
"a thousand failure modes into the one thing consumers feel) "
"and the discipline of NOT alerting on self-healing "
"mechanics separate calm platforms from pager hell. "
"'Retries are the system working' reframes oi-2's state "
"machine as an alerting philosophy. The empty-runbook test "
"('no documented response → not an alert') is a hiring-"
"grade heuristic interviewers themselves quote. Closing "
"with alert-volume-as-SLO shows you treat the humans as "
"part of the system's reliability budget — which is what "
"running 150 DAGs with a small team actually requires."
            ),
        },
    ],
}

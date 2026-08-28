"""
Enrichment for projects 1-5: turns each exercise into a mini-lesson.

Per exercise id:
  instructions - expanded, detailed task brief (markdown)
  refresher    - teachable concept section (markdown): ties the task back to
                 Python fundamentals, shows a worked example of the *pattern*
                 (never the solution itself), and explains why it matters
  objectives   - "after this exercise you can ..." checklist
  hints        - progressive hints, revealed one at a time in the UI
  resources    - links to learn the concept properly

curriculum.py merges these into the exercise dicts at import time.
"""

ENRICHMENT_CORE = {
    # ================================================== Task Forge
    "tf-1": {
        "instructions": (
"Build the core data model for Task Forge.\n\n"
"**Your task**\n\n"
"1. Define a dataclass `Task` with three fields:\n"
"   - `title: str` — required, no default\n"
"   - `done: bool = False` — new tasks start incomplete\n"
"   - `tags: list` — must default to a **new empty list for every task**\n"
"2. Add a method `complete()` that sets `done = True` and **returns the task itself** "
"(`return self`), so calls can chain: `store.get(3).complete()`.\n\n"
"**Watch out:** `tags: list = []` is the classic Python trap — that single list object "
"would be shared by *every* Task you ever create. The checker creates two tasks, mutates "
"one's tags, and fails you if the other task's tags changed too. The dataclasses module "
"has a specific tool for this — see the refresher."
        ),
        "refresher": (
"**From basics to this exercise.** In basic Python you wrote classes with an "
"`__init__` that copies arguments onto `self`:\n\n"
"```python\nclass Point:\n    def __init__(self, x, y=0):\n        self.x = x\n        self.y = y\n```\n\n"
"A **dataclass** generates that boilerplate for you from the field declarations — "
"plus a readable `__repr__` and `==` comparison:\n\n"
"```python\nfrom dataclasses import dataclass, field\n\n@dataclass\nclass Point:\n    x: int\n    y: int = 0\n    history: list = field(default_factory=list)\n```\n\n"
"**Why `field(default_factory=list)`?** Default values are evaluated **once**, when the "
"class is defined — not per instance. A mutable default like `[]` therefore becomes one "
"shared object: append to it on one instance and every other instance sees it. "
"`default_factory=list` instead calls `list()` fresh for each new object. (Plain "
"functions have the same trap: `def f(items=[])`.)\n\n"
"**Returning `self`** from a method is the *fluent interface* pattern — it's why "
"pandas lets you write `df.dropna().rename(...).groupby(...)`. Each call returns an "
"object you can immediately call the next method on.\n\n"
"**Practice beyond the exercise:** add a `rename(new_title)` method that also returns "
"`self`, then chain `t.rename('x').complete()` in your Task Forge project."
        ),
        "objectives": [
            "Declare a dataclass with required fields, defaults, and a safe mutable default",
            "Explain WHY `tags: list = []` shares one list across all instances",
            "Write chainable methods by returning self (the fluent pattern pandas uses)",
        ],
        "hints": [
            "Start from the refresher's Point example — your Task is the same shape: one required field, one simple default, one field(default_factory=...).",
            "For the shared-list trap: import `field` from dataclasses and declare `tags: list = field(default_factory=list)`.",
            "complete() is three short lines: set `self.done = True`, then `return self`.",
        ],
        "resources": [
            {"title": "dataclasses — official docs", "url": "https://docs.python.org/3/library/dataclasses.html"},
            {"title": "Mutable default arguments (the gotcha)", "url": "https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments"},
            {"title": "Real Python: Data Classes guide", "url": "https://realpython.com/python-data-classes/"},
        ],
    },
    "tf-2": {
        "instructions": (
"Give Task Forge a storage layer with honest error handling.\n\n"
"**Your task**\n\n"
"1. Keep the provided `TaskNotFoundError(Exception)` — a *custom exception type* for "
"this domain.\n"
"2. In `TaskStore`, implement:\n"
"   - `add(title)` — append a task (a dict or a Task, your choice) and return its id. "
"Ids are simply positions: first task is 0, next is 1, ...\n"
"   - `complete(task_id)` — mark that task done. If `task_id` doesn't exist, "
"`raise TaskNotFoundError(task_id)`.\n\n"
"**The design idea:** callers can now write `except TaskNotFoundError:` and handle "
"*your* failure specifically, without accidentally swallowing unrelated bugs like a "
"`TypeError`. The checker verifies both the happy path and that a bad id raises your "
"exception (not IndexError!)."
        ),
        "refresher": (
"**From basics to this exercise.** You know `try/except` from basic Python:\n\n"
"```python\ntry:\n    risky()\nexcept ValueError:\n    recover()\n```\n\n"
"The next level is *defining your own* exception types. It's one line — subclass "
"`Exception`:\n\n"
"```python\nclass OutOfStockError(Exception):\n    pass\n\ndef buy(item):\n    if item.count == 0:\n        raise OutOfStockError(item.name)\n```\n\n"
"**Why bother?** Because `except OutOfStockError:` communicates *exactly* what you're "
"handling. If `buy()` also had a typo bug raising `AttributeError`, a bare "
"`except Exception:` would silently hide it — a custom type never does.\n\n"
"**Guarding indexes.** `self.tasks[task_id]` on a bad id raises `IndexError` on its "
"own — but that leaks your internal list implementation to callers. Validate first "
"(`0 <= task_id < len(...)`), then raise *your* error. Also note Python's negative "
"indexing: `tasks[-1]` is valid list access, but is `-1` a valid *task id*? Your "
"range check should say no.\n\n"
"**Practice beyond the exercise:** add `get(task_id)` and `remove(task_id)` with the "
"same validation, and a pytest test using `pytest.raises(TaskNotFoundError)`."
        ),
        "objectives": [
            "Define and raise a custom exception type",
            "Explain why specific exception types beat generic ones for callers",
            "Validate inputs at the boundary instead of leaking IndexError",
        ],
        "hints": [
            "add(): append the task, then `return len(self.tasks) - 1` — position IS the id.",
            "complete(): first check `if not (0 <= task_id < len(self.tasks)):` then raise. Only touch the list after the check.",
            "Store tasks as simple dicts: `{'title': title, 'done': False}` — the checker doesn't care about the shape, only behavior.",
        ],
        "resources": [
            {"title": "Errors and exceptions — Python tutorial", "url": "https://docs.python.org/3/tutorial/errors.html"},
            {"title": "User-defined exceptions", "url": "https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions"},
            {"title": "Real Python: Python exceptions", "url": "https://realpython.com/python-exceptions/"},
        ],
    },
    "tf-3": {
        "instructions": (
"Make Task Forge's data survive the program exiting: serialization.\n\n"
"**Your task**\n\n"
"1. `to_json(tasks)` — take a list of plain dicts and return a JSON **string**.\n"
"2. `from_json(text)` — take that string and rebuild the original Python structure.\n"
"3. The round trip must be lossless: `from_json(to_json(data)) == data`.\n\n"
"Use the standard-library `json` module — no manual string building. In your real "
"Task Forge project you'll wrap these with file I/O (`Path.write_text` / "
"`read_text`) to get `save()` and `load()`."
        ),
        "refresher": (
"**From basics to this exercise.** Variables die with the process. To *persist* "
"data — or send it over a network — you must turn live objects into bytes/text and "
"back. That pair of operations is **serialization** and **deserialization**.\n\n"
"JSON is the everyday format, and the `json` module has exactly four functions worth "
"knowing — the s means *string*:\n\n"
"```python\nimport json\ntext = json.dumps({'a': [1, 2]})   # object -> str\nobj  = json.loads(text)            # str -> object\n# json.dump(obj, file) / json.load(file) work on file handles\n```\n\n"
"**What survives the trip:** dict, list, str, int, float, bool, None. What doesn't: "
"sets, datetimes, and your own classes — those need converting first (e.g. "
"`dataclasses.asdict(task)` turns a Task into a plain dict; a datetime becomes "
"`dt.isoformat()`).\n\n"
"**Why this matters later in your path:** every system you'll meet is doing this "
"constantly — Spark serializes rows between machines during shuffles, Airflow "
"serializes XCom values into its database, and every API response you'll build in "
"Project 4 is `json.dumps` in a trench coat.\n\n"
"**Practice beyond the exercise:** round-trip a Task dataclass via "
"`asdict()`, and try `json.dumps(..., indent=2)` to see pretty-printing."
        ),
        "objectives": [
            "Use json.dumps/loads confidently and know their file-handle siblings",
            "List which Python types survive a JSON round trip and which don't",
            "Explain serialization as the foundation of persistence, APIs, and Spark shuffles",
        ],
        "hints": [
            "Both functions are one-liners: json.dumps(...) and json.loads(...).",
            "If you're tempted to build the string with f-strings — don't. Quoting/escaping is exactly what the json module solves.",
        ],
        "resources": [
            {"title": "json module — official docs", "url": "https://docs.python.org/3/library/json.html"},
            {"title": "Real Python: Working with JSON", "url": "https://realpython.com/python-json/"},
        ],
    },
    # ================================================== Weather Watcher
    "ww-1": {
        "instructions": (
"APIs speak nested JSON; databases and DataFrames want flat rows. Transform between "
"them.\n\n"
"**Your task**\n\n"
"Write `flatten(payload, city)` that takes the Open-Meteo-shaped dict provided and "
"returns exactly:\n\n"
"```python\n{'city': city, 'time': ..., 'temperature': ..., 'windspeed': ...}\n```\n\n"
"pulling the three values out of the nested `current_weather` dict. This tiny "
"function is the **T in ETL** — pure input→output, no side effects, trivially "
"testable. Keep it that way in the real project."
        ),
        "refresher": (
"**From basics to this exercise.** This is dictionary access, the bread and butter "
"of basic Python — applied to real API data. Nested dicts chain lookups:\n\n"
"```python\nresp = {'user': {'address': {'city': 'Harare'}}}\ncity = resp['user']['address']['city']\n```\n\n"
"`d[key]` raises `KeyError` if missing; `d.get(key, default)` returns a fallback. "
"For an ETL transform, failing loudly (`[]` access) is often *correct* — you want to "
"know the API changed shape, not silently insert None into your database.\n\n"
"**The deeper lesson is about function purity.** A *pure function* depends only on "
"its arguments and only returns a value — no network, no files, no globals. "
"Splitting your pipeline into fetch (impure) → flatten (pure) → save (impure) means "
"the transform logic — where most bugs live — can be tested with a plain dict, no "
"internet needed. This is exactly how you'll structure Spark jobs later: pure "
"transformations over data.\n\n"
"**Practice beyond the exercise:** in your project, add a unit test that feeds "
"`flatten()` a payload with a missing key and asserts it raises KeyError — that's a "
"data-quality alarm, for free."
        ),
        "objectives": [
            "Navigate nested dicts fluently and choose between [] and .get()",
            "Write pure transform functions separated from I/O",
            "Explain why pure transforms make pipelines testable",
        ],
        "hints": [
            "Grab the inner dict once: `cw = payload['current_weather']` — then build the result from cw.",
            "Return a dict literal with the four keys; `city` comes from the argument, the rest from cw.",
        ],
        "resources": [
            {"title": "Dictionaries — Python tutorial", "url": "https://docs.python.org/3/tutorial/datastructures.html#dictionaries"},
            {"title": "Open-Meteo API docs (the real payloads)", "url": "https://open-meteo.com/en/docs"},
        ],
    },
    "ww-2": {
        "instructions": (
"Networks fail — briefly and randomly. Production code retries.\n\n"
"**Your task**\n\n"
"Write `with_retry(fn, attempts=3)`:\n\n"
"1. Call `fn()` and return its result if it succeeds.\n"
"2. If it raises, try again — up to `attempts` **total** calls.\n"
"3. If the last attempt also fails, re-raise that final exception (don't swallow it, "
"don't wrap it).\n\n"
"The checker uses a function that fails twice then succeeds (must return 'ok' after "
"exactly 3 calls) and one that always fails (must raise after exactly 2 when "
"`attempts=2`). In real code you'd sleep between tries (`time.sleep(2 ** i)` — "
"exponential backoff); skip sleeping here so the checks run fast."
        ),
        "refresher": (
"**From basics to this exercise.** Two basic-Python ideas combine here.\n\n"
"*1. Functions are objects.* You can pass a function into another function without "
"calling it — `with_retry(fetch)` passes the recipe, `fn()` cooks it. Any function "
"that takes/returns functions is a **higher-order function**; you already use them "
"(`sorted(data, key=len)`).\n\n"
"*2. try/except inside a loop* is the retry skeleton:\n\n"
"```python\nfor attempt in range(attempts):\n    try:\n        return do_thing()\n    except Exception as e:\n        last_error = e\nraise last_error\n```\n\n"
"Note how `return` inside try exits the whole function on success — the loop only "
"continues on failure.\n\n"
"**Why re-raise instead of returning None?** A pipeline step that quietly returns "
"None on failure poisons everything downstream. Fail loudly; let the orchestrator "
"decide. When you reach Project 8 you'll configure `retries=2` on an Airflow task "
"and recognize this exact pattern — implemented by the scheduler instead of a loop.\n\n"
"**Practice beyond the exercise:** extend your project version with "
"`time.sleep(2 ** attempt)` backoff and a `retry_on=(ConnectionError,)` parameter so "
"only *transient* errors retry — a `ValueError` from bad data should fail immediately."
        ),
        "objectives": [
            "Pass functions as arguments (higher-order functions)",
            "Build the retry loop pattern: try/except inside for, return on success",
            "Explain why failures should re-raise, and connect this to Airflow task retries",
        ],
        "hints": [
            "Loop `for _ in range(attempts):` — inside, try: return fn() / except Exception as e: save e.",
            "After the loop ends (all attempts failed), `raise last_error` — the saved exception.",
            "Common bug: `range(attempts - 1)` or retrying inside except — count your calls: attempts=3 means fn() runs at most 3 times.",
        ],
        "resources": [
            {"title": "Errors and exceptions — Python tutorial", "url": "https://docs.python.org/3/tutorial/errors.html"},
            {"title": "Real Python: higher-order functions", "url": "https://realpython.com/python-functional-programming/"},
            {"title": "tenacity — the retry library you'd use in production", "url": "https://tenacity.readthedocs.io/"},
        ],
    },
    "ww-3": {
        "instructions": (
"The L in ETL — and the single most important production habit: **idempotent loads**.\n\n"
"**Your task**\n\n"
"The table `readings(city, time, temp)` has a `UNIQUE(city, time)` constraint. "
"Implement `upsert(conn, rows)` (rows are `(city, time, temp)` tuples) using SQLite's "
"upsert syntax:\n\n"
"```sql\nINSERT INTO readings(city, time, temp) VALUES(?, ?, ?)\nON CONFLICT(city, time) DO UPDATE SET temp = excluded.temp\n```\n\n"
"The checker inserts 2 rows, re-runs with an updated temp for one of them, and then "
"requires: still exactly 2 rows, and the updated temp won. Run twice, same result — "
"that's idempotency.\n\n"
"Use `conn.executemany(...)` and remember to `conn.commit()`."
        ),
        "refresher": (
"**From basics to this exercise.** `sqlite3` is in the standard library — a real SQL "
"database in one file (or in memory), no server:\n\n"
"```python\nimport sqlite3\nconn = sqlite3.connect(':memory:')\nconn.execute('INSERT INTO t VALUES (?, ?)', (a, b))   # ? = placeholder\nconn.executemany('INSERT INTO t VALUES (?, ?)', rows) # many at once\nconn.commit()                                          # make it permanent\n```\n\n"
"**Always use `?` placeholders** — never f-strings — so values are escaped properly "
"(string-built SQL is how injection bugs happen).\n\n"
"**The idempotency idea.** An operation is *idempotent* if doing it twice equals "
"doing it once. Plain INSERT is not (rows duplicate); INSERT with "
"`ON CONFLICT ... DO UPDATE` is: the UNIQUE constraint detects 'already there' and "
"the conflict clause updates instead. `excluded` is SQLite's name for 'the row that "
"tried to get in'.\n\n"
"**Why this is the hill to die on:** every scheduler retries. Airflow will rerun "
"your load task after a network blip *by design* — if loads aren't idempotent, "
"every retry silently doubles your data, and you find out in a quarterly report. "
"Every pipeline you build from here on should pass the run-it-twice test.\n\n"
"**Practice beyond the exercise:** in your project DB, try the run-twice test on a "
"plain INSERT version and watch the duplicates appear — seeing the failure mode "
"once makes the habit stick."
        ),
        "objectives": [
            "Use sqlite3 with placeholders, executemany, and commit",
            "Write an UPSERT with ON CONFLICT ... DO UPDATE / excluded",
            "Define idempotency and apply the run-it-twice test to any pipeline step",
        ],
        "hints": [
            "The SQL is given in the instructions verbatim — pair it with conn.executemany(sql, rows).",
            "Forgot commit()? In-memory DBs are forgiving, but real files aren't — build the habit now.",
        ],
        "resources": [
            {"title": "sqlite3 — official docs", "url": "https://docs.python.org/3/library/sqlite3.html"},
            {"title": "SQLite UPSERT syntax", "url": "https://www.sqlite.org/lang_upsert.html"},
            {"title": "Airflow best practices (see 'idempotency')", "url": "https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html"},
        ],
    },
    # ================================================== LogMiner
    "lm-1": {
        "instructions": (
"Your first real generator — the mental model that later makes Spark click.\n\n"
"**Your task**\n\n"
"Write `numbers(lines)` — a **generator function** (uses `yield`) that takes any "
"iterable of raw strings and:\n\n"
"1. skips blank/whitespace-only lines,\n"
"2. skips comment lines starting with `#`,\n"
"3. yields every remaining line converted to `int`.\n\n"
"**Laziness is the point and the checker measures it:** it wraps the input in a "
"tracking iterator, pulls ONE value from your generator, and fails you if you "
"consumed more than 2 input lines to produce it. Building a list and returning it "
"flunks — no `return [...]`."
        ),
        "refresher": (
"**From basics to this exercise.** You know `for` loops and functions; a generator "
"is a function whose body *pauses*. Swap `return` for `yield`:\n\n"
"```python\ndef squares(nums):\n    for n in nums:\n        yield n * n\n\ng = squares([1, 2, 3])   # nothing runs yet!\nnext(g)                  # runs JUST until the first yield -> 1\n```\n\n"
"Calling a generator function executes none of its body — it returns a generator "
"object. Each `next()` resumes the frozen function, runs to the next `yield`, and "
"freezes again, keeping all local variables alive. A `for` loop over it calls "
"`next()` until the function ends.\n\n"
"**Why lazy beats eager for data work:** `[int(x) for x in lines]` materializes "
"everything in memory before you use any of it. A generator processes one item at a "
"time — a 100GB file streams through a few KB of RAM. Chain generators and you get "
"a *pipeline* where each line flows through all stages before the next line is even "
"read.\n\n"
"**The Spark connection (Project 6):** `df.filter(...).select(...)` also builds a "
"lazy recipe that only executes when an action demands results — Spark simply runs "
"your recipe over *partitions on many machines* instead of lines on one. Learn "
"yield deeply now and Spark's laziness will feel obvious.\n\n"
"**Practice beyond the exercise:** rewrite it as a generator expression "
"`(int(s) for s in lines if ...)` and check `next()` still works; then try "
"`sum(numbers(open('big.txt')))` on a large file in your project and watch memory "
"stay flat."
        ),
        "objectives": [
            "Write generator functions with yield and consume them with next()/for",
            "Explain why calling a generator runs none of its body",
            "Choose lazy generators over list-building for large data",
        ],
        "hints": [
            "Shape: `for line in lines:` → strip it → `continue` on blanks/# → `yield int(...)`.",
            "Strip once into a variable: `s = line.strip()`; test `if not s or s.startswith('#')`.",
            "If the checker says 'not lazy', you built a list somewhere — there should be no [ ] in your function.",
        ],
        "resources": [
            {"title": "Generators — Python tutorial", "url": "https://docs.python.org/3/tutorial/classes.html#generators"},
            {"title": "Real Python: introduction to generators", "url": "https://realpython.com/introduction-to-python-generators/"},
            {"title": "PEP 255 — why yield exists", "url": "https://peps.python.org/pep-0255/"},
        ],
    },
    "lm-2": {
        "instructions": (
"Real logs are messy text; regex turns them into structured data.\n\n"
"**Your task**\n\n"
"Write `parse(line)` for Apache-style access-log lines like:\n\n"
"```\n203.0.113.7 - - [27/Jul/2026:10:01:22] \"GET /api/x HTTP/1.1\" 200 512\n```\n\n"
"Return `{'ip': '203.0.113.7', 'status': 200, 'bytes': 512}` — note status and "
"bytes are **ints** — or `None` for lines that don't match (real logs always "
"contain garbage; a parser that crashes on line 40,001 of 10M is useless).\n\n"
"Use the `re` module with **capture groups**, and `re.compile` your pattern once "
"outside the function — compiled patterns are much faster in a loop."
        ),
        "refresher": (
"**From basics to this exercise.** String methods (`split`, `startswith`) handle "
"simple formats; regex handles the rest. The 20% you need for 80% of parsing:\n\n"
"```python\nimport re\nPAT = re.compile(r'(\\d+) errors')  # compile ONCE, reuse\nm = PAT.search('found 42 errors')   # None if no match\nif m:\n    count = int(m.group(1))         # group(1) = first (...) capture\n```\n\n"
"Building blocks: `\\d` digit, `+` one-or-more, `.` any char, `\\.` a literal dot, "
"`\\s` whitespace, `[^\"]` anything-but-quote, `^`/`$` line start/end. **Capture "
"groups `(...)`** are the payoff — they extract the pieces you care about, in order: "
"`m.group(1)`, `m.group(2)`...\n\n"
"Always write patterns as **raw strings** (`r'...'`) so backslashes reach the regex "
"engine intact. Test patterns interactively at regex101.com (set flavor to Python) — "
"it explains every token as you type.\n\n"
"**The match/None discipline:** `search`/`match` return None on failure, so the "
"caller decides — skip the line, count it, log it. Your parser reporting None "
"instead of raising is what lets a 10M-line stream keep flowing. (Same philosophy "
"as Spark's `mode='PERMISSIVE'` CSV parsing, which routes bad rows to a side "
"column rather than failing the job.)\n\n"
"**Practice beyond the exercise:** extend your project's pattern to also capture "
"the HTTP method and path from inside the quoted request string."
        ),
        "objectives": [
            "Read and write basic regex: \\d, +, character classes, anchors",
            "Extract fields with capture groups and convert types at the boundary",
            "Design parsers that return None on bad input instead of crashing streams",
        ],
        "hints": [
            "You need three captures: the IP at the start `(\\d+\\.\\d+\\.\\d+\\.\\d+)`, and the final two numbers `(\\d{3}) (\\d+)$`.",
            "You don't have to match every character in between — `.*` can swallow the middle: start-anchor IP, `.*`, then status and bytes at the end.",
            "Wrap up: `m = PAT.match(line)` → `if not m: return None` → build the dict with int() around groups 2 and 3.",
        ],
        "resources": [
            {"title": "Regex HOWTO — official tutorial", "url": "https://docs.python.org/3/howto/regex.html"},
            {"title": "re module reference", "url": "https://docs.python.org/3/library/re.html"},
            {"title": "regex101 — interactive tester (choose Python flavor)", "url": "https://regex101.com/"},
        ],
    },
    "lm-3": {
        "instructions": (
"Aggregate a stream you can only read once — a hand-rolled map/reduce.\n\n"
"**Your task**\n\n"
"Write `top_ips(rows, n)`: consume an iterable of `{'ip': ...}` dicts in a "
"**single pass** and return the `n` most frequent IPs as `[(ip, count), ...]`, "
"most frequent first.\n\n"
"The input is a generator — it cannot be rewound or len()'d. `collections.Counter` "
"does the heavy lifting: count in one pass, then `most_common(n)`.\n\n"
"This exact computation — count per key, take the top n — is what you'll write in "
"Spark in Project 6 as `df.groupBy('ip').count().orderBy(...).limit(n)`."
        ),
        "refresher": (
"**From basics to this exercise.** The manual counting pattern you learned early "
"on:\n\n"
"```python\ncounts = {}\nfor item in items:\n    counts[item] = counts.get(item, 0) + 1\n```\n\n"
"`collections.Counter` packages it with the useful extras:\n\n"
"```python\nfrom collections import Counter\nc = Counter(['a', 'b', 'a'])      # accepts any iterable\nc['a']            # 2 (missing keys -> 0, no KeyError)\nc.most_common(2)  # [('a', 2), ('b', 1)] — sorted for you\n```\n\n"
"Feed it a **generator expression** to stay single-pass and memory-flat: "
"`Counter(r['ip'] for r in rows)` pulls each row once, updates a count, and lets "
"the row be garbage-collected. Only the counts (one entry per *distinct* IP) live "
"in memory — 10M rows with 5,000 distinct IPs needs 5,000 dict entries.\n\n"
"**Why single-pass matters:** a generator is consumed by iterating; a second loop "
"over it sees nothing. Streams (sockets, huge files, Spark partitions) are all "
"one-shot. Design aggregations to need exactly one pass and you can run them on "
"anything.\n\n"
"**The distributed connection:** Counter-per-partition then merging counters is "
"literally Spark's combine-then-reduce strategy for `groupBy().count()` — you'll "
"build that merge yourself in Project 6's mini-Spark exercise.\n\n"
"**Practice beyond the exercise:** compute error-rate per IP in the same single "
"pass by updating two Counters in one loop."
        ),
        "objectives": [
            "Use Counter and most_common for top-N problems",
            "Write single-pass aggregations over one-shot iterables",
            "Reason about memory: counts per distinct key, not per row",
        ],
        "hints": [
            "One line: build Counter from a generator expression over rows, extracting r['ip'].",
            "most_common(n) already returns the [(ip, count), ...] list sorted descending — return it directly.",
        ],
        "resources": [
            {"title": "collections.Counter — official docs", "url": "https://docs.python.org/3/library/collections.html#collections.Counter"},
            {"title": "Real Python: Counter guide", "url": "https://realpython.com/python-counter/"},
        ],
    },
    # ================================================== DataDeck
    "dd-1": {
        "instructions": (
"Enforce data quality at the border of your service.\n\n"
"**Your task**\n\n"
"Define a pydantic model `Reading` with validation rules:\n\n"
"- `city: str` — must be at least 1 character (empty string rejected)\n"
"- `temperature: float` — must be between −90 and 60 (physically plausible on Earth)\n"
"- `time: str` — any string\n\n"
"Constructing `Reading(city='X', temperature=200.0, ...)` must raise "
"`ValidationError`. Use `Field(...)` with constraint arguments — see the refresher "
"for the exact knobs.\n\n"
"In DataDeck, FastAPI will run this validation automatically on every POST body — "
"you declare the model once and bad payloads get a detailed 422 response for free."
        ),
        "refresher": (
"**From basics to this exercise.** You've written manual validation:\n\n"
"```python\ndef __init__(self, temp):\n    if not -90 <= temp <= 60:\n        raise ValueError('implausible temp')\n```\n\n"
"Pydantic turns the *type hints you already know* into enforced runtime schema:\n\n"
"```python\nfrom pydantic import BaseModel, Field\n\nclass User(BaseModel):\n    name: str = Field(min_length=1)\n    age: int = Field(ge=0, le=150)   # ge/le = >= / <=\n```\n\n"
"`User(name='', age=-3)` raises `ValidationError` listing *every* violated rule. "
"Pydantic also *coerces* sensible inputs (`'42'` → 42 for an int field) — parsing, "
"not just checking.\n\n"
"**The principle — validate at the boundary:** check data once, where it enters "
"(API request, file read, message queue). Inside your program, a `Reading` object "
"is *proof* the data is clean — no defensive re-checking scattered everywhere. "
"Garbage is rejected at the door with a precise error message.\n\n"
"You'll meet this idea again as Spark DataFrame schemas (Project 6's explicit "
"`StructType`) and typed Airflow params — all boundaries, all validated once.\n\n"
"**Practice beyond the exercise:** add a `windspeed: float = Field(ge=0)` and try "
"`Reading(temperature='18.4', ...)` to watch coercion parse the string."
        ),
        "objectives": [
            "Declare pydantic models with Field constraints (min_length, ge, le)",
            "Explain validate-at-the-boundary and what it buys the rest of the code",
            "Distinguish validation (reject) from parsing/coercion (convert)",
        ],
        "hints": [
            "city: `str = Field(min_length=1)`; temperature: `float = Field(ge=-90, le=60)`; time needs no Field at all.",
            "The checker imports ValidationError for you — your model just has to raise it naturally on bad construction.",
        ],
        "resources": [
            {"title": "Pydantic: Fields & constraints", "url": "https://docs.pydantic.dev/latest/concepts/fields/"},
            {"title": "Pydantic: Models", "url": "https://docs.pydantic.dev/latest/concepts/models/"},
            {"title": "Parse, don't validate (the classic essay)", "url": "https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/"},
        ],
    },
    "dd-2": {
        "instructions": (
"Build and test a real HTTP endpoint — in one exercise, no server process.\n\n"
"**Your task**\n\n"
"1. On the provided FastAPI `app`, add a GET endpoint at path `/cities/{name}` — "
"note the `{name}` **path parameter** — returning `{'city': name, 'len': len(name)}`.\n"
"2. The checker then does `TestClient(app).get('/cities/Harare')` and expects "
"status 200 and that exact JSON.\n\n"
"Endpoints are plain functions wearing a decorator; the returned dict becomes the "
"JSON response automatically. This is the exact pattern serving the very app "
"you're using right now — after this project, read `app/main.py` in the DataForged "
"source and you'll recognize everything."
        ),
        "refresher": (
"**From basics to this exercise.** Two basics power web frameworks: *decorators* "
"and *type hints*.\n\n"
"A decorator wraps/registers a function — `@app.get(path)` simply records \"this "
"function handles GET requests to this path\":\n\n"
"```python\nfrom fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/items/{item_id}')\ndef read_item(item_id: int):      # {item_id} in path -> argument\n    return {'id': item_id}        # dict -> JSON, automatically\n```\n\n"
"The `item_id: int` hint isn't decoration — FastAPI *uses* it to convert and "
"validate: `/items/abc` gets an automatic 422 error without you writing a thing. "
"Type hints as machine-read contracts — same philosophy as pydantic (dd-1), which "
"is no coincidence: FastAPI is built on pydantic.\n\n"
"**Testing without a server:** `TestClient(app)` speaks HTTP directly to your app "
"object in-process — no port, no `uvicorn`, runs in milliseconds. This is how you "
"unit-test services in CI:\n\n"
"```python\nfrom fastapi.testclient import TestClient\nclient = TestClient(app)\nassert client.get('/items/5').json() == {'id': 5}\n```\n\n"
"**Practice beyond the exercise:** add a query parameter — "
"`def endpoint(name: str, upper: bool = False)` — and call "
"`/cities/harare?upper=true`; FastAPI wires it from the query string automatically. "
"Then open `localhost:8000/docs` on your DataDeck service to see the auto-generated "
"interactive docs."
        ),
        "objectives": [
            "Define GET endpoints with path parameters via decorators",
            "Explain how FastAPI uses type hints for conversion and validation",
            "Test endpoints in-process with TestClient",
        ],
        "hints": [
            "`@app.get('/cities/{name}')` above `def city(name: str):` — the path placeholder and argument name must match.",
            "Return the dict literally: `{'city': name, 'len': len(name)}` — FastAPI handles JSON conversion.",
        ],
        "resources": [
            {"title": "FastAPI: First steps", "url": "https://fastapi.tiangolo.com/tutorial/first-steps/"},
            {"title": "FastAPI: Path parameters", "url": "https://fastapi.tiangolo.com/tutorial/path-params/"},
            {"title": "FastAPI: Testing", "url": "https://fastapi.tiangolo.com/tutorial/testing/"},
        ],
    },
    "dd-3": {
        "instructions": (
"Feel concurrency instead of reading about it — the checker uses a stopwatch.\n\n"
"**Your task**\n\n"
"Write `async def gather_all(coros)` that runs a list of coroutines "
"**concurrently** and returns their results in the same order.\n\n"
"The checker launches three 0.1-second sleepers through your function. Run them "
"one-by-one (`for c in coros: await c`) and it takes 0.3s — **fail**. Run them "
"concurrently with `asyncio.gather` and all three sleeps overlap on one thread — "
"~0.1s — **pass**.\n\n"
"Mind the star: `gather(*coros)` unpacks the list into separate arguments."
        ),
        "refresher": (
"**From basics to this exercise.** A coroutine (`async def`) is a function that "
"can *pause*: `await` marks the pause points. While one coroutine waits (for a "
"timer, a network reply, a DB query), the **event loop** runs others — cooperative "
"multitasking on a single thread. If generators clicked in LogMiner, you're "
"already there: `await` freezes and resumes a frame just like `yield` does.\n\n"
"The trap this exercise sets:\n\n"
"```python\nfor c in coros:      # sequential: each await BLOCKS this coroutine\n    await c          # until it finishes -> 0.1 + 0.1 + 0.1 s\n```\n\n"
"versus:\n\n"
"```python\nawait asyncio.gather(*coros)   # all started together -> ~0.1 s\n```\n\n"
"`gather` schedules everything on the loop at once, then waits for the set; "
"results come back **in input order** regardless of finish order.\n\n"
"**The rule that makes async services fast (or ruins them):** only `await`-able "
"waiting overlaps. A blocking call — `time.sleep`, `requests.get`, heavy CPU — "
"freezes the whole event loop and every request on it. Inside async code: "
"`asyncio.sleep` not `time.sleep`, `httpx.AsyncClient` not `requests`; and push "
"heavy computation out of the request path entirely — which in this curriculum is "
"exactly why data crunching moves to Spark rather than living in an endpoint.\n\n"
"**Practice beyond the exercise:** in DataDeck, add an endpoint that fetches two "
"URLs with httpx concurrently and returns both — measure it against the "
"sequential version."
        ),
        "objectives": [
            "Explain coroutines, await, and the single-threaded event loop",
            "Run tasks concurrently with asyncio.gather and preserve result order",
            "Identify blocking calls that would freeze an async service",
        ],
        "hints": [
            "The whole function can be one line: return the awaited gather of the unpacked list.",
            "`asyncio.gather(coros)` (no star) passes the list as one argument and fails — `gather(*coros)`.",
            "gather returns a tuple-like; the checker accepts a list — wrap with list(...) if you want to be exact.",
        ],
        "resources": [
            {"title": "Coroutines and tasks — asyncio docs", "url": "https://docs.python.org/3/library/asyncio-task.html"},
            {"title": "FastAPI: async/await explained gently", "url": "https://fastapi.tiangolo.com/async/"},
            {"title": "Real Python: async IO walkthrough", "url": "https://realpython.com/async-io-python/"},
        ],
    },
    # ================================================== Pandas PowerPlant
    "pp-1": {
        "instructions": (
"Compute on a million values without a single Python loop.\n\n"
"**Your task**\n\n"
"Given numpy arrays `fare` and `km`, produce `fare_per_km` where:\n\n"
"- each element is `fare[i] / km[i]`\n"
"- wherever `km` is 0, the result is 0 (no division-by-zero warnings, no inf/nan)\n\n"
"**Rules enforced by the checker:** the result must be a numpy array equal to "
"`[5.0, 5.0, 0.0, 4.0]`, and your source must contain no `for`/`while` loops — "
"pure array operations only. `np.where(condition, if_true, if_false)` is the key "
"tool; the subtlety is avoiding the 0-division *before* it happens (see hint 2 if "
"stuck)."
        ),
        "refresher": (
"**From basics to this exercise.** In basic Python, elementwise math means a loop "
"or comprehension: `[f / k for f, k in zip(fare, km)]`. NumPy replaces the loop "
"with *array expressions*:\n\n"
"```python\nimport numpy as np\na = np.array([1.0, 2.0, 3.0])\na * 10          # array([10., 20., 30.]) — one C loop\na > 1.5         # array([False, True, True]) — boolean mask\nnp.where(a > 1.5, a, 0.0)   # pick per element: array([0., 2., 3.])\n```\n\n"
"**Why it's ~100x faster:** a numpy array is one contiguous block of typed memory. "
"`fare / km` runs a compiled C loop over raw doubles — no per-element interpreter "
"dispatch, no boxing ints into objects, CPU cache used perfectly. Your Python "
"loop pays interpreter overhead on every single element. Same algorithm, "
"different executor — this is THE performance idea of the entire data world.\n\n"
"**Handling the zero:** `np.where(km == 0, 0, fare/km)` still *computes* "
"`fare/km` everywhere first (both branches evaluate — it's an expression, not an "
"if). Cleanest is dividing by a doctored denominator so the division is always "
"safe, then masking the result. Real datasets are full of zeros/NaNs, so this "
"dance is everyday work.\n\n"
"**Where you'll see it again:** pandas columns *are* numpy arrays — `df.fare / "
"df.km` is this exercise. And Spark's vectorized engine applies the same "
"columnar-batch idea across a cluster; a Python UDF in Spark reintroduces the "
"slow loop, which is why Project 6 warns against them.\n\n"
"**Practice beyond the exercise:** time both versions on 10M elements with "
"`%timeit` in your notebook — measure the 100x yourself."
        ),
        "objectives": [
            "Replace element loops with vectorized array expressions",
            "Use boolean masks and np.where for conditional logic",
            "Explain WHY contiguous typed memory + C loops beat Python loops",
        ],
        "hints": [
            "Both branches of np.where evaluate — so make the division itself safe first.",
            "Divide by a safe denominator: `safe = np.where(km == 0, 1.0, km)`, then `np.where(km == 0, 0.0, fare / safe)`.",
            "Alternative pro move: `np.divide(fare, km, out=np.zeros_like(fare), where=(km != 0))`.",
        ],
        "resources": [
            {"title": "NumPy: the absolute basics", "url": "https://numpy.org/doc/stable/user/absolute_beginners.html"},
            {"title": "np.where reference", "url": "https://numpy.org/doc/stable/reference/generated/numpy.where.html"},
            {"title": "Real Python: NumPy array programming", "url": "https://realpython.com/numpy-array-programming/"},
        ],
    },
    "pp-2": {
        "instructions": (
"Split-apply-combine — the single most useful analytics pattern.\n\n"
"**Your task**\n\n"
"From the small trips DataFrame, produce `result`: **total fare per borough, "
"sorted descending** — Manhattan 32.0, Brooklyn 15.0, Queens 5.0.\n\n"
"The chain is: group by borough → select the fare column → sum → sort. Before you "
"aggregate, try `trips.groupby('borough')` alone in your notebook and inspect what "
"that lazy GroupBy object is — then `.groups`, then loop over it — to *see* the "
"split step before apply and combine."
        ),
        "refresher": (
"**From basics to this exercise.** By hand, grouping is a dict-of-lists (you did "
"this in LogMiner's Counter, and again in mini-Spark next project):\n\n"
"```python\ntotals = {}\nfor row in rows:\n    totals[row.borough] = totals.get(row.borough, 0) + row.fare\n```\n\n"
"Pandas names the three phases **split** (partition rows by key), **apply** (sum "
"each group), **combine** (assemble results into a Series indexed by key):\n\n"
"```python\ndf.groupby('borough')['fare'].sum()\n#  ^ split            ^ select   ^ apply+combine\n```\n\n"
"Selecting `['fare']` *before* aggregating matters: sum only what you need. The "
"result is a **Series** whose index is the group keys — sort it with "
"`.sort_values(ascending=False)`.\n\n"
"Other aggregations are drop-in: `.mean()`, `.count()`, `.max()`, or several at "
"once via `.agg(['sum', 'mean'])`. Groupby is the workhorse of every analytics "
"job you'll ever write.\n\n"
"**The scaling story:** this identical operation IS Spark's "
"`df.groupBy('borough').sum('fare')` in Project 6 — same mental model, except "
"Spark's *split* phase physically moves rows between machines (the shuffle). "
"Understanding pandas groupby means you already understand what Spark distributes.\n\n"
"**Practice beyond the exercise:** on your 1M-row taxi dataset, compute mean fare "
"per borough per *hour* (group by two keys: pass a list) and find the priciest "
"hour in each borough."
        ),
        "objectives": [
            "Use groupby + column selection + aggregation fluently",
            "Explain split-apply-combine and recognize it across tools",
            "Sort aggregated Series and read their index/values",
        ],
        "hints": [
            "trips.groupby('borough')['fare'].sum() gets the totals — then sort descending.",
            ".sort_values(ascending=False) on the resulting Series completes it.",
        ],
        "resources": [
            {"title": "pandas: Group by (split-apply-combine)", "url": "https://pandas.pydata.org/docs/user_guide/groupby.html"},
            {"title": "Real Python: pandas GroupBy", "url": "https://realpython.com/pandas-groupby/"},
        ],
    },
    "pp-3": {
        "instructions": (
"Join two tables, aggregate, and crown a winner — the everyday analytics combo.\n\n"
"**Your task**\n\n"
"1. Merge `trips` (zone_id, fare) with `zones` (zone_id, borough) on `zone_id`.\n"
"2. Total the fares per zone.\n"
"3. Set `winner` to the **zone_id with the highest total** (zone 1: 10+4+2 = 16.0).\n\n"
"Use `pd.merge`/`df.merge` and `idxmax()` — which returns the *index label* of the "
"max, not its position. While you're here, think through what `how='inner'` vs "
"`'left'` would do if a trip had `zone_id=99` with no match in zones — that choice "
"silently changes row counts in real pipelines."
        ),
        "refresher": (
"**From basics to this exercise.** A join is dict-lookup enrichment — for each "
"trip, look up its zone's info and glue the columns on. You could write it with a "
"loop; `merge` does it declaratively and fast:\n\n"
"```python\nmerged = trips.merge(zones, on='zone_id', how='inner')\n```\n\n"
"**The `how` parameter is where bugs live:**\n\n"
"- `inner` — keep only rows with a match on both sides (unmatched trips *vanish*)\n"
"- `left` — keep every trip; missing zone columns become NaN\n"
"- `outer` — keep everything from both sides\n\n"
"Sanity-check row counts after every join. A join key with duplicates on both "
"sides multiplies rows (cartesian per key) — the classic silent data bug.\n\n"
"**`idxmax()`** answers \"*which* group is the max?\": on a Series like "
"`totals = merged.groupby('zone_id')['fare'].sum()`, `totals.max()` is the value "
"(16.0) but `totals.idxmax()` is the *index label* — the zone_id you want.\n\n"
"**The scaling story:** joins are THE expensive operation in distributed systems — "
"Project 7 is largely about them. Matching rows must physically meet on the same "
"machine (shuffle join) unless one side is small enough to copy everywhere "
"(broadcast join — you'll hand-build one). Every instinct you form here about "
"keys, duplicates, and row counts transfers directly.\n\n"
"**Practice beyond the exercise:** add a zone_id=99 trip, run both `inner` and "
"`left`, and compare row counts and NaNs — five minutes that will save you real "
"debugging hours someday."
        ),
        "objectives": [
            "Merge DataFrames on keys and predict row counts for inner/left/outer",
            "Find the argmax of an aggregation with idxmax",
            "Anticipate join pitfalls: lost rows, duplicate-key blowups",
        ],
        "hints": [
            "Three steps chained: merge on zone_id → groupby('zone_id')['fare'].sum() → .idxmax().",
            "idxmax() returns the zone_id itself because zone_id became the Series index after groupby.",
        ],
        "resources": [
            {"title": "pandas: merge & joins user guide", "url": "https://pandas.pydata.org/docs/user_guide/merging.html"},
            {"title": "idxmax reference", "url": "https://pandas.pydata.org/docs/reference/api/pandas.Series.idxmax.html"},
            {"title": "Spark SQL joins (where this goes next)", "url": "https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-join.html"},
        ],
    },
}

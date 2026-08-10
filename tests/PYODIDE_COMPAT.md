# Browser (Pyodide) compatibility report

How the `runtime` tag on each exercise was determined — evidence, not guesswork.

## Method

Every one of the 85 exercises was executed inside **real headless Chromium**
running Pyodide (Python 3.14, `pyodide` npm package 314.0.3), using the same
script composition the app uses (`_USER_SOURCE` + learner code + check code).
Each exercise was run twice: once with its reference solution (must pass) and
once with the untouched starter code (must fail, proving the check is
meaningful).

Harness: `tests/pyodide/harness.html` + `tests/pyodide/run_compat.py` (kept out
of the shipped app; see `tests/pyodide/README.md` to re-verify).

## Results

| Outcome | Count | Exercises |
|---|---|---|
| Verified running in the browser | 76 | everything not listed below |
| Blocked only by the offline test sandbox | 7 | dd-1, dd-2, pp-1, pp-2, pp-3, cr-2, dt-1 |
| Genuinely impossible in a browser | 2 | fs-3, ss-3 |

**The 7 sandbox-blocked ones** need packages (`pydantic`, `fastapi`, `numpy`,
`pandas`, `duckdb`) that ship in the Pyodide distribution but are fetched from
a CDN the test sandbox could not reach. Two independent checks cover them:

1. Presence confirmed in `pyodide-lock.json` — numpy 2.4.3, pandas 3.0.2,
   scikit-learn 1.8.0, pydantic 2.12.5, fastapi 0.136.1, duckdb 1.5.1.
2. All 7 were run natively against **those exact library versions** and passed,
   so there are no API-compatibility surprises (pandas 3.0 and numpy 2.4 are
   newer than the local Docker stack's pandas 2.2 / numpy 1.26).

In production the browser downloads these from the CDN on first use, which is
why the UI shows a one-off "downloading pandas…" notice for those exercises.

**The 2 impossible ones** (`fs-3`, `ss-3`) start a real JVM Spark session.
There is no JVM in WebAssembly, so they are tagged `runtime: "local"` and the
app tells the learner to run them in the local Docker stack. The concepts they
teach are still covered in the browser by `fs-1` (map/shuffle/reduce) and
`fs-2` (lazy plans), which implement Spark's model in pure Python.

## Two findings this testing produced

**`pg-1` was flaky and is now fixed.** The consistent-hashing exercise used
Python's built-in `hash()`, which is randomized per process
(`PYTHONHASHSEED`), so the load-balance assertion could pass or fail depending
on the interpreter. It now uses an MD5-based `stable_hash` — which is what real
consistent-hashing implementations use, and for exactly this reason: two
machines computing different rings for the same key would break a distributed
cache. The lesson is now part of the exercise.

**`dd-2` no longer depends on threads.** `TestClient` runs the app through an
`anyio` blocking portal, which needs a threadpool that browsers may not
provide. The check now tries `TestClient` first and falls back to calling the
ASGI app directly — same request, same assertions, no threads. Both paths are
tested.

## Re-running the check

```bash
cd pyotest && npm install pyodide && ln -s node_modules/pyodide pyodide
python3 -m http.server 8899 &
python3 run_compat.py            # add an exercise id to test just one
```

With network access to `cdn.jsdelivr.net`, point `indexURL` at the CDN in
`harness.html` and all 85 (minus the two Spark ones) can be verified in one go.

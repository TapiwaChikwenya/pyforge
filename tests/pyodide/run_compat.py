"""Run every DataForged exercise inside real Pyodide (headless Chromium) and report
which ones work in the browser vs which need the local Docker runtime.

Paths are relative to this directory — no hardcoded absolute machine paths.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
EXERCISES_PATH = HERE / "exercises.json"
RESULTS_PATH = HERE / "compat_results.json"

if not EXERCISES_PATH.exists():
    sys.stderr.write(
        f"Missing {EXERCISES_PATH.name}. Generate it first — see README.md.\n"
    )
    sys.exit(2)

exercises = json.loads(EXERCISES_PATH.read_text(encoding="utf-8"))
only = sys.argv[1] if len(sys.argv) > 1 else None
if only:
    exercises = [e for e in exercises if e["id"] == only]

chromium_path = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH") or None

results = []
with sync_playwright() as p:
    launch_kwargs = {}
    if chromium_path:
        launch_kwargs["executable_path"] = chromium_path
    b = p.chromium.launch(**launch_kwargs)
    page = b.new_page()
    page.goto(f"http://localhost:8899/harness.html")
    ver = page.evaluate("bootPyodide()")
    print("Pyodide python:", ver.split()[0])

    for i, ex in enumerate(exercises, 1):
        try:
            r = page.evaluate(
                "async ([s, c]) => await runExercise(s, c)",
                [ex["solution"], ex["check"]],
            )
        except Exception as e:  # page crash / timeout
            r = {"ok": False, "out": "", "err": f"harness error: {e}"}
        starter_ok = False
        if r["ok"]:
            try:
                rs = page.evaluate(
                    "async ([s, c]) => await runExercise(s, c)",
                    [ex["starter"], ex["check"]],
                )
                starter_ok = rs["ok"]
            except Exception:
                starter_ok = False
        results.append({
            **ex,
            "ok": r["ok"],
            "err": r.get("err", ""),
            "out": r.get("out", ""),
            "starter_passes": starter_ok,
        })
        flag = "ok  " if r["ok"] else "FAIL"
        if starter_ok:
            flag = "WEAK"
        print(f"{i:>3}/{len(exercises)} {flag} {ex['id']}")
    b.close()

fails = [r for r in results if not r["ok"]]
weak = [r for r in results if r["starter_passes"]]
print(f"\n=== {len(results) - len(fails)}/{len(results)} run in the browser ===")
for r in fails:
    print(f"\n--- {r['id']} ({r['project']}) : {r['title']}")
    print("   ", (r["err"] or "").replace("\n", "\n    ")[:400])
if weak:
    print("\nWEAK checks (starter passes):", [r["id"] for r in weak])

RESULTS_PATH.write_text(json.dumps(results, indent=1), encoding="utf-8")
print(f"wrote {RESULTS_PATH}")

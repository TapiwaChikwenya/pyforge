"""
Prove every exercise is solvable and every check actually checks:
  1. the reference solution PASSES its check_code
  2. the untouched starter_code FAILS (no exercise passes by doing nothing)

Run:  python tests/test_exercises.py [--skip-heavy]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))
sys.path.insert(0, str(Path(__file__).parent))

from curriculum import PROJECTS  # noqa: E402
from runner import run_exercise  # noqa: E402
from reference_solutions import SOLUTIONS  # noqa: E402

skip_heavy = "--skip-heavy" in sys.argv
failures = []

for p in PROJECTS:
    for ex in p["exercises"]:
        heavy = ex.get("heavy", False)
        if heavy and skip_heavy:
            print(f"SKIP   {ex['id']} (heavy)")
            continue

        sol = SOLUTIONS.get(ex["id"])
        if sol is None:
            failures.append(f"{ex['id']}: no reference solution")
            continue

        # 1) reference solution must pass
        res = run_exercise(sol, ex["check_code"], heavy=heavy)
        if not res["passed"]:
            failures.append(f"{ex['id']}: SOLUTION FAILED\n{res['error']}\n{res['output']}")
            print(f"FAIL   {ex['id']} (solution rejected)")
        else:
            print(f"pass   {ex['id']}: {res['output'].strip().splitlines()[-1][:70]}")

        # 2) raw starter code must NOT pass
        res2 = run_exercise(ex["starter_code"], ex["check_code"], heavy=heavy)
        if res2["passed"]:
            failures.append(f"{ex['id']}: STARTER CODE PASSES (check is too weak)")
            print(f"WEAK   {ex['id']} (starter passes!)")

print()
if failures:
    print(f"{len(failures)} problem(s):")
    for f in failures:
        print("-", f)
    sys.exit(1)
print("ALL EXERCISES OK: solutions pass, starters fail.")

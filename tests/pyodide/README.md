# Browser-compatibility harness

Runs every exercise inside real headless Chromium + Pyodide, to decide which
can execute in a browser (hosted mode) and which need the local Docker stack.
Results and findings: `../PYODIDE_COMPAT.md`.

```bash
cd tests/pyodide
npm install pyodide && ln -s node_modules/pyodide pyodide   # runtime only
python3 corsserve.py &                                     # serves it with CORS
# export the exercises the app currently defines:
python3 - <<'PY'
import json, sys
sys.path[:0] = ['../../app', '..']
from curriculum import PROJECTS
from reference_solutions import SOLUTIONS
json.dump([{'project': p['id'], 'id': e['id'], 'title': e['title'],
            'solution': SOLUTIONS[e['id']], 'check': e['check_code'],
            'starter': e['starter_code']}
           for p in PROJECTS for e in p['exercises']], open('exercises.json', 'w'))
PY
python3 run_compat.py            # add an exercise id to test just one
```

The npm package ships the runtime but **not** the package wheels, so
numpy/pandas/pydantic/fastapi/duckdb exercises will report "not installed"
unless you point `indexURL` in `harness.html` at a full distribution
(`https://cdn.jsdelivr.net/pyodide/v0.28.3/full/`) or extract one locally.

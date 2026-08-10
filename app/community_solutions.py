"""Curated alternate solutions — unlocked only after an exercise is passed.

These are intentional variants with tradeoff notes for post-pass learning,
not the primary reference solutions used by the test harness.
"""

from __future__ import annotations

from typing import Any

# exercise_id -> list of {title, code, tradeoffs}
COMMUNITY_SOLUTIONS: dict[str, list[dict[str, Any]]] = {
    "tf-1": [
        {
            "title": "Explicit __post_init__ hygiene",
            "code": (
                "from dataclasses import dataclass, field\n\n"
                "@dataclass\n"
                "class Task:\n"
                "    title: str\n"
                "    done: bool = False\n"
                "    tags: list = field(default_factory=list)\n\n"
                "    def complete(self):\n"
                "        self.done = True\n"
                "        return self\n"
            ),
            "tradeoffs": (
                "Same as the common solution. Prefer `default_factory` over "
                "`tags: list = []` — mutable class defaults are a classic trap."
            ),
        },
        {
            "title": "Frozen dataclass + replace",
            "code": (
                "from dataclasses import dataclass, field, replace\n\n"
                "@dataclass(frozen=True)\n"
                "class Task:\n"
                "    title: str\n"
                "    done: bool = False\n"
                "    tags: list = field(default_factory=list)\n\n"
                "    def complete(self):\n"
                "        # frozen: return a new instance instead of mutating\n"
                "        return replace(self, done=True)\n"
            ),
            "tradeoffs": (
                "Immutability is nicer for concurrency, but this variant will "
                "**fail** the check that expects `complete()` to mutate and "
                "return `self`. Useful interview discussion: when to freeze."
            ),
        },
    ],
    "tf-2": [
        {
            "title": "Dict-backed store",
            "code": (
                "class TaskNotFoundError(Exception):\n"
                "    pass\n\n"
                "class TaskStore:\n"
                "    def __init__(self):\n"
                "        self._by_id = {}\n\n"
                "    def add(self, task):\n"
                "        self._by_id[task.id] = task\n"
                "        return task\n\n"
                "    def get(self, task_id):\n"
                "        try:\n"
                "            return self._by_id[task_id]\n"
                "        except KeyError:\n"
                "            raise TaskNotFoundError(task_id)\n"
            ),
            "tradeoffs": (
                "O(1) lookup by id vs a list scan. Slightly more memory; better "
                "once the store grows beyond a teaching example."
            ),
        },
    ],
    "tf-3": [
        {
            "title": "Pathlib + atomic-ish write",
            "code": (
                "import json\n"
                "from pathlib import Path\n\n"
                "def save_tasks(path, tasks):\n"
                "    p = Path(path)\n"
                "    tmp = p.with_suffix(p.suffix + '.tmp')\n"
                "    tmp.write_text(json.dumps(tasks, indent=2))\n"
                "    tmp.replace(p)\n\n"
                "def load_tasks(path):\n"
                "    p = Path(path)\n"
                "    if not p.exists():\n"
                "        return []\n"
                "    return json.loads(p.read_text())\n"
            ),
            "tradeoffs": (
                "Atomic replace avoids truncated files on crash. Overkill for "
                "tiny homework data; standard practice for real persistence."
            ),
        },
    ],
    "ww-1": [
        {
            "title": "Dict comprehension flatten",
            "code": (
                "def flatten(d, parent=''):\n"
                "    out = {}\n"
                "    for k, v in d.items():\n"
                "        key = f'{parent}.{k}' if parent else k\n"
                "        if isinstance(v, dict):\n"
                "            out.update(flatten(v, key))\n"
                "        else:\n"
                "            out[key] = v\n"
                "    return out\n"
            ),
            "tradeoffs": (
                "Recursive flatten is clear; a stack/queue version avoids "
                "recursion depth limits on pathological nesting."
            ),
        },
    ],
    "ww-2": [
        {
            "title": "Exponential backoff with jitter sketch",
            "code": (
                "import time, random\n\n"
                "def retry(fn, attempts=3, base=0.05):\n"
                "    last = None\n"
                "    for i in range(attempts):\n"
                "        try:\n"
                "            return fn()\n"
                "        except Exception as e:\n"
                "            last = e\n"
                "            time.sleep(base * (2 ** i) + random.random() * base)\n"
                "    raise last\n"
            ),
            "tradeoffs": (
                "Jitter prevents thundering herds. Sleeping in-request is fine "
                "for scripts; in APIs prefer async sleep or a task queue."
            ),
        },
    ],
    "lm-1": [
        {
            "title": "Generator with early stop",
            "code": (
                "def read_lines(path):\n"
                "    with open(path, encoding='utf-8') as f:\n"
                "        for line in f:\n"
                "            yield line.rstrip('\\n')\n"
            ),
            "tradeoffs": (
                "Streaming keeps memory flat. Materializing `list(open(...))` "
                "is simpler but dies on multi-GB logs — the point of this exercise."
            ),
        },
    ],
    "st-1": [
        {
            "title": "Two-sum hash map",
            "code": (
                "def two_sum(nums, target):\n"
                "    seen = {}\n"
                "    for i, x in enumerate(nums):\n"
                "        if target - x in seen:\n"
                "            return [seen[target - x], i]\n"
                "        seen[x] = i\n"
                "    return None\n"
            ),
            "tradeoffs": (
                "O(n) time / O(n) space. Nested loops are O(n²) and usually "
                "fail interview follow-ups on large inputs."
            ),
        },
    ],
}


def solutions_for(exercise_id: str) -> list[dict[str, Any]]:
    return list(COMMUNITY_SOLUTIONS.get(exercise_id, []))

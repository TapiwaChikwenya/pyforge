"""Mentor-mode debriefs — what the check expects, without the full solution."""

from __future__ import annotations

import re
from typing import Any


def build_mentor_debrief(exercise: dict[str, Any]) -> dict[str, Any]:
    """Derive a structured walkthrough from public exercise fields + check asserts."""
    objectives = list(exercise.get("objectives") or [])
    hints = list(exercise.get("hints") or [])
    check = exercise.get("check_code") or ""
    asserts = _extract_assert_messages(check)
    steps = objectives[:4] if objectives else [
        "Re-read the instructions and name the inputs/outputs out loud.",
        "Write the smallest function that type-checks, then satisfy one assert at a time.",
        "Compare your edge cases to the ones mentioned in the instructions.",
    ]
    return {
        "title": "Mentor walkthrough",
        "intro": (
            "You've attempted this a few times — here's a structured debrief. "
            "It explains what the checker looks for without pasting a full solution."
        ),
        "steps": steps,
        "checker_looks_for": asserts[:6] or [
            "A clean exit (all asserts pass) and the printed PASS line."
        ],
        "next_hint": hints[min(len(hints) - 1, 1)] if hints else (
            "Add a print/repr of the intermediate value the first assert uses."
        ),
        "fails_before_unlock": 3,
    }


def _extract_assert_messages(check_code: str) -> list[str]:
    """Pull human-readable assert messages and simple assert expressions."""
    out: list[str] = []
    for raw in check_code.splitlines():
        line = raw.strip()
        if not line.startswith("assert "):
            continue
        # assert cond, "message"
        m = re.match(r"assert\s+.+?,\s*[\"'](.+?)[\"']\s*$", line)
        if m:
            out.append(m.group(1))
            continue
        expr = line[len("assert ") :].strip()
        if len(expr) > 120:
            expr = expr[:117] + "..."
        if expr and "PASS" not in expr:
            out.append(f"Must hold: `{expr}`")
    return out

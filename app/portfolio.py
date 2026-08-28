"""Portfolio README + honor-system completion certificate generators."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from curriculum import PROJECTS, STAGE_LAYOUT


def progress_stats(progress: dict[str, Any]) -> dict[str, Any]:
    exercises = progress.get("exercises") or {}
    milestones = progress.get("milestones") or {}
    total_ex = sum(len(p["exercises"]) for p in PROJECTS)
    total_ms = sum(len(p["milestones"]) for p in PROJECTS)
    done_ex = sum(1 for p in PROJECTS for e in p["exercises"] if exercises.get(e["id"]))
    done_ms = sum(len(milestones.get(p["id"], [])) for p in PROJECTS)
    completed_projects = [
        p for p in PROJECTS
        if all(exercises.get(e["id"]) for e in p["exercises"])
        and len(milestones.get(p["id"], [])) >= len(p["milestones"])
    ]
    return {
        "exercises_done": done_ex,
        "exercises_total": total_ex,
        "milestones_done": done_ms,
        "milestones_total": total_ms,
        "projects_completed": len(completed_projects),
        "projects_total": len(PROJECTS),
        "completed_project_ids": [p["id"] for p in completed_projects],
        "pct": round(100 * (done_ex + done_ms) / max(1, total_ex + total_ms)),
    }


def build_portfolio_markdown(
    progress: dict[str, Any],
    user: dict[str, Any] | None = None,
) -> str:
    stats = progress_stats(progress)
    exercises = progress.get("exercises") or {}
    milestones = progress.get("milestones") or {}
    name = (user or {}).get("login") or (user or {}).get("name") or "DataForged learner"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# {name} — DataForged portfolio",
        "",
        f"Generated {today} from [DataForged](https://github.com/TapiwaChikwenya/data-forged).",
        "",
        "## Summary",
        "",
        f"- Path progress: **{stats['pct']}%**",
        f"- Exercises: **{stats['exercises_done']}/{stats['exercises_total']}**",
        f"- Milestones: **{stats['milestones_done']}/{stats['milestones_total']}**",
        f"- Projects completed: **{stats['projects_completed']}/{stats['projects_total']}**",
        "",
        "> Honor system: hosted exercise passes are browser-verified. Treat this "
        "as a learning portfolio, not a proctored credential.",
        "",
    ]
    for stage in STAGE_LAYOUT:
        lines.append(f"## {stage['title']}")
        lines.append("")
        for pid in stage["project_ids"]:
            p = next(x for x in PROJECTS if x["id"] == pid)
            ex_done = sum(1 for e in p["exercises"] if exercises.get(e["id"]))
            ms_done = len(milestones.get(pid, []))
            status = "done" if ex_done == len(p["exercises"]) and ms_done >= len(p["milestones"]) else "in progress" if ex_done or ms_done else "not started"
            lines.append(
                f"- **{p['num']}. {p['title']}** — {status} "
                f"({ex_done}/{len(p['exercises'])} exercises, "
                f"{ms_done}/{len(p['milestones'])} milestones) — {p['tagline']}"
            )
            if ex_done:
                passed = [e["title"] for e in p["exercises"] if exercises.get(e["id"])]
                lines.append(f"  - Passed: {', '.join(passed)}")
        lines.append("")
    lines.extend([
        "## Stack practiced",
        "",
        "Python, SQL/NoSQL, ETL patterns, Apache Spark, Airflow, and applied AI "
        "exercises depending on how far you progressed.",
        "",
        "## How to reproduce",
        "",
        "```bash",
        "git clone https://github.com/TapiwaChikwenya/data-forged.git",
        "cd dataforged && docker compose up -d --build",
        "# open http://localhost:8000",
        "```",
        "",
    ])
    return "\n".join(lines)


def build_certificate_html(
    progress: dict[str, Any],
    user: dict[str, Any] | None = None,
) -> str:
    stats = progress_stats(progress)
    name = (user or {}).get("name") or (user or {}).get("login") or "DataForged Learner"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>DataForged certificate</title>
<style>
body{{font-family:Georgia,serif;background:#0b0f17;color:#e7edf7;margin:0;padding:40px}}
.card{{max-width:720px;margin:0 auto;border:2px solid #38bdf8;padding:48px;text-align:center}}
h1{{font-size:28px;letter-spacing:.04em;margin:0 0 8px}}
.sub{{color:#8b9bb4;margin-bottom:28px}}
.name{{font-size:36px;color:#f97316;margin:18px 0}}
.meta{{color:#8b9bb4;font-size:14px;line-height:1.7}}
.note{{margin-top:28px;font-size:12px;color:#6b7c94;border-top:1px solid #223049;padding-top:14px}}
</style></head><body>
<div class="card">
  <h1>CERTIFICATE OF COMPLETION</h1>
  <div class="sub">DataForged — Python → Data Engineering → AI</div>
  <div>This acknowledges that</div>
  <div class="name">{name}</div>
  <div class="meta">
    has reached <b>{stats['pct']}%</b> of the learning path<br>
    ({stats['exercises_done']} exercises · {stats['projects_completed']} projects completed)<br>
    Issued {today}
  </div>
  <div class="note">
    Honor system / not proctored. Hosted passes are browser-verified.
    Do not present this as an accredited credential.
  </div>
</div>
</body></html>"""

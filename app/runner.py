"""
Sandboxed exercise runner (local mode only).

The user's code and the exercise's check code are combined into one script
and executed in a separate python subprocess with:
  - a hard timeout (longer for 'heavy' Spark exercises),
  - an output size cap,
  - a temporary working directory (cleaned up afterwards),
  - a scrubbed environment (no secrets, no Docker/AWS credentials),
  - optional OS-level resource limits on POSIX (CPU time, address space, files),
  - no inheritance of the app's working directory.

This is defence-in-depth for a learner's own machine — not a multi-tenant
jail. Learners on the same Docker network can still reach compose services
by design (SQL/Spark exercises need that). Do not expose local-mode ports
to untrusted networks; see RUNBOOK.md §Security.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_OUTPUT_CHARS = 20_000
DEFAULT_TIMEOUT = 15          # seconds, plain-python exercises
HEAVY_TIMEOUT = 180           # seconds, exercises that boot a local Spark

# Env vars never passed into learner code.
_BLOCKED_ENV_PREFIXES = (
    "AWS_", "GITHUB_", "SECRET", "TOKEN", "PASSWORD", "POSTGRES_",
    "DATABASE_URL", "REDIS_", "MONGO", "AIRFLOW__", "PYFORGE_",
)


def _scrubbed_env() -> dict[str, str]:
    """Minimal environment: PATH/HOME/LANG + Java/Spark bits for heavy exercises."""
    keep = {
        "PATH", "HOME", "USER", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TEMP", "TMP",
        "SYSTEMROOT", "COMSPEC",  # Windows
        "JAVA_HOME", "JDK_HOME", "PYSPARK_PYTHON", "PYSPARK_DRIVER_PYTHON",
        "SPARK_HOME", "HADOOP_HOME",
    }
    env: dict[str, str] = {}
    for key, val in os.environ.items():
        upper = key.upper()
        if any(upper.startswith(p) or p in upper for p in _BLOCKED_ENV_PREFIXES):
            continue
        if key in keep or upper.startswith("JAVA") or upper.startswith("SPARK"):
            env[key] = val
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    env.setdefault("PYTHONNOUSERSITE", "1")
    # Discourage accidental network use of credential helpers; does not block sockets.
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _posix_limits() -> None:
    """Tighten CPU/memory/file limits for the child (POSIX only)."""
    try:
        import resource
    except ImportError:
        return
    # ~2 minutes CPU for heavy Spark; wall clock is enforced by subprocess timeout.
    resource.setrlimit(resource.RLIMIT_CPU, (200, 200))
    # ~2 GiB address space — enough for Spark local, blocks accidental huge allocs.
    try:
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    except (ValueError, OSError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    except (ValueError, OSError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    except (ValueError, OSError):
        pass


def run_exercise(user_code: str, check_code: str, heavy: bool = False) -> dict:
    """Run user code + checks; return {passed, output, error, timed_out}."""
    timeout = HEAVY_TIMEOUT if heavy else DEFAULT_TIMEOUT

    script = (
        f"_USER_SOURCE = {user_code!r}\n"
        + user_code
        + "\n\n# ---- exercise checks ----\n"
        + check_code
    )

    with tempfile.TemporaryDirectory(prefix="pyforge-ex-") as tmp:
        script_path = Path(tmp) / "exercise.py"
        script_path.write_text(script, encoding="utf-8")
        run_kwargs: dict = {
            "args": [sys.executable, "-I", str(script_path)],
            "capture_output": True,
            "text": True,
            "timeout": timeout,
            "cwd": tmp,
            "env": _scrubbed_env(),
        }
        # preexec_fn is POSIX-only (unsupported on Windows).
        if os.name == "posix":
            run_kwargs["preexec_fn"] = _posix_limits
        try:
            proc = subprocess.run(**run_kwargs)
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "output": "",
                "error": (
                    f"Timed out after {timeout}s. Infinite loop? "
                    f"(Spark exercises get {HEAVY_TIMEOUT}s.)"
                ),
                "timed_out": True,
            }

    out = (proc.stdout or "")[:MAX_OUTPUT_CHARS]
    err = (proc.stderr or "")[:MAX_OUTPUT_CHARS]
    return {
        "passed": proc.returncode == 0,
        "output": out,
        "error": _friendly_error(err) if proc.returncode != 0 else "",
        "timed_out": False,
    }


def run_scratch(user_code: str, heavy: bool = False) -> dict:
    """Free-form 'just run it' mode: no checks, same sandbox."""
    return run_exercise(user_code, "", heavy=heavy)


def _friendly_error(stderr: str) -> str:
    """Trim tracebacks to the parts a learner needs (keep the tail)."""
    lines = stderr.strip().splitlines()
    if len(lines) > 25:
        lines = ["... (traceback trimmed) ..."] + lines[-22:]
    return "\n".join(lines)

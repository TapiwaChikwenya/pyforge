"""Local runner env is default-deny and does not inherit the host home."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from runner import run_exercise, sandbox_env  # noqa: E402


def test_sandbox_env_hides_host_home_and_secrets(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", "/home/student")
    monkeypatch.setenv("USERPROFILE", r"C:\Users\student")
    monkeypatch.setenv("USER", "student")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret-value")
    monkeypatch.setenv("MY_CUSTOM_VAR", "nope")
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SPARK_HOME", "/opt/spark")
    env = sandbox_env(str(tmp_path))
    assert env["HOME"] == str(tmp_path)
    assert env["USERPROFILE"] == str(tmp_path)
    assert env["TMPDIR"] == str(tmp_path)
    assert env["USER"] == "learner"
    assert env["PATH"] == "/usr/bin"
    assert env["SPARK_HOME"] == "/opt/spark"
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "MY_CUSTOM_VAR" not in env
    assert all("secret-value" not in value for value in env.values())
    assert all("/home/student" not in value for value in env.values())


def test_run_exercise_home_is_the_work_directory(monkeypatch):
    monkeypatch.setenv("HOME", "/home/student")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret-value")
    result = run_exercise(
        "import os\nprint(os.environ.get('HOME', ''))\nprint(os.environ.get('AWS_SECRET_ACCESS_KEY', ''))\n",
        "",
    )
    assert result["passed"] is True
    lines = result["output"].splitlines()
    assert lines[0]
    assert lines[0] != "/home/student"
    assert "pyforge-ex-" in lines[0]
    assert "secret-value" not in result["output"]
    assert lines[1] == ""

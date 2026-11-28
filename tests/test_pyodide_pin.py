"""The hosted runtime must be the build the exercise harness actually ran."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = "https://cdn.jsdelivr.net/pyodide/v314.0.3/full/"

PINNED_FILES = (
    "app/config.py",
    "docker-compose.hosted.yml",
    ".env.hosted.example",
    ".env.hosted.local.example",
    "infra/terraform/variables.tf",
    "infra/terraform/terraform.tfvars.example",
)


def test_default_pyodide_url_is_the_harness_pin():
    for rel in PINNED_FILES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert PIN in text, rel
        assert "v0.28.3" not in text, rel

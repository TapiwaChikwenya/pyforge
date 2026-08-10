# PyForge

Project-based learning platform: **Python → algorithms → SQL/NoSQL → ETL → Spark → Airflow → AI**.

34 projects · 10 stages · 85 exercises. Dual runtime:

| Mode | Who | Code execution | Progress |
|------|-----|----------------|----------|
| **local** (default) | you, on your machine | sandboxed server subprocess | JSON file |
| **hosted** | public site | browser via [Pyodide](https://pyodide.org) — server never runs learner code | Postgres (signed-in) / `localStorage` (anonymous) |

## Quick start (local)

```bash
docker compose up -d --build
# open http://localhost:8000
```

Optional profiles (see the Environment tab in each project):

```bash
docker compose --profile db up -d
docker compose --profile db --profile spark up -d
docker compose --profile db --profile spark --profile airflow up -d
```

## Docs

| Doc | When to read it |
|-----|-----------------|
| [RUNBOOK.md](RUNBOOK.md) | Day-to-day local stack, credentials, learning path, troubleshooting |
| [DEPLOY.md](DEPLOY.md) | Hosted deploy (Compose + Caddy), security model, checklists |
| [AWS.md](AWS.md) | AWS / ALB notes |
| [TESTING.md](TESTING.md) | Manual + automated test rehearsal |
| [docs/ENGINEERING.md](docs/ENGINEERING.md) | Security, migrations, rate limits, backups |
| [docs/LEARNING_FEATURES.md](docs/LEARNING_FEATURES.md) | Onboarding, mentor, review, portfolio, analytics |
| [infra/terraform/README.md](infra/terraform/README.md) | **AWS deploy** after Route 53 domain (near one-click) |

## Develop / test

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r app/requirements-hosted.txt
pip install pytest httpx
pip install -r app/requirements.txt   # only if you need the local exercise runner

pytest tests/test_app.py -q
python tests/test_exercises.py --skip-heavy
```

CI (GitHub Actions) runs unit tests, the exercise harness (skipping heavy Spark),
a hosted smoke check (`/api/run` must 404), and Terraform validate.

## Hosted progress trust

In hosted mode, exercise passes are **browser-verified** (honor system). The
server validates known exercise IDs and requires sign-in for cross-device
storage; it does **not** re-execute checks. Do not use checkmarks as
certificates or leaderboard proof without a separate proctoring layer.
Details: [DEPLOY.md](DEPLOY.md).

## License

MIT — see [LICENSE](LICENSE).

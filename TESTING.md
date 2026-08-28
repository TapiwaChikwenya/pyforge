# Testing DataForged locally before you deploy

Two rehearsals, in this order:

- **Part A — local mode.** The learning stack as your users will run it:
  34 projects, server-side exercise execution, databases, Spark, Airflow.
- **Part B — hosted mode, on your laptop.** The *production* stack (browser
  execution, GitHub sign-in, Postgres progress) pointed at localhost, so you
  find problems here instead of on a live domain.
- **Part C — the AWS plan**, without creating anything.

Budget about 40 minutes for A and B the first time, most of it waiting for
images to build.

---

## Automated checks (fast)

```bash
pip install -r app/requirements-hosted.txt pytest httpx
pytest tests/test_app.py -q
# frontend selector contract (no app import, runs in ~0.1s):
pytest tests/test_frontend_assets.py -q
# full exercise solvability (skip JVM Spark in CI):
pip install -r app/requirements.txt   # local deps
python tests/test_exercises.py --skip-heavy
```

GitHub Actions runs the same suite on every push/PR (see `.github/workflows/ci.yml`).

---

## Part A — local mode

### A1. Prerequisites

```bash
docker --version && docker compose version    # Compose must be v2.x
docker info | grep -i "total memory"          # 8 GB+ for the full stack
```

Ports that must be free: **8000, 8888** now; **5432, 27017, 6379** in A4;
**8080, 7077** in A5; **8085** in A6. Check one quickly with
`lsof -i :8000` (macOS/Linux) or `netstat -ano | findstr :8000` (Windows).

### A2. Start the base stack

```bash
cd dataforged
docker compose up -d --build
docker compose ps          # app + jupyter, both "running"
```

First build is 10–20 minutes (two images, ~7 GB pulled). Afterwards, seconds.

If it fails, the usual culprit is a port clash or Docker running out of disk —
`docker system prune -a` frees a lot.

### A3. Check the app

```bash
curl -s localhost:8000/healthz
# {"ok":true,"mode":"local","projects":34}
```

Then open **http://localhost:8000** and confirm, in order:

1. **Dashboard**: 10 stage headings, 34 project cards, "0% of the path".
2. **Open Structly → Exercises**: refresher, objectives, task, code editor.
   Check the editor's layout: the **first character of every line is fully
   visible** (not tucked behind the line numbers), and the numbers sit in one
   straight column. Then **click a second exercise's title to expand it** and
   check the same thing — editors are built when an exercise opens, so this is
   the case worth eyeballing.
3. **Break something on purpose**: type `def two_sum(` and pause — a red marker
   should appear in the editor gutter (that's the live linter).
4. **Solve it**: paste the one-pass solution, click **Run & Check** → green
   PASS, the dot beside the exercise title turns green, header % ticks up.
5. **Fail it**: change the return to `[0, 0]`, run again → red, with the
   assertion message. Checks that actually check are the whole point.
6. **Hints**: click 💡 three times — one hint each, then the button disables.
7. **Interview Q&A tab**: three questions, answers hidden until you click.
8. **Milestones tab**: tick one, it strikes through.

### A4. Databases (Stage 3, 4, 6, 9 projects)

```bash
docker compose --profile db up -d
sleep 25                                  # first start seeds the databases

docker compose exec warehouse psql -U dataforged -d warehouse \
  -c "SELECT count(*) FROM orders;"       # 5000
docker compose exec warehouse psql -U dataforged -d warehouse \
  -c "SELECT extname FROM pg_extension WHERE extname='vector';"   # vector
docker compose exec mongo mongosh appdata --quiet \
  --eval "db.reviews.countDocuments()"    # 800
docker compose exec redis redis-cli ping  # PONG
```

If a count comes back 0, the volume already existed from an earlier run and the
seed was skipped — see "Re-seeding a database" in RUNBOOK §4.

### A5. Spark (Stage 7)

```bash
docker compose --profile db --profile spark up -d
```

- **http://localhost:8080** — Spark master UI, 2 workers ALIVE.
- **http://localhost:8888** — JupyterLab. Open
  `notebooks/00_connect_to_spark.ipynb` and run both cells; the second prints a
  partition count and an average. Your notebook then appears as a running
  application in the Spark UI.
- **In the app**: First Spark → Exercises → **fs-3**. It has a normal Run
  button here (the local image ships a JVM). Paste the groupBy solution and
  run — allow ~35 seconds for the JVM to start. This is the exercise that
  can't run in a browser, so confirm it works locally.

### A6. Airflow (Stages 8, 10)

```bash
docker compose --profile db --profile spark --profile airflow up -d
docker compose logs -f airflow | grep -m1 "Listening at"    # ~90s on first boot
```

**http://localhost:8085**, login `admin` / `admin`. `example_taxi_dag` should be
listed. Unpause it, trigger a run, and watch the graph — `generate` and
`validate` should go green. (`transform_with_spark` needs the workspace paths,
which is the project's own milestone work.)

### A7. Progress survives a restart

```bash
docker compose restart app
curl -s localhost:8000/api/progress        # your ticks are still there
```

Progress lives in the `app-data` volume, not the container.

### A8. Stop (keeping everything)

```bash
docker compose --profile db --profile spark --profile airflow down
```

---

## Part B — hosted mode, on your laptop

This is the production configuration. Everything changes: Python runs in *your
browser*, the server exposes no execution endpoint, and progress goes to
Postgres per user.

### B1. Configure

```bash
cp .env.hosted.local.example .env.hosted.local
```

The values are already right for localhost — plain HTTP, no certificate,
`COOKIE_SECURE=false` (browsers silently drop `Secure` cookies over http, which
would make sign-in fail with no error message).

### B2. Start it

```bash
docker compose -f docker-compose.hosted.yml --env-file .env.hosted.local up -d --build
docker compose -f docker-compose.hosted.yml ps     # web, db, caddy
```

Port 80 must be free. This stack is independent of Part A's — different ports,
different containers — so both can run at once.

### B3. The security check that matters

```bash
curl -s localhost/healthz
# {"ok":true,"mode":"hosted","projects":34}     <- note "hosted"

curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost/api/run \
  -H 'Content-Type: application/json' -d '{"code":"import os"}'
# 404

curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost/api/lint \
  -H 'Content-Type: application/json' -d '{"code":"x="}'
# 404
```

Two 404s mean the public deployment has no endpoint that executes — or even
parses — submitted code. If either returns 200, you are running local mode and
must not deploy it.

### B4. Browser checks

Open **http://localhost**:

1. A blue banner: *"Your Python runs in this browser…"*.
   **No Sign in button yet** — that is expected. `.env.hosted.local.example`
   ships with the GitHub credentials empty, so the banner ends with *"GitHub
   sign-in is not configured on this deployment"*. The button appears once you
   do step B5. (In Part A you won't see a banner at all, just a small
   **local mode** chip in the header — local mode is single-user by design and
   has nothing to sign in to.)
2. Open Structly → Exercises. A "Starting the Python runtime" message appears
   while Pyodide downloads (~10 MB, once — needs internet).
3. Solve `two_sum` and run it. Green PASS, exactly as in Part A — but this time
   nothing was sent to the server. Confirm in DevTools → Network: no request on
   click.
4. **Reload the page.** The exercise is still ticked (anonymous progress lives
   in your browser).
5. Open **First Spark → Exercises → fs-3**: no Run button, and an amber notice
   explaining it needs the local stack. That's the intended behaviour for the 2
   of 85 exercises needing a JVM.
6. Try a package-heavy one: Pandas PowerPlant → **pp-2**. First run shows
   "Loading Python packages…" while pandas downloads, then passes.

### B5. Optional — rehearse GitHub sign-in

Worth doing, since the callback URL is the most common production mistake.

1. Create a **second, throwaway** OAuth app (github.com → Settings → Developer
   settings → OAuth Apps):
   - Homepage URL: `http://localhost`
   - Authorization callback URL: `http://localhost/auth/callback`
2. Put the id and secret into `.env.hosted.local`, then:
   ```bash
   docker compose -f docker-compose.hosted.yml --env-file .env.hosted.local up -d
   ```
3. Click **Sign in** → GitHub → back to the app with your avatar in the header.
4. Confirm the merge worked: the exercise you passed anonymously in B4 is still
   ticked, and is now on your account:
   ```bash
   curl -s localhost/api/progress -b "dataforged_session=<cookie from DevTools>"
   ```
   Simpler check: open a private window, sign in there, and see the same
   progress — that's the cross-device promise.

### B6. Clean up before production

```bash
docker compose -f docker-compose.hosted.yml --env-file .env.hosted.local down -v
```

`-v` deletes the test database. Do it — you don't want dry-run accounts in a
volume you might reuse. Delete the throwaway OAuth app too.

---

## Part C — check the AWS plan without creating anything

```bash
cd infra/terraform

pip install python-hcl2 && python3 lint.py    # references + template contract
terraform init
terraform validate                            # provider schemas
terraform fmt -check                          # formatting

cp terraform.tfvars.example terraform.tfvars  # fill in domain_name, repo_url
terraform plan                                # creates nothing
```

`plan` needs AWS credentials and a Route 53 hosted zone for your domain. Read
it before applying — expect ~30 resources created, 0 destroyed. If it says it
will *destroy* anything on a first run, stop and find out why.

---

## Go / no-go before deploying

- [ ] A3: exercise passes, wrong answer fails, linter marks bad syntax
- [ ] A4: warehouse 5000 orders, mongo 800 reviews, redis PONG
- [ ] A5: Spark UI shows 2 workers; **fs-3 runs in-app locally**
- [ ] A6: Airflow UI loads and `example_taxi_dag` runs
- [ ] A7: progress survives `docker compose restart app`
- [ ] B3: `/healthz` says **hosted**, `/api/run` and `/api/lint` both **404**
- [ ] B4: an exercise runs in the browser and survives a page reload
- [ ] B4: fs-3 shows the local-only notice instead of a Run button
- [ ] B5 (if tested): the Sign in button appears once credentials are set, sign-in
      works, and anonymous progress merged into the account
- [ ] B6: dry-run stack destroyed with `-v`, throwaway OAuth app deleted
- [ ] C: `terraform validate` clean and `plan` shows only creates

---

## If something misbehaves

| Symptom | Look here |
|---|---|
| Build fails on first `up` | Disk space (`docker system prune -a`), then the jupyter JDBC warning in RUNBOOK §6 — it's non-fatal by design |
| App up but browser shows nothing | `docker compose logs app`; hard-reload to bypass a cached page |
| Exercise hangs in hosted mode | Pyodide needs internet for the CDN; check DevTools → Network for a blocked `cdn.jsdelivr.net` |
| **No GitHub Sign in button** | Check the mode first: `curl -s localhost:8000/api/me` (local stack) or `curl -s localhost/api/me` (hosted). Local mode never has one. In hosted mode `auth_enabled:false` means either the GitHub credentials are empty or there's no database — the banner says which |
| Sign-in bounces back signed out | `COOKIE_SECURE` must be `false` over http, and `BASE_URL` must match the callback URL exactly |
| Database counts are 0 | Volume pre-existed, so seeds were skipped — RUNBOOK §4, "Re-seeding a database" |
| Port already allocated | Change the **left** side of the mapping in the compose file |

Full troubleshooting tables: **RUNBOOK.md §6** (local) and **DEPLOY.md §8**
(hosted).

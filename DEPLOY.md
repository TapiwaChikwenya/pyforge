# Deploying DataForged publicly

How to put DataForged on the internet so other developers can use it — safely.

---

## 1. What changes when you host it

DataForged runs in one of two modes, chosen by the `DATAFORGED_MODE` environment
variable. The local Docker stack you already have is unaffected.

| | `local` (default) | `hosted` |
|---|---|---|
| Where exercises run | server-side sandboxed subprocess | **the visitor's browser** (Pyodide) |
| Code-execution endpoints | `/api/run`, `/api/scratch`, `/api/lint` | **not registered at all** |
| Sign-in | none | GitHub OAuth (optional) |
| Progress | one JSON file | per user in Postgres; anonymous visitors use browser storage |
| Databases, Spark, Airflow | part of the stack | not deployed — learners run those locally |
| Anonymous access | n/a | `ALLOW_ANONYMOUS` (default true). Set false to require GitHub sign-in |

The security-relevant line: **in hosted mode the server has no endpoint that
executes, or even parses, submitted code.** Learner Python is compiled to
WebAssembly and runs inside the browser's sandbox on the visitor's own machine.
A malicious visitor can only attack their own tab.

### Progress is an honor system (hosted)

`POST /api/progress/exercise` accepts a browser-verified pass for a **known**
exercise id after sign-in. The server does **not** re-run the check (there is
no code-execution path). Merge payloads are sanitized to known exercise and
milestone keys only. Treat checkmarks as personal learning state — not as
certificates, exam grades, or leaderboard proof. The API surfaces
`progress_honor_system: true` so clients can display that clearly.

83 of the 85 exercises run in the browser. The two that start a real JVM Spark
session (`fs-3`, `ss-3`) can't — the app shows a note pointing at the local
stack, and the concepts are covered by the pure-Python exercises beside them.
Details and the test evidence: `tests/PYODIDE_COMPAT.md`.

---

## 2. Rehearse it locally first

Run the hosted stack on your own machine before pointing a domain at it —
`.env.hosted.local.example` is pre-configured for localhost. Steps and the
checks that matter (including proving `/api/run` returns 404) are in
**TESTING.md**, Part B.

---

## 3. Create the GitHub OAuth app (5 minutes)

Sign-in is optional — without it the site works and progress stays in each
visitor's browser. With it, progress follows them across devices.

1. GitHub → Settings → Developer settings → **OAuth Apps** → *New OAuth App*
2. Fill in:
   - **Application name**: DataForged
   - **Homepage URL**: `https://dataforged.example.com`
   - **Authorization callback URL**: `https://dataforged.example.com/auth/callback`
     (must match `BASE_URL` exactly, including scheme — this is the single most
     common setup mistake)
3. Generate a client secret, then put the client id and secret in `.env.hosted`.

The app requests the `read:user` scope only — public profile, nothing else. No
repository access, no email scope.

---

## 4. Deploy on a VPS (the simple path)

Any small box works: 1 vCPU / 1 GB RAM is genuinely enough, because the server
only serves JSON and static files. Roughly $5–7/month.

```bash
# on the server, with Docker installed and DNS A record pointing here
git clone <your repo> dataforged && cd dataforged

cp .env.hosted.example .env.hosted
nano .env.hosted                        # set SITE_ADDRESS, BASE_URL, secrets

# generate strong values
openssl rand -hex 32                    # -> SECRET_KEY
openssl rand -hex 24                    # -> POSTGRES_PASSWORD

docker compose -f docker-compose.hosted.yml --env-file .env.hosted up -d --build
docker compose -f docker-compose.hosted.yml logs -f web
```

Caddy obtains a TLS certificate automatically on first request, so ports 80 and
443 must be open and DNS must already resolve to the box. Then open your
domain — you should see the curriculum, a "Sign in" button, and a banner
explaining that Python runs in the browser.

Health check: `curl https://your-domain/healthz` → `{"ok":true,"mode":"hosted","db":"ok",...}`
(`/healthz` returns **503** when Postgres is unreachable — use it for load-balancer readiness.)

### Updating

```bash
git pull
docker compose -f docker-compose.hosted.yml --env-file .env.hosted up -d --build web
```

Progress lives in the `dataforged-db` volume and survives rebuilds.

### Backups

Automated daily dumps (Terraform EC2 installs a cron): `scripts/backup_postgres.sh`.
Manual:

```bash
./scripts/backup_postgres.sh
# or:
docker compose -f docker-compose.hosted.yml --env-file .env.hosted exec -T db \
  pg_dump -U dataforged dataforged | gzip > dataforged-$(date +%F).sql.gz
```

Set `S3_BACKUP_URI=s3://your-bucket/dataforged/db/` to also upload.

---

## 5. Deploy on AWS

See **AWS.md** — instance sizing (Graviton works), secrets in SSM, the
EC2-and-Compose path, when to move to ECS Fargate + RDS + ALB, costs, and
what happens to the Spark projects.

---

## 6. Deploy on a PaaS (Fly.io, Render, Railway…)

The app is a single stateless container plus a managed Postgres, so any PaaS
works. Point the build at `app/Dockerfile.hosted` and set these environment
variables:

```
DATAFORGED_MODE=hosted
BASE_URL=https://your-app.fly.dev
SECRET_KEY=<openssl rand -hex 32>
DATABASE_URL=<the managed Postgres connection string>
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
COOKIE_SECURE=true
```

Skip Caddy — the platform terminates TLS for you. Two notes: keep
`--proxy-headers` (already in the Dockerfile's CMD) so redirects use the right
scheme, and make sure the OAuth callback URL matches whatever hostname the
platform gives you.

---

## 7. Costs and scaling

Because Python runs client-side, per-user server cost is close to zero — a page
load is a few JSON responses. The realistic bill is the box plus bandwidth:
each new visitor downloads ~10 MB of Pyodide runtime from the CDN (not from
you), plus your ~1 MB of app assets. A 1 GB VPS comfortably serves thousands of
learners a day.

The database grows by a handful of rows per learner. Postgres will not be your
bottleneck.

---

## 8. Optional: self-host the Python runtime

By default browsers fetch Pyodide from jsDelivr. To avoid the third-party
dependency (or serve users behind a strict firewall), host it yourself:

1. Download the **full** distribution for the pinned version from the Pyodide
   releases (the file named `pyodide-<version>.tar.bz2` — the npm package alone
   does *not* include the package wheels).
2. Extract it to `app/static/pyodide/`.
3. Set `PYODIDE_INDEX_URL=/static/pyodide/` in `.env.hosted`.
4. Drop `https://cdn.jsdelivr.net` from the `Content-Security-Policy` in
   `Caddyfile`.

Expect ~200 MB on disk for the full set of wheels; browsers only download what
each exercise imports.

To pin a different Pyodide version, change `PYODIDE_INDEX_URL` — no code
changes. Verified against Pyodide 0.28.x / Python 3.14 (see
`tests/PYODIDE_COMPAT.md`).

---

## 9. Pre-flight checklist

- [ ] `SECRET_KEY` set to 32 random bytes (not the example value)
- [ ] `POSTGRES_PASSWORD` changed
- [ ] `BASE_URL` and the GitHub callback URL match exactly, both `https://`
- [ ] `COOKIE_SECURE=true`
- [ ] `.env.hosted` is git-ignored
- [ ] `docker compose -f docker-compose.hosted.yml ps` shows all three healthy
- [ ] `curl https://your-domain/api/run -X POST -d '{}'` returns **404**
      (proof that no execution endpoint exists in hosted mode)
- [ ] Postgres port is not published to the host (it isn't, in the compose file)
- [ ] Backups scheduled if you care about learner progress

---

## 10. What you are NOT hosting

The local Docker stack — JupyterLab, the Postgres warehouse, MongoDB, Redis,
the Spark cluster, Airflow — is intentionally not part of the public
deployment. Ten learners cannot meaningfully share one Airflow instance or one
warehouse; they would overwrite each other's DAGs and tables. Those services
are per-learner by nature, so the hosted site teaches the material and runs the
exercises, and each developer clones the repo to run the full platform on their
own machine. Each project's **Environment** tab shows the exact command.

If you ever do want per-user cloud environments, that's a different product:
per-user containers (JupyterHub-style), per-user database schemas, quotas and
idle reaping. Start here first — most learners are happy running the heavy
stack locally.

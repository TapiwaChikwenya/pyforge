# Engineering features

Operational and security hardening for the PyForge app and deploy path.

## Purpose

Keep the learning product reliable in CI, safer in local mode, and operable
when hosted publicly — without changing the curriculum pedagogy.

## Scope

- App process: FastAPI (`app/main.py`), auth, store, runner, rate limit
- Frontend static assets (`app/static/`)
- CI (`.github/workflows/ci.yml`), Dependabot
- Hosted backups (`scripts/backup_postgres.sh`)
- Terraform remote state + bootstrap cron

## Inputs / outputs

| Input | Output |
|-------|--------|
| `PYFORGE_MODE`, env secrets | Mode-gated API surface |
| Learner code (local only) | Pass/fail from sandboxed subprocess |
| Browser progress posts (hosted) | Whitelisted rows in Postgres |
| `/healthz` probes | 200 ready / 503 DB down (hosted) |

## Dependencies

FastAPI, uvicorn, pydantic; hosted adds psycopg2, itsdangerous, httpx.
Local exercise runner adds the scientific stack in `app/requirements.txt`.

## Functional flow

```mermaid
flowchart LR
  Client --> MW[middleware: request-id / anon gate / rate limit]
  MW --> API[FastAPI routes]
  API -->|local| Runner[scrubbed subprocess]
  API -->|hosted progress| Keys[progress_keys whitelist]
  Keys --> PG[(Postgres + migrations)]
  API --> Health["/healthz ping"]
  Health --> PG
```

## Failure paths

| Failure | Behaviour |
|---------|-----------|
| Rate limit exceeded | 429 `slow down` |
| Unknown exercise/milestone on write/merge | dropped or 404 |
| OAuth state replay | 400 after nonce consume |
| Postgres down (hosted) | `/healthz` → 503 |
| Corrupt local JSON progress | start fresh + warning log |

## Security considerations

- Hosted: no `/api/run`; progress is honor-system (see DEPLOY.md)
- `ALLOW_ANONYMOUS=false` forces GitHub sign-in for UI/API
- Local runner: env scrub, isolated cwd, POSIX rlimits — residual Docker-network access is intentional
- CSP baseline set in app middleware; Caddy may tighten further

## Performance considerations

- Hosted compute is on the client (Pyodide)
- Anonymous `/api/curriculum` gets short `Cache-Control`
- SQLite rate-limit DB shared across uvicorn workers on one host

## Frontend styling invariant: markdown code blocks vs. the editor

`app/static/app.css` styles markdown `<pre>` / `<code>` through an **explicit
list of prose containers**, never through `.ex-body`. Both halves of that rule
matter, and each has already caused a regression on its own:

- **Why not `.ex-body pre`.** CodeMirror renders every line of the editor as a
  `<pre>` inside `.ex-body`. A container-wide selector therefore styles the
  editor's internals; it only *looks* correct while CodeMirror's own stylesheet
  wins on specificity, which stops being true the moment that CDN file is slow,
  blocked, or version-bumped. `.CodeMirror pre.CodeMirror-line` keeps a
  defensive reset for that case.
- **Why the list must stay complete.** Community solutions render
  `<pre><code>` inside `.sol-card`, which also lives inside `.ex-body`.
  Narrowing the selectors without adding `.sol-card` left unlocked solutions as
  unstyled plain text after a learner passed an exercise.

```mermaid
flowchart TD
  ExBody[".ex-body (exercise container)"] --> Lesson[".lesson-body / .instructions / .refresher-body"]
  ExBody --> Editor["CodeMirror — every line is a &lt;pre&gt;"]
  ExBody --> Local[".local-only"]
  ExBody --> Sol[".sol-card (community solutions)"]
  Lesson --> Styled["scoped markdown pre/code rules"]
  Local --> Styled
  Sol --> Styled
  Editor --> Reset[".CodeMirror pre.CodeMirror-line reset"]
```

Adding any new container that renders markdown or a code snippet means adding
it to those three selector groups. `tests/test_frontend_assets.py` parses the
stylesheet and fails if a listed container is missing, if a bare
`.ex-body pre|code` selector reappears, or if the solutions markup stops
emitting `<pre><code>` inside `.sol-card`.

## Troubleshooting

| Symptom | Look at |
|---------|---------|
| 503 on `/healthz` | Postgres connectivity / `DATABASE_URL` |
| Everyone signed out | `SECRET_KEY` changed / missing |
| 401 on every API call | `ALLOW_ANONYMOUS=false` without a session |
| 429 under ALB | `TRUST_PROXY=true` so limits key on real client IP |
| Backup cron silent | `/var/log/pyforge-backup.log` on the EC2 host |
| Code snippet renders as plain text in the UI | Its container is missing from the scoped `pre` / `code` selector groups in `app.css` — run `pytest tests/test_frontend_assets.py` |
| Editor lines get boxes/padding | A broad `.ex-body pre` style crept back in; the same test catches it |

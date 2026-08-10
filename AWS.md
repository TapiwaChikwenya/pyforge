# Hosting PyForge on AWS

Companion to `DEPLOY.md`, with the AWS-specific decisions — and an honest
answer to the question everyone asks first: **what happens to the Spark
projects?**

---

## 1. What actually runs on AWS

Only two things: the app container and a Postgres database.

```
                    ┌──────────────────────────────────────────┐
  learner's         │  AWS                                     │
  browser  ────────▶│  ┌────────────┐      ┌────────────────┐  │
   │                │  │ PyForge    │─────▶│ Postgres       │  │
   │                │  │ (FastAPI)  │      │ (user progress)│  │
   │                │  └────────────┘      └────────────────┘  │
   │                │   serves JSON + static files.            │
   │                │   NEVER executes learner code.           │
   │                └──────────────────────────────────────────┘
   │
   ├──▶ jsDelivr CDN  (Pyodide runtime — not your bandwidth)
   │
   └──▶ Python runs HERE, in the browser's WebAssembly sandbox
```

The app is stateless: no learner code, no sessions in memory (the session is a
signed cookie), no local files that matter. That makes every AWS decision
easier — you can restart it, scale it horizontally, or replace it without
draining anything.

What is **not** on AWS: JupyterLab, the Spark cluster, Airflow, MongoDB, Redis,
and the warehouse. Those are the local learning stack. Read on.

---

## 2. The Spark projects (the important part)

Stage 7 has three Spark projects with two kinds of work, and they land in
different places.

**In-browser exercises — hosted on AWS, work for everyone.** `fs-1` (build
map/shuffle/reduce), `fs-2` (build lazy evaluation), `ss-1` (hash partitioning
and skew), `ss-2` (broadcast join) are pure Python by design: they teach
Spark's execution model by having the learner *implement* it. They run in the
browser like every other exercise. No cluster, no JVM, no cost to you.

**Two exercises that need a real JVM.** `fs-3` (a real PySpark session) and
`ss-3` (reading a Catalyst physical plan) start an actual Spark runtime. There
is no JVM in WebAssembly, so the hosted app shows a notice pointing at the
local stack, where they run in-app with a normal Run button. That's 2 of 85.

**The cluster milestones — always local.** The real learning in Stage 7 is the
milestone work: running jobs against a 2-worker cluster, watching stages and
shuffles in the Spark UI, deliberately causing skew, tuning
`spark.sql.shuffle.partitions`. Each learner does this on their own machine
with `docker compose --profile db --profile spark up -d`.

### Why not put Spark on AWS?

Three reasons, in order of how much they'll hurt:

**Isolation.** Spark is stateful per session. Two learners on one cluster
compete for executors, overwrite each other's `/workspace` files, and see each
other's jobs in the UI. The skew exercise — where one task deliberately runs
for minutes — becomes a denial of service for everyone else. A shared cluster
isn't a smaller version of the real thing; it's a broken version.

**Cost shape.** A cluster that's up 24/7 for occasional learners is the worst
possible spend pattern. EMR, EKS or even a couple of EC2 workers cost real
money per month whether anyone is learning or not, and the alternative
(spin-up-on-demand per learner) means 3–5 minutes of waiting before an exercise
and a scheduler you now have to operate.

**It teaches less.** Part of Stage 7 is learning that a Spark cluster is a
thing you *run* — with a master, workers, memory settings and a UI you have to
find your way around. Handing someone a pre-warmed cluster removes exactly the
operational muscle the projects are building. Running it locally with
`docker compose` is closer to what they'll do at work than clicking into a
managed console.

### If you decide you want cloud Spark anyway

Realistic options, roughly in order of sanity:

| Approach | How it works | Honest assessment |
|---|---|---|
| **Nothing (recommended)** | Learners run the cluster locally | Free, isolated, better pedagogy |
| **Per-learner EC2** | Each learner launches their own instance from an AMI with the stack baked in | Works, real isolation; you're now handing out AWS credentials and paying per learner-hour |
| **EMR Serverless** | Submit jobs to a managed Spark; no cluster to run | Good for *submitting* jobs, wrong for the exercises — there's no Spark UI to explore, no workers to watch, and per-learner IAM is fiddly |
| **Per-user containers on ECS/EKS** | JupyterHub-style: one isolated environment each, idle-reaped | This is a product, not a deployment. Weeks of work, and a bill that scales with signups |

If you go per-learner, the honest budget question is: is this cheaper than the
zero dollars it costs when they run Docker on their own laptop? Almost
certainly not — and the laptop version has no queue.

---

## 3. Recommended: one EC2 instance + Docker Compose

The architecture you already have, on a box. Start here.

> **There is Terraform for exactly this** in `infra/terraform/` — VPC, instance,
> Elastic IP, Route 53 record, SSM secrets, IAM role and a budget alarm, about
> 30 resources. Fill in one file (`terraform.tfvars`) and `terraform apply`.
> The manual steps below are what it automates, kept here so you know what it
> is doing. See `infra/terraform/README.md`.

**Instance:** `t4g.small` (2 vCPU, 2 GiB, Graviton/ARM). Every compiled
dependency in the hosted image publishes `aarch64` wheels — psycopg2-binary,
pydantic-core, uvloop, httptools, watchfiles — so ARM builds cleanly and costs
about 20% less than the x86 equivalent. `t4g.micro` also works for a small
audience.

```bash
# 1. Launch: Amazon Linux 2023 (arm64), 20 GB gp3, in a public subnet
#    Security group inbound:  80/tcp and 443/tcp from 0.0.0.0/0, 22 from your IP only
#    Attach an Elastic IP, point your Route 53 A record at it

# 2. On the instance
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user && newgrp docker
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-aarch64 \
  -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# 3. Deploy
git clone <your repo> pyforge && cd pyforge
cp .env.hosted.example .env.hosted
nano .env.hosted            # SITE_ADDRESS, BASE_URL, secrets (see below)
docker compose -f docker-compose.hosted.yml --env-file .env.hosted up -d --build
```

Caddy requests the TLS certificate automatically on first hit, so DNS must
already resolve and port 80 must be reachable.

**Secrets.** Don't leave them in a file if you can avoid it — put them in SSM
Parameter Store (free for standard parameters) and pull at boot:

```bash
aws ssm put-parameter --name /pyforge/SECRET_KEY --type SecureString --value "$(openssl rand -hex 32)"
aws ssm put-parameter --name /pyforge/POSTGRES_PASSWORD --type SecureString --value "$(openssl rand -hex 24)"
aws ssm put-parameter --name /pyforge/GITHUB_CLIENT_SECRET --type SecureString --value "..."

# in a small start script, with an instance role granting ssm:GetParameter
export SECRET_KEY=$(aws ssm get-parameter --name /pyforge/SECRET_KEY --with-decryption --query Parameter.Value --output text)
```

Give the instance an IAM role (not access keys) with `ssm:GetParameter` and, if
you want shell access without opening port 22 at all, `AmazonSSMManagedInstanceCore`
so you can use Session Manager instead.

**Backups.** The database is a container volume here. Either take nightly EBS
snapshots (Data Lifecycle Manager, a few clicks) or `pg_dump` to S3 on a cron:

```bash
docker compose -f docker-compose.hosted.yml exec -T db pg_dump -U pyforge pyforge \
  | gzip | aws s3 cp - s3://your-bucket/pyforge/$(date +%F).sql.gz
```

---

## 4. When it grows: ECS Fargate + RDS + ALB

Move here when you want zero-downtime deploys, managed backups, or more than
one app instance. The app needs no changes — it's already stateless and already
runs with `--proxy-headers`.

What changes:

- **Drop Caddy.** The ALB terminates TLS with an ACM certificate. Point the
  target group at container port **8000**, health check path **`/healthz`**
  (it returns `{"ok":true,...}` and touches nothing else).
- **Postgres becomes RDS**, `db.t4g.micro` to start, in private subnets, not
  publicly accessible, with automated backups. Set `DATABASE_URL` to its
  endpoint.
- **Secrets** come from Secrets Manager or SSM via the task definition's
  `secrets` block — never in the image or in plain `environment`.
- **Image** goes to ECR. If your Fargate tasks are ARM (`runtimePlatform:
  cpuArchitecture: ARM64`), build accordingly:
  `docker buildx build --platform linux/arm64 -f app/Dockerfile.hosted -t <ecr-url>:latest app --push`
- **Logs** to CloudWatch via the `awslogs` driver.
- **Sticky sessions: not needed.** Auth is a signed cookie, so any task can
  serve any request.

Minimum viable setup: 1 Fargate task (0.25 vCPU / 0.5 GB is genuinely enough),
an ALB, and one RDS instance.

---

## 5. What it costs

Approximate us-east-1 on-demand, mid-2026 — check the AWS calculator for your
region, and note prices change.

| Setup | Components | Rough monthly |
|---|---|---|
| **EC2 + Compose** (recommended start) | t4g.small ~$12, 20 GB gp3 ~$2, Elastic IP, modest egress | **~$16–20** |
| EC2 + RDS | above + db.t4g.micro ~$12 + storage | ~$30–35 |
| ECS Fargate + RDS + ALB | small task, ALB base ~$16–20 + LCUs, RDS ~$12 | ~$50–70 |

Per-learner marginal cost is close to zero: their browser does the compute, and
the ~10 MB Pyodide runtime comes from jsDelivr, not your egress. A `t4g.small`
serving JSON and static files handles thousands of learners a day. Your bill
grows with *uptime*, not signups — which is exactly why adding an always-on
Spark cluster would change the economics completely.

Free-tier note: if the account is new enough to have it, a `t4g.micro` may be
covered for the first year.

---

## 6. AWS-specific gotchas

- **Security group**: 80 and 443 open to the world; 22 restricted to your IP or
  closed entirely in favour of SSM Session Manager. Postgres port never
  published — in the compose file it isn't, and on RDS it should sit in a
  private subnet whose security group only accepts the app's.
- **`COOKIE_SECURE=true`** requires real HTTPS end-to-end. With an ALB, TLS
  terminates there and the app sees plain HTTP — `--proxy-headers` (already in
  the Dockerfile CMD) makes it trust `X-Forwarded-Proto` so OAuth redirects use
  `https://`. Get this wrong and sign-in loops.
- **`BASE_URL` must exactly match** the GitHub OAuth callback URL, including
  scheme and any `www.`. This is the number one setup failure.
- **Health checks**: use `/healthz`, not `/`. The root serves the full HTML.
- **Content-Security-Policy**: the `Caddyfile` allows jsDelivr and PyPI (for
  Pyodide and its packages). If you move behind an ALB you lose Caddy's
  headers — set them at the app or in CloudFront instead, or the browser will
  block the Python runtime.
- **Self-hosting Pyodide on S3 + CloudFront** is a reasonable option if you
  don't want the CDN dependency: upload the full distribution, set
  `PYODIDE_INDEX_URL` to the CloudFront domain, add that domain to the CSP, and
  make sure CORS on the bucket allows your origin. Budget ~200 MB of storage.
- **Region**: put the instance near your learners; the app is chatty only at
  page load, but latency is free to get right at launch.

---

## 7. Pre-flight

- [ ] `.env.hosted` never committed; secrets in SSM/Secrets Manager
- [ ] IAM role attached (no long-lived access keys on the box)
- [ ] DNS resolves to the Elastic IP / ALB before first start (Caddy/ACM need it)
- [ ] `curl https://your-domain/healthz` → `{"ok":true,"mode":"hosted",...}`
- [ ] `curl -X POST https://your-domain/api/run -d '{}'` → **404** (no execution
      endpoint exists in hosted mode)
- [ ] Sign-in works end to end, and signing in on a second device shows the same
      progress
- [ ] Backups scheduled (EBS snapshots or `pg_dump` to S3)
- [ ] Learners told to clone the repo for the Spark, Airflow and database
      milestones — the app's Environment tab gives them the exact command

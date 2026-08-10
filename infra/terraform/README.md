# PyForge on AWS — Terraform

Creates everything needed to run the hosted app: a small VPC, one EC2 instance
running the compose stack, an Elastic IP, the Route 53 record, secrets in SSM,
an IAM role, and a budget alarm. About 30 resources, ~$16–20/month.

`terraform destroy` removes all of it.

---

## Before you start

1. **Register your domain in Route 53.** Buying it there automatically creates
   the public hosted zone this configuration looks up — nothing else to
   configure in DNS. (If the domain is registered elsewhere, create a hosted
   zone for it in Route 53 and point the registrar's nameservers at it first.)
2. **Push your PyForge repo somewhere public**, or plan to upload the folder
   manually (see "Private repo" below).
3. **Have AWS credentials configured** — `aws sts get-caller-identity` should
   work.
4. **Install Terraform** (or OpenTofu — `tofu` is a drop-in replacement here).

---

## Deploy

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars — domain_name and repo_url are the ones that matter

# Remote state (recommended — state holds generated secrets):
cp backend.hcl.example backend.hcl   # set bucket + region first
terraform init -backend-config=backend.hcl

# Local-only experiment (no S3): terraform init -backend=false

terraform plan          # read this; it should create ~30 resources
terraform apply
```

Then wait about five minutes: the instance updates itself, installs Docker,
clones your repo, builds the image and starts the stack. Watch it happen:

```bash
# terraform output shell_command gives you this exact line
aws ssm start-session --region us-east-1 --target i-0123456789abcdef0
sudo tail -f /var/log/pyforge-bootstrap.log
```

Open `https://your-domain`. Caddy requests a Let's Encrypt certificate on the
first request, which works because Terraform created the DNS record before you
got there.

### Turning on GitHub sign-in

There's a deliberate chicken-and-egg here: GitHub needs your URL, and the URL
doesn't exist until the first apply. So the first deploy runs **without**
sign-in — the site is fully usable, with progress stored in each visitor's
browser.

Once it's up:

1. github.com → Settings → Developer settings → OAuth Apps → New OAuth App
   - Homepage URL: `https://your-domain`
   - Authorization callback URL: `https://your-domain/auth/callback`
     (`terraform output oauth_callback_url` prints this exactly — it must match
     character for character, or sign-in fails)
2. Put the client id and secret in `terraform.tfvars`
3. `terraform apply` — this updates SSM, nothing is rebuilt
4. Run `terraform output -raw apply_config_command` and execute it — the
   instance rebuilds its config from SSM and restarts the app in ~10 seconds

That last step is the pattern for **every** setting change (domain, sign-in
policy, Pyodide URL): apply, then reconfigure. The instance is never replaced,
so the database and everyone's progress stay put.

---

## Day-to-day

```bash
terraform output                  # all the URLs and helper commands
terraform output -raw shell_command   # shell without SSH or an open port

# deploy new application code
aws ssm send-command --instance-ids <id> --document-name AWS-RunShellScript \
  --parameters 'commands=["cd /opt/pyforge && git pull && systemctl restart pyforge"]'

# back up learner progress (also runs daily via /etc/cron.d/pyforge-backup)
aws ssm start-session --target <id>
sudo APP_DIR=/opt/pyforge /opt/pyforge/scripts/backup_postgres.sh
# optional: export S3_BACKUP_URI=s3://your-bucket/pyforge/db/
```

---

## What gets created

| | |
|---|---|
| Networking | VPC 10.20.0.0/16, one public subnet, internet gateway, route table |
| Security group | 80 and 443 open; 22 only if you set `ssh_ingress_cidr` |
| Compute | 1 × `t4g.small` (Graviton), encrypted 20 GB gp3 root, IMDSv2 required |
| Address | Elastic IP + A record (plus `www` when using the bare domain) |
| Secrets | SSM SecureString parameters under `/pyforge/<environment>/` |
| Identity | Instance role: Session Manager + read its own parameters. No access keys |
| Cost control | Budget alarm at 80% actual and 100% forecast spend |

Postgres runs as a container on the instance, on an encrypted volume. That's
the right trade at this size; move it to RDS when you want managed backups and
point-in-time recovery (see AWS.md).

---

## A note about state

`terraform.tfstate` contains the generated `SECRET_KEY` and database password
in plain text — this is true of any Terraform configuration that generates
secrets. Treat the file as sensitive: it's git-ignored here. Production
deploys should use the S3 backend (`backend.hcl.example`) so state is
encrypted, versioned, and locked.

Both generated secrets have `ignore_changes` set, so re-running apply never
rotates them by accident — rotating the signing key would sign everyone out,
and rotating the database password after the volume exists would lock the app
out of its own data.

---

## Private repo

`user_data` clones over public HTTPS. For a private repo, either:

- leave `repo_url = ""`, apply, then upload the folder yourself
  (`aws s3 cp`, or `scp` if you enabled SSH) into `/opt/pyforge` and run
  `sudo systemctl start pyforge`; or
- bake a deploy key into SSM and add a `git config` step to `user_data.sh`.

---

## Checks before you call it done

```bash
curl https://your-domain/healthz                  # {"ok":true,"mode":"hosted",...}
curl -X POST https://your-domain/api/run -d '{}'  # 404 — no execution endpoint exists
```

Then sign in, tick an exercise, and sign in on a second device to confirm
progress follows the account.

---

## Validating changes without AWS

`lint.py` parses every `.tf` file, checks that all variable / local / resource /
data references resolve, and verifies the `user_data.sh` template contract
(placeholders passed in, bash variables correctly escaped):

```bash
pip install python-hcl2 && python3 lint.py
```

It's not a replacement for `terraform validate`, which also checks provider
schemas — run both.

---

## Teardown

```bash
terraform destroy
```

Removes everything including the database volume and all learner progress.
Take a backup first if that matters. The Route 53 *hosted zone* and your domain
registration are not managed here, so they survive — as they should.

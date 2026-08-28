# DataForged on AWS — deploy guide

Closest path to **one-click**: buy the domain in Route 53 → fill three values → `terraform apply` → wait ~5 minutes. GitHub sign-in is a deliberate second apply (OAuth needs your live URL).

**Not zero-touch:** you still need AWS credentials and a Route 53 hosted zone. This is intentional — those can't be invented by Terraform.

---

## Prerequisites (once)

1. **AWS account** with credentials configured (`aws sts get-caller-identity` works).
2. **Terraform ≥ 1.5** installed.
3. **Domain in Route 53** — buy it there, or create a public hosted zone and point the registrar's NS records at it.
4. **This repo pushed to a public GitHub URL** (default in the example: `https://github.com/TapiwaChikwenya/data-forged.git`).

Optional: Session Manager plugin (for `shell_command` without SSH).

---

## Deploy (first apply)

### Option A — helper script (Linux / macOS / Git Bash)

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# edit: domain_name, budget_alert_email  (repo_url already points at this repo)
cd ../..
chmod +x scripts/deploy_aws.sh
./scripts/deploy_aws.sh            # or: ./scripts/deploy_aws.sh -auto-approve
```

### Option B — manual

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# set domain_name, repo_url, budget_alert_email

terraform init
terraform plan
terraform apply
```

Then wait ~5 minutes:

```bash
terraform output -raw shell_command
# on the instance:
sudo tail -f /var/log/dataforged-bootstrap.log
```

Open `terraform output -raw site_url`. Smoke checks:

```bash
curl "$(terraform output -raw site_url)/healthz"
curl -X POST "$(terraform output -raw site_url)/api/run" -d '{}'   # must be 404
```

`www.` is included automatically for apex domains (DNS + Caddy certificate).

---

## Sign-in (second apply — required for cross-device progress)

1. GitHub → Settings → Developer settings → OAuth Apps → New  
   - Homepage: `terraform output -raw site_url`  
   - Callback: `terraform output -raw oauth_callback_url`
2. Put `github_client_id` / `github_client_secret` in `terraform.tfvars`
3. `terraform apply`
4. Run `terraform output -raw apply_config_command` (reloads SSM, restarts app, **keeps the database**)

---

## What you get (~$16–20/month starting point)

| Piece | Notes |
|-------|--------|
| VPC + public subnet + SG | 80/443 open; SSH closed by default |
| `t4g.small` EC2 + EIP | Amazon Linux 2023, IMDSv2 |
| Route 53 A (+ www) | Points at the EIP |
| SSM secrets | Generated `SECRET_KEY` + DB password |
| Hosted Compose stack | App + Postgres + Caddy TLS |
| Extra encrypted EBS | Docker volumes / Postgres — survives instance replace |
| Daily backups | Local disk; set `backup_s3_bucket` for offsite |
| Budget alarm | Emails at 80% / forecast overspend |

`terraform destroy` removes it (including the data volume).

---

## Remote state (recommended after first success)

Local state is the default so `terraform init` is non-interactive. State holds secrets.

```bash
./scripts/bootstrap_tf_state.sh my-dataforged-tfstate us-east-1
# then uncomment backend "s3" {} in versions.tf
cd infra/terraform
terraform init -migrate-state -backend-config=backend.hcl
```

---

## Day-to-day

```bash
terraform output
terraform output -raw shell_command
terraform output -raw apply_config_command   # after OAuth / settings changes
```

Changing `repo_url` / `repo_branch` replaces the instance (intentional). The **data EBS** is re-attached so Postgres progress survives. Root disk content does not.

---

## Validating without spending money

```bash
cd infra/terraform
pip install python-hcl2
python lint.py
terraform init -backend=false
terraform validate
# plan needs real AWS creds + a real hosted zone for domain_name
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Plan fails on Route 53 data source | Domain has no public hosted zone in this account |
| Site never comes up | `bootstrap_log_command` output — almost always clone/DNS/compose |
| www TLS error | Re-apply so `SITE_ADDRESS` includes www; wait for Caddy reload |
| Signed out after apply | You rotated `SECRET_KEY` — don't; it has `ignore_changes` |
| Plan fails on a budget precondition | `monthly_budget_usd > 0` with an empty `budget_alert_email` — set a real inbox, or `monthly_budget_usd = 0` to skip the alarm |
| Plan rejects `budget_alert_email` | It is `@example.com` or too short to be an inbox |

---

## Honest scope

| One apply gets you | Still manual |
|--------------------|--------------|
| HTTPS site, curriculum, anonymous progress | Buying the domain |
| No server-side code execution | AWS credentials on your machine |
| Budget + backups wired | GitHub OAuth app (apply #2) |
| Public repo auto-cloned | Private repo upload / deploy key |

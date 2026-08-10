#!/bin/bash
# ---------------------------------------------------------------------------
# PyForge bootstrap. Runs once, as root, on first boot.
#
#   install Docker -> clone the repo -> build .env.hosted from SSM -> compose up
#
# Everything is logged to /var/log/pyforge-bootstrap.log. If the site doesn't
# come up, read that file first — it is almost always the answer.
#
# Note for readers: ${...} is substituted by Terraform when this file is
# rendered; $${...} and plain $VAR are left alone for bash.
# ---------------------------------------------------------------------------
set -euo pipefail
exec > >(tee -a /var/log/pyforge-bootstrap.log) 2>&1
echo "=== pyforge bootstrap starting $(date -Is) ==="

APP_DIR=/opt/pyforge

# --- packages ---------------------------------------------------------------
dnf update -y
dnf install -y docker git tar jq

# The AWS CLI ships with AL2023; install it if that ever changes.
command -v aws >/dev/null 2>&1 || dnf install -y awscli-2 || dnf install -y aws-cli

systemctl enable --now docker
usermod -aG docker ec2-user || true

# Compose v2 as a docker plugin: prefer the distro package, fall back to the
# official release binary.
if ! dnf install -y docker-compose-plugin; then
  echo "docker-compose-plugin not in repos; fetching the release binary"
  ARCH="$(uname -m)" # aarch64 or x86_64 — matches the asset names
  mkdir -p /usr/local/lib/docker/cli-plugins
  curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$${ARCH}" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi
docker compose version

# --- application code -------------------------------------------------------
REPO_URL="${repo_url}"
if [ -n "$REPO_URL" ]; then
  git clone --depth 1 --branch "${repo_branch}" "$REPO_URL" "$APP_DIR"
else
  echo "No repo_url set — creating $APP_DIR for you to upload the code into."
  mkdir -p "$APP_DIR"
fi

# --- reconfigure helper -----------------------------------------------------
# Rebuilds .env.hosted from SSM and restarts the app. Run it after changing any
# setting with Terraform (adding GitHub OAuth credentials, for example) — no
# instance rebuild, no downtime beyond a container restart.
#
#   sudo /usr/local/bin/pyforge-reconfigure
#
# The parameter name becomes the variable name:
#   /pyforge/prod/BASE_URL  ->  BASE_URL=...
# so adding a setting later means adding an SSM parameter; this never changes.
cat > /usr/local/bin/pyforge-reconfigure <<'SCRIPT'
#!/bin/bash
set -euo pipefail
APP_DIR=/opt/pyforge

umask 077
aws ssm get-parameters-by-path \
  --region "${aws_region}" \
  --path "${ssm_prefix}" \
  --with-decryption \
  --query 'Parameters[].{n:Name,v:Value}' \
  --output json |
  jq -r '.[] | "\(.n | split("/") | last)=\(.v)"' |
  # "unset" is the placeholder written before the GitHub OAuth app exists;
  # blank it so the app simply runs without sign-in.
  sed 's/^\(GITHUB_[A-Z_]*\)=unset$/\1=/' > "$APP_DIR/.env.hosted"
chmod 600 "$APP_DIR/.env.hosted"
umask 022

for required in SECRET_KEY POSTGRES_PASSWORD BASE_URL SITE_ADDRESS; do
  grep -q "^$required=." "$APP_DIR/.env.hosted" || {
    echo "FATAL: $required missing from SSM — check the instance role"
    exit 1
  }
done
echo "configuration written: $(grep -c . "$APP_DIR/.env.hosted") settings"

if systemctl is-enabled pyforge.service >/dev/null 2>&1; then
  systemctl restart pyforge.service
  echo "pyforge restarted"
fi
SCRIPT
chmod 755 /usr/local/bin/pyforge-reconfigure

# --- service ----------------------------------------------------------------
cat > /etc/systemd/system/pyforge.service <<'EOF'
[Unit]
Description=PyForge (docker compose)
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/pyforge
ExecStart=/usr/bin/docker compose -f docker-compose.hosted.yml --env-file .env.hosted up -d --build
ExecStop=/usr/bin/docker compose -f docker-compose.hosted.yml --env-file .env.hosted down
TimeoutStartSec=1800

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pyforge.service

# Write the config (service not started yet, so this just creates .env.hosted)
/usr/local/bin/pyforge-reconfigure

if [ -f "$APP_DIR/docker-compose.hosted.yml" ]; then
  systemctl start pyforge.service
  echo "=== pyforge started. Caddy requests its certificate on the first request. ==="
else
  echo "=== no docker-compose.hosted.yml yet — upload the code to $APP_DIR, then:"
  echo "===   sudo systemctl start pyforge"
fi

# --- automated Postgres backups --------------------------------------------
# Daily dump to /var/backups/pyforge. Set S3_BACKUP_URI in the environment
# (or edit the cron line) to also push gzipped dumps to S3.
mkdir -p /var/backups/pyforge
if [ -f "$APP_DIR/scripts/backup_postgres.sh" ]; then
  chmod +x "$APP_DIR/scripts/backup_postgres.sh"
  cat > /etc/cron.d/pyforge-backup <<'CRON'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
15 3 * * * root APP_DIR=/opt/pyforge /opt/pyforge/scripts/backup_postgres.sh >>/var/log/pyforge-backup.log 2>&1
CRON
  chmod 644 /etc/cron.d/pyforge-backup
  echo "installed daily backup cron (/etc/cron.d/pyforge-backup)"
fi

touch /opt/pyforge-bootstrap-complete
echo "=== pyforge bootstrap finished $(date -Is) ==="

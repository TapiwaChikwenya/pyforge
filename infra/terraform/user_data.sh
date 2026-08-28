#!/bin/bash
# ---------------------------------------------------------------------------
# DataForged bootstrap. Runs once, as root, on first boot.
#
#   install Docker -> clone the repo -> build .env.hosted from SSM -> compose up
#
# Everything is logged to /var/log/dataforged-bootstrap.log. If the site doesn't
# come up, read that file first — it is almost always the answer.
#
# Note for readers: a $${name} placeholder is substituted by Terraform when this
# file is rendered. Doubling the dollar sign escapes it, and plain $VAR is left
# alone for bash.
# ---------------------------------------------------------------------------
set -euo pipefail
exec > >(tee -a /var/log/dataforged-bootstrap.log) 2>&1
echo "=== dataforged bootstrap starting $(date -Is) ==="

APP_DIR=/opt/dataforged

# --- packages ---------------------------------------------------------------
dnf update -y
dnf install -y docker git tar jq

# The AWS CLI ships with AL2023; install it if that ever changes.
command -v aws >/dev/null 2>&1 || dnf install -y awscli-2 || dnf install -y aws-cli

# --- durable data volume (Postgres Docker volumes) --------------------------
# Terraform attaches an encrypted EBS at /dev/sdf (may appear as /dev/nvme1n1).
# Attachment can lag a few seconds behind first boot — wait for it.
DATA_DEV=""
for _i in $(seq 1 60); do
  for candidate in /dev/sdf /dev/xvdf /dev/nvme1n1; do
    if [ -b "$candidate" ]; then DATA_DEV="$candidate"; break 2; fi
  done
  sleep 2
done
if [ -n "$DATA_DEV" ]; then
  echo "preparing data volume on $DATA_DEV"
  if ! blkid "$DATA_DEV" >/dev/null 2>&1; then
    mkfs.xfs -f "$DATA_DEV"
  fi
  mkdir -p /var/lib/docker/volumes
  systemctl stop docker 2>/dev/null || true
  if ! mountpoint -q /var/lib/docker/volumes; then
    UUID="$(blkid -s UUID -o value "$DATA_DEV")"
    grep -q "$UUID" /etc/fstab || echo "UUID=$UUID /var/lib/docker/volumes xfs defaults,nofail 0 2" >> /etc/fstab
    mount /var/lib/docker/volumes
  fi
  echo "data volume mounted at /var/lib/docker/volumes"
else
  echo "WARNING: no data volume device found after 120s — Postgres will live on the root disk"
fi

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
#   sudo /usr/local/bin/dataforged-reconfigure
#
# The parameter name becomes the variable name:
#   /dataforged/prod/BASE_URL  ->  BASE_URL=...
# so adding a setting later means adding an SSM parameter; this never changes.
cat > /usr/local/bin/dataforged-reconfigure <<'SCRIPT'
#!/bin/bash
set -euo pipefail
APP_DIR=/opt/dataforged

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

if systemctl is-enabled dataforged.service >/dev/null 2>&1; then
  systemctl restart dataforged.service
  echo "dataforged restarted"
fi
SCRIPT
chmod 755 /usr/local/bin/dataforged-reconfigure

# --- service ----------------------------------------------------------------
cat > /etc/systemd/system/dataforged.service <<'EOF'
[Unit]
Description=DataForged (docker compose)
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/dataforged
ExecStart=/usr/bin/docker compose -f docker-compose.hosted.yml --env-file .env.hosted up -d --build
ExecStop=/usr/bin/docker compose -f docker-compose.hosted.yml --env-file .env.hosted down
TimeoutStartSec=1800

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dataforged.service

# Write the config (service not started yet, so this just creates .env.hosted)
/usr/local/bin/dataforged-reconfigure

if [ -f "$APP_DIR/docker-compose.hosted.yml" ]; then
  systemctl start dataforged.service
  echo "=== dataforged started. Caddy requests its certificate on the first request. ==="
else
  echo "=== no docker-compose.hosted.yml yet — upload the code to $APP_DIR, then:"
  echo "===   sudo systemctl start dataforged"
fi

# --- automated Postgres backups --------------------------------------------
# Daily dump to /var/backups/dataforged. Set S3_BACKUP_URI in the environment
# (or edit the cron line) to also push gzipped dumps to S3.
mkdir -p /var/backups/dataforged
if [ -f "$APP_DIR/scripts/backup_postgres.sh" ]; then
  chmod +x "$APP_DIR/scripts/backup_postgres.sh"
  cat > /etc/cron.d/dataforged-backup <<'CRON'
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
15 3 * * * root bash -lc 'set -a; [ -f /opt/dataforged/.env.hosted ] && . /opt/dataforged/.env.hosted; set +a; APP_DIR=/opt/dataforged /opt/dataforged/scripts/backup_postgres.sh' >>/var/log/dataforged-backup.log 2>&1
CRON
  chmod 644 /etc/cron.d/dataforged-backup
  echo "installed daily backup cron (/etc/cron.d/dataforged-backup)"
fi

touch /opt/dataforged-bootstrap-complete
echo "=== dataforged bootstrap finished $(date -Is) ==="

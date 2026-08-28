#!/usr/bin/env bash
# Dump the hosted Postgres database and optionally upload to S3.
#
# Env:
#   COMPOSE_FILE   default: docker-compose.hosted.yml
#   ENV_FILE       default: .env.hosted
#   BACKUP_DIR     default: /var/backups/dataforged
#   RETAIN_DAYS    default: 14
#   S3_BACKUP_URI  optional, e.g. s3://my-bucket/dataforged/db/
#
# Cron example (installed by Terraform user_data):
#   15 3 * * * root /opt/dataforged/scripts/backup_postgres.sh >>/var/log/dataforged-backup.log 2>&1
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/dataforged}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.hosted.yml}"
ENV_FILE="${ENV_FILE:-.env.hosted}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/dataforged}"
RETAIN_DAYS="${RETAIN_DAYS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${BACKUP_DIR}/dataforged-${STAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"

echo "[$(date -Is)] starting backup -> $OUT"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T db \
  pg_dump -U "${POSTGRES_USER:-dataforged}" "${POSTGRES_DB:-dataforged}" \
  | gzip -c > "$OUT"

chmod 600 "$OUT"
echo "[$(date -Is)] wrote $(du -h "$OUT" | awk '{print $1}')"

if [ -n "${S3_BACKUP_URI:-}" ]; then
  aws s3 cp "$OUT" "${S3_BACKUP_URI%/}/$(basename "$OUT")"
  echo "[$(date -Is)] uploaded to $S3_BACKUP_URI"
fi

find "$BACKUP_DIR" -name 'dataforged-*.sql.gz' -mtime "+${RETAIN_DAYS}" -delete
echo "[$(date -Is)] prune complete (retain ${RETAIN_DAYS}d)"

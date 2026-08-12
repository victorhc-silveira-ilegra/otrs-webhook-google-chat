#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE=(
  docker compose
  --env-file "${ROOT_DIR}/.env"
  -f "${ROOT_DIR}/infra/docker/docker-compose.yml"
  --project-directory "${ROOT_DIR}/infra/docker"
)
DB_USER="${OTRS_DB_USER:-otrs}"
DB_PASSWORD="${OTRS_DB_PASSWORD:-otrssecret}"
DB_NAME="${OTRS_DB_NAME:-otrs}"
MAX_ATTEMPTS="${SCHEMA_WAIT_ATTEMPTS:-90}"

ensure_dispatch_table() {
  "${COMPOSE[@]}" exec -T mariadb \
    mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" <<'SQL'
CREATE TABLE IF NOT EXISTS gchat_alert_dispatch (
    ticket_id BIGINT NOT NULL,
    dedup_hash CHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    queue_name VARCHAR(200) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (ticket_id),
    UNIQUE KEY uq_gchat_alert_dedup_hash (dedup_hash),
    KEY idx_gchat_alert_created_at (created_at)
);
SQL
}

echo "Aguardando schema OTRS (ticket/queue/gchat_alert_dispatch)..."
for _ in $(seq 1 "${MAX_ATTEMPTS}"); do
  ensure_dispatch_table >/dev/null 2>&1 || true
  count="$("${COMPOSE[@]}" exec -T mariadb \
    mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" -N -e \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}' AND table_name IN ('ticket','queue','gchat_alert_dispatch')" \
    2>/dev/null | tr -d '[:space:]' || true)"
  if [[ "${count}" == "3" ]]; then
    echo "Schema OTRS pronto."
    exit 0
  fi
  sleep 2
done

echo "Schema OTRS nao ficou pronto a tempo (tabelas ticket/queue/gchat_alert_dispatch ausentes)." >&2
exit 1

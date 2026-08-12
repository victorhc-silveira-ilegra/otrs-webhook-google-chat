#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE=(docker compose -f "${ROOT_DIR}/infra/docker/docker-compose.yml" --project-directory "${ROOT_DIR}/infra/docker")
DB_USER="${OTRS_DB_USER:-otrs}"
DB_PASSWORD="${OTRS_DB_PASSWORD:-otrssecret}"
DB_NAME="${OTRS_DB_NAME:-otrs}"
MAX_ATTEMPTS="${SCHEMA_WAIT_ATTEMPTS:-90}"

echo "Aguardando schema OTRS (ticket/queue)..."
for _ in $(seq 1 "${MAX_ATTEMPTS}"); do
  count="$("${COMPOSE[@]}" exec -T mariadb \
    mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" -N -e \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}' AND table_name IN ('ticket','queue')" \
    2>/dev/null | tr -d '[:space:]' || true)"
  if [[ "${count}" == "2" ]]; then
    echo "Schema OTRS pronto."
    exit 0
  fi
  sleep 2
done

echo "Schema OTRS nao ficou pronto a tempo (tabelas ticket/queue ausentes)." >&2
exit 1

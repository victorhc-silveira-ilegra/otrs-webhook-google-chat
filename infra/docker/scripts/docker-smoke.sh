#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
COMPOSE=(
  docker compose
  --env-file "${ENV_FILE}"
  -f "${ROOT_DIR}/infra/docker/docker-compose.yml"
  --project-directory "${ROOT_DIR}/infra/docker"
)

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Arquivo .env nao encontrado em ${ENV_FILE}" >&2
  exit 1
fi

if ! grep -Eq '^[[:space:]]*WEBHOOK_URL=.+' "${ENV_FILE}"; then
  echo "WEBHOOK_URL ausente ou vazio no .env" >&2
  exit 1
fi

ledger_count() {
  local title="$1"
  "${COMPOSE[@]}" exec -T mariadb \
    mysql -uotrs -potrssecret otrs -N -e \
    "SELECT COUNT(*) FROM gchat_alert_dispatch WHERE title='${title}' AND queue_name='Raw';" \
    | tr -d '[:space:]'
}

run_alert() {
  local ticket_id="$1"
  local title="$2"
  "${COMPOSE[@]}" exec -T notifier otrs-gchat-alert \
    --ticket-id "${ticket_id}" \
    --ticket-number "20260812${ticket_id}" \
    --title "${title}" \
    --queue "Raw"
}

expect_ledger() {
  local expected="$1"
  local title="$2"
  local label="$3"
  local actual
  actual="$(ledger_count "${title}")"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "Falha ${label}: esperado ${expected} claim(s) no ledger para '${title}', obtido ${actual}" >&2
    exit 1
  fi
}

bash "${ROOT_DIR}/infra/docker/scripts/wait-for-otrs-schema.sh"

"${COMPOSE[@]}" exec -T mariadb \
  mysql -uotrs -potrssecret otrs -e "DELETE FROM gchat_alert_dispatch;" >/dev/null

run_alert 9101 "smoke-dedup"
expect_ledger 1 "smoke-dedup" "primeiro envio"

run_alert 9101 "smoke-dedup"
expect_ledger 1 "smoke-dedup" "reenvio mesmo ticket_id"

run_alert 9102 "smoke-dedup"
expect_ledger 1 "smoke-dedup" "ticket distinto com mesmo titulo/fila"

"${COMPOSE[@]}" exec -T mariadb \
  mysql -uotrs -potrssecret otrs -e "DELETE FROM gchat_alert_dispatch WHERE title='smoke-race';" >/dev/null

run_alert 9201 "smoke-race" &
pid1=$!
run_alert 9202 "smoke-race" &
pid2=$!
wait "${pid1}"
wait "${pid2}"
expect_ledger 1 "smoke-race" "corrida entre dois tickets similares"

echo "[OK] docker-smoke (envio real via .env + idempotencia + race)"

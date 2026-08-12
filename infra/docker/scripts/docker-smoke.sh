#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE=(docker compose -f "${ROOT_DIR}/infra/docker/docker-compose.yml" --project-directory "${ROOT_DIR}/infra/docker")
WIREMOCK_URL="${WIREMOCK_URL:-http://localhost:8080}"
SMOKE_WEBHOOK_URL="${SMOKE_WEBHOOK_URL:-http://mock-webhook:8080/v1/spaces/POC/messages}"

request_count() {
  curl -sf "${WIREMOCK_URL}/__admin/requests" | python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("requests", [])))'
}

reset_requests() {
  curl -sf -X DELETE "${WIREMOCK_URL}/__admin/requests" >/dev/null
}

run_alert() {
  local ticket_id="$1"
  local title="$2"
  "${COMPOSE[@]}" exec -T \
    -e OTRS_DISABLE_DOTENV=1 \
    -e WEBHOOK_URL="${SMOKE_WEBHOOK_URL}" \
    -e DEDUP_ENABLED=true \
    -e DEDUP_WINDOW_MINUTES=30 \
    -e OTRS_DB_HOST=mariadb \
    -e OTRS_DB_PORT=3306 \
    -e OTRS_DB_NAME=otrs \
    -e OTRS_DB_USER=otrs \
    -e OTRS_DB_PASSWORD=otrssecret \
    -e LOG_LEVEL=INFO \
    -e LOG_FORMAT=text \
    notifier otrs-gchat-alert \
    --ticket-id "${ticket_id}" \
    --ticket-number "20260812${ticket_id}" \
    --title "${title}" \
    --queue "Raw"
}

expect_count() {
  local expected="$1"
  local label="$2"
  local actual
  actual="$(request_count)"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "Falha ${label}: esperado ${expected} request(s) no WireMock, obtido ${actual}" >&2
    exit 1
  fi
}

curl -sf "${WIREMOCK_URL}/health" >/dev/null
curl -sf "${WIREMOCK_URL}/__admin/mappings" >/dev/null
bash "${ROOT_DIR}/infra/docker/scripts/wait-for-otrs-schema.sh"

"${COMPOSE[@]}" exec -T mariadb \
  mysql -uotrs -potrssecret otrs -e "DELETE FROM gchat_alert_dispatch;" >/dev/null

reset_requests
run_alert 9101 "smoke-dedup"
expect_count 1 "primeiro envio"

run_alert 9101 "smoke-dedup"
expect_count 1 "reenvio mesmo ticket_id"

run_alert 9102 "smoke-dedup"
expect_count 1 "ticket distinto com mesmo titulo/fila"

reset_requests
run_alert 9201 "smoke-race" &
pid1=$!
run_alert 9202 "smoke-race" &
pid2=$!
wait "${pid1}"
wait "${pid2}"
expect_count 1 "corrida entre dois tickets similares"

echo "[OK] docker-smoke (envio + idempotencia + race)"

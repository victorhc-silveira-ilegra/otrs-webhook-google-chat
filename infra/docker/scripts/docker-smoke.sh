#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
CREATE_TICKET_PL="${ROOT_DIR}/infra/docker/scripts/otrs-create-raw-ticket.pl"
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

if ! grep -Eq '^[[:space:]]*GCHAT_WEBHOOK_URL=.+' "${ENV_FILE}"; then
  echo "GCHAT_WEBHOOK_URL ausente ou vazio no .env" >&2
  exit 1
fi

if [[ ! -f "${CREATE_TICKET_PL}" ]]; then
  echo "Script ausente: ${CREATE_TICKET_PL}" >&2
  exit 1
fi

ledger_count() {
  local title="$1"
  "${COMPOSE[@]}" exec -T mariadb \
    mysql -uotrs -potrssecret otrs -N -e \
    "SELECT COUNT(*) FROM gchat_alert_dispatch WHERE title='${title}' AND queue_name='Raw';" \
    | tr -d '[:space:]'
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

create_raw_ticket() {
  local title="$1"
  local line ticket_id ticket_number queue
  line="$(
    "${COMPOSE[@]}" exec -T -e WINDOW_ENABLED=false otrs perl /tmp/otrs-create-raw-ticket.pl "${title}" \
      | tr -d '\r' \
      | grep -E '^[0-9]+[[:space:]]' \
      | tail -n 1
  )"
  IFS=$'\t' read -r ticket_id ticket_number queue <<<"${line}"
  if [[ -z "${ticket_id}" || -z "${ticket_number}" || "${queue}" != "Raw" ]]; then
    echo "Falha ao criar ticket Raw para title='${title}' (saida='${line}')" >&2
    exit 1
  fi
  echo "${ticket_id}"
}

bash "${ROOT_DIR}/infra/docker/scripts/wait-for-otrs-schema.sh"

echo "Aguardando OTRS HTTP..."
for _ in $(seq 1 60); do
  code="$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8081/otrs/index.pl || true)"
  if [[ "${code}" == "200" || "${code}" == "302" ]]; then
    break
  fi
  sleep 2
done
if [[ "${code:-}" != "200" && "${code:-}" != "302" ]]; then
  echo "OTRS HTTP nao respondeu 200/302 a tempo (ultimo=${code:-none})" >&2
  exit 1
fi

"${COMPOSE[@]}" cp "${CREATE_TICKET_PL}" otrs:/tmp/otrs-create-raw-ticket.pl
"${COMPOSE[@]}" exec -T otrs /opt/otrs/bin/otrs.RebuildConfig.pl >/dev/null

"${COMPOSE[@]}" exec -T mariadb \
  mysql -uotrs -potrssecret otrs -e "DELETE FROM gchat_alert_dispatch;" >/dev/null

ticket_a="$(create_raw_ticket "smoke-dedup")"
expect_ledger 1 "smoke-dedup" "primeiro TicketCreate Raw"

ticket_b="$(create_raw_ticket "smoke-dedup")"
expect_ledger 1 "smoke-dedup" "segundo TicketCreate com mesmo titulo/fila"

if [[ "${ticket_a}" == "${ticket_b}" ]]; then
  echo "Falha: esperava TicketIDs distintos no cenário de dedup (${ticket_a})" >&2
  exit 1
fi

"${COMPOSE[@]}" exec -T mariadb \
  mysql -uotrs -potrssecret otrs -e "DELETE FROM gchat_alert_dispatch WHERE title='smoke-race';" >/dev/null

create_raw_ticket "smoke-race" >/tmp/otrs-smoke-race-a.tid &
pid1=$!
create_raw_ticket "smoke-race" >/tmp/otrs-smoke-race-b.tid &
pid2=$!
wait "${pid1}"
wait "${pid2}"
expect_ledger 1 "smoke-race" "corrida entre dois TicketCreate Raw"

echo "[OK] docker-smoke (TicketCreate Raw real + webhook .env + idempotencia + race)"

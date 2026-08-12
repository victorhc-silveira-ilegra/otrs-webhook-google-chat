#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE=(
  docker compose
  --env-file "${ROOT_DIR}/.env"
  -f "${ROOT_DIR}/infra/docker/docker-compose.yml"
  --project-directory "${ROOT_DIR}/infra/docker"
)

echo "=== 1. OTRS Application (HTTP 8081) ==="
curl -sI http://localhost:8081/otrs/index.pl | grep -iE 'HTTP/|Server:|X-Powered-By:' || true

echo
echo "=== 2. WireMock Webhook (HTTP 8080) ==="
curl -s http://localhost:8080/health | grep -qx 'ok' && echo "HTTP/1.1 200 OK (body=ok)" || {
  echo "WireMock /health FAIL" >&2
  exit 1
}

echo
echo "=== 3. MariaDB Database (TCP 3306) ==="
if "${COMPOSE[@]}" exec -T mariadb mysqladmin ping -h 127.0.0.1 -uroot -prootsecret --silent; then
  echo "otrs-mariadb OK (mysqladmin ping)"
else
  echo "otrs-mariadb FAIL" >&2
  exit 1
fi

echo
echo "=== 4. Notifier Worker CLI (Runtime Python) ==="
"${COMPOSE[@]}" exec -T notifier otrs-gchat-alert --help >/dev/null
echo "otrs-notifier OK (CLI pronta)"

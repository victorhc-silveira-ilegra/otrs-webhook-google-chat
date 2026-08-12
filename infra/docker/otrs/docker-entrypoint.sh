#!/bin/bash
set -euo pipefail

DB_HOST="${OTRS_DB_HOST:-mariadb}"
DB_PORT="${OTRS_DB_PORT:-3306}"
DB_NAME="${OTRS_DB_NAME:-otrs}"
DB_USER="${OTRS_DB_USER:-otrs}"
DB_PASSWORD="${OTRS_DB_PASSWORD:-otrssecret}"

CONFIG_PM="/opt/otrs/Kernel/Config.pm"
SCHEMA_SQL="/opt/otrs/scripts/database/otrs-schema.mysql.sql"
INSERT_SQL="/opt/otrs/scripts/database/otrs-initial_insert.mysql.sql"
POST_SQL="/opt/otrs/scripts/database/otrs-schema-post.mysql.sql"

if [[ -f "${CONFIG_PM}" ]]; then
  sed -i -E \
    -e "s|(\\\$Self->\{DatabaseHost\}[[:space:]]*=[[:space:]]*)'[^']*'|\1'${DB_HOST}'|" \
    -e "s|^([[:space:]]*)\\\$Self->\{Database\}[[:space:]]*=[[:space:]]*'[^']*'|\1\$Self->{Database} = '${DB_NAME}';|" \
    -e "s|(\\\$Self->\{DatabaseUser\}[[:space:]]*=[[:space:]]*)'[^']*'|\1'${DB_USER}'|" \
    -e "s|(\\\$Self->\{DatabasePw\}[[:space:]]*=[[:space:]]*)'[^']*'|\1'${DB_PASSWORD}'|" \
    "${CONFIG_PM}" || true
fi

for _ in $(seq 1 60); do
  if mysqladmin ping -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASSWORD}" --silent >/dev/null 2>&1; then
    echo "OTRS ready: MariaDB acessivel em ${DB_HOST}:${DB_PORT}"
    break
  fi
  sleep 2
done

mysql_cmd() {
  mysql -h"${DB_HOST}" -P"${DB_PORT}" -u"${DB_USER}" -p"${DB_PASSWORD}" "$@"
}

schema_ready() {
  local count
  count="$(mysql_cmd -N -e \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}' AND table_name IN ('ticket','queue')")"
  [[ "${count}" == "2" ]]
}

full_schema_ready() {
  local count
  count="$(mysql_cmd -N -e \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${DB_NAME}' AND table_name='ticket_history'")"
  [[ "${count}" == "1" ]]
}

if [[ ! -f /opt/otrs/var/.db_initialized ]]; then
  if [[ -f "${SCHEMA_SQL}" ]] && ! full_schema_ready; then
    mysql_cmd -e "SET FOREIGN_KEY_CHECKS=0; DROP TABLE IF EXISTS ticket; DROP TABLE IF EXISTS queue; SET FOREIGN_KEY_CHECKS=1;" "${DB_NAME}"
    mysql_cmd "${DB_NAME}" < "${SCHEMA_SQL}"
    mysql_cmd "${DB_NAME}" < "${INSERT_SQL}"
    mysql_cmd "${DB_NAME}" < "${POST_SQL}"
  fi
  if ! schema_ready; then
    echo "OTRS schema incomplete: tabelas ticket/queue ausentes em ${DB_NAME}" >&2
    exit 1
  fi
  mkdir -p /opt/otrs/var
  touch /opt/otrs/var/.db_initialized
fi

if [[ -d /opt/otrs/bin/cgi-bin ]]; then
  chmod -R a+rx /opt/otrs/bin/cgi-bin || true
fi
if compgen -G "/opt/otrs/bin/otrs.*" >/dev/null; then
  chmod a+rx /opt/otrs/bin/otrs.* || true
fi
if id otrs >/dev/null 2>&1 && getent group apache >/dev/null; then
  chown -R otrs:apache /opt/otrs || true
fi

if [[ -x /opt/otrs/bin/otrs.RebuildConfig.pl ]]; then
  /opt/otrs/bin/otrs.RebuildConfig.pl >/dev/null
  if id otrs >/dev/null 2>&1 && getent group apache >/dev/null; then
    chown otrs:apache /opt/otrs/Kernel/Config/Files/ZZZAAuto.pm 2>/dev/null || true
  fi
fi

echo "OTRS ready: schema ok, iniciando Apache"
exec "$@"

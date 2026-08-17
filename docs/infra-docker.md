# Infra Docker

Stack local da PoC OTRS → Google Chat (notifier Python + MariaDB + WireMock + OTRS legado).

## Servicos

| Servico | Porta | Papel |
|---------|-------|--------|
| `otrs` | 8081 | OTRS 3.2.1 (CentOS 7 + Apache + Perl); UI em `/otrs/index.pl`; Event Module chama a CLI |
| `mariadb` | 3306 | Banco (schema minimo `init.sql` + ledger de dispatch) |
| `mock-webhook` | 8080 | WireMock (opcional; PoC pode usar webhook real via `.env`) |
| `notifier` | - | Imagem Python com `otrs-gchat-alert` |

## Comandos

```bash
make docker-up
make docker-rebuild
make docker-ps
make docker-sh
make docker-smoke
make docker-health
make docker-down
make docker-clean
```

- `docker-clean` e destrutivo (remove volumes, MariaDB incluso).
- `docker-rebuild` refaz build e recria containers.
- `docker-sh` abre `/bin/bash` no servico (`DOCKER_SERVICE=otrs` por padrao; tambem `notifier`, `mariadb`, `mock-webhook`).
- `docker-smoke` espera schema (`ticket`/`queue`/`gchat_alert_dispatch`), cria tickets reais na fila `Raw` via API Perl (`TicketCreate` + Event Module) e valida webhook do `.env` + idempotencia + race no ledger (`infra/docker/scripts/docker-smoke.sh`, helper `otrs-create-raw-ticket.pl`). O smoke força `WINDOW_ENABLED=false` no `TicketCreate` para nao depender do relogio.
- `docker-health` valida OTRS (`/otrs/index.pl`), WireMock (`/health`), MariaDB (`mysqladmin ping`) e a CLI do notifier.
- `docker-logs` mostra as ultimas `200` linhas de `otrs` e `notifier` por padrao (`DOCKER_LOGS_SERVICES`; use `DOCKER_SERVICE=mariadb` ou `mock-webhook` quando precisar; `F=1` para follow).
- Apos o rebuild, espere linhas `OTRS ready` / `notifier ready`. O smoke dispara o caminho completo OTRS → Event Module → CLI → webhook (logs da CLI aparecem no terminal do smoke).
- WireMock continua na stack como mock opcional; com `GCHAT_WEBHOOK_URL` real no `.env`, o smoke nao depende dele.
- Event Module filtra `Queue=Raw` (`GoogleChatAlert.xml` + check no Perl).

Se o schema nao aparecer: `make docker-clean && make docker-up`.

## Schema MariaDB (PoC)

`infra/docker/mariadb/init.sql` (montado em `/docker-entrypoint-initdb.d/`):

- cria `queue` e `ticket` minimos
- cria `gchat_alert_dispatch` (PK `ticket_id`, UNIQUE `dedup_hash`)
- seed da fila `Raw` (schema minimo da PoC; no OTRS completo a fila `Raw` ja vem no seed oficial)

Volumes ja existentes: `wait-for-otrs-schema.sh` aplica `CREATE TABLE IF NOT EXISTS` do ledger.
## Event Module

- `infra/docker/otrs/Kernel/System/Ticket/Event/GoogleChatAlert.pm`
- `infra/docker/otrs/Kernel/Config/Files/GoogleChatAlert.xml`

No `TicketCreate`, chama:

```text
otrs-gchat-alert --ticket-id ... --ticket-number ... --title ... --queue ...
```

`NOTIFIER_BIN` aponta para a CLI no container OTRS (`/opt/notifier/bin/otrs-gchat-alert`).

UI local: `http://localhost:8081/otrs/index.pl` (esperado `200` ou `302`). O Dockerfile baixa o tarball do OTRS (`ftp.otrs.org` com fallback `download.znuny.org`) e exige `bin/cgi-bin/index.pl`. O entrypoint roda `otrs.RebuildConfig.pl` para gerar `ZZZAAuto.pm` (necessario para `TicketCreate` via CLI/smoke).

## Variaveis

Fonte: `.env` na raiz (`docker compose --env-file .env`). O Python tambem carrega esse arquivo em `Settings.from_env()`.

| Variavel | Exemplo / nota |
|----------|----------------|
| `GCHAT_WEBHOOK_URL` | Incoming Webhook Google Chat ou WireMock |
| `HTTP_TIMEOUT_SECONDS` | `10` |
| `OTRS_BASE_URL` | `https://portal.ilegra.com/otrs/index.pl` |
| `LOG_LEVEL` / `LOG_FORMAT` / `LOG_FILE` / `LOG_DIR` | logging semantico; `LOG_DIR` diario em `logs/otrs-gchat-YYYY-MM-DD.log` |
| `DEDUP_ENABLED` | compose forca `true` no `notifier` e no `otrs` (CLI do Event Module) |
| `DEDUP_WINDOW_MINUTES` | `30` |
| `WINDOW_ENABLED` | `true` |
| `WINDOW_DAYS` / `WINDOW_START` / `WINDOW_END` / `WINDOW_TIMEZONE` | janela comercial |
| `OTRS_DB_*` | no `notifier`/`otrs` o compose fixa host `mariadb` |
| `NOTIFIER_BIN` | so no container `otrs` |

No host (CLI local), use `OTRS_DB_HOST=127.0.0.1` no `.env`. Dentro do compose, o servico `notifier` usa `mariadb`.

## Relacionados

- [arquitetura.md](arquitetura.md)
- [engineering-python.md](engineering-python.md)
- [engineering-logging.md](engineering-logging.md)

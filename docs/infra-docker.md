# Infra Docker

Stack local da PoC OTRS → Google Chat (notifier Python + MariaDB + WireMock + OTRS legado).

## Servicos

| Servico | Porta | Papel |
|---------|-------|--------|
| `otrs` | 8081 | OTRS 3.2.1 (CentOS 7 + Apache + Perl); Event Module chama a CLI |
| `mariadb` | 3306 | Banco (schema minimo `init.sql` + ledger de dispatch) |
| `mock-webhook` | 8080 | WireMock (opcional; PoC pode usar webhook real via `.env`) |
| `notifier` | - | Imagem Python com `otrs-gchat-alert` |

## Comandos

```bash
make docker-up
make docker-rebuild
make docker-ps
make docker-smoke
make docker-down
make docker-clean
```

- `docker-clean` e destrutivo (remove volumes, MariaDB incluso).
- `docker-rebuild` refaz build e recria containers.
- `docker-smoke` espera schema (`ticket`/`queue`/`gchat_alert_dispatch`) e valida envio + idempotencia + race no WireMock (`infra/docker/scripts/docker-smoke.sh`), forcando `WEBHOOK_URL` mock via `OTRS_DISABLE_DOTENV=1`.

Se o schema nao aparecer: `make docker-clean && make docker-up`.

## Schema MariaDB (PoC)

`infra/docker/mariadb/init.sql` (montado em `/docker-entrypoint-initdb.d/`):

- cria `queue` e `ticket` minimos
- cria `gchat_alert_dispatch` (PK `ticket_id`, UNIQUE `dedup_hash`)
- seed das filas `Raw` e `CloudTeam`

Volumes ja existentes: `wait-for-otrs-schema.sh` aplica `CREATE TABLE IF NOT EXISTS` do ledger.
## Event Module

- `infra/docker/otrs/Kernel/System/Ticket/Event/GoogleChatAlert.pm`
- `infra/docker/otrs/Kernel/Config/Files/GoogleChatAlert.xml`

No `TicketCreate`, chama:

```text
otrs-gchat-alert --ticket-id ... --ticket-number ... --title ... --queue ...
```

`NOTIFIER_BIN` aponta para a CLI no container OTRS (`/opt/notifier/bin/otrs-gchat-alert`).

## Variaveis

Fonte: `.env` na raiz (`docker compose --env-file .env`). O Python tambem carrega esse arquivo em `Settings.from_env()`.

| Variavel | Exemplo / nota |
|----------|----------------|
| `WEBHOOK_URL` | Incoming Webhook Google Chat ou WireMock |
| `HTTP_TIMEOUT_SECONDS` | `10` |
| `OTRS_BASE_URL` | `https://portal.ilegra.com/otrs/index.pl` |
| `LOG_LEVEL` / `LOG_FORMAT` / `LOG_FILE` | logging semantico |
| `DEDUP_ENABLED` | compose forca `true` no `notifier` |
| `DEDUP_WINDOW_MINUTES` | `30` |
| `OTRS_DB_*` | no `notifier`/`otrs` o compose fixa host `mariadb` |
| `NOTIFIER_BIN` | so no container `otrs` |

No host (CLI local), use `OTRS_DB_HOST=127.0.0.1` no `.env`. Dentro do compose, o servico `notifier` usa `mariadb`.

## Relacionados

- [arquitetura.md](arquitetura.md)
- [engineering-python.md](engineering-python.md)
- [engineering-logging.md](engineering-logging.md)

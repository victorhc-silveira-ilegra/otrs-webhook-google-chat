# Infra Docker

Stack local da PoC OTRS → Google Chat (notifier Python + MariaDB + WireMock + OTRS legado).

## Servicos

| Servico | Porta | Papel |
|---------|-------|--------|
| `otrs` | 8081 | OTRS 3.2.1 (CentOS 7 + Apache + Perl); Event Module chama a CLI |
| `mariadb` | 3306 | Banco (schema minimo `init.sql` + dedup) |
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
- `docker-smoke` espera tabelas `ticket`/`queue` (`infra/docker/scripts/wait-for-otrs-schema.sh`) e executa a CLI no `notifier`.

Se o schema nao aparecer: `make docker-clean && make docker-up`.

## Schema MariaDB (PoC)

`infra/docker/mariadb/init.sql` (montado em `/docker-entrypoint-initdb.d/`):

- cria `queue` e `ticket` minimos para dedup
- seed das filas `Raw` e `CloudTeam`

Quando a imagem OTRS traz `/opt/otrs/scripts/database/*.sql`, o `docker-entrypoint.sh` pode aplicar o schema oficial (substituindo o minimo se necessario).

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

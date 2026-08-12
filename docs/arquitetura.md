# Arquitetura da PoC OTRS → Google Chat

## Visao geral

Servico Python em arquitetura **hexagonal / DDD**: regras de negocio e contratos ficam isolados da entrega HTTP e do MariaDB. O destino do webhook (`WEBHOOK_URL` no `.env`) pode ser WireMock ou Google Chat Incoming Webhook sem alterar dominio ou application.

```text
OTRS 3.2.1 (TicketCreate)
        |
        v
Perl Event Module (GoogleChatAlert.pm)
        |
        v
CLI otrs-gchat-alert  (presentation/cli)  <-- composition root
        |
        v
ProcessAlertUseCase   (application)
   |            |                |
   v            v                v
Ticket +   DuplicateCheckerPort  NotifierPort
Formatter         |                   |
                  v                   v
        OTRSDatabaseDuplicateChecker  GoogleChatWebhookAdapter
                  |                   |
                  v                   v
              MariaDB            WireMock / Google Chat
```

## Camadas

### Domain (`app/src/domain`)

| Modulo | Papel |
|--------|--------|
| `entities/ticket.py` | `Ticket` imutavel: `ticket_id`, `ticket_number`, `title`, `queue` com validacao |
| `services/alert_message_formatter.py` | Monta payload Google Chat **somente** `{"text": ...}` com link Zoom |

O dominio **nao** loga e **nao** conhece httpx, PyMySQL nem arquivos `.env`.

### Application (`app/src/application`)

| Modulo | Papel |
|--------|--------|
| `ports/notifier.py` | `NotifierPort.send(payload)` |
| `ports/duplicate_checker.py` | `DuplicateCheckerPort.is_duplicate(...)` |
| `use_cases/process_alert.py` | Orquestra dedup opcional → format → send |

`ProcessAlertResult` (`StrEnum`):

- `sent` — alerta despachado
- `skipped_duplicate` — dedup bloqueou o envio (exit CLI `0`)

O use case **nao** loga; a presentation interpreta o resultado.

### Infrastructure (`app/src/infrastructure`)

| Modulo | Papel |
|--------|--------|
| `config/settings.py` | `Settings.from_env()` — le `.env` + ambiente |
| `config/dotenv_loader.py` | Carrega `.env` da raiz (`override=True` em runtime) |
| `adapters/google_chat_webhook.py` | POST JSON via `httpx`; `WebhookDeliveryError` |
| `adapters/otrs_db_duplicate_checker.py` | SQL no MariaDB; fail-open em erro |
| `logging/*` | `log_event`, constantes de evento, redact |

### Presentation (`app/src/presentation`)

| Modulo | Papel |
|--------|--------|
| `cli/main.py` | Composition root: Settings → adapters → use case |
| `logging/*` | Setup root logger (`text` / `json`), silence httpx |

CLI: `--ticket-id`, `--ticket-number`, `--title`, `--queue`.

Exit codes: `0` (sent ou skipped_duplicate), `1` (validacao / config / entrega).

## Deduplicacao

Gate na CLI: instancia `OTRSDatabaseDuplicateChecker` somente se `DEDUP_ENABLED` **e** `Settings.otrs_db_ready()`.

Consulta (simplificada):

- mesmo `title` + mesma fila (`queue.name`)
- `create_time` dentro de `DEDUP_WINDOW_MINUTES`
- exclui o ticket atual (`id <> exclude_ticket_id`)
- estados abertos: `ticket_state_id IN (1, 4)`

Fail-open: qualquer falha de DB gera `alert.dedup.check_failed` (WARNING) e **permite** o envio.

## Contrato do webhook

`POST` JSON em `WEBHOOK_URL`. Corpo:

```json
{
  "text": "*Novo ticket OTRS*\n*Numero:* `20260812000042`\n*ID:* `42`\n*Titulo:* Falha VPN\n*Link:* <https://portal.ilegra.com/otrs/index.pl?Action=AgentTicketZoom;TicketID=42|Acessar Ticket>"
}
```

Sem `cardsV2`. Link Zoom usa `OTRS_BASE_URL`.

## Configuracao (Python)

Carregada por `Settings.from_env()` a partir do `.env` na raiz (e Compose `--env-file .env`).

| Variavel | Default | Obrigatoria |
|----------|---------|-------------|
| `WEBHOOK_URL` | — | sim |
| `HTTP_TIMEOUT_SECONDS` | `10` | nao |
| `LOG_LEVEL` | `INFO` | nao |
| `LOG_FORMAT` | `text` (`text`\|`json`) | nao |
| `LOG_FILE` | vazio | nao |
| `OTRS_BASE_URL` | `https://portal.ilegra.com/otrs/index.pl` | nao |
| `DEDUP_ENABLED` | `false` | nao |
| `DEDUP_WINDOW_MINUTES` | `30` | nao |
| `OTRS_DB_HOST` | vazio | para dedup |
| `OTRS_DB_PORT` | `3306` | nao |
| `OTRS_DB_NAME` | vazio | para dedup |
| `OTRS_DB_USER` | vazio | para dedup |
| `OTRS_DB_PASSWORD` | vazio | para dedup |
| `OTRS_DISABLE_DOTENV` | `false` | testes (desliga `.env`) |

Detalhes Docker: [infra-docker.md](infra-docker.md). Logging: [engineering-logging.md](engineering-logging.md). Eng. Python: [engineering-python.md](engineering-python.md).

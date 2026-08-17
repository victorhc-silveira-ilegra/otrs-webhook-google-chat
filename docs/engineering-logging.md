# Engenharia de logging semantico

## Objetivo

Orquestrar o runtime do alerta com poucos eventos nomeados, sem dump de payload nem URL com segredo.

API: `log_event(logger, level, event, **fields)` em `infrastructure/logging/emit.py`.
Constantes em `infrastructure/logging/events.py`.

## Eventos

| Evento | Nivel | Origem |
|--------|-------|--------|
| `alert.run.started` | INFO | CLI |
| `alert.run.skipped_duplicate` | INFO | CLI |
| `alert.run.skipped_outside_hours` | INFO | CLI |
| `alert.dispatch.claim_failed` | WARNING | `OTRSDatabaseAlertDispatchLedger` (fail-open) |
| `alert.webhook.sent` | INFO | `GoogleChatWebhookAdapter` |
| `alert.webhook.failed` | ERROR | `GoogleChatWebhookAdapter` |
| `alert.run.finished` | INFO | CLI |
| `alert.run.failed` | ERROR | CLI |

Caminhos tipicos:

- Sucesso: `started` → `webhook.sent` → `finished` (3 linhas INFO)
- Skip duplicata: `started` → `skipped_duplicate` (sem webhook / sem `finished`)
- Skip fora da janela comercial: `started` → `skipped_outside_hours` (sem webhook / sem `finished`)
- Fail-open claim: `started` → `dispatch.claim_failed` → `webhook.sent` → `finished`
- Falha entrega: `started` → `webhook.failed` → `run.failed` (claim liberado)

## Variaveis

| Env | Default | Descricao |
|-----|---------|-----------|
| `LOG_LEVEL` | `INFO` | Nivel root |
| `LOG_FORMAT` | `text` | `text` (key=value) ou `json` |
| `LOG_FILE` | vazio | Se definido, tambem grava em arquivo extra |
| `LOG_DIR` | `logs` | Tee de stdout/stderr em `LOG_DIR/otrs-gchat-YYYY-MM-DD.log` (fuso `WINDOW_TIMEZONE`); vazio desliga. No Docker o compose monta `logs/` do host em `/var/log/otrs-gchat`. `make app-clean` remove arquivos em `logs/` que nao sejam o do dia atual nem `.gitkeep` |

Setup: `presentation.logging.setup_logging(...)`.

## Anti-poluicao

- Dominio nao loga.
- Use case nao loga.
- `httpx` / `httpcore` / `urllib3` em `WARNING`.
- Query string de webhook redigida (`redact_webhook_url` → `?***`).
- Campo logado como `webhook_host` (URL sem query secreta).
- `title_preview` truncado (`truncate_preview`, 80 chars).
- `payload_bytes` so em DEBUG no evento `sent`.
- `exc_info` so quando `LOG_LEVEL=DEBUG` em falhas.

## Exemplo (text)

```text
2026-08-12 10:00:00,001 INFO event=alert.run.started ticket_id=42 ticket_number=20260812000042 title_preview=Falha VPN
2026-08-12 10:00:00,050 INFO event=alert.webhook.sent http_status=200 ticket_id=42 webhook_host=https://chat.googleapis.com/v1/spaces/POC/messages?***
2026-08-12 10:00:00,051 INFO event=alert.run.finished status=ok ticket_id=42
```

## Exemplo (skip)

```text
2026-08-12 10:00:00,001 INFO event=alert.run.started ticket_id=42 ticket_number=20260812000042 title_preview=Falha VPN
2026-08-12 10:00:00,010 INFO event=alert.run.skipped_duplicate ticket_id=42 title=Falha VPN queue=Raw
```

## Exemplo (fora da janela comercial)

```text
2026-08-15 10:00:00,001 INFO event=alert.run.started ticket_id=42 ticket_number=20260812000042 title_preview=Falha VPN
2026-08-15 10:00:00,010 INFO event=alert.run.skipped_outside_hours ticket_id=42 title=Falha VPN queue=Raw
```

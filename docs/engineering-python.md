# Engenharia Python

Guia de engenharia do servico `otrs-gchat-alert` (camadas, qualidade, config e runtime).

## Objetivos

- Hexagonal / DDD com cobertura 100%
- Composition root na CLI
- Logging semantico enxuto (ver [engineering-logging.md](engineering-logging.md))
- Config centralizada no `.env` da raiz
- Sem comentarios no codigo de aplicacao

## Fluxo de runtime

1. CLI parseia `--ticket-id`, `--ticket-number`, `--title`, `--queue`
2. `Settings.from_env()` carrega `.env` (salvo `OTRS_DISABLE_DOTENV`)
3. Tee de stdout/stderr para `LOG_DIR` (arquivo do dia), setup de logging (`LOG_LEVEL` / `LOG_FORMAT` / `LOG_FILE`)
4. Emite `alert.run.started`
5. Opcionalmente monta `OTRSDatabaseAlertDispatchLedger`
6. `ProcessAlertUseCase.execute(ticket)`:
   - fora da janela comercial → `skipped_outside_hours` (sem claim / sem webhook)
   - `try_claim` rejeitado → `skipped_duplicate`
   - senao formata texto + `NotifierPort.send` (release do claim se o envio falhar)
7. CLI emite `skipped_outside_hours`, `skipped_duplicate` ou `finished` / `failed`

## Ports e adapters

| Port | Adapter | Notas |
|------|---------|--------|
| `NotifierPort` | `GoogleChatWebhookAdapter` | `httpx`; redact de query no log |
| `AlertDispatchLedgerPort` | `OTRSDatabaseAlertDispatchLedger` | INSERT atomico; IntegrityError = skip; fail-open em erro de conexao |

Ports sao `typing.Protocol` (sem ABC).

## Domain services

`AlertMessageFormatter`:

- entrada: `Ticket` + `otrs_base_url` (via construtor / Settings)
- saida: `{"text": "..."}` apenas
- link: `<{OTRS_BASE_URL}?Action=AgentTicketZoom;TicketID={id}|Acessar Ticket>`

`BusinessHoursWindow`:

- `WINDOW_DAYS` (0=segunda ... 6=domingo via `mon`..`sun`)
- intervalo `[WINDOW_START, WINDOW_END)` no `WINDOW_TIMEZONE`
- desligada quando `WINDOW_ENABLED=false`

## Qualidade

| Comando | O que roda |
|---------|------------|
| `make app-lint` | Ruff, mypy strict, vulture, limite 300 linhas |
| `make app-test` | pytest-xdist + coverage 100% (branch) |
| `make app-security` | bandit + pip-audit |
| `make app-pre-commit-run` | hooks em todos os arquivos |

Orquestrador: `app/scripts/operations/clean_workspace.py` (`--area python|docker|github|scripts` + `--stage`). Detalhes: [devops.md](devops.md).

Convencoes:

- Conventional Commits (`linters/commitlint.config.mjs`)
- Sem emojis em codigo / logs / docs tecnicas
- Sem comentarios no codigo Python de `app/src`

## Testes

```text
app/tests/
├── unit/domain/
├── unit/application/
├── unit/infrastructure/
├── unit/presentation/
└── integration/infrastructure/
```

`conftest.py` define `OTRS_DISABLE_DOTENV=1` para isolar testes do `.env` local.

Fakes/Mocks: `FakeNotifier`, `FakeDispatchLedger`, `httpx` transport, `pymysql.connect` patchado.

## Config e segredos

- `.env` na raiz (gitignored); template em `.env.example`
- Compose: `env_file` de `.env` e opcional (`required: false`) para o CI usar so `.env.example` na interpolacao.
- Compose: `docker compose --env-file .env ...`
- Python: `load_project_dotenv(override=True)` em `Settings.from_env()`
- Nunca commitar `GCHAT_WEBHOOK_URL` real

Tabela completa de variaveis: [arquitetura.md](arquitetura.md#configuracao-python).

## Entry points

| Entrada | Como |
|---------|------|
| CLI instalada | `otrs-gchat-alert ...` (`pyproject` scripts) |
| Repo root | `python run.py ...` / `make app-run` |
| Container `notifier` | mesma CLI no PATH |
| OTRS Event Module | `NOTIFIER_BIN` → CLI com args do ticket |

## Relacionados

- [arquitetura.md](arquitetura.md) — camadas e fluxo
- [structure.md](structure.md) — arvore do repo
- [engineering-logging.md](engineering-logging.md) — eventos
- [infra-docker.md](infra-docker.md) — stack Docker

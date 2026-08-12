# Estrutura do repositorio

Layout operacional da PoC OTRS (`app/`, `infra/`, `linters/`, `docs/`).

```text
.
├── app/
│   ├── src/
│   │   ├── domain/
│   │   │   ├── entities/ticket.py
│   │   │   └── services/alert_message_formatter.py
│   │   ├── application/
│   │   │   ├── ports/
│   │   │   │   ├── notifier.py
│   │   │   │   └── duplicate_checker.py
│   │   │   └── use_cases/process_alert.py
│   │   ├── infrastructure/
│   │   │   ├── adapters/
│   │   │   │   ├── google_chat_webhook.py
│   │   │   │   └── otrs_db_duplicate_checker.py
│   │   │   ├── config/
│   │   │   │   ├── settings.py
│   │   │   │   └── dotenv_loader.py
│   │   │   └── logging/
│   │   │       ├── emit.py
│   │   │       ├── events.py
│   │   │       └── redact.py
│   │   └── presentation/
│   │       ├── cli/main.py
│   │       └── logging/
│   │           ├── config.py
│   │           └── formatters.py
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── domain/
│   │   │   ├── application/
│   │   │   ├── infrastructure/
│   │   │   └── presentation/
│   │   └── integration/
│   ├── scripts/
│   │   ├── setup.sh
│   │   └── operations/clean_workspace.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── requirements-dev.txt
├── docs/
├── infra/docker/
│   ├── docker-compose.yml
│   ├── mariadb/init.sql
│   ├── notifier/
│   ├── otrs/
│   ├── scripts/wait-for-otrs-schema.sh
│   └── wiremock/
├── linters/
├── Makefile
├── AGENTS.md
├── .env.example
└── run.py
```

## Regras de dependencia

- `domain` e `application` **nao** importam `infrastructure` nem `presentation`.
- `infrastructure` e `presentation` dependem de `application` / `domain`.
- `presentation/cli` e o **composition root**: instancia Settings, adapters e o use case.
- Qualidade operacional vive em `app/scripts/operations` (`make app-lint|app-test|app-security`).

## Pacotes Python (imports)

`pythonpath` / editable install apontam para `app/src`. Imports absolutos:

```python
from domain.entities.ticket import Ticket
from application.use_cases.process_alert import ProcessAlertUseCase
from infrastructure.config.settings import Settings
from presentation.cli.main import run
```

Sem prefixo `app.src`.

## Dependencias runtime

| Pacote | Uso |
|--------|-----|
| `httpx` | POST do webhook |
| `PyMySQL` | Dedup no MariaDB |

Lista pinada: `app/requirements.txt` e `app/pyproject.toml` (Docker instala via `pip install .`).

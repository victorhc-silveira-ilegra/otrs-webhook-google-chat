# App package

Codigo-fonte da PoC OTRS → Google Chat (`app/src`).

## Layout

```text
src/
├── domain/           # Ticket, AlertMessageFormatter
├── application/      # ports + ProcessAlertUseCase
├── infrastructure/   # adapters, Settings, logging
└── presentation/     # CLI + setup de logging
```

## Documentacao

| Doc | Conteudo |
|-----|----------|
| [../docs/arquitetura.md](../docs/arquitetura.md) | Arquitetura hexagonal |
| [../docs/engineering-python.md](../docs/engineering-python.md) | Engenharia Python |
| [../docs/engineering-logging.md](../docs/engineering-logging.md) | Logging semantico |
| [../docs/structure.md](../docs/structure.md) | Estrutura do repositorio |
| [../README.md](../README.md) | Setup e comandos |

## Qualidade local

Na raiz do repo:

```bash
make app-lint
make app-test
make app-security
```

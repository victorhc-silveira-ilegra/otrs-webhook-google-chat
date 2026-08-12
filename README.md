# OTRS Webhook Google Chat

PoC de integracao de alertas entre **OTRS 3.2.1** e **Google Chat**, com servico Python em arquitetura hexagonal / DDD, TDD e stack Docker legada (CentOS 7, Apache, Perl 5.16, MariaDB).

Layout operacional com `app/`, `Makefile`, `clean_workspace` e `linters/`.

## Documentacao

| Doc | Conteudo |
|-----|----------|
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Historico de releases (semantic-release) |
| [docs/arquitetura.md](docs/arquitetura.md) | Camadas, ports, dedup, contrato do webhook, env |
| [docs/structure.md](docs/structure.md) | Arvore do repo e regras de dependencia |
| [docs/engineering-python.md](docs/engineering-python.md) | Engenharia do servico Python |
| [docs/engineering-logging.md](docs/engineering-logging.md) | Eventos semanticos e anti-poluicao |
| [docs/infra-docker.md](docs/infra-docker.md) | Compose, schema, Event Module |

## Requisitos

- Python 3.13 (Linux)
- Docker e Docker Compose
- Make
- Git / Node (apenas para commitlint via npx)

## Setup

```bash
cp .env.example .env
# edite WEBHOOK_URL (e demais vars)
make app-setup
```

Ou:

```bash
make app-install
make app-pre-commit
```

Dependencias:

- Runtime: [`app/requirements.txt`](app/requirements.txt) (`httpx`, `PyMySQL`)
- Dev: [`app/requirements-dev.txt`](app/requirements-dev.txt)
- Fora do pip: Node.js (commitlint) e gitleaks (CI)

## Qualidade

```bash
make app-lint
make app-test
make app-security
make app-clean
```

Cobertura minima: 100%. Commits: Conventional Commits (`linters/commitlint.config.mjs`).

## CLI

Configure o `.env` na raiz (carregado automaticamente pelo Python):

```bash
make app-run
```

Ou:

```bash
otrs-gchat-alert --ticket-id 42 --ticket-number 20260812000042 --title "Falha VPN" --queue Raw
```

Args obrigatorios: `--ticket-id`, `--ticket-number`, `--title`, `--queue`.

## Docker

```bash
make docker-up
make docker-smoke
```

Detalhes em [docs/infra-docker.md](docs/infra-docker.md).

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml):

- jobs paralelos: lint, test, security (actions compostas)
- job `release` (semantic-release) apos qualidade em `main`
- tags sincronizadas via `.github/actions/sync-tags`
- changelog em [`docs/CHANGELOG.md`](docs/CHANGELOG.md)

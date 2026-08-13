# OTRS Webhook Google Chat

[![CI](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/actions/workflows/ci.yml/badge.svg)](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/victorhc-silveira-ilegra/otrs-webhook-google-chat?display_name=tag&sort=semver)](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/releases)
[![Python](https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Requires Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fvictorhc-silveira-ilegra%2Fotrs-webhook-google-chat%2Fmain%2Fapp%2Fpyproject.toml)](app/pyproject.toml)

[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](app/pyproject.toml)
[![Ruff](https://img.shields.io/badge/linter-ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![mypy](https://img.shields.io/badge/mypy-strict-blue)](https://mypy-lang.org/)
[![bandit](https://img.shields.io/badge/security-bandit-yellow)](https://bandit.readthedocs.io/)
[![pip-audit](https://img.shields.io/badge/deps-pip--audit-informational)](https://pypi.org/project/pip-audit/)

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow?logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org/)
[![Semantic Release](https://img.shields.io/badge/release-semantic--release-e10079?logo=semantic-release&logoColor=white)](https://semantic-release.gitbook.io/)
[![SemVer](https://img.shields.io/badge/semver-2.0.0-blue)](https://semver.org/)

[![Architecture](https://img.shields.io/badge/architecture-hexagonal%20%2F%20DDD-0A66C2)](docs/arquitetura.md)
[![TDD](https://img.shields.io/badge/tests-TDD%20%2B%20pytest-0A9EDC?logo=pytest&logoColor=white)](docs/engineering-python.md)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker&logoColor=white)](docs/infra-docker.md)
[![OTRS](https://img.shields.io/badge/OTRS-3.2.1-orange)](docs/infra-docker.md)
[![License](https://img.shields.io/badge/license-Proprietary-lightgrey)](app/pyproject.toml)

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

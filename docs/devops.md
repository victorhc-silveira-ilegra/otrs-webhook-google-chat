# DevOps e CI/CD

Pipelines de integracao e release da PoC OTRS → Google Chat.

## Visao do pipeline (push em `main`)

```mermaid
flowchart LR
  subgraph ci [CI paralelo por area]
    PY[Python]
    DK[Docker]
    GH[GitHub]
    SH[Scripts]
  end
  PY --> R[Release]
  DK --> R
  GH --> R
  SH --> R
  R --> S[Resumo]
  PY --> S
```

| Fase | Job | Notas |
|------|-----|-------|
| CI | Python / Docker / GitHub / Scripts | Orquestrador + stages iguais ao pre-commit (`fail_fast`) |
| Release | Semantic release | Apos gates verdes em `main` |
| Resumo | Status no GitHub Summary | Sempre no push `main` |

Sem Kubernetes, Terraform, Azure OIDC ou destroy: a PoC sobe via Compose local (`make docker-up`).

## Workflows

| Workflow | Gatilho | Uso |
|----------|---------|-----|
| [ci.yml](../.github/workflows/ci.yml) | push/PR `main`, manual | CI matriz; release no push `main` |

Documentacao interna de `.github/`: [`.github/workflows.md`](../.github/workflows.md).

## Composite actions

```text
.github/actions/
├── shared/
│   └── pipeline-summary/
└── ci/
    ├── setup-python/
    ├── validate-docker/
    ├── validate-github/
    ├── validate-scripts/
    ├── release/
    └── sync-tags/
```

## Stages crash-first

Em cada categoria (`Python`, `Docker`, `GitHub`, `Scripts`), o orquestrador `app/scripts/operations/clean_workspace.py` executa estritamente os 5 estagios obrigatorios na ordem fixa:

1. `<Categoria> | Lint`
2. `<Categoria> | Seguranca`
3. `<Categoria> | Testes`
4. `<Categoria> | Validate`
5. `<Categoria> | Build`

```bash
python app/scripts/operations/clean_workspace.py --area <python|docker|github|scripts> --stage <lint|security|test|validate|build|clean>
```

| Area | Lint | Seguranca | Testes | Validate | Build |
|------|------|-----------|--------|----------|-------|
| python | Ruff, mypy, vulture, limite 300 | Bandit, pip-audit, Gitleaks (`gitleaks detect --source . --verbose --redact`) | pytest cov 100% | `pip install -e` + import | `python -m build` |
| docker | Hadolint (`infra/docker/.hadolint.yaml`) | Trivy config/fs | `compose config --quiet` (`.env` ou `.env.example`) | arquivos + compose | build da imagem **notifier** |
| github | actionlint | Gitleaks em `.github` + regex | actionlint | estrutura de actions | diretorios ci/shared |
| scripts | `bash -n` + `make -n help` | grep de segredos | `make help` | scripts do Makefile | sintaxe shell |

## Comandos manuais no `Makefile`

Os comandos `make app-*` executam o respectivo estágio em **todas** as categorias (`Python` + `Docker` + `GitHub` + `Scripts`):

| Estagio | Comando | Escopo |
|---------|---------|--------|
| Lint | `make app-lint` | Lint de tudo (`python`, `docker`, `github`, `scripts`) |
| Seguranca | `make app-security` | Seguranca de tudo (`python`, `docker`, `github`, `scripts`) |
| Testes | `make app-test` (`make app-tests`) | Testes de tudo (`python`, `docker`, `github`, `scripts`) |
| Validate | `make app-validate` | Validate de tudo (`python`, `docker`, `github`, `scripts`) |
| Build | `make app-build` | Build de tudo (`python`, `docker`, `github`, `scripts`) |

## Pre-commit

Espelha a matriz CI (sequencial com `fail_fast: true`): `Commitlint (Conventional Commits)` seguido pelas categorias `Python`, `Docker`, `GitHub` e `Scripts` nos 5 estagios `Lint` → `Seguranca` → `Testes` → `Validate` → `Build`. Detalhes: [linters/README.md](../linters/README.md).

## Secrets

| Secret | Uso |
|--------|-----|
| `GITHUB_TOKEN` | Release, sync-tags e Gitleaks (fornecido pelo Actions) |

## Operacao

### Push em `main`

1. CI paralelo por area.
2. Release semantica se todos os gates passarem.
3. Marcador `[skip-cd]` na mensagem do commit: so CI; sem release.
4. `workflow_dispatch` com `skip_cd=true`: so CI.

### Pull request

Somente jobs CI por area (sem release).

## Relacionados

- [engineering-python.md](engineering-python.md)
- [infra-docker.md](infra-docker.md)
- [arquitetura.md](arquitetura.md)

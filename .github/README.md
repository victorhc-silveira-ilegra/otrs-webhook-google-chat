# GitHub Actions

Pipelines de integracao e release da PoC OTRS → Google Chat.

Documentacao completa: [docs/devops.md](../docs/devops.md).

## Visao (push em `main`)

```mermaid
flowchart LR
  subgraph ci [CI paralelo]
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
```

## Composite actions

```text
.github/actions/
├── shared/pipeline-summary/
└── ci/
    ├── setup-python/
    ├── validate-docker/
    ├── validate-github/
    ├── validate-scripts/
    ├── release/
    └── sync-tags/
```

## Secrets

| Secret | Uso |
|--------|-----|
| `GITHUB_TOKEN` | Release e Gitleaks |

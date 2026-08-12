# GitHooks e linters — OTRS Webhook Google Chat

## Pre-commit (Python)

```bash
make app-pre-commit
```

Ou:

```bash
bash linters/git-hooks/install.sh
```

## Commitlint (Node.js, fora do pip)

Requer Node.js + npm. O hook `commit-msg` usa:

```bash
npx --yes -p @commitlint/cli -p @commitlint/config-conventional \
  commitlint --config linters/commitlint.config.mjs --edit
```

Config: [`commitlint.config.mjs`](commitlint.config.mjs)

## CI seguranca (binario, fora do pip)

- **gitleaks** — varredura de secrets no GitHub Actions (action `security`)
- Config do repositorio: [`.gitleaks.toml`](../.gitleaks.toml)

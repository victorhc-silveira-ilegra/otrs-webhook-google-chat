# Skill: pre-commit / quality gates

## Quando usar

Instalar ou executar gates de qualidade.

## Passos

```bash
make app-pre-commit
make app-lint
make app-test
make app-security
make app-pre-commit-run
```

## Sucesso

- Lint/mypy/vulture OK
- Cobertura 100%
- Bandit/pip-audit concluem

# AGENTS.md

Projeto: PoC OTRS 3.2.1 → Google Chat (DDD / Hexagonal).

## Prioridades

1. Preservar camadas em `app/src` (`domain`, `application`, `infrastructure`, `presentation`).
2. Usar `make app-lint|app-test|app-security` (via `clean_workspace.py`) apos mudancas.
3. Nao escrever comentarios no codigo.
4. Manter cobertura 100% e Conventional Commits.
5. Config via `.env` na raiz (`WEBHOOK_URL`, `OTRS_BASE_URL`, `DEDUP_*`, `OTRS_DB_*`).
6. Manter docs em `docs/` alinhadas ao codigo (arquitetura, structure, engineering-*).

## Comandos uteis

```bash
make app-install
make app-lint
make app-test
make docker-up
make docker-smoke
```

## Docs de referencia

- [docs/arquitetura.md](docs/arquitetura.md)
- [docs/engineering-python.md](docs/engineering-python.md)
- [docs/engineering-logging.md](docs/engineering-logging.md)
- [docs/structure.md](docs/structure.md)
- [docs/infra-docker.md](docs/infra-docker.md)

## Fora de escopo

- Hardening de producao do OTRS legado
- Migracao de versao OTRS
- Operacao/SLA de canal Google Chat de producao (PoC pode apontar webhook real via `.env`)

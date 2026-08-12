# Skill: stack Docker OTRS

## Quando usar

Subir ou validar a stack local OTRS 3.2.1 + notifier + MariaDB.

## Passos

```bash
make docker-up
make docker-ps
make docker-smoke
make docker-logs
```

## Sucesso

- Containers healthy/up
- `docker-logs` mostra `OTRS ready` e `notifier ready`
- `docker-smoke` envia via `WEBHOOK_URL` do `.env` e valida idempotencia/race no ledger

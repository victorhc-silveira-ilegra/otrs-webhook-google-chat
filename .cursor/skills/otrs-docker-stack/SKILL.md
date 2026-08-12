# Skill: stack Docker OTRS

## Quando usar

Subir ou validar a stack local OTRS 3.2.1 + notifier + MariaDB.

## Passos

```bash
make docker-up
make docker-ps
make docker-health
make docker-smoke
make docker-logs
make docker-sh
```

## Sucesso

- Containers healthy/up
- `docker-health` OK (OTRS 200, WireMock `/health`, MariaDB ping, CLI notifier)
- `docker-logs` mostra `OTRS ready` e `notifier ready`
- `curl -sI http://localhost:8081/otrs/index.pl` responde `200` ou `302`
- Event Module filtra fila `Raw`
- `docker-smoke` cria tickets reais em `Raw` (`TicketCreate`), envia via `WEBHOOK_URL` do `.env` e valida idempotencia/race no ledger
- `docker-sh` abre bash no servico (`DOCKER_SERVICE=otrs` por padrao)

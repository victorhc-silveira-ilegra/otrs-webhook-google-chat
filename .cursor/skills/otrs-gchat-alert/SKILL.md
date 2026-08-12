# Skill: disparar alerta OTRS → Chat

## Quando usar

Validar o fluxo CLI → use case → webhook mock.

## Passos

```bash
export WEBHOOK_URL=http://localhost:8080/v1/spaces/POC/messages
make app-run
curl -s http://localhost:8080/__admin/requests
```

## Sucesso

- Exit code 0
- WireMock registra POST em `/v1/spaces/POC/messages`

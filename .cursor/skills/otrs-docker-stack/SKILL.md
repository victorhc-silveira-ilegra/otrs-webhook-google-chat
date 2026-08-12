# Skill: stack Docker OTRS

## Quando usar

Subir ou validar a stack local OTRS 3.2.1 + WireMock.

## Passos

```bash
make docker-up
make docker-ps
make docker-smoke
```

## Sucesso

- Containers healthy/up
- Smoke envia alerta e WireMock responde

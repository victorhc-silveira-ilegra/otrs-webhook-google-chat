# Changelog

## [1.3.0](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/compare/v1.2.0...v1.3.0) (2026-08-17)

## Unreleased

- Pre-commit espelha a matriz CI (Python/Docker/GitHub/Scripts + stages crash-first; `fail_fast`; commitlint primeiro).
- CI/CD em matriz por area (Python, Docker, GitHub, Scripts) com stages crash-first e release semantica.
- Nomes de config alinhados ao padrao corporativo: `GCHAT_WEBHOOK_URL` e `WINDOW_*` (sem aliases legados).
- Log diario em `logs/otrs-gchat-YYYY-MM-DD.log` (`LOG_DIR`; tee de stdout/stderr); Docker monta `logs/` no host; `make app-clean` remove logs que nao sejam do dia atual.

## [1.2.0](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/compare/v1.1.1...v1.2.0) (2026-08-12)

## [1.1.1](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/compare/v1.1.0...v1.1.1) (2026-08-12)

## [1.1.0](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/compare/v1.0.0...v1.1.0) (2026-08-12)

## 1.0.0 (2026-08-12)

## 1.0.0 (2026-08-12)

Historico de releases gerado automaticamente pelo semantic-release.

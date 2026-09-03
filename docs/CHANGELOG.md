# Changelog

## [1.3.1](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/compare/v1.3.0...v1.3.1) (2026-09-03)

### Bug Fixes

* pin dependencias do semantic-release no CI ([43e97a3](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/commit/43e97a36b774bcced502b13a8141de3cc6e15ebe))
* torna env_file do Compose opcional no CI ([ca2e407](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/commit/ca2e407ddce121ccc92f8ec3570dbfe325b273a8))

## [1.3.0](https://github.com/victorhc-silveira-ilegra/otrs-webhook-google-chat/compare/v1.2.0...v1.3.0) (2026-08-17)

## Unreleased

- Fix: gate Docker no CI aceita ausencia de `.env` (`env_file` opcional + fallback `.env.example`).
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

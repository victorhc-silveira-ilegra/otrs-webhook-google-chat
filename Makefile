SHELL := /bin/bash
APP_DIR=app
DOCKER_DIR=infra/docker
DOCKER_COMPOSE=docker compose --env-file .env -f $(DOCKER_DIR)/docker-compose.yml --project-directory $(DOCKER_DIR)
DOCKER_LOGS_TAIL ?= 200
DOCKER_LOGS_SERVICES ?= otrs notifier

RESOLVE_PY := $(shell bash linters/git-hooks/bin/resolve_venv_python.sh 2>/dev/null || echo python3)
PYTHON := $(RESOLVE_PY)

GREEN  := \033[1;32m
YELLOW := \033[1;33m
BLUE   := \033[1;34m
CYAN   := \033[1;36m
RED    := \033[1;31m
RESET  := \033[0m

.DEFAULT_GOAL := help

.PHONY: help \
	app-install app-run app-pre-commit app-pre-commit-run app-setup app-clean \
	app-lint app-security app-test app-tests app-validate app-build \
	python-lint python-security python-test python-tests python-validate python-build python-clean \
	docker-lint docker-security docker-test docker-tests docker-validate docker-build \
	docker-up docker-down docker-ps docker-logs docker-sh docker-smoke docker-health docker-restart docker-clean docker-rebuild \
	github-lint github-security github-test github-tests github-validate github-build \
	scripts-lint scripts-security scripts-test scripts-tests scripts-validate scripts-build

help:
	@echo -e "$(BLUE)========================================================================$(RESET)"
	@echo -e "$(GREEN)              OTRS WEBHOOK GOOGLE CHAT - MENU DE AJUDA                  $(RESET)"
	@echo -e "$(BLUE)========================================================================$(RESET)"
	@echo -e "Uso: $(CYAN)make <comando>$(RESET)"
	@echo -e ""
	@echo -e "$(YELLOW)Python:$(RESET) $(PYTHON)"
	@echo -e ""
	@echo -e "$(YELLOW)App (Runtime & Setup):$(RESET)"
	@echo -e "  $(GREEN)app-run$(RESET)            - Executa CLI (requer GCHAT_WEBHOOK_URL)"
	@echo -e "  $(GREEN)app-clean$(RESET)          - Limpa caches e logs antigos"
	@echo -e "  $(GREEN)app-install$(RESET)        - Pip no .venv"
	@echo -e "  $(GREEN)app-setup$(RESET)          - Bootstrap .venv + deps (+ hooks se houver git)"
	@echo -e "  $(GREEN)app-pre-commit$(RESET)     - Instala hooks (matriz CI, fail_fast)"
	@echo -e "  $(GREEN)app-pre-commit-run$(RESET) - Roda hooks em todos os arquivos"
	@echo -e ""
	@echo -e "$(YELLOW)CI/CD - Python (App):$(RESET)"
	@echo -e "  $(GREEN)app-lint$(RESET)           - Python | Lint (ruff/mypy/vulture/300 linhas)"
	@echo -e "  $(GREEN)app-security$(RESET)       - Python | Seguranca (bandit/pip-audit/gitleaks)"
	@echo -e "  $(GREEN)app-test$(RESET)           - Python | Testes + cobertura 100% (ou app-tests)"
	@echo -e "  $(GREEN)app-validate$(RESET)       - Python | Validate (pip install -e + smoke import)"
	@echo -e "  $(GREEN)app-build$(RESET)          - Python | Build (python -m build)"
	@echo -e ""
	@echo -e "$(YELLOW)CI/CD - Docker:$(RESET)"
	@echo -e "  $(GREEN)docker-lint$(RESET)        - Docker | Lint (hadolint)"
	@echo -e "  $(GREEN)docker-security$(RESET)    - Docker | Seguranca (trivy config/fs)"
	@echo -e "  $(GREEN)docker-test$(RESET)        - Docker | Testes (compose config; ou docker-tests)"
	@echo -e "  $(GREEN)docker-validate$(RESET)    - Docker | Validate (arquivos + compose config)"
	@echo -e "  $(GREEN)docker-build$(RESET)       - Docker | Build (imagem otrs-notifier:ci)"
	@echo -e ""
	@echo -e "$(YELLOW)CI/CD - GitHub:$(RESET)"
	@echo -e "  $(GREEN)github-lint$(RESET)        - GitHub | Lint (actionlint)"
	@echo -e "  $(GREEN)github-security$(RESET)    - GitHub | Seguranca (gitleaks + secrets scan)"
	@echo -e "  $(GREEN)github-test$(RESET)        - GitHub | Testes (actionlint; ou github-tests)"
	@echo -e "  $(GREEN)github-validate$(RESET)    - GitHub | Validate (estrutura de actions)"
	@echo -e "  $(GREEN)github-build$(RESET)       - GitHub | Build (diretorios ci/shared/workflows)"
	@echo -e ""
	@echo -e "$(YELLOW)CI/CD - Scripts:$(RESET)"
	@echo -e "  $(GREEN)scripts-lint$(RESET)       - Scripts | Lint (bash -n + make -n help)"
	@echo -e "  $(GREEN)scripts-security$(RESET)   - Scripts | Seguranca (secrets scan)"
	@echo -e "  $(GREEN)scripts-test$(RESET)       - Scripts | Testes (make help; ou scripts-tests)"
	@echo -e "  $(GREEN)scripts-validate$(RESET)   - Scripts | Validate (scripts obrigatorios)"
	@echo -e "  $(GREEN)scripts-build$(RESET)      - Scripts | Build (sintaxe shell)"
	@echo -e ""
	@echo -e "$(YELLOW)Docker (Runtime):$(RESET)"
	@echo -e "  $(GREEN)docker-up$(RESET)          - Sobe OTRS + MariaDB + WireMock + notifier"
	@echo -e "  $(GREEN)docker-smoke$(RESET)       - Smoke via TicketCreate Raw real + .env (idempotencia + race)"
	@echo -e "  $(GREEN)docker-health$(RESET)      - Healthcheck OTRS/WireMock/MariaDB/notifier"
	@echo -e "  $(GREEN)docker-rebuild$(RESET)     - Rebuild das imagens e recria containers"
	@echo -e "  $(GREEN)docker-down$(RESET)        - Para containers (preserva volumes)"
	@echo -e "  $(GREEN)docker-clean$(RESET)       - $(RED)DESTRUTIVO$(RESET): remove containers, redes e volumes"
	@echo -e "  $(GREEN)docker-restart$(RESET)     - Restart da stack"
	@echo -e "  $(GREEN)docker-ps$(RESET)          - Status"
	@echo -e "  $(GREEN)docker-logs$(RESET)        - Logs (DOCKER_SERVICE=... ou DOCKER_LOGS_SERVICES; F=1)"
	@echo -e "  $(GREEN)docker-sh$(RESET)          - Shell /bin/bash no servico (DOCKER_SERVICE=otrs|notifier|mariadb|mock-webhook)"
	@echo -e "$(BLUE)========================================================================$(RESET)"

app-install:
	@test -d .venv || python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r $(APP_DIR)/requirements.txt -r $(APP_DIR)/requirements-dev.txt
	$(PYTHON) -m pip install -e $(APP_DIR)

app-lint python-lint:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area python --stage lint

app-security python-security:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area python --stage security

app-test app-tests python-test python-tests:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area python --stage test

app-validate python-validate:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area python --stage validate

app-build python-build:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area python --stage build

app-clean python-clean:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area python --stage clean

docker-lint:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area docker --stage lint

docker-security:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area docker --stage security

docker-test docker-tests:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area docker --stage test

docker-validate:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area docker --stage validate

docker-build:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area docker --stage build

github-lint:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area github --stage lint

github-security:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area github --stage security

github-test github-tests:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area github --stage test

github-validate:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area github --stage validate

github-build:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area github --stage build

scripts-lint:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area scripts --stage lint

scripts-security:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area scripts --stage security

scripts-test scripts-tests:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area scripts --stage test

scripts-validate:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area scripts --stage validate

scripts-build:
	$(PYTHON) $(APP_DIR)/scripts/operations/clean_workspace.py --area scripts --stage build

app-run:
	$(PYTHON) run.py --ticket-id $${TICKET_ID:-1} --ticket-number $${TICKET_NUMBER:-20260812000001} --title "$${TITLE:-PoC alerta}" --queue "$${QUEUE:-Raw}"

app-pre-commit:
	bash linters/git-hooks/install.sh
	chmod +x linters/git-hooks/bin/resolve_venv_python.sh linters/git-hooks/bin/python linters/git-hooks/bin/pre-commit linters/git-hooks/commitlint.sh linters/git-hooks/commit-msg

app-pre-commit-run:
	$(PYTHON) -m pre_commit run --all-files -c .pre-commit-config.yaml

app-setup:
	bash app/scripts/setup.sh

docker-up:
	@test -f .env || cp .env.example .env
	$(DOCKER_COMPOSE) up -d --build

docker-rebuild:
	@test -f .env || cp .env.example .env
	@echo -e "$(YELLOW)Rebuild das imagens OTRS/notifier e recriacao dos containers$(RESET)"
	$(DOCKER_COMPOSE) build --pull
	$(DOCKER_COMPOSE) up -d --force-recreate --remove-orphans
	@$(DOCKER_COMPOSE) ps

docker-down:
	$(DOCKER_COMPOSE) down

docker-clean:
	@test -f .env || cp .env.example .env
	@echo -e "$(RED)Removendo containers, redes e volumes da stack OTRS$(RESET)"
	$(DOCKER_COMPOSE) down --volumes --remove-orphans
	@$(DOCKER_COMPOSE) ps

docker-restart:
	@test -f .env || cp .env.example .env
	$(DOCKER_COMPOSE) restart

docker-ps:
	$(DOCKER_COMPOSE) ps

docker-logs:
	$(DOCKER_COMPOSE) logs --timestamps --tail=$(DOCKER_LOGS_TAIL) $(if $(F),-f,) $(if $(DOCKER_SERVICE),$(DOCKER_SERVICE),$(DOCKER_LOGS_SERVICES))

docker-sh:
	@echo -e "$(CYAN)Abrindo /bin/bash em '$(or $(DOCKER_SERVICE),otrs)' (DOCKER_SERVICE=otrs|notifier|mariadb|mock-webhook)$(RESET)"
	$(DOCKER_COMPOSE) exec $(or $(DOCKER_SERVICE),otrs) /bin/bash

docker-smoke:
	@bash infra/docker/scripts/docker-smoke.sh

docker-health:
	@bash infra/docker/scripts/docker-health.sh

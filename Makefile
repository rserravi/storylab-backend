# =========================
# StoryLab Backend Makefile
# =========================

# --- Config ---
SHELL := /bin/bash
DC    := docker compose
PY    := poetry run
ALEMBIC := poetry run alembic

# API defaults (mantén en .env si prefieres)
APP_MODULE := app.main:app
HOST := 0.0.0.0
PORT := 8080

# ------------- Ayuda -------------
.PHONY: help
help:
	@echo ""
	@echo "Comandos comunes:"
	@echo "  make setup            - Instalar dependencias (poetry install)"
	@echo "  make dev              - Levantar API local (uvicorn --reload)"
	@echo "  make models           - Descargar modelos (scripts/pull_models.sh)"
	@echo "  make revision m='...' - Alembic autogenerate revision"
	@echo "  make migrate          - Alembic upgrade head"
	@echo "  make up               - Levantar stack Docker (db, ollama, pull, api)"
	@echo "  make down             - Parar stack Docker"
	@echo "  make logs-api         - Logs del servicio api (Docker)"
	@echo "  make ps               - Estado servicios Docker"
	@echo "  make lint             - Lint con ruff"
	@echo "  make fmt              - Formatear con ruff"
	@echo "  make test             - Tests con pytest"
	@echo "  make lock             - Congelar dependencias (poetry lock --no-update)"
	@echo "  make clean-venv       - Borrar .venv local"
	@echo "  make reset-db         - (Peligroso) Drop schema y migrar de cero (Docker)"
	@echo ""

# ------------- Entorno local -------------
.PHONY: setup
setup:
	poetry install

.PHONY: dev
dev:
	$(PY) uvicorn $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

.PHONY: models
models:
	bash scripts/pull_models.sh

# ------------- Migraciones (local) -------------
.PHONY: revision
revision:
ifndef m
	$(error Debes pasar el mensaje de revision: make revision m="init schema")
endif
	$(ALEMBIC) revision --autogenerate -m "$(m)"

.PHONY: migrate
migrate:
	$(ALEMBIC) upgrade head

.PHONY: downgrade-base
downgrade-base:
	$(ALEMBIC) downgrade base

# ------------- Calidad -------------
.PHONY: lint
lint:
	$(PY) ruff check .

.PHONY: fmt
fmt:
	$(PY) ruff format .

.PHONY: test
test:
	$(PY) pytest -q

.PHONY: lock
lock:
	poetry lock --no-update

.PHONY: clean-venv
clean-venv:
	rm -rf .venv

# ------------- Docker Compose -------------
.PHONY: up
up:
	$(DC) up -d db ollama
	@echo "Esperando Ollama..."
	@until curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; do sleep 2; done
	@echo "Pull de modelos (llama3.1:8b, qwen2.5:32b, openhermes)..."
	@$(DC) run --rm ollama bash -lc 'ollama pull llama3.1:8b && ollama pull qwen2.5:32b && ollama pull openhermes'
	$(DC) up -d api
	$(DC) ps

.PHONY: down
down:
	$(DC) down

.PHONY: ps
ps:
	$(DC) ps

.PHONY: logs-api
logs-api:
	$(DC) logs -f api

.PHONY: logs-ollama
logs-ollama:
	$(DC) logs -f ollama

.PHONY: logs-db
logs-db:
	$(DC) logs -f db

# ------------- DB Utils (Docker) -------------
# ATENCIÓN: reset-db borra TODO el esquema 'public' dentro del contenedor 'db'
.PHONY: reset-db
reset-db:
	@read -p "⚠️  Esto vaciará la base de datos. ¿Continuar? (yes/NO) " ans; \
	if [ "$$ans" = "yes" ]; then \
		$(DC) exec -T db psql -U storylab -d storylab -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; \
		$(ALEMBIC) upgrade head; \
	else \
		echo "Cancelado."; \
	fi

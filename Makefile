COMPOSE = docker compose -f infra/docker-compose.yml --env-file infra/.env

-include infra/.env
TEST_DB = $(POSTGRES_DB)_test
POSTGRES_HOST_PORT ?= 5432
REDIS_HOST_PORT ?= 6379

# Tests on the laptop use the test database and Redis of `make up`. Only for these targets:
# Compose takes variables from the shell before infra/.env, so `make up` must not get them.
TEST_TARGETS = test test-unit migration
$(TEST_TARGETS): export JUMBAQ_DATABASE_URL ?= postgresql+asyncpg://jumbaq_app:$(JUMBAQ_APP_PASSWORD)@localhost:$(POSTGRES_HOST_PORT)/$(TEST_DB)
$(TEST_TARGETS): export JUMBAQ_MIGRATION_DATABASE_URL ?= postgresql+asyncpg://jumbaq_owner:$(JUMBAQ_OWNER_PASSWORD)@localhost:$(POSTGRES_HOST_PORT)/$(TEST_DB)
# Redis database 1, so the worker of `make up` (database 0) does not run the tasks of tests.
$(TEST_TARGETS): export JUMBAQ_REDIS_URL ?= redis://localhost:$(REDIS_HOST_PORT)/1

# Number of the next migration file: 0002, 0003, ...
NEXT_REV = $(shell printf '%04d' $$(( $$(ls backend/migrations/versions/*.py | wc -l) + 1 )))

.PHONY: help env up down reset logs ps psql migration test test-unit lint fmt

help:
	@echo "make env        create infra/.env, or add the keys that are new in the example"
	@echo "make up         build and start everything (API on http://localhost:8000)"
	@echo "make down       stop everything (data stays in volumes)"
	@echo "make reset      stop everything and delete the data"
	@echo "make logs       follow the logs"
	@echo "make psql       psql in the dev database as the owner of the tables"
	@echo "make migration m=\"add something\"   new migration from the models"
	@echo "make test       all backend tests (needs make up)"
	@echo "make test-unit  tests that need no services"
	@echo "make lint       ruff, format check and import-linter"
	@echo "make fmt        fix lint and format"

env:
	@test -f infra/.env || cp infra/.env.example infra/.env
	@for key in $$(grep -o '^[A-Z0-9_]*=' infra/.env.example); do \
		grep -q "^$$key" infra/.env || { grep "^$$key" infra/.env.example >> infra/.env; echo "added $$key"; }; \
	done
	@echo "infra/.env is ready"

up: env
	$(COMPOSE) up -d --build --wait

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down --volumes

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

psql:
	$(COMPOSE) exec -e PGPASSWORD=$(JUMBAQ_OWNER_PASSWORD) postgres \
		psql -h localhost -U jumbaq_owner -d $(POSTGRES_DB)

# Compares the models with the test database, which the tests keep at the last migration.
migration:
	@test -n "$(m)" || { echo 'usage: make migration m="add something"'; exit 1; }
	cd backend && uv run alembic upgrade head \
		&& uv run alembic revision --autogenerate --rev-id $(NEXT_REV) -m "$(m)"

# pyproject skips integration tests by default; -m "" runs all of them.
test:
	cd backend && uv run pytest -m ""

test-unit:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run lint-imports

fmt:
	cd backend && uv run ruff check --fix . && uv run ruff format .

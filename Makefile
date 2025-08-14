.PHONY: dev db-up migrate revision downgrade

dev:
\tdocker compose up --build

db-up:
\tdocker compose up -d db

migrate:
\tdocker compose run --rm api poetry run alembic upgrade head

revision:
\tdocker compose run --rm api poetry run alembic revision -m "$(m)" --autogenerate

downgrade:
\tdocker compose run --rm api poetry run alembic downgrade -1

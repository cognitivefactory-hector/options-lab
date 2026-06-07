.PHONY: run up down test lint fmt install

# One-command local run (Docker).
run: up

up:
	docker compose up --build

down:
	docker compose down

# Local (non-Docker) workflow.
install:
	pip install -r requirements-dev.txt

test:
	pytest

lint:
	ruff check .

fmt:
	ruff format .

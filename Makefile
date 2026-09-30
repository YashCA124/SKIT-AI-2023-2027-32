.PHONY: up down logs build config ps validate health wait status backup-db

PYTHON ?= python3
OPS := $(PYTHON) devops/scripts/parkmate_ops.py

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

build:
	docker compose build

config:
	docker compose config -q

ps:
	docker compose ps

validate:
	$(OPS) validate-env

health:
	$(OPS) health

wait:
	$(OPS) wait

status:
	$(OPS) status

backup-db:
	$(OPS) backup-db

.PHONY: up down logs build config ps validate health wait status backup-db lint test ci

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

lint:
	cd frontend && npm run lint
	$(PYTHON) -m compileall -q Backend ml

test:
	cd Backend && PYTHONPATH=. $(PYTHON) -m unittest discover -s tests -v

ci: config lint test
	docker build -t parkmate-backend ./Backend
	docker build -t parkmate-frontend ./frontend
	docker build -t parkmate-celery ./ml
	docker build -t parkmate-redis ./devops/redis

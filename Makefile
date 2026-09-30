.PHONY: up down logs build config ps

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

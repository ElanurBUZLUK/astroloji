COMPOSE_FILE=infra/docker/docker-compose.yml
BACKEND_DIR=backend
PYTHON=python3

.PHONY: help install lint format test docker-up docker-down docker-logs ingest-mock

help:
	@echo "Available targets:"
	@echo "  install      Install backend dependencies"
	@echo "  format       Run code formatters (black, isort)"
	@echo "  lint         Run lint checks (flake8)"
	@echo "  test         Run pytest suite"
	@echo "  docker-up    Start local stack (API + Redis + Qdrant + OpenSearch)"
	@echo "  docker-down  Stop local stack"
	@echo "  docker-logs  Tail API logs from docker-compose"
	@echo "  ingest-mock  Seed search indexes with mock documents"

install:
	cd $(BACKEND_DIR) && pip install -r requirements.txt

format:
	cd $(BACKEND_DIR) && black app tests && isort app tests

lint:
	cd $(BACKEND_DIR) && flake8 app tests

test:
	cd $(BACKEND_DIR) && pytest -q

docker-up:
	docker compose -f $(COMPOSE_FILE) up -d --build

docker-down:
	docker compose -f $(COMPOSE_FILE) down

docker-logs:
	docker compose -f $(COMPOSE_FILE) logs -f api

ingest-mock:
	cd $(BACKEND_DIR) && python -m scripts.ingest_mock_data

COMPOSE_FILE=infra/docker/docker-compose.yml
BACKEND_DIR=backend
PYTHON=python3
EVAL_FILE?=/tmp/rag_eval.jsonl
EVAL_K?=5

.PHONY: help install lint format test docker-up docker-down docker-logs ingest-mock up ingest-qdrant ingest-opensearch eval-hybrid

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
	@echo "  up           Start local stack (root docker-compose.yml)"
	@echo "  ingest-qdrant    Ingest markdown/text corpus into Qdrant"
	@echo "  ingest-opensearch Ingest markdown/text corpus into OpenSearch"
	@echo "  eval-hybrid  Evaluate dense/sparse/hybrid retrieval (configure EVAL_FILE)"

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

up:
	docker compose -f docker-compose.yml up -d --build

ingest-qdrant:
	cd $(BACKEND_DIR) && SEARCH_BACKEND=QDRANT python scripts/ingest_corpus.py --path data

ingest-opensearch:
	cd $(BACKEND_DIR) && SEARCH_BACKEND=OPENSEARCH python scripts/ingest_corpus.py --path data

eval-hybrid:
	cd $(BACKEND_DIR) && python scripts/run_eval_hybrid.py --file $(EVAL_FILE) --k $(EVAL_K) --alpha $${ALPHA:-0.6}

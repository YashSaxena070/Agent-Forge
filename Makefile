# AgentForge Makefile

.PHONY: help install dev test lint format typecheck build docker-build docker-up docker-down migrate clean

# Default target
help:
	@echo "AgentForge - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install       Install all dependencies"
	@echo "  dev           Start development environment"
	@echo "  dev-backend   Start backend only"
	@echo "  dev-frontend  Start frontend only"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run all tests"
	@echo "  test-backend  Run backend tests"
	@echo "  test-frontend Run frontend tests"
	@echo "  test-e2e      Run end-to-end tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          Run linters"
	@echo "  format        Format code"
	@echo "  typecheck     Run type checking"
	@echo ""
	@echo "Database:"
	@echo "  migrate       Run database migrations"
	@echo "  migrate-create Create new migration"
	@echo "  db-reset      Reset database"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build all Docker images"
	@echo "  docker-up     Start all services"
	@echo "  docker-down   Stop all services"
	@echo "  docker-logs   View logs"
	@echo ""
	@echo "Kubernetes:"
	@echo "  k8s-deploy-staging  Deploy to staging"
	@echo "  k8s-deploy-prod     Deploy to production"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean         Clean build artifacts"

# Installation
install:
	pip install --upgrade pip
	pip install -e ".[dev]"
	cd apps/frontend && npm install

# Development
dev:
	docker-compose up -d postgres redis qdrant neo4j kafka temporal minio
	@echo "Waiting for services to be ready..."
	@sleep 10
	cd apps/backend && uvicorn src.main:app --reload & \
	cd apps/frontend && npm run dev

dev-backend:
	docker-compose up -d postgres redis qdrant neo4j kafka temporal minio
	cd apps/backend && uvicorn src.main:app --reload

dev-frontend:
	cd apps/frontend && npm run dev

# Testing
test: test-backend test-frontend

test-backend:
	cd apps/backend && pytest --cov=src --cov-report=term-missing

test-frontend:
	cd apps/frontend && npm run test:coverage

test-e2e:
	cd apps/backend && pytest tests/e2e/ -v

test-integration:
	cd apps/backend && pytest tests/integration/ -v

# Code Quality
lint:
	ruff check .
	cd apps/frontend && npm run lint

format:
	ruff format .
	cd apps/frontend && npm run format

typecheck:
	mypy apps/backend/src
	cd apps/frontend && npm run typecheck

# Database
migrate:
	cd apps/backend && alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	cd apps/backend && alembic revision --autogenerate -m "$$msg"

db-reset:
	cd apps/backend && alembic downgrade base && alembic upgrade head

# Docker
docker-build:
	docker build -t agentforge/backend:latest -f infra/docker/Dockerfile.backend .
	docker build -t agentforge/frontend:latest -f infra/docker/Dockerfile.frontend .
	docker build -t agentforge/worker:latest -f infra/docker/Dockerfile.worker .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down -v

docker-logs:
	docker-compose logs -f

docker-ps:
	docker-compose ps

# Kubernetes
k8s-deploy-staging:
	kubectl apply -k infra/kubernetes/overlays/staging
	kubectl rollout status deployment/agentforge-backend -n agentforge --timeout=300s
	kubectl rollout status deployment/agentforge-frontend -n agentforge --timeout=300s

k8s-deploy-prod:
	kubectl apply -k infra/kubernetes/overlays/production
	kubectl rollout status deployment/agentforge-backend -n agentforge --timeout=300s
	kubectl rollout status deployment/agentforge-frontend -n agentforge --timeout=300s

k8s-logs-backend:
	kubectl logs -f deployment/agentforge-backend -n agentforge

k8s-logs-frontend:
	kubectl logs -f deployment/agentforge-frontend -n agentforge

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/backend/.coverage apps/backend/htmlcov 2>/dev/null || true
	rm -rf apps/frontend/.next apps/frontend/coverage 2>/dev/null || true
	rm -rf .coverage htmlcov 2>/dev/null || true

# Generate secrets
generate-secrets:
	@echo "Generating secure secrets..."
	@echo "SECRET_KEY=$$(openssl rand -hex 32)"
	@echo "JWT_SECRET=$$(openssl rand -hex 32)"
	@echo "POSTGRES_PASSWORD=$$(openssl rand -base64 32)"
	@echo "NEO4J_PASSWORD=$$(openssl rand -base64 32)"
	@echo "MINIO_SECRET_KEY=$$(openssl rand -base64 32)"
	@echo "GRAFANA_PASSWORD=$$(openssl rand -base64 16)"
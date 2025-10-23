# Optimization Planner Makefile
# Provides common development and deployment commands

.PHONY: help install dev test lint format clean build run deploy

# Default target
help:
	@echo "Optimization Planner - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     Install dependencies"
	@echo "  dev         Start development server"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo ""
	@echo "Database:"
	@echo "  db-init     Initialize database"
	@echo "  db-migrate  Run database migrations"
	@echo "  db-upgrade  Upgrade database schema"
	@echo "  db-downgrade Downgrade database schema"
	@echo "  db-reset    Reset database"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build    Build Docker image"
	@echo "  docker-run      Run Docker container"
	@echo "  docker-compose  Start with Docker Compose"
	@echo "  docker-stop     Stop Docker containers"
	@echo ""
	@echo "Deployment:"
	@echo "  build       Build for production"
	@echo "  deploy      Deploy to production"
	@echo "  clean       Clean build artifacts"
	@echo ""
	@echo "Utilities:"
	@echo "  logs        View application logs"
	@echo "  health      Check system health"
	@echo "  admin       Create admin user"

# Development commands
install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-debug:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Testing commands
test:
	pytest tests/ -v

test-unit:
	pytest tests/test_unit/ -v

test-integration:
	pytest tests/test_integration.py -v

test-security:
	pytest tests/test_security.py -v

test-performance:
	pytest tests/test_performance.py -v

test-e2e:
	pytest tests/test_e2e.py -v

test-coverage:
	pytest tests/ --cov=app --cov-report=html --cov-report=xml

# Code quality commands
lint:
	flake8 app/ tests/
	mypy app/
	bandit -r app/
	safety check

format:
	black app/ tests/
	isort app/ tests/

format-check:
	black --check app/ tests/
	isort --check-only app/ tests/

# Database commands
db-init:
	python -c "from app.db.base import engine; from app.db.base_all import Base; Base.metadata.create_all(bind=engine)"

db-migrate:
	alembic revision --autogenerate -m "$(MESSAGE)"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-reset:
	rm -f optimization_planner.db
	make db-init
	make admin

# Docker commands
docker-build:
	docker build -t optimization-planner .

docker-run:
	docker run -p 8000:8000 optimization-planner

docker-compose:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec app bash

# Build commands
build:
	python -m build

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/

# Deployment commands
deploy:
	@echo "Deploying to production..."
	git push origin main
	@echo "Deployment triggered via CI/CD"

deploy-staging:
	@echo "Deploying to staging..."
	git push origin staging
	@echo "Staging deployment triggered"

# Utility commands
logs:
	tail -f logs/app.log

health:
	curl -f http://localhost:8000/health || echo "Service is down"

admin:
	python create_admin_user.py

seed-data:
	python scripts/seed_data.py

backup:
	python scripts/backup.py

restore:
	python scripts/restore.py

# Security commands
security-scan:
	bandit -r app/
	safety check
	semgrep --config=auto app/

vulnerability-scan:
	trivy fs .
	trivy image optimization-planner:latest

# Performance commands
benchmark:
	python scripts/benchmark.py

profile:
	python -m cProfile -o profile.stats app/main.py

# Documentation commands
docs:
	mkdocs serve

docs-build:
	mkdocs build

# Monitoring commands
monitor:
	python scripts/monitor.py

metrics:
	curl http://localhost:8000/metrics

# Backup and restore
backup-db:
	python scripts/backup_database.py

restore-db:
	python scripts/restore_database.py

# Development setup
setup-dev:
	make install
	make db-init
	make admin
	@echo "Development environment setup complete!"

setup-test:
	make install
	pip install pytest pytest-asyncio pytest-cov
	@echo "Test environment setup complete!"

# Production setup
setup-prod:
	make install
	make db-migrate
	@echo "Production environment setup complete!"

# CI/CD commands
ci-test:
	make lint
	make test-coverage
	make security-scan

ci-build:
	make clean
	make build
	make docker-build

# Maintenance commands
maintenance-on:
	@echo "MAINTENANCE_MODE=true" > .env.maintenance
	@echo "Maintenance mode enabled"

maintenance-off:
	rm -f .env.maintenance
	@echo "Maintenance mode disabled"

# Database maintenance
db-backup:
	make backup-db

db-optimize:
	python scripts/optimize_database.py

# Cache management
cache-clear:
	python scripts/clear_cache.py

cache-warm:
	python scripts/warm_cache.py

# Log management
log-rotate:
	python scripts/rotate_logs.py

log-clean:
	find logs/ -name "*.log.*" -mtime +30 -delete

# System monitoring
system-status:
	@echo "=== System Status ==="
	@echo "Database: $$(curl -s http://localhost:8000/health | jq -r '.services.api // "Unknown"')"
	@echo "Redis: $$(curl -s http://localhost:8000/health | jq -r '.services.redis // "Unknown"')"
	@echo "API: $$(curl -s http://localhost:8000/health | jq -r '.services.api // "Unknown"')"

# Quick development workflow
quick-start:
	make install
	make dev

quick-test:
	make format
	make lint
	make test

quick-deploy:
	make ci-test
	make deploy

# Environment management
env-dev:
	cp env.example .env
	@echo "Development environment file created"

env-prod:
	cp env.example .env.prod
	@echo "Production environment file created"

# Database seeding
seed-dev:
	python scripts/seed_development_data.py

seed-test:
	python scripts/seed_test_data.py

# API testing
api-test:
	python scripts/test_api.py

api-docs:
	@echo "API Documentation available at: http://localhost:8000/docs"

# Load testing
load-test:
	locust -f scripts/load_test.py --host=http://localhost:8000

# Performance testing
perf-test:
	python scripts/performance_test.py

# Integration testing
integration-test:
	python scripts/integration_test.py

# End-to-end testing
e2e-test:
	python scripts/e2e_test.py

# All tests
test-all:
	make test-unit
	make test-integration
	make test-security
	make test-performance
	make test-e2e

# Full CI pipeline
ci-full:
	make clean
	make install
	make format-check
	make lint
	make test-all
	make security-scan
	make docker-build
	@echo "Full CI pipeline completed successfully!"

# Development helpers
watch-logs:
	tail -f logs/app.log | grep -E "(ERROR|WARN|INFO)"

watch-requests:
	tail -f logs/app.log | grep -E "(GET|POST|PUT|DELETE)"

watch-errors:
	tail -f logs/app.log | grep ERROR

# Quick fixes
fix-imports:
	isort app/ tests/
	@echo "Imports fixed"

fix-format:
	black app/ tests/
	@echo "Code formatted"

fix-lint:
	autopep8 --in-place --recursive app/ tests/
	@echo "Linting issues fixed"

# Git helpers
git-hooks:
	cp scripts/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Git hooks installed"

# Release commands
release-patch:
	@echo "Releasing patch version..."
	bumpversion patch
	git push --tags

release-minor:
	@echo "Releasing minor version..."
	bumpversion minor
	git push --tags

release-major:
	@echo "Releasing major version..."
	bumpversion major
	git push --tags

# Help for specific commands
help-dev:
	@echo "Development Commands:"
	@echo "  make dev          - Start development server"
	@echo "  make dev-debug    - Start development server with debug logging"
	@echo "  make watch-logs   - Watch application logs"
	@echo "  make watch-errors - Watch error logs only"

help-test:
	@echo "Testing Commands:"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-e2e     - Run end-to-end tests"
	@echo "  make test-coverage - Run tests with coverage report"

help-db:
	@echo "Database Commands:"
	@echo "  make db-init      - Initialize database"
	@echo "  make db-migrate   - Create new migration"
	@echo "  make db-upgrade   - Apply migrations"
	@echo "  make db-reset     - Reset database completely"

help-docker:
	@echo "Docker Commands:"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo "  make docker-compose - Start with Docker Compose"
	@echo "  make docker-logs    - View Docker logs"

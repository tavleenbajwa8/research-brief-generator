.PHONY: help install install-dev test test-cov lint format clean run run-dev build docker-build docker-run

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with Black and isort"
	@echo "  clean        - Clean up generated files"
	@echo "  run          - Run the FastAPI server"
	@echo "  run-dev      - Run the FastAPI server in development mode"
	@echo "  build        - Build the package"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e .[dev]

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 app/ tests/ cli.py --max-line-length=88 --extend-ignore=E203,W503
	mypy app/ --ignore-missing-imports
	bandit -r app/ -f json -o bandit-report.json || true

format:
	black app/ tests/ cli.py
	isort app/ tests/ cli.py

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f bandit-report.json

# Running the application
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Building
build:
	python setup.py sdist bdist_wheel

# Docker commands
docker-build:
	docker build -t research-brief-generator .

docker-run:
	docker run -p 8000:8000 --env-file .env research-brief-generator

# CLI commands
cli-help:
	python cli.py --help

cli-generate:
	python cli.py generate --help

cli-interactive:
	python cli.py interactive

# Database commands
db-init:
	python -c "from app.database import db_manager; print('Database initialized')"

# Health check
health:
	python cli.py health

# Development workflow
dev-setup: install-dev
	cp env.example .env
	@echo "Development environment setup complete!"
	@echo "Please edit .env with your API keys and configuration."

dev-test: format lint test

# CI/CD simulation
ci: install-dev lint test-cov

# Documentation
docs-serve:
	@echo "Starting documentation server..."
	@echo "Visit http://localhost:8000/docs for API documentation"
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# Performance testing
benchmark:
	python -m pytest tests/ -v --benchmark-only

# Security checks
security:
	bandit -r app/ -f json -o bandit-report.json
	safety check

# Environment management
venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  source venv/bin/activate  # Linux/Mac"
	@echo "  venv\\Scripts\\activate     # Windows"

# Quick start
quickstart: venv
	@echo "Activating virtual environment..."
	@echo "source venv/bin/activate && make install-dev"
	@echo "cp env.example .env"
	@echo "Edit .env with your API keys"
	@echo "make run-dev" 
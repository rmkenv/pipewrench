
.PHONY: help install dev test lint format clean docker-build docker-up docker-down

help:
	@echo "Pipewrench - Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make dev          - Run development server"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean temporary files"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"

install:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt

dev:
	. venv/bin/activate && python main.py

test:
	. venv/bin/activate && pytest test_main.py -v

lint:
	. venv/bin/activate && flake8 . --exclude=venv --max-line-length=120
	. venv/bin/activate && mypy . --exclude venv --ignore-missing-imports

format:
	. venv/bin/activate && black . --exclude venv

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

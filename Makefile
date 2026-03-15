.PHONY: help setup dev down clean test lint format

help:
	@echo "OBELISK Development Commands"
	@echo "============================"
	@echo "make setup   - Initial setup"
	@echo "make dev     - Start development environment"
	@echo "make down    - Stop all services"
	@echo "make clean   - Clean all containers and volumes"
	@echo "make test    - Run tests"
	@echo "make lint    - Run linters"
	@echo "make format  - Format code"

setup:
	@echo "Setting up OBELISK..."
	cd backend && python -m venv venv
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	@echo "Setup complete!"

dev:
	docker-compose up

down:
	docker-compose down

clean:
	docker-compose down -v
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

test:
	cd backend && pytest

lint:
	cd backend && flake8 app/
	cd frontend && npm run lint

format:
	cd backend && black app/
	cd frontend && npm run format

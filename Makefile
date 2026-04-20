.PHONY: help setup dev down clean test lint format datasets datasets-quick datasets-offline \
	load-validate benchmark-analyze ml-gates ml-version ml-pipeline adversarial-check adversarial-compare

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
	@echo "make datasets-quick - Build a small local ML dataset bundle"
	@echo "make datasets - Build a larger ML dataset bundle"
	@echo "make datasets-offline - Rebuild processed files from local raw cache"
	@echo "make load-validate - Run backend concurrency/load validation"
	@echo "make benchmark-analyze - Benchmark /api/packages/analyze latency"
	@echo "make ml-gates - Enforce ML acceptance thresholds"
	@echo "make ml-version - Create versioned artifact manifest"
	@echo "make ml-pipeline - Run train/eval/gate/version ML pipeline"
	@echo "make adversarial-check - Run synthetic adversarial suite with pass/fail gates"
	@echo "make adversarial-compare - Run suite and compare against baseline report"

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

datasets-quick:
	python3 backend/ml_models/datasets/collect_and_prepare.py \
		--max-npm-malicious 20 --max-npm-benign 20 \
		--max-pypi-malicious 20 --max-pypi-benign 20 \
		--synthetic-code-samples 200

datasets:
	python3 backend/ml_models/datasets/collect_and_prepare.py

datasets-offline:
	python3 backend/ml_models/datasets/collect_and_prepare.py --offline-only

load-validate:
	cd backend && .venv311/bin/python scripts/load_validate.py --enforce

benchmark-analyze:
	cd backend && .venv311/bin/python scripts/benchmark_analyze.py --mode live

ml-gates:
	python3 backend/ml_models/train/check_model_gates.py

ml-version:
	python3 backend/ml_models/train/version_artifacts.py

ml-pipeline:
	python3 backend/ml_models/train/run_pipeline.py

adversarial-check:
	backend/.venv311/bin/python scripts/adversarial_suite.py \
		--require-docker-sandbox \
		--output reports/adversarial/latest.json \
		--enforce

adversarial-compare:
	@if [ -z "$(BASELINE)" ]; then \
		echo "Usage: make adversarial-compare BASELINE=reports/adversarial/before.json"; \
		exit 1; \
	fi
	backend/.venv311/bin/python scripts/adversarial_suite.py \
		--require-docker-sandbox \
		--baseline $(BASELINE) \
		--output reports/adversarial/after.json \
		--enforce

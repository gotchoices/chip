# CHIP Reproduction Makefile

# Use python3 by default (macOS), override with: make PYTHON=python ...
PYTHON ?= python3

.PHONY: help setup install run dry-run clean test lint format

help:
	@echo "CHIP Reproduction Pipeline"
	@echo ""
	@echo "Usage:"
	@echo "  make setup      Create venv and install dependencies (run first)"
	@echo "  make run        Run the full reproduction pipeline"
	@echo "  make dry-run    Validate config without fetching data"
	@echo "  make clean      Remove generated files"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linting"
	@echo ""
	@echo "If 'python3' isn't right for your system:"
	@echo "  make PYTHON=python setup"

# Create venv and install - run this first
setup:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	@echo ""
	@echo "✅ Setup complete. Now run:"
	@echo "   source .venv/bin/activate"
	@echo "   make run"
	@echo ""
	@echo "Don't forget to set up secrets:"
	@echo "   cp ../secrets.example.toml ../secrets.toml"
	@echo "   # Edit ../secrets.toml with your FRED API key"

# For manual install (assumes venv is already activated)
install:
	pip install -e ".[dev]"

run:
	@if [ -f .venv/bin/python ]; then \
		.venv/bin/python -m chip_repro.main; \
	else \
		python -m chip_repro.main; \
	fi

dry-run:
	@if [ -f .venv/bin/python ]; then \
		.venv/bin/python -m chip_repro.main --dry-run; \
	else \
		python -m chip_repro.main --dry-run; \
	fi

clean:
	rm -rf output/logs/*
	rm -rf output/intermediate/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

test:
	@if [ -f .venv/bin/pytest ]; then .venv/bin/pytest; else pytest; fi

lint:
	@if [ -f .venv/bin/ruff ]; then \
		.venv/bin/ruff check . && .venv/bin/black --check .; \
	else \
		ruff check . && black --check .; \
	fi

format:
	@if [ -f .venv/bin/black ]; then \
		.venv/bin/black . && .venv/bin/ruff check --fix .; \
	else \
		black . && ruff check --fix .; \
	fi

# CHIP Workbench Makefile
# Common commands for development and analysis

# Use python3 by default, can override with: make PYTHON=python run
PYTHON ?= python3
VENV = .venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip

.PHONY: help setup run clean test lint format

help:
	@echo "CHIP Workbench Commands:"
	@echo ""
	@echo "  make setup     - Create virtual environment and install dependencies"
	@echo "  make clean     - Remove generated files (keeps cache)"
	@echo "  make realclean - Remove everything including cache"
	@echo ""
	@echo "Scripts:"
	@echo "  make coverage  - Run data coverage analysis"
	@echo "  make nominal   - Test nominal vs deflated CHIP"
	@echo "  make timeseries - Run time series analysis"
	@echo "  make compare   - Compare aggregation methods"
	@echo ""
	@echo "Development:"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Check code style"
	@echo "  make format    - Auto-format code"

# Setup virtual environment
setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e ".[dev]"
	@echo ""
	@echo "Setup complete. Activate with: source $(VENV)/bin/activate"

# Run scripts
coverage:
	$(VENV_PYTHON) scripts/analyze_data_coverage.py

nominal:
	$(VENV_PYTHON) scripts/test_nominal_chip.py

timeseries:
	$(VENV_PYTHON) scripts/chip_time_series.py

compare:
	$(VENV_PYTHON) scripts/compare_aggregators.py

# Cleaning
clean:
	rm -rf output/
	rm -rf __pycache__ lib/__pycache__ scripts/__pycache__
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

realclean: clean
	rm -rf data/
	rm -rf $(VENV)

# Development
test:
	$(VENV_PYTHON) -m pytest tests/ -v

lint:
	$(VENV_PYTHON) -m ruff check lib/ scripts/

format:
	$(VENV_PYTHON) -m black lib/ scripts/
	$(VENV_PYTHON) -m ruff check --fix lib/ scripts/

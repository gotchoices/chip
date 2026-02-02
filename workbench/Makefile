# CHIP Workbench Makefile
# Maintenance and development tasks only
# For running scripts, use: ./run.sh

PYTHON ?= python3
VENV = .venv
VENV_PYTHON = $(VENV)/bin/python
VENV_PIP = $(VENV)/bin/pip

.PHONY: help setup clean realclean distclean test lint format

help:
	@echo "Workbench Maintenance Commands:"
	@echo ""
	@echo "  make setup     - Create virtual environment and install dependencies"
	@echo "  make clean     - Remove output files (keeps cache and venv)"
	@echo "  make realclean - Remove output and cache (keeps venv)"
	@echo "  make distclean - Remove everything including venv"
	@echo ""
	@echo "Development:"
	@echo "  make test      - Run tests"
	@echo "  make lint      - Check code style"
	@echo "  make format    - Auto-format code"
	@echo ""
	@echo "For running scripts:"
	@echo "  ./run.sh --help"

# Setup
setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -e ".[dev]"
	@echo ""
	@echo "Setup complete!"
	@echo ""
	@echo "Run scripts with:"
	@echo "  ./run.sh coverage       # Run coverage analysis"
	@echo "  ./run.sh coverage -v    # Run and view report"
	@echo "  ./run.sh --list         # List all scripts"
	@echo "  ./run.sh --help         # Show all options"

# Cleaning
clean:
	rm -rf output/logs output/summaries output/reports
	rm -rf __pycache__ lib/__pycache__ scripts/__pycache__
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

realclean: clean
	rm -rf data/

distclean: realclean
	rm -rf $(VENV)

# Development
test:
	$(VENV_PYTHON) -m pytest tests/ -v

lint:
	$(VENV_PYTHON) -m ruff check lib/ scripts/

format:
	$(VENV_PYTHON) -m black lib/ scripts/
	$(VENV_PYTHON) -m ruff check --fix lib/ scripts/

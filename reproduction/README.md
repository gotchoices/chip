# CHIP Valuation Reproduction

Python reproduction of the original CHIP valuation study.

## Goal

Reproduce the original $2.53/hour result using:
- The same data sources (ILOSTAT, PWT 10.0, FRED)
- The same methodology (Cobb-Douglas, distortion factor, GDP weighting)
- The same date range and country exclusions

Success = matching the original result within reasonable tolerance (~5%).

## Setup

```bash
# From the reproduction/ folder:
cd reproduction/

# Option A: Use make (recommended)
make setup                 # Creates venv and installs deps
source .venv/bin/activate
cp ../secrets.example.toml ../secrets.toml
# Edit ../secrets.toml and add your FRED API key

# Option B: Manual setup
python3 -m venv .venv      # Use python3 on macOS
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp ../secrets.example.toml ../secrets.toml
# Edit ../secrets.toml and add your FRED API key
```

Note: Secrets are stored at the project root (`../secrets.toml`) so they can be shared across subprojects.

## Usage

```bash
# Option A: Use make (recommended)
make run

# Option B: Use the installed command
chip-reproduce

# Option C: Use Python module directly
python -m chip_repro.main

# Validate config without fetching data
make dry-run
```

## Structure

```
reproduction/
├── Makefile             # Build commands
├── pyproject.toml       # Python dependencies
├── config.yaml          # Study parameters (dates, exclusions, etc.)
├── chip_repro/          # Python package
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── logging_config.py
│   └── pipeline/
│       ├── __init__.py
│       ├── fetch.py     # Data fetching from APIs
│       ├── clean.py     # Data cleaning and merging
│       ├── estimate.py  # Cobb-Douglas estimation
│       └── aggregate.py # Global aggregation
├── output/              # Results (gitignored except reports)
│   ├── logs/
│   └── reports/
└── tests/
```

## Configuration

See `config.yaml` for all parameters including:
- Date range (1992-2019 for original study)
- Country exclusions
- Outlier treatment
- Weighting scheme

## Logging

All pipeline steps are logged to `output/logs/`. Summary report generated at `output/reports/`.

## Output

After a successful run:
- `output/reports/report_YYYYMMDD_HHMMSS.md` - Human-readable summary
- `output/reports/report_YYYYMMDD_HHMMSS.json` - Machine-readable results
- `output/logs/chip_YYYYMMDD_HHMMSS.log` - Full log file

If `save_intermediate: true` in config:
- `output/intermediate/clean_data_*.csv` - Merged and cleaned dataset
- `output/intermediate/mpl_data_*.csv` - MPL and distortion factors

## Data Flow

```
ILOSTAT (wages) ─┐
                 │
PWT (capital,   ─┼── DataFetcher ── DataCleaner ── Estimator ── Aggregator ── Report
    output)      │
                 │
FRED (deflator) ─┘
```

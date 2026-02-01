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

All parameters are in `config.yaml`. Here are the key "knobs":

### Data Source (`data_source`)

Controls where data comes from:

| Value | Behavior |
|-------|----------|
| `"original"` | Use local files from original study (for strict reproduction) |
| `"api"` | Always fetch fresh data from APIs (ignore cache) |
| `"cache"` | Use cache if available, otherwise fetch (default) |

```yaml
data_source: "original"  # For reproduction: $2.56
data_source: "api"       # For fresh estimates
```

### Date Range (`dates`)

```yaml
dates:
  start_year: 1992    # First year to include
  end_year: 2019      # Last year to include (extend to 2025 for recent data)
  deflator_base_year: 2017  # Base year for real wage calculation
```

### Time Weighting (`aggregation.time_weighting`)

How to aggregate multi-year data to country averages:

| Value | Behavior |
|-------|----------|
| `"all_years"` | Simple average (original methodology) |
| `"recent_only"` | Use only the most recent year per country |
| `"rolling"` | Use only last N years (see `rolling_window_years`) |
| `"exponential"` | Weight by recency with decay (see `half_life_years`) |

```yaml
aggregation:
  time_weighting: "all_years"     # Original methodology
  rolling_window_years: 5         # For "rolling" mode
  half_life_years: 3              # For "exponential" mode
```

### Global Weighting (`aggregation.primary_weight`)

How to aggregate countries to global CHIP:

| Value | Behavior |
|-------|----------|
| `"gdp"` | Weight by GDP (original methodology) |
| `"labor"` | Weight by labor force size |
| `"unweighted"` | Equal weight per country |

### Country Exclusions (`exclusions`)

```yaml
exclusions:
  countries:           # Exclude entire countries
    - "Cambodia"
  country_years:       # Exclude specific observations
    - country: "Albania"
      year: 2012
```

### Output Options (`output`)

```yaml
output:
  log_level: "INFO"          # DEBUG, INFO, WARNING, ERROR
  save_intermediate: true    # Save CSV files for inspection
```

## Example Configurations

**Strict reproduction of original study:**
```yaml
data_source: "original"
dates:
  start_year: 1992
  end_year: 2019
aggregation:
  time_weighting: "all_years"
  primary_weight: "gdp"
```

**Fresh estimate with recent data:**
```yaml
data_source: "api"
dates:
  start_year: 2015
  end_year: 2025
aggregation:
  time_weighting: "rolling"
  rolling_window_years: 5
  primary_weight: "gdp"
```

## Logging

All pipeline steps are logged to `output/logs/`. Summary report generated at `output/reports/`.

## Output

After a successful run:

| File | Contents |
|------|----------|
| `output/reports/report_*.md` | Human-readable summary |
| `output/reports/report_*.json` | Machine-readable results |
| `output/reports/country_summary_*.csv` | Per-country CHIP values |
| `output/logs/chip_*.log` | Full pipeline log |

If `save_intermediate: true`:

| File | Contents |
|------|----------|
| `output/intermediate/clean_data_*.csv` | Merged and cleaned dataset |
| `output/intermediate/mpl_data_*.csv` | MPL, distortion factors, adjusted wages |

## Expected Results

| Configuration | CHIP Value | Notes |
|---------------|------------|-------|
| `data_source: "original"` | ~$2.56 | Matches original study |
| `data_source: "api"` (current) | ~$1.19 | Fresh data, different coverage |

The difference is expected — statistical agencies revise historical data, so "Italy 2010" 
downloaded in 2022 ≠ "Italy 2010" downloaded in 2026.

## Data Flow

```
ILOSTAT (wages) ─┐
                 │
PWT (capital,   ─┼── DataFetcher ── DataCleaner ── Estimator ── Aggregator ── Report
    output)      │
                 │
FRED (deflator) ─┘
```

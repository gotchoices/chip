# CHIP Workbench

Exploratory analysis environment for CHIP estimation research.

---

## Purpose

The workbench provides a modular, flexible environment for:

- **Data exploration**: Analyze data coverage, quality, and consistency
- **Hypothesis testing**: Test theories from research papers
- **Method comparison**: Compare different estimation approaches
- **Sensitivity analysis**: Understand how assumptions affect results

This is the "laboratory" where ideas are tested before becoming official estimators.

---

## Design Philosophy

### Independence

Workbench is **completely independent** of `reproduction/`. While it was informed by that codebase, workbench:

- Has its own rewritten library modules
- Can evolve freely without breaking reproduction
- Maintains its own data cache

### Modularity

The library is designed for composition:

```python
from lib import fetcher, clean, models, aggregate

# Fetch data (auto-caches)
data = fetcher.get_all()

# Clean with custom settings
cleaned = clean.exclude_countries(data["wages"], ["Nepal", "Pakistan"])
cleaned = clean.filter_unskilled(cleaned)

# Estimate with chosen model
result = models.cobb_douglas(cleaned)

# Aggregate with chosen method
chip = aggregate.gdp_weighted(result.chip_by_country)
```

### Self-Healing Cache

The data cache automatically rebuilds when deleted:

```bash
rm -rf data/          # Delete cache
./run.sh coverage     # Runs fine - data auto-fetched
```

### Other Projects Can Import

Future projects (like `estimates/`) should call workbench modules rather than duplicating code:

```python
# From estimates/estimate_chip.py
from workbench.lib import fetcher, models, aggregate

data = fetcher.get_all()  # Uses workbench's cache
```

---

## Quick Start

```bash
# Setup
cd workbench
make setup

# Run an analysis
./run.sh coverage

# Run and view report (requires glow, mdcat, or similar)
./run.sh coverage -v

# View last report
./run.sh --view coverage

# List available scripts
./run.sh --list
```

No need to activate the virtual environment — `run.sh` handles it.

---

## Project Structure

```
workbench/
├── lib/                   # Reusable modules
│   ├── __init__.py        # Package exports
│   ├── fetcher.py         # Data retrieval + caching
│   ├── cache.py           # Cache management
│   ├── normalize.py       # Column standardization
│   ├── clean.py           # Data cleaning utilities
│   ├── models.py          # Estimation models
│   ├── aggregate.py       # Weighting schemes
│   ├── output.py          # Report generation
│   ├── config.py          # Configuration management
│   └── logging_config.py  # Structured logging
│
├── scripts/               # Analysis scripts
│   ├── coverage.py        # Data coverage analysis
│   ├── nominal.py         # Nominal vs deflated CHIP
│   ├── timeseries.py      # CHIP over time
│   └── compare.py         # Aggregation method comparison
│
├── data/                  # Cache (gitignored)
│   └── cache/
│
├── output/                # Results (gitignored)
│   ├── reports/           # Markdown analysis reports
│   ├── logs/              # Timestamped execution logs
│   └── summaries/         # JSON summaries of each run
│
├── config.yaml            # Configuration
├── pyproject.toml         # Dependencies
├── Makefile               # Maintenance tasks (setup, clean, lint)
├── run.sh                 # Script runner (use this for analysis)
└── README.md              # This file
```

---

## The Runner (`run.sh`)

All scripts are executed through `run.sh`, which handles:

- Virtual environment activation
- Running the script
- Optionally viewing the generated report

**Usage:**

```bash
./run.sh <script>              # Run script, save report
./run.sh <script> -v           # Run and view report
./run.sh --view <script>       # View last report for script
./run.sh --view <path>         # View specific report file
./run.sh --list                # List available scripts
```

**Viewer detection:** Automatically uses `glow` → `mdcat` → `bat` → `cat` (first available).

**Output:**
- Progress goes to stdout (brief status updates)
- Full analysis goes to `output/reports/<script>_<timestamp>.md`
- Execution log goes to `output/logs/<script>_<timestamp>.log`
- Summary JSON goes to `output/summaries/<script>_<timestamp>.json`

---

## Library Modules

### `fetcher.py` — Data Retrieval

Fetches data from external sources with automatic caching.

```python
from lib import fetcher

# Individual datasets
employment = fetcher.get_employment()
wages = fetcher.get_wages()
pwt = fetcher.get_pwt()
deflator = fetcher.get_deflator()

# All at once
data = fetcher.get_all()

# Force refresh
data = fetcher.refresh_all()
```

**Sources:**
| Dataset | Source | Notes |
|---------|--------|-------|
| Employment | ILOSTAT | By occupation |
| Wages | ILOSTAT | Monthly, by occupation |
| Hours | ILOSTAT | Hours worked |
| PWT | Penn World Tables 10.0 | GDP, capital, labor share |
| Deflator | FRED | US GDP deflator |
| Freedom Index | Heritage/Fraser | Planned |

### `cache.py` — Cache Management

Low-level cache operations (usually called by fetcher).

```python
from lib import cache

cache.is_cached("pwt")           # Check if cached
cache.get_metadata("pwt")        # Get fetch timestamp
cache.invalidate("pwt")          # Clear specific dataset
cache.invalidate()               # Clear all
cache.list_cached()              # List cached datasets
```

### `normalize.py` — Column Standardization

Converts raw data to consistent column names.

```python
from lib import normalize

# Auto-detects format and standardizes
emp = normalize.normalize_ilostat(raw_data, "employment")
pwt = normalize.normalize_pwt(raw_pwt)
defl = normalize.normalize_deflator(raw_defl, base_year=2017)

# Check format
fmt = normalize.detect_format(df)  # "ilostat_api", "ilostat_csv", etc.
```

### `clean.py` — Data Cleaning

Filtering, harmonization, and preprocessing.

```python
from lib import clean

# Country handling
df = clean.harmonize_countries(df)           # Standardize names
df = clean.exclude_countries(df, ["Nepal"])  # Remove specific countries
coverage = clean.get_country_coverage(df)    # Analyze coverage

# Occupation handling
df = clean.filter_unskilled(df)              # Keep only elementary occupations
df = clean.classify_skill_level(df)          # Add skill_level column

# Data quality
df = clean.filter_outliers(df, "wage")       # Remove statistical outliers
df = clean.require_complete(df, ["wage", "gdp"])  # Require non-null
df = clean.filter_years(df, 2010, 2020)      # Year range

# Merging
merged = clean.merge_datasets(emp, wages, hours, pwt)
```

### `models.py` — Estimation Models

Economic models for CHIP estimation.

```python
from lib import models

# Cobb-Douglas (original study method)
result = models.cobb_douglas(df, estimate_alpha=True)

# Direct wage averaging (simpler alternative)
result = models.direct_wage(df, use_ppp=True)

# Result contains:
#   result.chip_by_country  - DataFrame of country estimates
#   result.parameters       - Model parameters used
#   result.diagnostics      - Fit statistics
#   result.model_name       - "cobb_douglas", "direct_wage", etc.
```

**Available models:**
| Model | Description | Status |
|-------|-------------|--------|
| `cobb_douglas` | Production function approach | ✅ Implemented |
| `direct_wage` | Simple wage averaging | ✅ Implemented |
| `ces_production` | CES production function | 🚧 Planned |
| `stochastic_frontier` | Efficiency-based | 🚧 Planned |

### `aggregate.py` — Global Aggregation

Combine country estimates into global CHIP value.

```python
from lib import aggregate

# Different weighting schemes
gdp = aggregate.gdp_weighted(df)
labor = aggregate.labor_weighted(df)
freedom = aggregate.freedom_weighted(df)
simple = aggregate.unweighted(df)

# Compare all methods
comparison = aggregate.compare_weightings(df)

# Results include:
#   result.chip_value       - Global CHIP value
#   result.contributions    - Country breakdown
#   result.n_countries      - Countries included
#   result.metadata         - Additional stats
```

### `output.py` — Report Generation

Generate reports, tables, and visualizations.

```python
from lib import output

# Generate report
path = output.generate_report(results, title="My Analysis")

# Export data
output.save_csv(df, "country_chips")
output.save_json(results, "analysis_results")

# Visualizations
output.plot_chip_by_country(df)
output.plot_time_series(df)

# Format tables
print(output.to_table(df, format="markdown"))
```

### `config.py` — Configuration

Load and manage configuration settings.

```python
from lib import config

# Load from file
cfg = config.load_config()  # Reads config.yaml

# Access settings
cfg.data.year_start           # 2000
cfg.cleaning.exclude_countries  # ["Nepal", ...]
cfg.model.default_alpha       # 0.33

# Get defaults
cfg = config.get_default_config()
```

---

## Scripts

All scripts are run via `run.sh`:

### `baseline.py`

Reproduce the $2.56 CHIP value from the original study.

```bash
./run.sh baseline        # Run baseline reproduction
./run.sh baseline -v     # Run and view report
```

**Purpose:**
- Integration test for the entire library
- Validates against known target ($2.56)
- Reports validation status: PASSED, MARGINAL, or FAILED

### `coverage.py`

Examine which countries have consistent data across which time periods.

```bash
./run.sh coverage        # Run and save report
./run.sh coverage -v     # Run and view report
```

**Output:**
- Country coverage summary
- Data quality flags
- Recommendations for exclusions

### `nominal.py`

Compare CHIP values computed with and without deflation.

```bash
./run.sh nominal -v
```

**Tests hypothesis from `inflation-tracking.md`:**
- Does nominal CHIP naturally track inflation?
- How does deflation affect the result?

### `timeseries.py`

Analyze how CHIP value changes over time.

```bash
./run.sh timeseries -v
```

**Output:**
- Year-by-year CHIP values
- Trend analysis
- Stability assessment

### `compare.py`

Test different weighting schemes.

```bash
./run.sh compare -v
```

**Compares:**
- GDP-weighted (original method)
- Labor-force weighted
- Freedom-weighted
- Unweighted average

---

## Configuration

Edit `config.yaml` to customize behavior:

```yaml
data:
  year_start: 2000
  year_end: 2022
  use_cache: true

cleaning:
  exclude_countries:
    - Nepal
    - Pakistan
  outlier_threshold: 1.5

model:
  default_model: cobb_douglas
  estimate_alpha: true

aggregation:
  default_weighting: gdp_weighted
```

Or override programmatically:

```python
from lib.config import load_config

cfg = load_config()
cfg.data.year_start = 2010
cfg.cleaning.outlier_threshold = 2.0
```

---

## Development Workflow

### Adding a New Script

1. Create `scripts/my_analysis.py`
2. Import from `lib` as needed
3. The script will automatically be available via `./run.sh my_analysis`
4. Document in this README

### Adding a New Model

1. Add function to `lib/models.py`
2. Return a `ModelResult` for consistency
3. Add to model comparison table above

### Extending Data Sources

1. Add fetch function to `lib/fetcher.py`
2. Add normalizer to `lib/normalize.py` if needed
3. Document the new source

---

## Relationship to Other Folders

```
chip/
├── original/      # Frozen: Original study (R code + data)
├── reproduction/  # Frozen: Python reproduction of original
├── workbench/     # Active: Exploratory analysis (YOU ARE HERE)
├── estimates/     # Future: Official CHIP estimator
└── docs/          # Research papers and documentation
```

- **reproduction/** is frozen — a historical artifact proving we can replicate $2.56
- **workbench/** is active — where new ideas are tested
- **estimates/** (future) will import from workbench for official calculations

---

## Next Steps

See `docs/STATUS.md` for the full project roadmap.

Current workbench priorities:
1. Complete script implementations
2. Test freedom-weighted aggregation
3. Validate time series behavior
4. Prepare data for `weighting-analysis.md`

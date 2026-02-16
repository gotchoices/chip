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

## Project Structure

```
workbench/
├── lib/                          # Shared library (reusable modules)
│   ├── fetcher.py                # Data retrieval + caching
│   ├── cache.py                  # Cache management
│   ├── normalize.py              # Column standardization
│   ├── clean.py                  # Data cleaning utilities
│   ├── impute.py                 # MICE-style imputation
│   ├── pipeline.py               # Shared CHIP estimation pipeline
│   ├── models.py                 # Estimation models
│   ├── aggregate.py              # Weighting schemes
│   ├── output.py                 # Report generation
│   ├── config.py                 # Configuration management
│   └── logging_config.py         # Structured logging
│
├── studies/                      # Individual studies (one dir per investigation)
│   ├── baseline/                 # Reproduce original CHIP estimate
│   │   ├── study.py              # The computation
│   │   ├── README.md             # Objectives: research question, hypothesis, methodology
│   │   ├── FINDINGS.md           # Interpretation: results, conclusions, limitations
│   │   └── output/               # Reports, logs, summaries, plots (gitignored)
│   │
│   ├── coverage/                 # Data coverage analysis
│   │   ├── study.py
│   │   ├── README.md
│   │   ├── FINDINGS.md
│   │   └── output/
│   │
│   ├── timeseries/               # Year-by-year CHIP time series
│   │   ├── study.py
│   │   ├── README.md
│   │   ├── FINDINGS.md
│   │   └── output/
│   │
│   ├── nominal/                  # Nominal vs deflated CHIP (scaffold)
│   │   ├── study.py
│   │   ├── README.md
│   │   ├── FINDINGS.md
│   │   └── output/
│   │
│   └── weighting/                # Aggregation weighting methods (scaffold)
│       ├── study.py
│       ├── README.md
│       ├── FINDINGS.md
│       └── output/
│
├── data/                         # Shared data cache (gitignored, self-healing)
│   └── cache/
│
├── config.yaml                   # Base configuration (shared defaults)
├── pyproject.toml                # Dependencies
├── Makefile                      # Maintenance tasks (setup, clean, lint)
├── run.sh                        # Study runner
└── README.md                     # This file
```

---

## Quick Start

```bash
# Setup
cd workbench
make setup

# Run a study
./run.sh coverage

# Run and view report (requires glow, mdcat, or similar)
./run.sh coverage -v

# View last report
./run.sh --view coverage

# List available studies
./run.sh --list
```

No need to activate the virtual environment — `run.sh` handles it.

---

## Studies

Each study is a self-contained directory under `studies/`. A study has:

| File | Purpose | Committed? |
|------|---------|------------|
| `study.py` | The computation — runnable via `./run.sh <name>` | Yes |
| `README.md` | Objectives: research question, hypothesis, methodology | Yes |
| `FINDINGS.md` | Interpretation: results, conclusions, limitations | Yes |
| `config.yaml` | Optional overrides for base config | Yes |
| `output/` | Reports, logs, summaries, plots | No (gitignored) |

### Current Studies

| Study | Status | Description |
|-------|--------|-------------|
| **baseline** | Complete | Reproduce original $2.56 CHIP estimate ($2.33 achieved) |
| **coverage** | Complete | Analyze country/year data coverage across sources |
| **timeseries** | Complete | Year-by-year CHIP series, stable panel, inflation tracking |
| **nominal** | Scaffold | Formal test of nominal vs deflated CHIP (H1) |
| **weighting** | Scaffold | Compare GDP, labor, freedom, and unweighted aggregation |

### Running a Study

```bash
./run.sh <study>              # Run study, save output
./run.sh <study> -v           # Run and view report
./run.sh --view <study>       # View last report for study
./run.sh --pdf <study>        # Generate PDF from FINDINGS.md
./run.sh --list               # List all studies
```

Output goes to `studies/<name>/output/`:
- `reports/<name>_<timestamp>.md` — Analysis report
- `logs/<name>_<timestamp>.log` — Execution log
- `summaries/<name>_<timestamp>.json` — Machine-readable summary
- `plots/*.png` — Generated visualizations

---

## Creating a New Study

1. Create a directory under `studies/`:

```bash
mkdir -p studies/my_study
```

2. Add `study.py` with this boilerplate:

```python
#!/usr/bin/env python3
"""
My Study Title

Purpose:
    One-line description.

Usage:
    ./run.sh my_study
"""

import sys
from pathlib import Path

STUDY_DIR = Path(__file__).parent
WORKBENCH_ROOT = STUDY_DIR.parent.parent
sys.path.insert(0, str(WORKBENCH_ROOT))

from lib.logging_config import setup_logging, ScriptContext
from lib import fetcher, pipeline
from lib.config import load_config

OUTPUT_DIR = STUDY_DIR / "output"


def main():
    script_name = Path(__file__).parent.name
    setup_logging(script_name, output_dir=OUTPUT_DIR)

    with ScriptContext(script_name, output_dir=OUTPUT_DIR) as ctx:
        config = load_config(study_dir=STUDY_DIR)
        data = fetcher.get_all()

        # ... your analysis ...

        ctx.set_result("key_finding", value)


if __name__ == "__main__":
    main()
```

3. Add `README.md` with objectives:

```markdown
# My Study Title

## Research Question
What are we investigating?

## Hypothesis
What do we expect to find, and why?

## Methodology
How will we test this?

## Status
Current state: scaffold | active | complete
```

4. Add `FINDINGS.md` (fill in as results arrive):

```markdown
# My Study Title — Findings

## Results
Summary of findings.

## Interpretation
What do the results mean?

## Limitations
Known caveats.
```

5. Optionally add `config.yaml` to override base settings:

```yaml
# Only include what differs from workbench/config.yaml
data:
  year_start: 1990
```

The study is now runnable via `./run.sh my_study`.

---

## Study Documentation Convention

Each study has two documentation files:

**README.md** — Written *before* running the study. Visible when browsing the
repository. Contains the research question, hypothesis, and methodology. This
is the study's "charter."

**FINDINGS.md** — Written *after* results arrive. Contains interpretation of
results, conclusions, and known limitations. This is the study's "lab notebook."
Embed plots with standard markdown image syntax:

```markdown
![Four-panel comparison](output/plots/timeseries_4panel.png)
```

Together, they provide a complete narrative: why we ran the study, how we ran
it, what we found, and what it means.

### Generating PDFs

To generate a PDF from a study's FINDINGS.md (with embedded plots):

```bash
./run.sh --pdf timeseries
```

This produces `studies/timeseries/FINDINGS.pdf`. Requires
[pandoc](https://pandoc.org/) and a LaTeX engine:

```bash
brew install pandoc
brew install --cask basictex    # minimal LaTeX (recommended)
# or: brew install --cask mactex  # full LaTeX
```

To generate a PDF manually (e.g., with custom options):

```bash
cd studies/timeseries
pandoc FINDINGS.md -o FINDINGS.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V colorlinks=true
```

Run `pandoc` from the study directory so that relative image paths
(e.g., `output/plots/...`) resolve correctly.

---

## Shared Library

All studies import from `lib/`, which provides reusable building blocks:

### `fetcher.py` — Data Retrieval

```python
from lib import fetcher

data = fetcher.get_all()           # All datasets at once
wages = fetcher.get_wages()        # Individual datasets
data = fetcher.refresh_all()       # Force re-fetch
```

**Sources:**

| Dataset | Source | Notes |
|---------|--------|-------|
| Employment | ILOSTAT | By occupation |
| Wages | ILOSTAT | Monthly, by occupation |
| Hours | ILOSTAT | Hours worked |
| PWT | Penn World Tables 10.0 | GDP, capital, labor share |
| Deflator | FRED | US GDP deflator |

### `pipeline.py` — CHIP Estimation Pipeline

```python
from lib import fetcher, normalize, pipeline

data = fetcher.get_all()
deflator = normalize.normalize_deflator(data["deflator"], base_year=2017)

result = pipeline.prepare_labor_data(data, 1992, 2019, deflator_df=deflator)
chip_value, countries, est = pipeline.estimate_chip(result["est_data"])
```

### `models.py` — Estimation Models

| Model | Description | Status |
|-------|-------------|--------|
| `cobb_douglas` | Production function approach | Implemented |
| `direct_wage` | Simple wage averaging | Implemented |
| `ces_production` | CES production function | Planned |
| `stochastic_frontier` | Efficiency-based | Planned |

### `aggregate.py` — Global Aggregation

```python
from lib import aggregate

gdp = aggregate.gdp_weighted(df)
labor = aggregate.labor_weighted(df)
simple = aggregate.unweighted(df)
comparison = aggregate.compare_weightings(df)
```

### `config.py` — Configuration

Configuration is layered:
1. Built-in defaults
2. Base config (`workbench/config.yaml`)
3. Per-study overrides (`studies/<name>/config.yaml`)

```python
from lib.config import load_config

# Load with study-specific overrides
config = load_config(study_dir=STUDY_DIR)

config.data.year_start           # 2000 (or overridden)
config.cleaning.exclude_countries  # ["Nepal", ...]
config.model.default_alpha       # 0.33
```

### Self-Healing Cache

The data cache automatically rebuilds when deleted:

```bash
rm -rf data/          # Delete cache
./run.sh coverage     # Runs fine — data auto-fetched
```

---

## Configuration

Edit `config.yaml` to customize base behavior for all studies:

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

Individual studies can override any setting by placing a `config.yaml` in
their study directory containing only the keys that differ.

---

## Development Workflow

### Adding a New Model

1. Add function to `lib/models.py`
2. Return a `ModelResult` for consistency
3. Document in the models table above

### Extending Data Sources

1. Add fetch function to `lib/fetcher.py`
2. Add normalizer to `lib/normalize.py` if needed
3. Document the new source

### Maintenance

```bash
make setup       # Create venv and install dependencies
make clean       # Remove caches and output
make lint        # Run ruff linter
make format      # Run black formatter
```

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
1. Complete nominal and weighting study implementations
2. Test freedom-weighted aggregation
3. Validate time series behavior
4. Prepare data for `docs/weighting-analysis.md`

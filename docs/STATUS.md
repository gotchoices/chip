# Project Status

Detailed tracking of completed and pending work items.

**Last updated:** 2026-02-10

---

## Phase 1: Foundation

### 1.1 Original Study Analysis
- [x] Read and understand original R code (`chips.R`, `chips_old.R`, `chips_with_ict_capital.R`)
- [x] Document original methodology in [`original/README.md`](../original/README.md)
- [x] Identify data sources (ILOSTAT, PWT, FRED)
- [x] Understand the five "chips" variants and which is preferred (chips4 / DF I)
- [x] Sanitize identifying information from original code (API keys, paths)

### 1.2 Project Setup
- [x] Initialize repository structure
- [x] Create `.gitignore` (secrets, data/, Python artifacts)
- [x] Set up secrets management (`secrets.toml`, `secrets.example.toml`)
- [x] Platform decision: Python (documented in README)

### 1.3 Documentation — Critical Review
- [x] Create and write `docs/original-review.md` (Sections 1-11)
- [ ] Review and refine draft

### 1.4 Documentation — Weighting Analysis
- [x] Create outline for `docs/weighting-analysis.md`
- [x] Write Sections 1-3, 5 (Introduction, Schemes, Philosophy, Recommendations)
- [ ] Write Section 4: Empirical Comparison — requires `scripts/compare.py` output

### 1.5 Documentation — Alternative Models
- [x] Create outline for `docs/alternative-models.md`
- [ ] Content development — **DEFERRED to Phase 3**

### 1.6 Documentation — Inflation Tracking ✅
- [x] Write full paper `docs/inflation-tracking.md`
- [x] Formulate testable hypotheses (H1-H4)

### 1.7 Documentation — Future Labor Value
- [x] Create outline for `docs/labor-value-future.md`
- [x] Added Section 3.4: Cross-country evidence (US labor rates)
- [ ] Write full paper from outline

### 1.8 Python Reproduction ✅
- [x] Implement full pipeline (`fetch.py`, `clean.py`, `estimate.py`, `aggregate.py`)
- [x] Validate: $2.56/hour with `data_source: "original"`
- [x] Validate: $2.35/hour with `data_source: "api"` (fresh data)
- [x] Configurable: data_source, time_weighting options
- [x] Explicit normalization layer (`pipeline/normalize.py`)

---

## Phase 2: Workbench Development

### 2.1 Workbench Scaffolding ✅
- [x] Create folder structure (`workbench/`)
- [x] Create workbench README with full documentation
- [x] Create pyproject.toml
- [x] Simplify Makefile to maintenance-only (setup/clean/lint)
- [x] Create unified `run.sh` for script execution and report viewing

### 2.2 Library Implementation ✅

**Data Layer:**
- [x] `lib/fetcher.py` — ILOSTAT, PWT (rug.nl Excel), FRED with retries and caching
- [x] `lib/cache.py` — Parquet cache, metadata, invalidation
- [x] `lib/normalize.py` — Format detection, ILOSTAT/PWT/deflator standardization
- [x] `lib/logging_config.py` — Structured logging, ScriptContext, JSON summaries

**Processing Layer:**
- [x] `lib/clean.py` — Country handling (harmonize, exclude, include, coverage),
      occupation filtering (unskilled, skill classification), outlier removal,
      year filtering, merging, `pivot_to_ratios()`, `weighted_aggregate()`
- [x] `lib/impute.py` — MICE-style `norm_predict()`, wage ratio and alpha imputation
- [x] `lib/config.py` — YAML config loading with typed dataclasses

**Estimation & Output:**
- [x] `lib/models.py` — Cobb-Douglas, direct wage, ModelResult dataclass
- [x] `lib/aggregate.py` — GDP/labor/freedom/unweighted, compare_weightings()
- [x] `lib/output.py` — Markdown reports, CSV/JSON export, matplotlib plots

### 2.3 Baseline Validation ✅
- [x] `scripts/baseline.py` — Full pipeline reproducing original methodology
- [x] **Result: $2.33/hour (0.9% deviation from reproduction's $2.35)**
- [x] Key methodology details documented in baseline.py header:
  - Wage ratios calculated per country-year, then averaged
  - All employment kept for effective labor (not just rows with wages)
  - Alpha estimated on full PWT data (~2000 obs), not just wage rows (~650)
  - MICE-style imputation for wage ratios and alphas
  - Country-year exclusions with both ISO codes and names

### 2.4 Data Coverage Script ✅
- [x] `scripts/coverage.py` — Analyzes country/year coverage across all data sources
- [x] Generates markdown report with tables and recommendations

### 2.5 Time Series Exploration (Next)
Single configurable script: `scripts/timeseries.py`

**Purpose:** Build year-by-year CHIP time series under various assumptions to
understand the data before testing specific hypotheses.

Configurable knobs:
- [ ] Deflation: on (2017 base) or off (nominal dollars)
- [ ] Country filter: all available, stable panel (continuous coverage), or custom list
- [ ] Year range and window size (single year, 3-year rolling, 5-year rolling)
- [ ] Weighting: GDP-weighted, labor-weighted, unweighted

Discovery steps:
- [ ] Generate raw time series with all available data — observe trends, noise
- [ ] Identify stable-panel countries (continuous data across desired time span)
- [ ] Compare full dataset vs. stable panel — isolate composition effects
- [ ] Evaluate whether spotty-coverage countries add material information
- [ ] Overlay CPI/deflator for visual comparison to inflation

### 2.6 Hypothesis Testing (Requires 2.5)
From `docs/inflation-tracking.md`, using time series output:
- [ ] H1: Nominal CHIP should track inflation
- [ ] H2: Deflated CHIP stable when country sample held constant
- [ ] H3: Windowed averaging produces coherent time series
- [ ] H4: Recent-year nominal CHIP more actionable

### 2.7 Additional Research Scripts
- [ ] `scripts/compare.py` — GDP vs labor vs freedom weighting

---

## Phase 3: Production Estimates

### 3.1 Estimates Pipeline
- [ ] Create `estimates/` folder (imports from `workbench/lib/`)
- [ ] Implement nominal (non-deflated) output option
- [ ] Implement trailing window methodology
- [ ] Produce time series of annual CHIP values
- [ ] Validate against official inflation benchmarks
- [ ] Establish annual update process for MyCHIPs

### 3.2 Weighting Analysis
- [ ] Generate empirical comparison data (`scripts/compare.py`)
- [ ] Complete `docs/weighting-analysis.md` Section 4
- [ ] Document sensitivity range across weighting schemes

---

## Phase 4: Alternative Models

### 4.1 CES Production Function
- [ ] Research CES specification for CHIP context
- [ ] Implement and compare to Cobb-Douglas baseline

### 4.2 Stochastic Frontier Analysis
- [ ] Research applicability
- [ ] Implement if warranted

### 4.3 Direct Wage Methods
- [ ] Design simpler wage-averaging approach with PPP adjustments
- [ ] Compare to production-function approach

### 4.4 Model Comparison
- [ ] Run all models on same data
- [ ] Document in `docs/alternative-models.md`

---

## Immediate Next Steps

1. **Build `scripts/timeseries.py`** (2.5) — configurable time series explorer
2. **Discovery phase** — generate series, identify stable panel, isolate composition effects
3. **Test hypotheses** (2.6) — validate H1-H4 using time series output
4. **Generate weighting comparison** — `scripts/compare.py` for `weighting-analysis.md` Section 4
5. **Write labor-value-future.md full paper** — convert outline to prose

---

## Recent Accomplishments

- ✅ **Workbench baseline FULLY validated** (`workbench/scripts/baseline.py`)
  - Result: **$2.33/hour** (0.9% deviation from reproduction's $2.35)
  - Matches reproduction methodology with identical fresh API data
  - Key fixes to match reproduction:
    - Wage ratios: calculate per country-year, then average
    - Keep all employment for effective labor (don't drop rows without wages)
    - Estimate alpha on ALL PWT data (2030 obs), not just wage rows (650 obs)
    - PWT source aligned (same rug.nl Excel as reproduction)
  - MICE-style imputation for wage ratios and alphas
  - Thoroughly documented with extensive methodology comments
- ✅ **Workbench infrastructure complete** — run.sh, logging, Makefile, report viewer
- ✅ **All library modules implemented** — 10 modules in `workbench/lib/`
- ✅ **Coverage script working** — `scripts/coverage.py` with Rich markdown reports
- ✅ **Reproduction validated** — $2.56 (original data), $2.35 (fresh API)
- ✅ **Inflation-tracking paper complete** — with testable hypotheses H1-H4
- ✅ **Labor-value-future outline complete** — with cross-country evidence section

---

*This file tracks detailed progress. For high-level project overview, see [`../README.md`](../README.md).*

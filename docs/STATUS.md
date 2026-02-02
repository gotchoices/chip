# Project Status

Detailed tracking of completed and pending work items.

**Last updated:** 2026-02-02

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
- [x] Create outline for `docs/original-review.md`
- [x] Write Section 1: Executive Summary
- [x] Write Section 2: Introduction
- [x] Write Section 3: The CHIP Definition
- [x] Write Section 4: Overview of Original Study
- [x] Write Section 5: Theoretical Framework
- [x] Write Section 6: Empirical Methodology
- [x] Write Section 7: Definition Alignment Analysis
- [x] Write Section 8: Strengths
- [x] Write Section 9: Limitations
- [x] Write Section 10: Conclusions
- [x] Write Section 11: References
- [ ] Review and refine draft

### 1.4 Documentation — Weighting Analysis
- [x] Create outline for `docs/weighting-analysis.md`
- [x] Write Section 1: Introduction (The Aggregation Problem)
- [x] Write Section 2: Weighting Schemes (theoretical description)
- [x] Write Section 3: Philosophical Considerations
- [ ] Write Section 4: Empirical Comparison — **BLOCKED: requires reproduction data**
- [x] Write Section 5: Recommendations

### 1.5 Documentation — Alternative Models
- [x] Create outline for `docs/alternative-models.md`
- [ ] Content development — **DEFERRED to Phase 3**

### 1.6 Documentation — Inflation Tracking
- [x] Create outline for `docs/inflation-tracking.md`
- [x] Analyze deflator's role and appropriateness for MyCHIPs
- [x] Propose windowed averaging alternatives
- [x] Run preliminary empirical tests (different year windows)
- [x] Formulate testable hypotheses (H1-H4)
- [x] Add epistemological discussion (can we know if labor value truly changes?)
- [x] Write full paper from outline

### 1.7 Documentation — Future Labor Value
- [x] Create outline for `docs/labor-value-future.md`
- Explores: Will AI/automation make labor more or less valuable?
- Market-based analysis only (no UBI/redistribution assumptions)
- [ ] Write full paper from outline

### 1.8 Python Reproduction
- [x] Set up Python environment (`pyproject.toml`)
- [x] Create config.yaml with study parameters
- [x] Implement data fetching module (`pipeline/fetch.py`)
- [x] Implement data cleaning pipeline (`pipeline/clean.py`)
- [x] Implement Cobb-Douglas estimation (`pipeline/estimate.py`)
- [x] Implement global aggregation (`pipeline/aggregate.py`)
- [x] Create main runner with logging (`main.py`)
- [x] Create Makefile for easy execution
- [x] Fix ILOSTAT API (switched to rplumber endpoint)
- [x] Add data_source config option (original/api/cache)
- [x] Add time_weighting config option (all_years/recent_only/rolling/exponential)
- [x] Validate: reproduce $2.56 result with `data_source: "original"`
- [x] Refactor: Create explicit data normalization layer (`pipeline/normalize.py`)
- [ ] Test: Verify API data source produces reasonable results
- [ ] Generate weighting comparison data for `weighting-analysis.md`

---

## Phase 2: Validation & Sensitivity

### 2.1 Weighting Sensitivity
- [ ] Calculate CHIP value under GDP weighting
- [ ] Calculate CHIP value under labor-force weighting
- [ ] Calculate CHIP value under equal (unweighted) scheme
- [ ] Document sensitivity range

### 2.2 Data Quality
- [ ] Analyze outlier treatment sensitivity
- [ ] Explore informal economy data availability
- [ ] Document country coverage gaps

### 2.3 Temporal Analysis
- [ ] Extend time series beyond original study period
- [ ] Analyze CHIP value stability over time
- [ ] Compare to inflation benchmarks

---

## Phase 3: Alternative Models

### 3.1 CES Production Function
- [ ] Research CES specification for CHIP context
- [ ] Implement estimation
- [ ] Compare results to Cobb-Douglas baseline

### 3.2 Stochastic Frontier Analysis
- [ ] Research applicability
- [ ] Implement if warranted
- [ ] Compare results

### 3.3 Direct Wage Methods
- [ ] Design simpler wage-averaging approach
- [ ] Implement with PPP adjustments
- [ ] Compare to production-function approach

### 3.4 Model Comparison
- [ ] Define comparison metrics
- [ ] Run all models on same data
- [ ] Document in `docs/alternative-models.md`

---

## Phase 4: Automation

### 4.1 Data Pipeline
- [ ] Automated data fetching (scheduled or on-demand)
- [ ] Data validation and anomaly detection
- [ ] Caching strategy for API rate limits

### 4.2 Estimation Pipeline
- [ ] End-to-end script from data fetch to CHIP estimate
- [ ] Configurable for different model specifications
- [ ] Output formatting (JSON, markdown report)

### 4.3 Review Process
- [ ] AI-assisted outlier review
- [ ] Change detection from prior estimates
- [ ] Documentation of each estimate run

---

## Phase 5: Workbench Development

### 5.1 Workbench Scaffolding ✅
- [x] Create folder structure (`workbench/`)
- [x] Create lib module stubs with docstrings
- [x] Create script stubs
- [x] Create workbench README with full documentation
- [x] Create pyproject.toml
- [x] Simplify Makefile to maintenance-only (setup/clean/lint)
- [x] Create unified `run.sh` for script execution and report viewing
- [x] Implement `lib/logging_config.py` with structured logging
- [x] Implement `lib/fetcher.py` with ILOSTAT, PWT, FRED support

### 5.2 Library Implementation ✅
All library modules are now implemented.

**Data Layer:**
- [x] `lib/fetcher.py` — Fetch from ILOSTAT, PWT, FRED with caching
- [x] `lib/cache.py` — Cache validation, invalidation, metadata
- [x] `lib/normalize.py` — Column standardization for all sources
  - [x] `detect_format()` — Identify ILOSTAT API vs CSV, PWT version
  - [x] `normalize_ilostat()` — Standardize ILOSTAT data
  - [x] `normalize_pwt()` — Standardize PWT data
  - [x] `normalize_deflator()` — Standardize FRED deflator

**Processing Layer:**
- [x] `lib/clean.py` — Data cleaning and merging
  - [x] `harmonize_countries()` — Standardize country names
  - [x] `exclude_countries()` — Remove configured exclusions
  - [x] `filter_unskilled()` — Keep only elementary occupations
  - [x] `classify_skill_level()` — Map ISCO codes to skill labels
  - [x] `filter_outliers()` — Statistical outlier removal
  - [x] `merge_datasets()` — Join employment, wages, hours, PWT
  - [x] `filter_years()` — Filter by year range
  - [x] `require_complete()` — Remove incomplete rows

**Estimation Layer:**
- [x] `lib/models.py` — Economic models
  - [x] `cobb_douglas()` — Production function estimation
  - [x] `direct_wage()` — Simple wage averaging (alternative)
  - [x] `ModelResult` dataclass for consistent output

**Aggregation Layer:**
- [x] `lib/aggregate.py` — Global CHIP calculation
  - [x] `gdp_weighted()` — Original study method
  - [x] `labor_weighted()` — Alternative: weight by labor hours
  - [x] `unweighted()` — Simple average
  - [x] `freedom_weighted()` — Weight by economic freedom index
  - [x] `compare_weightings()` — Run all methods, compare results

**Output Layer:**
- [x] `lib/output.py` — Report generation
  - [x] `generate_report()` — Create markdown report
  - [x] `save_csv()` — Export data
  - [x] `save_json()` — Export results
  - [x] `to_table()` — Format for display

**Configuration:**
- [x] `lib/config.py` — Load and validate config.yaml

### 5.3 Baseline Validation Script ✅ (COMPLETE)
- [x] Create `scripts/baseline.py` — Reproduce reproduction's result with fresh API data
- [x] Implemented correct methodology directly in baseline.py:
  - [x] Calculate effective_labor using skill-weighted hours across ALL occupations
  - [x] Implement wage ratio calculation (relative to Managers, per country-year then average)
  - [x] Use ILOSTAT effective_labor (not PWT employment) for k/L ratio
  - [x] Fixed MPL formula: `(1-α) × (K/L × hc)^α` (hc inside power)
  - [x] Fixed wage dataset: use HOURLY wages (`EAR_4HRL`) not monthly
  - [x] Separate elementary wage from aggregate wage
  - [x] Calculate adjusted_wage = elementary_wage × θ
  - [x] Filter to SEX_T (totals only, not male/female breakdowns)
  - [x] Keep ALL employment data for effective labor (don't require wages)
  - [x] Estimate alpha on full PWT data (not just rows with wages)
  - [x] Apply MICE-style imputation for wage ratios and alphas
  - [x] Apply country-year exclusions (ISO codes + names)
- [x] **VALIDATION RESULT: $2.33/hour (0.9% deviation from reproduction's $2.35)**
  - Status: ✅ PASSED — matches reproduction methodology with fresh API data
  - Target: $2.35 (reproduction with `data_source: api`)
  - Mean α: 0.65, Countries: 99
  - Thoroughly documented with extensive comments in baseline.py

### 5.4 Research Scripts (BLOCKED: requires 5.2 + 5.3)
- [ ] `scripts/coverage.py` — Data coverage analysis ✅ (uses only fetcher)
- [ ] `scripts/nominal.py` — Test H1: nominal CHIP tracks inflation
- [ ] `scripts/timeseries.py` — Test H2, H3: CHIP stability over time
- [ ] `scripts/compare.py` — Test GDP vs labor vs freedom weighting

### 5.5 Hypothesis Testing (BLOCKED: requires 5.4)
Using workbench scripts, test hypotheses from inflation-tracking paper:
- [ ] H1: Nominal CHIP should track inflation
- [ ] H2: Deflated CHIP stable when country sample held constant
- [ ] H3: Windowed averaging produces coherent time series
- [ ] H4: Recent-year nominal CHIP more actionable

---

## Immediate Next Steps

1. **Implement research scripts** (5.4) — nominal, timeseries, compare
2. **Test hypotheses** (5.5) — validate H1-H4 from inflation-tracking paper
3. **Write labor-value-future.md full paper** — convert outline to prose
4. **Generate weighting comparison data** — for `weighting-analysis.md` Section 4

---

## Recent Accomplishments

- ✅ **Workbench baseline FULLY validated** (`workbench/scripts/baseline.py`)
  - Result: **$2.33/hour** (0.9% deviation from reproduction's $2.35)
  - Matches reproduction methodology with fresh API data
  - Key fixes to match reproduction:
    - Wage ratios: calculate per country-year, then average (not average wages then ratio)
    - Keep all employment for effective labor (don't drop rows without wages)
    - Estimate alpha on ALL PWT data (2030 obs), not just rows with wages (650 obs)
    - Then filter to rows with wages for final MPL/CHIP calculation
  - MICE-style imputation for wage ratios and alphas
  - Thoroughly documented with extensive methodology comments
- ✅ **Workbench infrastructure complete** (`workbench/`)
  - Modular library architecture designed
  - `run.sh` unified script runner with report viewing
  - Makefile simplified to maintenance-only
  - Structured logging with file output
  - `fetcher.py` implemented (ILOSTAT, PWT, FRED)
  - `coverage.py` script working
- ✅ **Inflation-tracking paper complete** (`docs/inflation-tracking.md`)
  - Analyzed deflator appropriateness for MyCHIPs use case
  - Proposed windowed averaging methodology
  - Ran empirical tests showing composition sensitivity
  - Formulated testable hypotheses
- ✅ **Labor-value-future outline complete** (`docs/labor-value-future.md`)
  - Explores AI/automation impact on labor value
  - Market-based analysis (no redistribution assumptions)
  - Added regulatory paradox (open-source vs concentration)
- ✅ Reproduction validated: $2.56/hour with `data_source: "original"`
- ✅ Created explicit normalization layer (`reproduction/pipeline/normalize.py`)
- ✅ ILOSTAT API fixed (switched to rplumber endpoint)

---

*This file tracks detailed progress. For high-level project overview, see [`../README.md`](../README.md).*

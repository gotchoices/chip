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

### 5.1 Workbench Scaffolding
- [x] Create folder structure (`workbench/`)
- [x] Create lib modules with docstrings:
  - [x] `lib/fetcher.py` — Data retrieval with caching
  - [x] `lib/cache.py` — Cache management
  - [x] `lib/normalize.py` — Column standardization
  - [x] `lib/clean.py` — Data cleaning utilities
  - [x] `lib/models.py` — Estimation models (Cobb-Douglas, direct wage)
  - [x] `lib/aggregate.py` — Weighting schemes
  - [x] `lib/output.py` — Report generation
  - [x] `lib/config.py` — Configuration management
- [x] Create example script stubs:
  - [x] `scripts/analyze_data_coverage.py`
  - [x] `scripts/test_nominal_chip.py`
  - [x] `scripts/chip_time_series.py`
  - [x] `scripts/compare_aggregators.py`
- [x] Create workbench README with full documentation
- [x] Create pyproject.toml and Makefile

### 5.2 Workbench Implementation
- [ ] Complete `analyze_data_coverage.py` — identify reliable country/year combinations
- [ ] Complete `test_nominal_chip.py` — test H1 from inflation-tracking paper
- [ ] Complete `chip_time_series.py` — test H2, H3 from inflation-tracking
- [ ] Complete `compare_aggregators.py` — test GDP vs labor vs freedom weighting
- [ ] Fetch and integrate economic freedom index data
- [ ] Validate full pipeline with fresh API data

### 5.3 Hypothesis Testing
Using workbench scripts, test hypotheses from inflation-tracking paper:
- [ ] H1: Nominal CHIP should track inflation
- [ ] H2: Deflated CHIP stable when country sample held constant
- [ ] H3: Windowed averaging produces coherent time series
- [ ] H4: Recent-year nominal CHIP more actionable

---

## Immediate Next Steps

1. **Complete workbench scripts** — implement the logic in the script stubs
2. **Run data coverage analysis** — identify which countries are reliable
3. **Test hypotheses** — validate H1-H4 from inflation-tracking paper
4. **Write labor-value-future.md full paper** — convert outline to prose

---

## Recent Accomplishments

- ✅ **Workbench created** (`workbench/`)
  - Modular library architecture (fetcher, clean, models, aggregate, output)
  - Independent from reproduction/ (can evolve freely)
  - Self-healing cache design
  - Example script stubs for key analyses
- ✅ **Inflation-tracking paper complete** (`docs/inflation-tracking.md`)
  - Analyzed deflator appropriateness for MyCHIPs use case
  - Proposed windowed averaging methodology
  - Ran empirical tests showing composition sensitivity
  - Formulated testable hypotheses
- ✅ **Labor-value-future paper complete** (`docs/labor-value-future.md`)
  - Explores AI/automation impact on labor value
  - Market-based analysis (no redistribution assumptions)
  - Added regulatory paradox (open-source vs concentration)
- ✅ Reproduction validated: $2.56/hour with `data_source: "original"`
- ✅ Created explicit normalization layer (`pipeline/normalize.py`)
- ✅ ILOSTAT API fixed (switched to rplumber endpoint)

---

*This file tracks detailed progress. For high-level project overview, see [`../README.md`](../README.md).*

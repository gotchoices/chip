# Project Status

Detailed tracking of completed and pending work items.

**Last updated:** 2026-02-16

---

## Phase 1: Foundation

### 1.1 Original Study Analysis ✅
- [x] Read and understand original R code (`chips.R`, `chips_old.R`, `chips_with_ict_capital.R`)
- [x] Document original methodology in [`original/README.md`](../original/README.md)
- [x] Identify data sources (ILOSTAT, PWT, FRED)
- [x] Understand the five "chips" variants and which is preferred (chips4 / DF I)
- [x] Sanitize identifying information from original code (API keys, paths)

### 1.2 Project Setup ✅
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
- [ ] Write Section 4: Empirical Comparison — requires `weighting` study output

### 1.5 Documentation — Alternative Models
- [x] Create outline for `docs/alternative-models.md`
- [ ] Content development — **DEFERRED to Phase 4**

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
- [x] Refactor scripts into `studies/` directory structure (study.py + README.md + FINDINGS.md + output/)
- [x] Add PDF generation capability to `run.sh`

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
- [x] `lib/pipeline.py` — Shared CHIP estimation pipeline (prepare_labor_data, estimate_chip)
- [x] `lib/models.py` — Cobb-Douglas, direct wage, ModelResult dataclass
- [x] `lib/aggregate.py` — GDP/labor/freedom/unweighted, compare_weightings()
- [x] `lib/output.py` — Markdown reports, CSV/JSON export, matplotlib plots

### 2.3 Study: Baseline ✅
- [x] `studies/baseline/study.py` — Full pipeline reproducing original methodology
- [x] **Result: $2.33/hour (1.0% deviation from reproduction's $2.35)**
- [x] FINDINGS.md written with top-10 countries, implementation lessons, limitations
- [x] Key methodology details documented in study.py header

### 2.4 Study: Coverage ✅
- [x] `studies/coverage/study.py` — Country/year coverage across all data sources
- [x] **Result: 123 viable countries, 79 excellent, recommended range 2000–2019**
- [x] FINDINGS.md written with quality tiers, binding constraints, implications

### 2.5 Study: Time Series ✅
- [x] `studies/timeseries/study.py` — Year-by-year CHIP under multiple configurations
- [x] All-countries and stable-panel series (constant and nominal)
- [x] Rolling averages (3-year, 5-year)
- [x] **Key discovery: deflation cancels in the CHIP formula**
- [x] H1 (inflation tracking): Confirmed (nominal rises +95%, constant +41%)
- [x] H2 (composition effects): Partially supported (panel tighter in level, not std)
- [x] H3 (real stability): Supported (panel constant CHIP std = $0.12, 2005–2019)
- [x] FINDINGS.md written with hypothesis assessments, plots, limitations
- [x] Generates 4 plots: 4-panel comparison, nominal vs deflator, country count, constant vs nominal

### 2.6 Study: Nominal — Absorbed
- [x] Core question (does deflation matter?) answered by timeseries study
- [x] README updated to reference timeseries findings
- No further implementation needed

### 2.7 Study: Production (Next)
- [ ] Implement trailing-window CHIP estimator (1, 3, 5 year windows)
- [ ] Test PWT bridge for years beyond 2019 (ILOSTAT + extrapolated capital)
- [ ] Test CPI extrapolation accuracy between recalculations
- [ ] Evaluate stable-panel-only estimation for bridge period
- [ ] Assemble recommended production methodology
- See `studies/production/README.md` for full design

### 2.8 Study: Stability
- [ ] Simulate vintage changes (compute CHIP with truncated data, compare)
- [ ] Decompose year-over-year CHIP changes (inflation / composition / real)
- [ ] Measure CPI-extrapolation correction distribution
- [ ] Establish confidence bounds for update continuity
- See `studies/stability/README.md` for full design

### 2.9 Study: Weighting
- [ ] Implement GDP, labor-force, freedom-index, and unweighted aggregation
- [ ] Compare CHIP values across weighting schemes
- [ ] Analyze country contribution breakdown
- [ ] Generate data for `docs/weighting-analysis.md` Section 4
- See `studies/weighting/README.md` for full design

---

## Phase 3: Production Estimates

### 3.1 Estimates Pipeline
- [ ] Create `estimates/` folder (imports from `workbench/lib/`)
- [ ] Implement recommended methodology from `production` study
- [ ] Produce time series of annual nominal CHIP values
- [ ] Validate against official inflation benchmarks
- [ ] Establish annual update process for MyCHIPs
- [ ] Document methodology for external reviewers

### 3.2 Documentation Updates
- [ ] Complete `docs/weighting-analysis.md` Section 4 (requires weighting study)
- [ ] Update `docs/inflation-tracking.md` with timeseries findings (deflation cancellation)
- [ ] Write production methodology paper

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

1. **Implement `production` study** (2.7) — trailing window, PWT bridge, CPI extrapolation
2. **Implement `stability` study** (2.8) — vintage simulation, change decomposition
3. **Implement `weighting` study** (2.9) — aggregation sensitivity analysis
4. **Write labor-value-future.md full paper** — convert outline to prose
5. **Create `estimates/` pipeline** (3.1) — official CHIP estimator using production study findings

---

## Key Results to Date

| Study | Primary Result | Status |
|-------|---------------|--------|
| Reproduction | $2.56/hr (original data), $2.35/hr (fresh API) | Complete |
| Baseline | $2.33/hr (1.0% deviation from reproduction) | Complete |
| Coverage | 123 viable countries, 79 excellent, range 2000–2019 | Complete |
| Timeseries | Real CHIP ~$3.50/hr (panel), deflation cancels in formula | Complete |
| Nominal | Absorbed into timeseries findings | N/A |
| Production | — | Scaffold |
| Stability | — | Scaffold |
| Weighting | — | Scaffold |

---

*This file tracks detailed progress. For high-level project overview, see [`../README.md`](../README.md).
For study-specific details, see each study's `README.md` and `FINDINGS.md` under `workbench/studies/`.*

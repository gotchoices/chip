# Project Status

Detailed tracking of completed and pending work items.

**Last updated:** 2026-02-17

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
- [x] `lib/fetcher.py` — ILOSTAT, PWT, FRED, Heritage Freedom Index, UNDP HDI with retries and caching
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
- [x] `lib/aggregate.py` — GDP/labor/freedom/HDI/unweighted, compare_weightings()
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

### 2.7 Study: Production ✅
- [x] Implement trailing-window CHIP estimator (1, 3, 5 year windows)
- [x] Test PWT bridge for years beyond PWT — freeze and slope methods
- [x] Test CPI extrapolation accuracy between recalculations
- [x] Identify stable panel with PWT 11.0 (10 countries)
- [x] Produce current CHIP estimate: **$3.17/hr nominal (2022), ~$3.44–$3.55 est. 2026**
- [x] FINDINGS.md with inline plots, hypothesis assessments, recommendations
- [ ] Evaluate stable-panel-only estimation for bridge period (deferred to stability)
- [ ] Re-test bridge at non-COVID freeze year (future work)
- [ ] Assemble recommended production pipeline in `estimates/` (Phase 3)
- See `studies/production/README.md` and `FINDINGS.md` for full results

### 2.8 Study: Stability (reduced scope)
- [ ] Vintage comparison: PWT 10.0 vs 11.0 CHIP for 2000–2019 overlap
- [ ] Country-level revision analysis (which countries shifted most?)
- [ ] Summary statistics for Design Goal 6 validation
- ~~Decompose year-over-year changes~~ — deferred (practical response already implemented)
- ~~CPI correction distribution~~ — answered by production study (std ~6.4%, mean-reverting)
- See `studies/stability/README.md` for full design

### 2.9 Study: Weighting ✅
- [x] Implement Heritage Foundation freedom index fetcher (tested, cached)
- [x] Implement UNDP HDI fetcher (tested, cached)
- [x] Add HDI-weighted scheme to `lib/aggregate.py`
- [x] Implement study: GDP, labor, freedom, HDI, and unweighted aggregation
- [x] Compare CHIP values across 5 weighting schemes
- [x] Analyze country contribution breakdown
- [x] Produce country-specific multipliers (Design Goal 10) — 85 countries
- [ ] Generate data for `docs/weighting-analysis.md` Section 4
- **Key finding:** Weighting is a first-order choice — $1.67 (labor) to $2.85 (freedom), CV 21%
- **Recommendation:** Retain GDP-weighted ($2.68) as primary; publish full range for transparency
- See `studies/weighting/FINDINGS.md` for full results

---

## Phase 3: Production Estimates & Deployment

### 3.1 Estimates Pipeline
- [ ] Create `estimates/` folder (imports from `workbench/lib/`)
- [ ] Implement recommended methodology from `production` study
- [ ] Produce time series of annual nominal CHIP values
- [ ] Validate against official inflation benchmarks
- [ ] Publish country-specific multipliers (country CHIP / global CHIP)
- [ ] Document methodology for external reviewers

### 3.2 Automated Publishing (Two-Tier Model)
- [ ] **Daily/weekly extrapolation script** — applies latest CPI (or GDP
      deflator) to the official base value, produces current nominal CHIP
- [ ] **Annual recalculation** — full pipeline re-estimation when new source
      data arrives (ILOSTAT, PWT); updates base parameters and records
      correction magnitude
- [ ] **API endpoint** — HTTP service returning current global CHIP and
      per-country multipliers (replaces/evolves `updateCPI` cron on mychips.org)
- [ ] **Snap-back mechanism** — when recalculation produces a new base value,
      the daily script's parameters are updated automatically; the magnitude
      and direction of the snap are logged for transparency
- [ ] Integration testing: daily script → recalculation → snap → daily script

### 3.3 Country-Specific Outputs
- [ ] Per-country multiplier table (θ-derived or direct wage ratio)
- [ ] Historical multiplier series per country
- [ ] Publish alongside global CHIP via API endpoint (3.2)
- [ ] Documentation: how to interpret and use country multipliers

### 3.4 Documentation Updates
- [ ] Complete `docs/weighting-analysis.md` Section 4 (data now available from weighting study)
- [x] Update `docs/inflation-tracking.md` — empirical evidence (Sec 8), market dynamics (Sec 7.4), two-tier model (Sec 7.3)
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

1. **Implement `stability` study** (2.8) — PWT 10.0 vs 11.0 vintage comparison (reduced scope)
2. **Complete `weighting-analysis.md` Section 4** — empirical data now available from weighting study
3. **Create `estimates/` pipeline** (3.1) — official CHIP estimator using production study findings
4. **Build automated publishing** (3.2) — two-tier extrapolation + recalculation, API endpoint
5. **Publish country multipliers** (3.3) — per-country labor-valuation ratios via API
6. **Update chipcentral.net** — revised CHIP value from PWT 11.0 ($3.17 nominal 2022)
7. **Write labor-value-future.md full paper** — convert outline to prose

---

## Key Results to Date

| Study | Primary Result | Status |
|-------|---------------|--------|
| Reproduction | $2.56/hr (original data), $2.35/hr (fresh API) | Complete |
| Baseline | $2.33/hr (1.0% deviation from reproduction) | Complete |
| Coverage | 123 viable countries, 79 excellent, range 2000–2019 | Complete |
| Timeseries | Real CHIP ~$3.50/hr (panel), deflation cancels in formula | Complete |
| Nominal | Absorbed into timeseries findings | N/A |
| Production | 5yr window recommended, $3.17 nominal (2022), ~$3.50 est. 2026 | Complete |
| Stability | — | Scaffold |
| Weighting | $1.67–$2.85 range; GDP-weighted $2.68 recommended; 85 country multipliers | Complete |

---

*This file tracks detailed progress. For high-level project overview, see [`../README.md`](../README.md).
For study-specific details, see each study's `README.md` and `FINDINGS.md` under `workbench/studies/`.*

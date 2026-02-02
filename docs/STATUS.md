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

## Immediate Next Steps

1. **Create `estimates/` project** — implement nominal CHIP methodology with trailing windows
2. **Test hypotheses from inflation-tracking paper** — validate H1-H4
3. **Write labor-value-future.md full paper** — convert outline to prose

## Recent Accomplishments

- ✅ **Inflation-tracking paper complete** (`docs/inflation-tracking.md`)
  - Analyzed deflator appropriateness for MyCHIPs use case
  - Proposed windowed averaging methodology
  - Ran empirical tests showing composition sensitivity
  - Formulated testable hypotheses
- ✅ **Labor-value-future outline created** (`docs/labor-value-future.md`)
  - Explores AI/automation impact on labor value
  - Market-based analysis (no redistribution assumptions)
- ✅ Reproduction validated: $2.56/hour with `data_source: "original"`
- ✅ Created explicit normalization layer (`pipeline/normalize.py`)
- ✅ ILOSTAT API fixed (switched to rplumber endpoint)

---

*This file tracks detailed progress. For high-level project overview, see [`../README.md`](../README.md).*

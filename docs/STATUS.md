# Project Status

Detailed tracking of completed and pending work items.

**Last updated:** 2026-02-01

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

### 1.6 Python Reproduction
- [x] Set up Python environment (`pyproject.toml`)
- [x] Create config.yaml with study parameters
- [x] Implement data fetching module (`pipeline/fetch.py`)
- [x] Implement data cleaning pipeline (`pipeline/clean.py`)
- [x] Implement Cobb-Douglas estimation (`pipeline/estimate.py`)
- [x] Implement global aggregation (`pipeline/aggregate.py`)
- [x] Create main runner with logging (`main.py`)
- [x] Create Makefile for easy execution
- [ ] Install dependencies and run pipeline
- [ ] Validate: reproduce $2.53 result within tolerance
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

1. **Run the reproduction pipeline**
   ```bash
   cd /Users/kyle/share/devel/chip/reproduction
   make setup
   source .venv/bin/activate
   cp ../secrets.example.toml ../secrets.toml
   # Edit ../secrets.toml to add FRED API key
   make run
   ```
2. **Validate reproduction** — confirm result is within 5% of $2.53
3. **Complete weighting-analysis.md Section 4** — use reproduction data for empirical comparison

---

*This file tracks detailed progress. For high-level project overview, see [`../README.md`](../README.md).*

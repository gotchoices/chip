# CHIP Valuation Project

Estimating the global value of one hour of unskilled labor to serve as the basis for the [CHIP currency](https://gotchoices.org/book/epub/gotchoices.epub).

## Background

The **CHIP** (Credit Hour In Pool) is a proposed currency anchored to the value of human time. From the [formal definition](https://gotchoices.org/mychips/definition.html):

> Credit for the *value* produced by one continuously applied hour of adult human work; in such circumstance where there is neither a shortage nor a surplus of such willing labor available; and where the job can be reasonably understood with only minimal training and orientation; and without considering the added productivity due to the use of labor-saving capital equipment; and where the person performing the work has a normal, or average, functioning mind and body...

In essence: **What would one hour of nominal unskilled labor be worth in a hypothetical worldwide, free, and balanced market with no borders, tariffs, or other distortions?**

The term "nominal unskilled" (from the canonical definition) is important: it does **not** mean "no skills." A CHIP-rate worker can read, write, communicate, and do basic arithmetic—they simply lack *specialized* training. One CHIP equals one hour of this baseline labor. Skilled labor is valued as multiples of CHIPs based on training, expertise, and productivity.

This project aims to quantify that base value using global labor market data and economic theory.

## Design Goals

The CHIP estimator exists to serve a practical purpose: anchoring the
[MyCHIPs](https://gotchoices.org/mychips/) credit system to the real value of
human labor. The following goals guide both the research and the eventual
production pipeline.

### Core Definition

1. **Nominal labor index.** CHIP is denominated in current (nominal) dollars,
   not inflation-adjusted dollars. One CHIP represents what one hour of
   unskilled labor is worth *today*, at today's prices. (See the
   [formal definition](https://gotchoices.org/mychips/definition.html).)

2. **Global, objective measure.** CHIP is derived from publicly available
   world data (ILOSTAT, Penn World Tables), not from any single country or
   proprietary source. It should be reproducible by anyone with access to the
   same data.

### Inflation Behavior

3. **Inflation immunity.** When a currency loses purchasing power, the CHIP
   value stated in that currency should rise proportionally. A user holding
   CHIPs is holding labor-hours, not dollars — their value is preserved as
   currencies inflate. This is a *feature* of using labor as the index.

4. **Real changes are accepted.** If the real demand for unskilled human labor
   shifts (due to automation, demographics, or other structural forces), CHIP
   reflects that change honestly. Ideally, we can quantify the real component
   separately from inflation. (See `docs/labor-value-future.md` for analysis of
   long-term labor demand under AI/automation.)

### Operational Stability

5. **Periodic, repeatable estimation.** The CHIP value is recalculated
   periodically (at least annually) using fresh data. The pipeline must be
   automated and deterministic — same data in, same number out.

6. **Continuity between updates.** When new data arrives and the index is
   recalculated, the update should not produce a large discontinuity. Between
   official recalculations, the CHIP value can be extrapolated using CPI or a
   similar price index, so the next official value is largely predictable and
   requires only a small correction.

7. **Stable methodology.** Changes to the estimation methodology should be
   rare and well-justified. Users and implementors need confidence that the
   number won't shift dramatically due to a modeling decision.

### Practical Use

8. **Actionable for MyCHIPs.** The published CHIP value must be immediately
   usable: a user sees "1 CHIP = $X.XX" in their native currency, with no
   further calculation required. The estimate should be date-stamped and
   expressed in nominal terms. (See `docs/inflation-tracking.md` Sec 4 for the
   academic-vs-practical tension.)

9. **Transparent and auditable.** The data sources, methodology, and code are
   open. Anyone can verify how the number was derived, reproduce it, or propose
   improvements.

## Project Structure

```
chip/
├── original/          # Read-only reference: original R-based studies
├── reproduction/      # Python reproduction of original methodology
├── workbench/         # Exploratory analysis environment (active)
│   ├── lib/           # Modular Python library
│   ├── studies/       # Individual research investigations
│   └── data/          # Cached data (gitignored, self-healing)
├── estimates/         # Production estimates (to be created)
└── docs/              # Methodology reviews, papers, formal analysis
```

### `original/`

The original CHIP valuation research (R-based, read-only reference):
- **Initial study**: Estimated CHIP value at **$2.53/hour** using Solow-Swan growth model
- **ICT extension**: Explored whether ICT capital explains developed/developing wage gaps
- See [`original/README.md`](original/README.md) for details

## Research Journey

This project follows a deliberate progression from understanding existing work to developing improved methodologies.

### Step 1: Original Study ✅
**Folder**: [`original/`](original/)

Started with an R-based academic study that estimated CHIP at **$2.53/hour** using:
- Solow-Swan growth model with Cobb-Douglas production function
- ILOSTAT labor data + Penn World Tables macro data
- GDP-weighted global aggregation
- GDP deflation to 2017 constant dollars

### Step 2: Critical Analysis ✅
**Paper**: [`docs/original-review.md`](docs/original-review.md)

Analyzed the original methodology:
- Evaluated theoretical framework and assumptions
- Assessed alignment with canonical CHIP definition
- Identified strengths (rigorous, data-driven) and limitations (composition effects, deflation)
- Explored weighting alternatives: [`docs/weighting-analysis.md`](docs/weighting-analysis.md)

### Step 3: Python Reproduction ✅
**Folder**: [`reproduction/`](reproduction/)

Replicated the original study in Python:
- Achieved **$2.56/hour** (within 1% of original)
- Created configurable pipeline with logging
- Validated data handling and methodology
- Established baseline for further experimentation

### Step 4: Stress Testing & Hypothesis Formation ✅
**Paper**: [`docs/inflation-tracking.md`](docs/inflation-tracking.md)

Subjected the reproduction to sensitivity analysis:
- Tested different year windows (2006-2008, 2010-2012, 2014-2016, 2017-2019)
- Discovered significant sensitivity to country composition
- Identified mismatch between academic methodology and practical MyCHIPs needs
- **Key finding**: The GDP deflator, while academically appropriate, conflicts with CHIP's purpose as a nominal labor-value index

Formulated testable hypotheses:
- H1: Nominal CHIP should track inflation
- H2: Deflated CHIP is stable when country sample is held constant
- H3: Windowed averaging produces coherent time series
- H4: Recent-year nominal CHIP is more actionable for users

### Step 5: Future Labor Value Analysis ✅
**Paper**: [`docs/labor-value-future.md`](docs/labor-value-future.md)

Explored the long-term question: Will AI/automation make human labor more or less valuable?
- Standard narrative: Supply/demand says less valuable
- Contrarian view: Reservation wage argument says more valuable (leisure becomes the alternative)
- Bifurcation hypothesis: Commoditized tasks → worthless; human-presence tasks → premium
- Implications for CHIP's long-term viability
- Market-based analysis only (no redistribution schemes)

### Step 6: Workbench Development ✅
**Folder**: [`workbench/`](workbench/)

Created a modular exploratory analysis environment:
- **Independent from reproduction/** — can evolve freely without breaking the validated baseline
- **Modular library** (`workbench/lib/`) — 11 modules: fetcher, normalize, clean, impute, pipeline, models, aggregate, output, config, cache, logging
- **Self-healing cache** — delete data, it auto-fetches on next run
- **Study-based structure** — each investigation lives in `studies/<name>/` with its own `study.py`, `README.md`, `FINDINGS.md`, and `output/`
- **Reusable by future projects** — `estimates/` will import from `workbench.lib`

Completed studies:
- `baseline` ✅ — reproduces original methodology ($2.33/hr, within 1% of target)
- `coverage` ✅ — data coverage analysis (123 viable countries, 2000–2019 range)
- `timeseries` ✅ — year-by-year CHIP series, stable panel, inflation tracking; key discovery that deflation cancels in the CHIP formula

Planned studies:
- `production` — trailing-window methodology for current-year estimates (Design Goal 5–6)
- `stability` — vintage stability, update continuity, change decomposition (Design Goal 6–7)
- `weighting` — GDP vs labor vs unweighted aggregation sensitivity

### Step 7: Production Estimates (Next)
**Folder**: `estimates/` (to be created)

Will implement and test the hypotheses from Step 4:
- Build pipeline with nominal (non-deflated) output option
- Implement trailing window methodology
- Produce time series of annual CHIP values
- Validate against official inflation benchmarks
- Establish annual update process for MyCHIPs

### Future: Alternative Models
**Paper outline**: [`docs/alternative-models.md`](docs/alternative-models.md)

Explore whether different economic models yield materially different results:
- CES production functions
- Stochastic frontier analysis
- Direct wage comparison methods

---

## Reading Guide

The papers in `docs/` build on each other. For readers new to this project:

1. **[Original Study Review](docs/original-review.md)** -- What the original study did, how it works, and where it falls short. Start here.
2. **[Data Sources](docs/data-sources.md)** -- The three external data sources (ILOSTAT, PWT, FRED): what they provide, their coverage and limitations, versioning policy, and alternatives.
3. **[Weighting Analysis](docs/weighting-analysis.md)** -- Deep dive into one specific limitation: how country-level values are aggregated into a global CHIP.
4. **[Inflation Tracking](docs/inflation-tracking.md)** -- The central methodological question: should CHIP track inflation? Argues yes, proposes alternatives, formulates testable hypotheses (H1-H4).
5. **[Future Labor Value](docs/labor-value-future.md)** -- Will AI/automation make human labor worthless? Explores long-term viability of a labor-anchored currency.
6. **[Alternative Models](docs/alternative-models.md)** -- (Outline) Other economic models that could replace or supplement Cobb-Douglas.

---

## Project Phases (Summary)

| Phase | Focus | Status |
|-------|-------|--------|
| **1. Foundation** | Understand & validate original study | ✅ Complete |
| **2. Workbench** | Build modular analysis environment | ✅ Infrastructure complete, research scripts next |
| **3. Production** | Implement improved methodology | Next |
| **4. Alternatives** | Explore other models | Planned |

## Platform & Tooling

**Decision: Python** for all new work.
- Mature data science ecosystem (pandas, statsmodels, linearmodels)
- Excellent API clients for data sources (ilostat, pandas-datareader)
- Faster iteration than compiled languages
- Sufficient performance for periodic batch updates

## Data Sources

| Source | Data | Notes |
|--------|------|-------|
| **ILOSTAT** | Employment, wages, hours by occupation | Primary labor data |
| **Penn World Tables** | GDP, capital stock, human capital index | Primary macro data |
| **FRED** | US GDP deflator | Inflation adjustment only |
| **World Bank API** | Alternative/supplementary | To evaluate |
| **OECD.Stat** | ICT capital, productivity | Used in ICT extension |

## Current Status

**Phase 2 (Workbench) research studies substantially complete. Transitioning to production methodology.**

Recent milestones:
- ✅ Reproduction validated at $2.56/hour (original data) and $2.35/hour (fresh API)
- ✅ Workbench baseline validated at $2.33/hour (matches reproduction within 1%)
- ✅ All 11 library modules implemented (including shared `pipeline.py`)
- ✅ Inflation-tracking analysis complete with testable hypotheses (H1-H4)
- ✅ Time series study complete — deflation cancellation discovered, real CHIP ~$3.50/hr (stable panel), nominal tracking confirmed
- ✅ Coverage study complete — 123 viable countries, 79 excellent, recommended range 2000–2019
- 🔄 Current: Design production methodology studies (trailing window, vintage stability)
- 🔜 Next: Implement production pipeline, then create `estimates/` for official values

See [`docs/STATUS.md`](docs/STATUS.md) for detailed tracking.

## Setup

1. Copy `secrets.example.toml` to `secrets.toml`
2. Add your API keys to `secrets.toml` (this file is gitignored)
3. Get a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html

## Contributing

This is an exploratory project. Contributions welcome for:
- Economic modeling expertise
- Data engineering
- Statistical validation

## References

- Bateman, K. (2022). *Got Choices*. https://gotchoices.org
- Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). Penn World Table 10.0
- ILO. ILOSTAT Database. https://ilostat.ilo.org

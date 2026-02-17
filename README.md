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

6. **Two-tier update model.** The system operates at two cadences:
   - **Daily/weekly extrapolation:** A lightweight script applies the latest
     CPI (or GDP deflator) to the last official base value, publishing an
     up-to-date nominal CHIP. This runs automatically on a server and
     exposes an endpoint that MyCHIPs (and chipcentral.net) can query.
   - **Annual (or on-data) recalculation:** When new source data arrives
     (ILOSTAT wages, a new PWT release), the full pipeline re-estimates
     CHIP from scratch. The recalculated base value replaces the parameters
     used by the daily extrapolation script, "snapping" the published value
     to the more accurate estimate. The correction magnitude is recorded
     for transparency.

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

### Country-Level Outputs

10. **Country-specific multipliers.** In addition to the global CHIP value,
    the pipeline publishes per-country multipliers indicating how a country's
    actual unskilled labor compensation compares to the global CHIP. A
    multiplier of 0.6 means workers in that country are typically paid 60% of
    the global rate; a multiplier of 2.5 means 250%. This gives users in any
    country an intuitive sense of local labor valuation relative to the global
    norm. (The distortion factor θ and country-level CHIP values needed for
    this are already computed by the pipeline.)

11. **Queryable API.** The published CHIP value — global and per-country —
    should be available via a simple HTTP endpoint suitable for integration
    by MyCHIPs nodes, wallet apps, and third-party services. The current
    embodiment is the `updateCPI` cron script on mychips.org; the goal is to
    evolve this into a proper API backed by the `estimates/` pipeline.

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
- **Thesis:** AI amplifies labor productivity; labor value rises if tools are accessible at competitive prices, falls if concentrated by monopoly/regulatory capture
- The "access fork" — same technology, two opposite outcomes depending on market structure
- Regulatory paradox: heavy regulation favors concentration; open environments distribute capability
- CHIP's evolution from measured index (Phase 1) to market-discovered price (Phase 2)
- The tethered market: why CHIP resists speculation (labor as delivery mechanism)
- Advocacy conclusion: open AI is an economic prerequisite for labor value
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
- `production` ✅ — trailing-window methodology, PWT bridge, CPI extrapolation; **$3.17/hr nominal (2022), ~$3.50 est. 2026**
- `stability` ✅ — PWT vintage comparison (10.0 vs 11.0); mean |revision| 3.8% for mature years, upward bias
- `weighting` ✅ — five schemes (GDP, labor, unweighted, freedom, HDI); $1.67–$2.85 range; GDP-weighted ($2.68) recommended; 85 country multipliers

### Step 7: Production Estimates & Deployment (Next)
**Folder**: `estimates/` (to be created)

Build the operational CHIP pipeline using findings from completed studies:
- Implement 5-year trailing-window methodology (from `production` study)
- GDP-weighted aggregation (from `weighting` study)
- Two-tier update model: daily CPI extrapolation + annual recalculation (Design Goal 6)
- Publish country-specific multipliers via API endpoint (Design Goals 10–11)
- Snap-back mechanism when new source data arrives

### Future: Alternative Models
**Paper outline**: [`docs/alternative-models.md`](docs/alternative-models.md)

Explore whether different economic models yield materially different results:
- CES production functions
- Stochastic frontier analysis
- Direct wage comparison methods

### Future: Open Research Directions

The following areas could strengthen the CHIP methodology and are good
entry points for contributors:

- **Baumol effect quantification** — How fast does the real price of
  labor-intensive services rise relative to goods?  Provides a floor on
  CHIP's long-run real appreciation.  (See `docs/labor-value-future.md`
  Section 7.1.)
- **Automation exposure scoring** — What fraction of ISCO-9 (elementary
  occupations, CHIP's reference category) are at high risk of full
  automation vs. "human-presence" tasks?  (Section 7.2.)
- **Reservation wage estimation** — Is there a measurable relationship
  between a country's standard of living and the floor wage its workers
  will accept?  PWT + ILOSTAT data may answer this.  (Section 7.3.)
- **Labor share trends** — PWT's `labsh` variable tracks labor's share
  of national income.  Has the declining-labor-share narrative been
  uniform across countries, or is it concentrated in specific regulatory
  environments?  (Section 7.4.)
- **Bridge methodology improvements** — The `production` study tested
  freeze and slope methods for extending CHIP beyond the latest PWT
  release.  Better extrapolation approaches (e.g., incorporating
  preliminary national accounts data) could reduce snap-back magnitude.
- **Additional data sources** — World Bank, OECD, and ICP data could
  supplement or cross-validate ILOSTAT and PWT.  Evaluating these
  against existing sources would improve coverage and robustness.

---

## Reading Guide

The papers in `docs/` build on each other. For readers new to this project:

1. **[Original Study Review](docs/original-review.md)** -- What the original study did, how it works, and where it falls short. Start here.
2. **[Data Sources](docs/data-sources.md)** -- The three external data sources (ILOSTAT, PWT, FRED): what they provide, their coverage and limitations, versioning policy, and alternatives.
3. **[Weighting Analysis](docs/weighting-analysis.md)** -- How country-level values are aggregated into a global CHIP. Compares five weighting schemes (GDP, labor, unweighted, freedom, HDI); recommends GDP-weighted ($2.68/hr) with full range disclosure.
4. **[Inflation Tracking](docs/inflation-tracking.md)** -- The central methodological question: should CHIP track inflation? Argues yes, proposes alternatives, formulates testable hypotheses (H1-H4).
5. **[Future Labor Value](docs/labor-value-future.md)** -- Will AI raise or lower the value of labor? Argues that open AI access at competitive prices raises labor value; regulatory concentration lowers it. Includes CHIP's evolution from index to market price.
6. **[Alternative Models](docs/alternative-models.md)** -- (Outline) Other economic models that could replace or supplement Cobb-Douglas.

---

## Project Phases (Summary)

| Phase | Focus | Status |
|-------|-------|--------|
| **1. Foundation** | Understand & validate original study | ✅ Complete |
| **2. Workbench** | Build modular analysis environment & studies | ✅ Complete (6 studies, 5 papers) |
| **3. Production** | Estimates pipeline, automated publishing, API | Next |
| **4. Alternatives** | Explore other economic models | Planned |

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
| **Penn World Tables** | GDP, capital stock, human capital index, labor share | Primary macro data (10.0, 10.01, 11.0) |
| **FRED** | US GDP deflator, CPI-U | Inflation adjustment & extrapolation |
| **Heritage Foundation** | Index of Economic Freedom (0–100) | Weighting study |
| **UNDP** | Human Development Index (0–1) | Weighting study |
| **World Bank API** | Alternative/supplementary | To evaluate |
| **OECD.Stat** | ICT capital, productivity | Used in ICT extension |

## Current Status

**Phase 2 (Workbench) complete. All six studies finished, all documentation papers written. Transitioning to Phase 3 (production pipeline and deployment).**

Research milestones:
- ✅ Reproduction validated at $2.56/hour (original data) and $2.35/hour (fresh API)
- ✅ Workbench baseline validated at $2.33/hour (matches reproduction within 1%)
- ✅ All 11 library modules implemented (including Heritage and HDI fetchers)
- ✅ Production study complete — **$3.17/hr nominal (2022), ~$3.50 est. 2026** (PWT 11.0, 5-year trailing window)
- ✅ Stability study complete — PWT vintage revisions quantified (mean 3.8% for mature years)
- ✅ Weighting study complete — five schemes compared, GDP-weighted ($2.68) recommended, 85 country multipliers produced
- ✅ All five documentation papers written (original-review, weighting-analysis, inflation-tracking, labor-value-future, data-sources)
- 🔜 Next: Build `estimates/` pipeline, automated publishing (two-tier model), and API endpoint

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

# CHIP Valuation Project

Estimating the global value of one hour of unskilled labor to serve as the basis for the [CHIP currency](https://gotchoices.org/book/epub/gotchoices.epub).

## Background

The **CHIP** (Credit Hour In Pool) is a proposed currency anchored to the value of human time. From the [formal definition](https://gotchoices.org/mychips/definition.html):

> Credit for the *value* produced by one continuously applied hour of adult human work; in such circumstance where there is neither a shortage nor a surplus of such willing labor available; and where the job can be reasonably understood with only minimal training and orientation; and without considering the added productivity due to the use of labor-saving capital equipment; and where the person performing the work has a normal, or average, functioning mind and body...

In essence: **What would one hour of nominal unskilled labor be worth in a hypothetical worldwide, free, and balanced market with no borders, tariffs, or other distortions?**

The term "nominal unskilled" (from the canonical definition) is important: it does **not** mean "no skills." A CHIP-rate worker can read, write, communicate, and do basic arithmetic—they simply lack *specialized* training. One CHIP equals one hour of this baseline labor. Skilled labor is valued as multiples of CHIPs based on training, expertise, and productivity.

This project aims to quantify that base value using global labor market data and economic theory.

## Project Structure

```
chip/
├── original/          # Read-only reference: original R-based studies
├── reproduction/      # Python reproduction of original methodology
├── workbench/         # Exploratory analysis environment (active)
│   ├── lib/           # Modular Python library
│   ├── scripts/       # Analysis scripts
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

### Step 4b: Future Labor Value Analysis ✅
**Paper**: [`docs/labor-value-future.md`](docs/labor-value-future.md)

Explored the long-term question: Will AI/automation make human labor more or less valuable?
- Standard narrative: Supply/demand says less valuable
- Contrarian view: Reservation wage argument says more valuable (leisure becomes the alternative)
- Bifurcation hypothesis: Commoditized tasks → worthless; human-presence tasks → premium
- Implications for CHIP's long-term viability
- Market-based analysis only (no redistribution schemes)

### Step 5: Workbench Development ✅ (In Progress)
**Folder**: [`workbench/`](workbench/)

Created a modular exploratory analysis environment:
- **Independent from reproduction/** — can evolve freely without breaking the validated baseline
- **Modular library** (`workbench/lib/`) — fetcher, cleaner, models, aggregators, output generators
- **Self-healing cache** — delete data, it auto-fetches on next run
- **Reusable by future projects** — `estimates/` will import from `workbench.lib`

Scripts to implement:
- `analyze_data_coverage.py` — which countries have reliable data?
- `test_nominal_chip.py` — test hypothesis H1 (CHIP tracks inflation)
- `chip_time_series.py` — test H2, H3 (temporal stability)
- `compare_aggregators.py` — GDP vs labor vs freedom weighting

### Step 6: Production Estimates (Next)
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

## Project Phases (Summary)

| Phase | Focus | Status |
|-------|-------|--------|
| **1. Foundation** | Understand & validate original study | ✅ Complete |
| **2. Analysis** | Stress test, form hypotheses | ✅ Complete |
| **3. Workbench** | Build modular analysis environment | 🔄 In Progress |
| **4. Production** | Implement improved methodology | Next |
| **5. Alternatives** | Explore other models | Planned |
| **6. Automation** | Annual update pipeline | Planned |

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

**Phases 1-2 complete. Phase 3 (Workbench) in progress.**

Recent milestones:
- ✅ Reproduction validated at $2.56/hour
- ✅ Inflation-tracking analysis complete with testable hypotheses
- ✅ Labor-value-future paper explores AI/automation impact
- ✅ Workbench scaffolded with modular library and script stubs
- 🔄 Current: Complete workbench scripts, test hypotheses
- 🔜 Next: Create `estimates/` project to implement nominal CHIP methodology

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

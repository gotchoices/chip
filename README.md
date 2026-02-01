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
├── estimates/         # Production estimates using validated methods
│   └── YYYY-MM/       # Dated estimate runs
├── experiments/       # Alternative models, exploratory analysis
├── docs/              # Methodology reviews, papers, formal analysis
├── lib/               # Shared Python modules (data fetching, utilities)
└── data/              # Downloaded/cached data (gitignored)
```

### `original/`

The original CHIP valuation research (R-based, read-only reference):
- **Initial study**: Estimated CHIP value at **$2.53/hour** using Solow-Swan growth model
- **ICT extension**: Explored whether ICT capital explains developed/developing wage gaps
- See [`original/README.md`](original/README.md) for details

## Project Phases

### Phase 1: Foundation (Current)
Understand, document, and validate the original study.

- **Critical review** of original methodology ([`docs/original-review.md`](docs/original-review.md))
- **Weighting analysis** — explore GDP vs. labor-force weighting implications ([`docs/weighting-analysis.md`](docs/weighting-analysis.md))
- **Python reproduction** — replicate $2.53 result using same data/methodology

### Phase 2: Validation & Sensitivity
Test robustness of the original approach.

- Sensitivity analysis across weighting schemes
- Informal economy adjustments (where data permits)
- Temporal stability analysis

### Phase 3: Alternative Models
Explore whether different economic models yield materially different results.

- CES production functions
- Stochastic frontier analysis
- Direct wage comparison methods
- Model comparison framework ([`docs/alternative-models.md`](docs/alternative-models.md))

### Phase 4: Automation
Create a sustainable, periodic update process.

- Automated data fetching from ILOSTAT, PWT, FRED APIs
- Anomaly detection for data quality issues
- Reproducible pipeline with version control
- Target: Annual updates with minimal manual intervention

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

**Phase 1 in progress.** See [`docs/STATUS.md`](docs/STATUS.md) for detailed tracking.

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

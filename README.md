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

## Objectives

### 1. Reproduce Original Study in Python
Validate understanding by reproducing the $2.53 result using:
- The original source data (ILOSTAT, PWT, FRED)
- The same Cobb-Douglas / distortion-factor methodology
- Python instead of R

Success = matching the original result within reasonable tolerance.

### 2. Platform & Tooling
**Decision: Python** (not Rust) for this project.
- Mature data science ecosystem (pandas, statsmodels, linearmodels)
- Excellent API clients for data sources
- Faster iteration than compiled languages
- Sufficient performance for periodic batch updates

### 3. Data Sources
Document and evaluate all data sources:
| Source | Data | Notes |
|--------|------|-------|
| **ILOSTAT** | Employment, wages, hours by occupation | Primary labor data |
| **Penn World Tables** | GDP, capital stock, human capital index | Primary macro data |
| **FRED** | US GDP deflator | Inflation adjustment only |
| **World Bank API** | Alternative/supplementary | To evaluate |
| **OECD.Stat** | ICT capital, productivity | Used in ICT extension |

### 4. Methodology Review
Produce a formal review document (`docs/methodology-review.md`) covering:
- Strengths and limitations of the original approach
- **Definition alignment**: How well does the methodology match the canonical CHIP definition?
  - "Nominal unskilled labor" vs. ISCO-08 "elementary occupations"
  - Distortion factor as proxy for "free market" equilibrium
  - Capital separation via Cobb-Douglas
- Alternative models worth exploring (CES, stochastic frontier, etc.)
- Weighting scheme implications (GDP vs. labor-force weighted)
- Informal economy and data coverage issues

### 5. Alternative Models
Can different economic models be evaluated via the same pipeline?
- Fetch data → Clean → Apply model → Summarize
- Models as swappable modules
- Compare results across approaches

### 6. Automation
Create a sustainable, periodic update process:
- Automated data fetching from APIs
- Anomaly detection for data quality issues
- Reproducible pipeline with version control
- AI-assisted review of results and outliers
- Target: Annual updates with minimal manual intervention

## Current Status

- [x] Original study analyzed and documented
- [x] Platform decision: Python
- [ ] Reproduce original study in Python
- [ ] Methodology review document
- [ ] Automated data pipeline
- [ ] Alternative model experiments
- [ ] Production estimation workflow

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

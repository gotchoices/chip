# CHIP Valuation Project

Estimating the global value of one hour of unskilled labor to serve as the basis for the [CHIP currency](https://gotchoices.org/book/epub/gotchoices.epub).

## Background

The CHIP (Credit Hour In Pool) is a proposed currency anchored to the value of human time. This project aims to quantify that value using global labor market data and economic theory.

## Project Structure

```
chip/
├── original/     # Original human-authored studies (R-based)
└── [new study]   # AI-assisted replication and extension (planned)
```

### `original/`

Contains the original CHIP valuation research:
- **Initial study**: Estimated CHIP value at **$2.53/hour** using Solow-Swan growth model
- **ICT extension**: Explored whether ICT capital explains developed/developing wage gaps
- See [`original/README.md`](original/README.md) for details

## New Study Goals

This project will develop an AI-assisted approach to CHIP valuation, addressing:

### 1. Platform Selection
Is Rust the optimal platform for CHIP calculations?
- Performance requirements for periodic updates
- Data pipeline complexity
- Ecosystem maturity for econometrics
- Alternatives: Python, Julia, R

### 2. Economic Model Review
Is there a better model than Cobb-Douglas with country fixed effects?
- CES production functions
- Stochastic frontier analysis
- Machine learning approaches
- Panel cointegration methods

### 3. Definition Alignment
Does the current methodology match the CHIP definition?
- "One hour of basic work" vs. ISCO-08 "elementary occupations"
- Global weighting scheme (GDP-weighted vs. labor-weighted vs. equal)
- Treatment of informal economy
- Purchasing power considerations

### 4. Automation
Can we create a sustainable update process?
- Automated data fetching from ILOSTAT, PWT, FRED APIs
- Anomaly detection for data quality issues
- Reproducible pipeline with version control
- AI-assisted review of results and outliers
- Target: Quarterly or annual updates with minimal manual intervention

## Current Status

- [x] Original study analyzed and documented
- [ ] Platform evaluation
- [ ] Model comparison framework
- [ ] Automated data pipeline
- [ ] New valuation methodology
- [ ] Validation against original results

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

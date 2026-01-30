# Original CHIP Valuation Study

This folder contains the original CHIP valuation research conducted by an anonymous Ph.D. economist, commissioned by Kyle Bateman.

## Purpose

Estimate the global value of one hour of unskilled labor, adjusted for market distortions, to serve as the baseline value for the CHIP currency.

**Main Finding:** **$2.53 per hour** (89 countries, 1992-2019)

## Folder Structure

```
Code/       R analysis scripts
Data/       Input datasets and generated outputs
writeup/    LaTeX paper and figures
```

## Code Versions

| File | Description |
|------|-------------|
| `chips_old.R` | Baseline version using pre-downloaded CSV files |
| `chips.R` | Current version with live API data fetching |
| `chips_with_ict_capital.R` | Extended version incorporating ICT capital data |

## Key Concepts (Not Obvious from Inspection)

### The Economic Model

Uses a Cobb-Douglas production function estimated per-country:
```
Y = K^α × (h × Σ aᵢLᵢ)^(1-α)
```
- `α` = capital share (estimated via fixed-effects regression)
- `h` = human capital index (from PWT)
- `aᵢ` = skill weight (wage ratio relative to managers)
- `Lᵢ` = labor hours by occupation

### Distortion Factor (DF)

The ratio of theoretical marginal product of labor to actual wages:
```
θ = MPL / wage
```
- θ = 1: Perfect market
- θ > 1: Workers underpaid
- θ < 1: Workers overpaid

### The Five "chips" Variables

| Variable | Capital Measure | Labor Measure | Notes |
|----------|----------------|---------------|-------|
| `chips1` | None (α=0) | Effective hours | Just wage weighting |
| `chips2` | rnna (national prices) | Total hours | Ignores skill differences |
| `chips3` | cn (PPP) | Total hours | Ignores skill differences |
| `chips4` | rnna (national prices) | **Effective hours** | **PREFERRED** |
| `chips5` | cn (PPP) | Effective hours | PPP conversion |

### "Effective Labor"

Labor hours weighted by relative productivity:
```
Effective_Labor = Σ (hours_i × wage_i / wage_managers)
```
This accounts for the fact that a manager-hour contributes more than an elementary-worker-hour.

### Why "Elementary Occupations"?

ISCO-08 category 9 ("Elementary occupations") represents unskilled labor—the CHIP definition. The final CHIP value is the elementary wage × distortion factor, weighted by GDP.

## Setup

The R scripts require a FRED API key. Copy `../secrets.example.toml` to `../secrets.toml` and add your key. See the main [README](../README.md) for details.

## Data Sources

- **ILOSTAT**: Employment, wages, hours worked by occupation
- **Penn World Tables 10.0**: GDP, capital stock, human capital index
- **FRED**: US GDP deflator for inflation adjustment
- **EU KLEMS / OECD**: ICT capital data (extended version only)

## Known Issues / Outliers Removed

The code manually excludes several country-years with suspected data errors:
- Albania 2012, Ghana 2017, Egypt 2009, Rwanda 2014
- Cambodia, Laos, Timor-Leste (entire countries)
- Various other specific observations

## Outputs

- `Data/table1.tex`: Summary statistics for distortion factors
- `Data/time_series.xlsx`: CHIP values 2017-2022
- `writeup/chips_note.pdf`: Full research paper

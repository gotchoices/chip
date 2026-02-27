# CHIP Production Methodology

*The locked methodology for computing the official CHIP value.*

**Status:** COMPLETE  
**Last updated:** 2026-02-24

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Scope](#2-scope)
3. [Data Inputs](#3-data-inputs)
4. [Pipeline Steps](#4-pipeline-steps)
   - 4.1 Data Acquisition and Normalization
   - 4.2 Effective Labor Construction
   - 4.3 Capital Share Estimation
   - 4.4 CHIP Estimation (Marginal Product of Labor)
   - 4.5 GDP-Weighted Annual Aggregation
   - 4.6 5-Year Trailing Window
   - 4.7 Country Multipliers
   - 4.8 CPI Reference Capture
5. [Extrapolation Between Recalculations](#5-extrapolation-between-recalculations)
6. [Key Parameters](#6-key-parameters)
7. [Design Decisions and Rationale](#7-design-decisions-and-rationale)
   - 7.1 Why GDP Weighting?
   - 7.2 Why a 5-Year Window?
   - 7.3 Why CPI-U for Extrapolation?
   - 7.4 Why Constant National Prices (Not PPP)?
   - 7.5 Why MICE Imputation?
8. [Known Limitations](#8-known-limitations)
9. [Validation and Confidence](#9-validation-and-confidence)
10. [References](#10-references)

---

## 1. Purpose

This document describes the methodology used by the `estimates/` pipeline
to compute the official CHIP (Credit Hour In Pool) value.  It is intended
for:

- **Auditors** who want to verify the calculation
- **Replicators** who want to reproduce it independently
- **Consumers** (MyCHIPs, chipcentral.net) who need to understand what the
  published number represents

The methodology was developed through six workbench studies (baseline,
coverage, timeseries, production, stability, weighting) and is now locked
for production use.  Changes require explicit justification and
documentation.

## 2. Scope

The production pipeline computes:

1. **Global CHIP value** — the estimated price of one hour of unskilled
   labor in a hypothetical distortion-free global market, expressed in
   nominal US dollars.
2. **Country multipliers** — per-country ratios indicating how each
   country's implied labor value compares to the global average.
3. **CPI-extrapolated current value** — a lightweight update between annual
   recalculations, applying US consumer price changes to the last computed
   base value.

It does **not** compute:

- PPP-adjusted values (the pipeline uses constant national prices)
- Informal economy adjustments
- Alternative production function specifications (CES, translog)

These are acknowledged limitations and potential areas for future research.

## 3. Data Inputs

| Source | Dataset | Role |
|--------|---------|------|
| **ILOSTAT** | Employment by occupation (`EMP_TEMP_SEX_OCU_NB_A`) | Hours worked by skill level |
| **ILOSTAT** | Hourly earnings by occupation (`EAR_4HRL_SEX_OCU_CUR_NB_A`) | Observed wages by skill level |
| **ILOSTAT** | Hours worked by occupation (`HOW_TEMP_SEX_OCU_NB_A`) | Actual hours per occupation |
| **Penn World Tables** | Real GDP (`rgdpna`), Capital stock (`rnna`), Human capital (`hc`) | Production function inputs |
| **FRED** | US GDP implicit price deflator (`GDPDEF`) | Deflating to constant dollars |
| **FRED** | US CPI-U (`CPIAUCSL`) | Monthly extrapolation between recalculations |

For detailed source documentation, see `docs/data-sources.md`.

## 4. Pipeline Steps

### 4.1 Data Acquisition and Normalization

Raw data is fetched from ILOSTAT (REST API), Penn World Tables (Excel
download), and FRED (API or CSV).  All datasets are cached locally in
Parquet format for reproducibility and speed.

Normalization standardizes column names, country codes (ISO 3166-1 alpha-3),
and time periods.  The GDP deflator is rebased to the PWT constant-dollar
reference year (2017 = 100).

### 4.2 Effective Labor Construction

Labor hours are weighted by relative productivity to construct "effective
labor" — a single quantity reflecting the skill-adjusted labor input.

**Wage ratios** are computed for each country-year by dividing each
occupation's hourly wage by the managerial wage:

$$a_i = \frac{w_i}{w_\text{managers}}$$

**Effective labor** is then:

$$L_s = h \cdot \sum_{i} a_i \cdot \text{Hours}_i$$

where $h$ is the PWT human capital index (based on years of schooling and
returns to education).

Missing wage ratios are imputed using regression-based methods (see
Section 4.3).

### 4.3 Capital Share Estimation

The capital share $\alpha$ (capital's fraction of output) is estimated
per-country using fixed-effects regression on the intensive form:

$$\ln\!\left(\frac{Y}{L_s}\right) = \alpha \cdot \ln\!\left(\frac{K}{L_s}\right) + \epsilon$$

Estimates outside the valid range ($0 < \alpha < 1$) are discarded.
Missing values are imputed using MICE-style linear regression (iterative
conditional imputation of both wage ratios and alpha).

### 4.4 CHIP Estimation (Marginal Product of Labor)

For each country-year, the marginal product of labor is:

$$MPL = (1 - \alpha) \cdot \left(\frac{K}{L_s}\right)^\alpha$$

The distortion factor captures the gap between theoretical equilibrium and
observed wages:

$$\theta = \frac{MPL}{w_\text{avg}}$$

The country-level CHIP value is the distortion-adjusted elementary wage:

$$\text{CHIP}_j = \theta_j \cdot w_{\text{elementary}, j}$$

This yields a constant-dollar CHIP per country per year, expressed in PWT
base-year (2017) US dollars.

### 4.5 GDP-Weighted Annual Aggregation

Country-level values are aggregated to a single global CHIP per year:

$$\text{CHIP}_t = \frac{\sum_j \text{CHIP}_{j,t} \cdot \text{GDP}_{j,t}}{\sum_j \text{GDP}_{j,t}}$$

where GDP is real GDP at constant national prices (`rgdpna` from PWT).

Years with fewer than 5 countries reporting are excluded.

### 4.6 5-Year Trailing Window

The annual series is smoothed using a 5-year trailing window.  For target
year $T$:

1. Collect constant-dollar CHIP values for years $[T{-}4, \ldots, T]$
2. Re-inflate each to target-year dollars using the GDP deflator:
   $\text{CHIP}_y^\text{nominal} = \text{CHIP}_y^\text{constant} \times \frac{\text{deflator}_T}{100}$
3. Average the re-inflated values

This produces the **headline nominal CHIP value** for year $T$.

### 4.7 Country Multipliers

For each country with data in the target year:

$$\text{multiplier}_j = \frac{\text{CHIP}_{j,T}^\text{constant}}{\text{CHIP}_\text{global}^\text{constant}}$$

A multiplier of 1.28 means the country's implied labor value is 28% above
the global average.

### 4.8 CPI Reference Capture

At recalculation time, the latest CPI-U observation is fetched from FRED
and stored alongside the estimate.  This serves as the baseline for
extrapolation (Section 5).

## 5. Extrapolation Between Recalculations

Between annual recalculations, the CHIP value is updated using CPI-U:

$$\text{CHIP}_\text{now} = \text{CHIP}_\text{base} \times \frac{\text{CPI}_\text{now}}{\text{CPI}_\text{base}}$$

This assumes real CHIP is unchanged and all movement is due to US dollar
inflation.  The production study found that CPI extrapolation introduces a
mean correction of approximately −0.7% per year (std 6.4%), with
corrections that are mean-reverting even through major disruptions like
COVID.

The extrapolator runs on the production server (typically weekly via cron)
and writes to a local cache file that is not tracked in version control.
When a new annual recalculation is published, the extrapolator automatically
detects the updated base and adjusts accordingly.

## 6. Key Parameters

All parameters are locked in `estimates/config.yaml`:

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `pwt_version` | 11.0 | Penn World Table version |
| `pwt_base_year` | 2017 | Constant-dollar reference year |
| `year_start` | 1992 | Earliest year for pipeline input |
| `year_end` | 2023 | Latest year for pipeline input |
| `window_years` | 5 | Trailing-window size |
| `weighting` | gdp | Aggregation weighting scheme |
| `enable_imputation` | true | MICE imputation for missing values |
| `wage_averaging` | simple | Wage ratio averaging method |
| `min_countries` | 5 | Minimum countries per year |
| `cpi_u` | CPIAUCSL | FRED series for extrapolation |

## 7. Design Decisions and Rationale

### 7.1 Why GDP Weighting?

Five weighting schemes were tested (GDP, labor-force, unweighted, freedom
index, HDI).  Results ranged from $1.67 (labor-force) to $2.85 (freedom),
with GDP-weighted at $2.68.

GDP weighting was retained because:
- It gives proportionate influence to both population size and economic
  activity — large, productive economies count more.
- It avoids ideological inputs (unlike freedom or HDI weighting).
- It was used in the original study, providing continuity.
- It is neither the highest nor lowest value, sitting near the median.

See `docs/weighting-analysis.md` for the full five-scheme comparison and
elimination rationale.

### 7.2 Why a 5-Year Window?

Single-year CHIP estimates exhibit ~20% year-over-year volatility, driven
largely by which countries report data in a given year.  The 5-year trailing
window reduces this to ~5% while preserving the same long-run mean.

The 3-year window was also tested (6.8% volatility) but the 5-year window
was preferred for its additional smoothness and its better handling of
data-sparse early years.

### 7.3 Why CPI-U for Extrapolation?

CPI-U (Consumer Price Index for All Urban Consumers) was chosen over the
GDP deflator for monthly extrapolation because:
- It is updated monthly (GDP deflator is quarterly)
- It is widely understood and reported
- It directly measures what consumers experience as inflation

The production study tested CPI extrapolation accuracy and found corrections
are small and mean-reverting, validating CPI-U as a practical interim
measure.

### 7.4 Why Constant National Prices (Not PPP)?

The CHIP pipeline uses PWT's `rgdpna` (real GDP at constant national
prices) rather than PPP-adjusted output.  This choice follows the original
study and avoids introducing a second layer of cross-country price
adjustment on top of the distortion factor.  The distortion factor already
adjusts for the gap between observed wages and theoretical equilibrium.

### 7.5 Why MICE Imputation?

Many country-years have partial data (e.g., employment counts but no wages
for some occupations, or missing capital share estimates).  Rather than
dropping these observations entirely, the pipeline uses MICE-style
(Multiple Imputation by Chained Equations) linear regression to fill gaps.

This increases the effective sample size (particularly in early years where
coverage is sparse) without introducing systematic bias, as demonstrated
by the baseline study's close match to the original methodology.

## 8. Known Limitations

1. **Informal economy bias**: ILOSTAT primarily captures formal-sector
   wages.  In developing countries, informal workers (often lower-paid)
   are underrepresented.  This likely biases the global estimate upward.

2. **Capital separation is approximate**: The Cobb-Douglas function
   separates capital and labor contributions econometrically, but observed
   wages already reflect the tools workers use.  The separation is
   theoretically sound but practically approximate.

3. **Country composition effects**: The number of reporting countries
   varies by year (5 in 2000, 64 in 2014, 46 in 2022).  Years with fewer
   countries are less representative.  The 5-year trailing window mitigates
   this but does not eliminate it.

4. **PWT vintage sensitivity**: When PWT releases a new version with
   revised data, CHIP values change.  The stability study found mean
   |revision| of 3.8% for mature years (2002–2019) with a consistent
   upward bias of +5.9%.

5. **Single production function**: Only the Cobb-Douglas specification
   is used.  CES, translog, and direct-wage alternatives remain untested.

6. **CPI extrapolation drift**: Between recalculations, the CPI
   extrapolation assumes constant real CHIP.  Corrections of ±6-12% are
   possible in disrupted periods (e.g., COVID), though they are
   mean-reverting.

## 9. Validation and Confidence

The methodology has been validated through multiple independent checks:

| Check | Result |
|-------|--------|
| Python reproduction of original R study | $2.35/hr vs original $2.53 (data vintage effect) |
| Workbench baseline (independent implementation) | $2.33/hr (1% of reproduction) |
| CPI extrapolation from original base ($2.53 → 2022) | $3.18 — matches pipeline's $3.17 |
| PWT 10.0 → 11.0 vintage comparison | Mean |revision| 3.8% for 2002–2019 |
| 5-year CPI extrapolation accuracy | Mean correction −0.7%, std 6.4% |

The 23-year backfilled series (2000–2022) shows a nominal CHIP rising from
$1.94 to $3.27, consistent with US inflation over the period.  The
constant-dollar series fluctuates between $2.26 and $3.12 without a
persistent trend, consistent with the hypothesis that real labor value is
approximately stable.

**Confidence statement**: The current nominal CHIP of **$3.27/hr** (2022
base year) is a defensible central estimate.  Methodological choices
(primarily weighting) could shift it by ±20%.  Data limitations (informal
economy, country coverage) introduce additional uncertainty that is
difficult to quantify but likely skews upward.

## 10. References

Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). The Next Generation
of the Penn World Table. *American Economic Review*, 105(10): 3150-3182.

International Labour Organization. ILOSTAT Database.
https://ilostat.ilo.org

Solow, R.M. (1956). A Contribution to the Theory of Economic Growth.
*The Quarterly Journal of Economics*, 70(1): 65-94.

van Buuren, S. & Groothuis-Oudshoorn, K. (2011). MICE: Multivariate
Imputation by Chained Equations in R. *Journal of Statistical Software*,
45(3): 1-67.

---

*For operational details (how to run the scripts, backfill, deploy),
see `estimates/README.md`.  For the original study critique, see
`docs/original-review.md`.  For the weighting rationale, see
`docs/weighting-analysis.md`.*

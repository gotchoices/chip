# Baseline Reproduction

## Research Question

Can we reproduce the original CHIP estimate ($2.56/hour) using an independent
Python implementation of the same Cobb-Douglas production function methodology?

## Hypothesis

Using the same data sources (ILOSTAT, Penn World Tables, FRED deflator) and the
same methodology (skill-weighted effective labor, fixed-effects alpha estimation,
GDP-weighted global aggregation), we should get a value within 10% of $2.56.

With fresh API data (vs the original study's frozen CSV snapshots), we expect a
slightly different result due to data revisions. The reproduction pipeline yields
$2.35 with fresh data, so that is the primary validation target.

## Methodology

1. Fetch labor data (employment, wages, hours) for all 9 ISCO occupation groups
2. Calculate wage ratios relative to Managers (skill weights)
3. Compute effective labor: sum of hours x skill_weight across occupations
4. Merge with Penn World Tables (capital stock, GDP, human capital index)
5. Estimate capital share (alpha) via fixed-effects regression on full PWT data
6. Calculate Marginal Product of Labor using Cobb-Douglas formula
7. Derive distortion factor (theta = MPL / average_wage)
8. Adjust elementary (unskilled) wage by distortion factor to get per-country CHIP
9. GDP-weighted global average

Key implementation details documented in the study script's header:
wage ratios per country-year (not averaged first), alpha estimated on full PWT
data (not just rows with wages), simple mean for average wage, MICE-style
imputation for missing alphas.

## Status

**Complete.** Result: $2.33/hour (0.9% deviation from reproduction target of $2.35).
Validation: PASSED.

# Baseline Reproduction — Findings

## Results

**Calculated CHIP: $2.33/hour** (GDP-weighted global average, 1992–2019)

| Metric | Value |
|--------|-------|
| Calculated CHIP | $2.33/hr |
| Target (fresh API data) | $2.35/hr |
| Deviation | -1.0% |
| Validation | **PASSED** |
| Countries | 99 |
| Country-year observations | 618 |
| Mean capital share (alpha) | 0.650 |
| Mean distortion factor (theta) | 1.764 |

The original study reports $2.56/hr using frozen CSV data. The reproduction
pipeline yields $2.35/hr with fresh API data. Our independent workbench
implementation produces $2.33/hr — within 1% of the reproduction target and
within 10% of the original study.

### Top 10 Countries by CHIP Value

| Country | CHIP ($/hr) | Elem. Wage | Theta | Alpha |
|---------|-------------|------------|-------|-------|
| CHE | $4.94 | $37.91 | 0.13 | 0.61 |
| IRL | $4.53 | $20.10 | 0.23 | 0.83 |
| BEL | $4.44 | $16.82 | 0.27 | 0.59 |
| LUX | $4.30 | $17.92 | 0.24 | 0.53 |
| AUT | $4.27 | $14.26 | 0.30 | 0.60 |
| SWE | $4.25 | $17.02 | 0.25 | 0.60 |
| FRA | $4.25 | $12.50 | 0.34 | 0.60 |
| FIN | $3.94 | $22.53 | 4.83 | 0.61 |
| DEU | $3.79 | $13.87 | 0.27 | 0.62 |
| USA | $3.70 | $16.88 | 0.22 | 0.79 |

The ranking is economically plausible: high-wage OECD economies dominate
the top, with Switzerland's high elementary wage driving its leading position.

## Interpretation

The close match ($2.33 vs $2.35, -1.0%) confirms that our independent Python
implementation correctly reproduces the original Cobb-Douglas methodology.
The small deviation is well within the expected tolerance from:

- Data vintage differences (ILOSTAT revises historical data)
- Country name harmonization (99 vs 90 countries in the reproduction)
- Numerical precision in regression-based alpha estimation

This gives us confidence that the `lib/pipeline.py` module correctly
implements the CHIP estimation methodology and can be reliably used as the
foundation for other studies (timeseries, weighting, nominal).

### Key Implementation Lessons

Five implementation details were critical to matching the reproduction:

1. **Wage ratios per country-year first.** Calculate wage/manager_wage for
   each country-year observation, then average across years. Not: average
   wages first, then compute ratio.

2. **Keep all employment data.** Wage ratios are computed from rows with
   wages, but effective labor is computed from ALL employment rows (using
   fillna(1.0) for missing ratios).

3. **Alpha on full PWT data.** The capital share regression uses all
   country-years with PWT data (~2000 obs), not just those with wage data
   (~650 obs). This stabilizes the alpha estimates.

4. **Simple mean for average wage.** The reproduction uses an unweighted
   mean across occupations, not a labor-weighted average.

5. **MICE-style imputation.** Missing alphas are imputed via regression on
   ln(GDP/worker) and ln(capital/worker), not dropped.

## Limitations

1. **Data vintage sensitivity.** The $0.21 gap between the original ($2.56)
   and fresh-API ($2.35) results shows that ILOSTAT data revisions materially
   affect the estimate. Any production CHIP should document its data vintage.

2. **Country count differs.** The workbench finds 99 countries vs the
   reproduction's 90. The additional 9 countries come from improved country
   harmonization and do not significantly shift the GDP-weighted result
   (small economies).

3. **Theta outliers.** Slovakia (SVK) has theta = 60.25, suggesting a
   wage data anomaly. Finland (FIN) has theta = 4.83. These are absorbed
   by GDP weighting but warrant investigation if country-level CHIP values
   are used directly.

4. **Single cross-section.** Baseline aggregates all years into one number.
   It does not reveal trends or stability. See the timeseries study for
   year-by-year analysis.

5. **GDP weighting dominance.** The USA alone accounts for a large share
   of the GDP-weighted average. See the weighting study (planned) for
   sensitivity analysis.

# Aggregation Weighting Methods

## Research Question

How sensitive is the global CHIP estimate to the choice of aggregation weights?
The original study uses GDP-weighted averaging. Does switching to labor-force
weighting, development-based weighting, or simple unweighted averaging
materially change the result?

This study addresses **Design Goals 1, 7, and 10** from the project README:
grounding CHIP in real labor data, stable methodology, and country-specific
multipliers.

## Hypothesis

GDP-weighting gives disproportionate influence to large rich economies (USA,
EU, Japan), which tend to have higher wages. We expect:

- **Labor-weighted** CHIP to be *lower* (developing countries with large
  workforces pull the average down)
- **Unweighted** CHIP to be *lower still* (each country counts equally,
  removing the rich-country bias)
- **Freedom-weighted** to fall between GDP-weighted and unweighted (the
  Heritage freedom index partly correlates with GDP but penalizes less-free
  high-GDP economies)
- **HDI-weighted** to fall near GDP-weighted (HDI correlates with income,
  but health and education components add differentiation)

If all five methods converge to a similar range, the CHIP estimate is robust
to weighting choice. If they diverge significantly, the choice of weights
is a first-order methodological decision that must be defended.

## Weighting Schemes

| # | Scheme | Weight Source | Rationale |
|---|--------|-------------|-----------|
| 1 | **GDP-weighted** | PWT `rgdpna` | Original study method; larger economies have more influence |
| 2 | **Labor-weighted** | PWT `emp` | Countries with more workers count more; closer to "per-worker" average |
| 3 | **Unweighted** | Equal (1/N) | Each country counts equally; reveals rich-country bias in GDP scheme |
| 4 | **Freedom-weighted** | Heritage × GDP | Market-freedom argument: economically free countries better approximate competitive equilibrium |
| 5 | **HDI-weighted** | UNDP HDI | Standard-of-living argument: developed countries where workers have genuine choices better reflect the free-market wage |

### On Freedom vs HDI Weighting

Both schemes 4 and 5 attempt to answer the same philosophical question:
*which countries best represent the competitive labor market we are trying
to measure?*

The Heritage index measures **market openness** (property rights, trade
freedom, regulatory burden). It captures how *free* the economy is.
However, it is published by a politically aligned think tank and some of
its components are debatable.

The UNDP HDI measures **development outcomes** (life expectancy, education,
per-capita income). It captures how *well* people actually live — which
is arguably a better proxy for "workers have genuine choices about employment."
It is published by the UN and widely accepted as politically neutral.

Including both lets us see whether the distinction matters empirically.

## Methodology

1. Run the standard Cobb-Douglas pipeline to produce country-level CHIP
   values for the most recent year with good data (2022, PWT 11.0).
2. Merge country-level data with:
   - PWT employment (`emp`) for labor-weighting
   - Heritage Foundation freedom scores for freedom-weighting
   - UNDP HDI values for HDI-weighting
3. Apply all five weighting schemes via `lib/aggregate.py`.
4. Compare resulting global CHIP values.
5. Analyze country contribution breakdown for each method:
   - Top 10 contributors and their weight share
   - How much does the #1 country (usually USA/China) dominate?
6. Produce **country-specific multipliers** (country CHIP / global CHIP)
   for the recommended weighting scheme. This directly supports Design
   Goal 10.
7. Sensitivity analysis: range, max pairwise difference, and coefficient
   of variation across the five schemes.

## Data Sources

| Source | Fetcher | Status |
|--------|---------|--------|
| ILOSTAT wages/employment | `fetcher.get_wages()` etc. | Implemented |
| PWT 11.0 (GDP, capital, employment) | `fetcher.get_pwt(version="11.0")` | Implemented |
| Heritage Foundation Freedom Index | `fetcher.get_freedom_index()` | **Implemented** |
| UNDP Human Development Index | `fetcher.get_hdi()` | **Implemented** |

## Expected Outputs

- Comparison table: 5 weighting schemes × (CHIP value, N countries, top contributor)
- Bar chart: CHIP value by weighting scheme
- Stacked contribution chart: country shares under each scheme
- Country multiplier table (for recommended scheme)
- Sensitivity summary (range, CV)
- FINDINGS.md with hypothesis assessment and recommendations

## Dependencies

- `lib/pipeline.py` for core CHIP estimation
- `lib/aggregate.py` for all five weighting methods
- `lib/fetcher.py` for Heritage and HDI data (newly implemented)
- `production` study (completed — validates the pipeline with PWT 11.0)

## Status

**Ready to implement.** All data sources and library functions are in place.
The Heritage and HDI fetchers have been tested and cached. The `aggregate.py`
module supports all five weighting schemes including the new `hdi_weighted()`.

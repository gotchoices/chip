# Update Stability & Change Decomposition

## Research Question

How stable is the CHIP estimate across data vintages? When new data arrives,
how large is the correction — and can we predict it? When the CHIP value
changes year-over-year, how much is inflation, how much is country composition,
and how much is a genuine shift in labor demand?

This study directly addresses **Design Goals 4, 6, and 7** from the project
README: accepting real changes while quantifying them, continuity between
updates, and stable methodology.

## Background

Goal 6 requires that new data not cause large discontinuities. Goal 4 says we
"roll with" real changes in labor demand — but we need to know what those
changes are. Currently, we observe that real CHIP moves slowly (~$0.12 std in
the stable panel), but we haven't separated that movement into interpretable
components.

### Natural Experiment: PWT 10.0 → 11.0

We now have a concrete vintage test. The version-aware fetcher
(`lib/fetcher.py`) can retrieve both PWT 10.0 (1950–2019) and PWT 11.0
(1950–2023) independently. PWT 11.0 incorporates the ICP 2021 PPP revision,
updated national accounts, and 2 additional countries. For the 2000–2019
overlap, any difference in CHIP values is attributable entirely to data
revisions — the methodology is identical. This is exactly the vintage
stability test that Design Goal 6 requires.

The production study (Phase 1) will generate the PWT 11.0 series. This study
consumes both series to quantify the vintage shift.

## Hypotheses

**H1 (Vintage stability):** Recalculating CHIP for 2000–2019 using PWT 11.0
instead of PWT 10.0 changes individual year values by less than 5%, and the
overall mean by less than 3%. Historical CHIP values are approximately
"settled" across PWT releases.

**H2 (Composition dominance):** Most year-over-year variation in the
all-countries CHIP series is explained by changes in which countries report
data, not by real economic shifts. Decomposition will show the composition
component exceeds the real component in most years.

**H3 (Predictable corrections):** The difference between a CPI-extrapolated
CHIP and the subsequently calculated value (when new data arrives) has a
standard deviation small enough to be practically ignorable (< 3% of the
CHIP value).

**H4 (Real changes are slow):** After removing inflation and composition
effects, the residual "real CHIP" changes by less than 2% per year on average.
Larger changes correspond to identifiable economic events (e.g., 2008 crisis,
2020 COVID shock).

## Methodology

### Phase 1: Vintage Simulation (PWT 10.0 vs 11.0)

1. Retrieve CHIP time series computed with PWT 10.0 (from timeseries study
   outputs or by re-running with `pwt_version: "10.0"`)
2. Retrieve CHIP time series computed with PWT 11.0 (from production study
   Phase 1 outputs)
3. For each overlapping year (2000–2019), compute:
   - Absolute difference in CHIP value
   - Percentage change
   - Direction (did the revision push CHIP up or down?)
4. Compute summary statistics: mean absolute revision, max revision, bias
5. Identify which countries/years shifted most (join at country level)
6. Assess whether the ICP 2021 PPP revision introduced a systematic bias

### Phase 2: Change Decomposition

For each consecutive year pair (Y, Y+1) in the all-countries series:

7. **Inflation component:** CHIP_nominal(Y+1) - CHIP_nominal(Y) attributable
   to the deflator change alone
8. **Composition component:** Compute CHIP on the intersection of Y and Y+1
   countries vs CHIP on all Y+1 countries — the difference is the composition
   effect
9. **Real component:** The residual after removing inflation and composition
10. Tabulate and visualize the decomposition across all years
11. Test whether the stable panel eliminates the composition component
    (it should, by construction)

### Phase 3: Correction Forecasting

12. For each year Y from 2005–2022, extrapolate CHIP from Y to Y+1 using CPI
13. Compare the extrapolation to the calculated Y+1 value
14. Compute the distribution of corrections (mean, std, max)
15. Test whether the correction is predictable from observable variables
    (e.g., number of new countries reporting, GDP growth divergence)

### Phase 4: Reporting

16. Produce a vintage stability table (PWT 10.0 vs 11.0 by year)
17. Produce a decomposition chart: stacked bar of inflation / composition /
    real components by year
18. Produce a correction accuracy table and histogram
19. Summarize findings and implications for the production pipeline

## Expected Outputs

- Vintage stability table and scatter plot (10.0 vs 11.0 CHIP by year)
- Year-over-year decomposition table and stacked bar chart
- CPI extrapolation correction distribution
- Summary statistics for Design Goal 6 validation

## Dependencies

- `timeseries` study (completed — PWT 10.0 series)
- `production` study Phase 1 (PWT 11.0 series for the same year range)
- `lib/pipeline.py` for core CHIP estimation
- Both PWT 10.0 and 11.0 via `fetcher.get_pwt(version=...)`

## Status

**Scaffold.** Implementation pending. Should be run after the `production`
study generates the PWT 11.0 series (Phase 1), so both vintage datasets are
available for comparison.

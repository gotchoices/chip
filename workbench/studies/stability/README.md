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

Goal 6 requires that new data not cause large discontinuities. But we have
never tested this. ILOSTAT revises historical data, PWT releases new versions
(PWT 10.0 → 10.01 → 11.0), and the set of reporting countries changes over
time. Each of these could shift the CHIP estimate for years we thought were
settled.

Goal 4 says we "roll with" real changes in labor demand — but we need to
know what those changes are. Currently, we observe that real CHIP moves
slowly (~$0.12 std in the stable panel), but we haven't separated that
movement into interpretable components.

## Hypotheses

**H1 (Vintage stability):** Recalculating CHIP for a given year using a later
data vintage (e.g., computing 2015 CHIP using PWT data released in 2017 vs
2019) changes the result by less than 5%. Historical values are approximately
"settled."

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
Larger changes correspond to identifiable economic events (e.g., 2008 crisis).

## Methodology

### Phase 1: Vintage Simulation

1. Compute CHIP for 2010–2015 using only data available through 2015
   (simulate "what we would have published in 2016")
2. Recompute the same years using all data available through 2019
3. Measure the vintage shift for each year
4. If PWT data revisions are available (10.0 vs 10.01), test those too

### Phase 2: Change Decomposition

For each consecutive year pair (Y, Y+1) in the all-countries series:

5. **Inflation component:** CHIP_nominal(Y+1) - CHIP_nominal(Y) attributable
   to the deflator change
6. **Composition component:** Difference between CHIP computed on the
   intersection of Y and Y+1 countries vs CHIP computed on all Y+1 countries
7. **Real component:** The residual after removing inflation and composition
8. Tabulate and visualize the decomposition across all years

### Phase 3: Correction Forecasting

9. For each year Y from 2005–2018, extrapolate CHIP from Y to Y+1 using CPI
10. Compare the extrapolation to the calculated Y+1 value
11. Compute the distribution of corrections (mean, std, max)
12. Test whether the correction is predictable from observable variables
    (e.g., number of new countries reporting)

### Phase 4: Reporting

13. Produce a decomposition chart showing inflation / composition / real
    components stacked by year
14. Produce a vintage stability table
15. Produce a correction accuracy table
16. Summarize findings for the production pipeline design

## Dependencies

- `timeseries` study (completed — provides the all-countries and panel series)
- `production` study (for the CPI extrapolation methodology)
- `lib/pipeline.py` for core CHIP estimation
- Possibly historical PWT versions (if available) for vintage testing

## Status

**Scaffold.** Implementation pending. Should be run after `production` study
establishes the trailing-window methodology.

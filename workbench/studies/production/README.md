# Production Methodology

## Research Question

Can we produce a defensible, current-year CHIP estimate using a trailing-window
methodology — and can we bridge the gap beyond the last year of Penn World
Tables data using only ILOSTAT wages and a price index?

This study directly addresses **Design Goals 2, 3, 5, 6, and 8** from the
project README: periodic estimation, inflation immunity, repeatable pipeline,
continuity between updates, and actionable output for MyCHIPs.

## Background

The timeseries study established that:

- Real CHIP is approximately stable (~$3.50/hr in constant 2017$ for the stable
  panel, ~$2.89 for all countries, from 2005–2019).
- Deflation cancels in the CHIP formula, so "nominal CHIP" must be constructed
  by multiplying real CHIP by the price level.
- PWT data ends at 2019, but ILOSTAT has data through ~2025.

The baseline and timeseries studies answered "does the methodology work?" This
study answers "how do we use it to produce a number people can rely on?"

## Hypotheses

**H1 (Trailing window is smooth):** A 3-year or 5-year trailing window, with
each year's CHIP re-inflated to the target year's price level, produces a
smoother series than single-year estimates while remaining responsive to real
changes.

**H2 (PWT bridge is viable):** For years beyond PWT coverage (2020+), we can
hold capital stock and GDP estimates constant (or extrapolate with IMF/World
Bank growth projections) and still produce a CHIP estimate within ±10% of what
a full PWT update would yield. Alternatively, if the deflation-cancellation
finding holds, we may be able to compute CHIP from ILOSTAT wages alone without
PWT for the bridge period.

**H3 (CPI extrapolation works):** Between annual recalculations, nominal CHIP
can be extrapolated forward using CPI (or GDP deflator), and the next official
value will differ from the extrapolation by less than 5%.

**H4 (Stable panel suffices for bridge):** Using only the 11 stable-panel
countries (identified in the timeseries study) for the bridge period produces
a result within the historical range of the full-panel estimate.

## Methodology

### Phase 1: Trailing Window

1. Implement a trailing-window CHIP estimator (configurable: 1, 3, 5 years)
2. For each target year Y, compute CHIP for years [Y-k, ..., Y], re-inflate
   each to year-Y dollars, then average
3. Compare windows: smoothness (std of year-over-year changes), lag
   (responsiveness to a known shock), and level (mean over 2005–2019)
4. Select the recommended window size

### Phase 2: PWT Bridge

5. Compute CHIP for 2017–2019 using full PWT data (the "truth")
6. Re-compute for 2017–2019 using only ILOSTAT data + extrapolated PWT
   (hold capital/GDP constant at last known year, or use IMF projections)
7. Compare: how far off is the bridge estimate?
8. Test whether the deflation-cancellation makes PWT unnecessary for the
   CHIP value itself (PWT provides alpha and MPL — can we use a fixed alpha?)

### Phase 3: CPI Extrapolation

9. Take the 2017 calculated CHIP, extrapolate to 2018 and 2019 using CPI
10. Compare extrapolated values to calculated values
11. Measure the "correction" that would occur when official data arrives
12. Repeat for multiple base years to establish the typical correction range

### Phase 4: Production Pipeline

13. Assemble the recommended methodology into a clean pipeline
14. Produce a complete time series: calculated values where data exists,
    extrapolated values for the gap period, with clear labeling
15. Document the methodology for `estimates/` implementation

## Dependencies

- `baseline` and `timeseries` studies (completed)
- `lib/pipeline.py` for core CHIP estimation
- CPI/GDP deflator data from FRED (already in fetcher)
- Possibly IMF World Economic Outlook data for GDP/capital projections

## Status

**Scaffold.** Implementation pending.

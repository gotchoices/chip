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

The baseline and timeseries studies answered "does the methodology work?" This
study answers "how do we use it to produce a number people can rely on?"

### Data Availability

This study uses **PWT 11.0** (released October 2025), which extends coverage
from 2019 to **2023** and incorporates the ICP 2021 PPP benchmarks. This
shrinks the bridge gap from ~6 years (2019→2025 with PWT 10.0) to ~2 years
(2023→2025). ILOSTAT has wage data through ~2025 for many countries. FRED
deflator data is current.

The version-aware fetcher (`lib/fetcher.py`) caches PWT versions independently.
This study defaults to PWT 11.0 while prior studies remain pinned to PWT 10.0
via their `config.yaml`. See `docs/data-sources.md` for details on all sources.

## Hypotheses

**H1 (Trailing window is smooth):** A 3-year or 5-year trailing window, with
each year's CHIP re-inflated to the target year's price level, produces a
smoother series than single-year estimates while remaining responsive to real
changes.

**H2 (PWT bridge is viable):** For the ~2-year gap beyond PWT 11.0 coverage
(2024–2025), we can hold capital stock and GDP estimates constant at 2023
levels (or extrapolate with IMF/World Bank growth projections) and still
produce a CHIP estimate within ±10% of what a full PWT update would yield.
The deflation-cancellation finding suggests PWT's main contribution is the
alpha estimate and MPL — if we use a fixed alpha from the last known year,
the bridge may be simpler than expected.

**H3 (CPI extrapolation works):** Between annual recalculations, nominal CHIP
can be extrapolated forward using CPI (or GDP deflator), and the next official
value will differ from the extrapolation by less than 5%.

**H4 (Stable panel suffices for bridge):** Using only stable-panel countries
for the bridge period produces a result within the historical range of the
full-panel estimate. (The timeseries study identified 11 countries with
PWT 10.0; this number may change with PWT 11.0's 4 additional years.)

## Methodology

### Phase 1: Extend the Series

1. Run the full CHIP pipeline with PWT 11.0 data (2000–2023)
2. Compare the 2000–2019 overlap with previous timeseries results (PWT 10.0)
   to gauge vintage sensitivity (feeds into the stability study)
3. Examine the 2020–2023 extension: country count, CHIP levels, COVID effects
4. Re-identify the stable panel with the extended year range

### Phase 2: Trailing Window

5. Implement a trailing-window CHIP estimator (configurable: 1, 3, 5 years)
6. For each target year Y, compute CHIP for years [Y-k, ..., Y], re-inflate
   each to year-Y dollars, then average
7. Compare windows: smoothness (std of year-over-year changes), lag
   (responsiveness to the 2020 COVID shock), and level (mean over 2005–2023)
8. Select the recommended window size

### Phase 3: PWT Bridge

9. Compute CHIP for 2021–2023 using full PWT 11.0 data (the "truth")
10. Re-compute for 2021–2023 using only ILOSTAT data + frozen PWT values
    (hold capital/GDP/alpha constant at 2020 levels)
11. Compare: how far off is the bridge estimate?
12. Test a fixed-alpha approach: use the mean alpha from 2015–2023 for all
    bridge years, compute CHIP from ILOSTAT wages + deflator only

### Phase 4: CPI Extrapolation

13. Take the 2021 calculated CHIP, extrapolate to 2022 and 2023 using CPI
14. Compare extrapolated values to calculated values
15. Measure the "correction" that would occur when official data arrives
16. Repeat for multiple base years to establish the typical correction range

### Phase 5: Production Pipeline

17. Assemble the recommended methodology into a clean pipeline
18. Produce a complete time series: calculated values where PWT exists,
    bridge values for the gap, extrapolated values for the current year
19. Label each value: "calculated", "bridge", or "extrapolated"
20. Document the methodology for `estimates/` implementation

## Expected Outputs

- Time series of nominal CHIP values, 2000–present, with method labels
- Trailing-window comparison table and plots
- Bridge accuracy table (bridge estimate vs truth for withheld years)
- CPI extrapolation accuracy table
- Recommended production methodology document

## Dependencies

- `baseline` and `timeseries` studies (completed, pinned to PWT 10.0)
- `lib/pipeline.py` for core CHIP estimation
- PWT 11.0 (default version in fetcher)
- CPI/GDP deflator data from FRED (already in fetcher)
- Possibly IMF World Economic Outlook data for GDP/capital projections

## Status

**Complete.** Phases 1–4 implemented and analyzed. See FINDINGS.md for results.
Phase 5 (production pipeline assembly) deferred to `estimates/` implementation.

# Time Series Discovery

## Research Question

How does the CHIP value evolve year-by-year from 1992 to 2019? Is it stable
in real terms? Does the nominal CHIP track inflation as hypothesized in
`docs/inflation-tracking.md` (H1)?

## Hypothesis

**H1 (Inflation Tracking):** Nominal CHIP should rise roughly in line with
the US GDP deflator, since CHIP is denominated in dollars and wages are
reported in current-year dollars.

**H2 (Composition Effects):** Year-to-year volatility in the all-countries
series may be driven by changes in which countries report data, not by real
economic changes. A stable panel (countries with consistent coverage) should
produce a smoother series.

**H3 (Real Stability):** Constant-dollar CHIP should be relatively stable
across years, reflecting the slow-moving nature of global labor productivity.

## Methodology

1. Run the full CHIP pipeline for 1992-2019 (all countries, deflated to 2017$)
2. Aggregate to per-year CHIP values using GDP weighting
3. Trim years with fewer than 5 contributing countries
4. Identify a "stable panel" of countries with >= 70% year coverage
5. Create nominal series by re-inflating constant-dollar CHIP with GDP deflator
6. Compare all-countries vs stable-panel, constant vs nominal
7. Generate rolling-window smoothed variants (3-year, 5-year)
8. Plot nominal CHIP index against GDP deflator index

Key discovery: deflation cancels in the CHIP formula (elementary_wage and
average_wage are scaled identically), so "nominal" series must be constructed
by explicit re-inflation.

## Status

**Complete.** Produces a discovery report with four time series (all/panel x
constant/nominal), rolling averages, plots, and preliminary observations on
H1 and H2.

See also: `docs/inflation-tracking.md` for the full hypothesis framework.

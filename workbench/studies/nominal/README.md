# Nominal vs Deflated CHIP

## Research Question

Does computing CHIP with nominal (un-deflated) wage data produce a different
result than the deflated approach? If so, does the nominal CHIP naturally
track currency inflation?

This is the formal test of **H1** from `docs/inflation-tracking.md`.

## Hypothesis

Based on the timeseries study's discovery that deflation cancels in the CHIP
formula (both elementary_wage and average_wage are scaled by the same deflator),
we expect nominal and deflated CHIP to be identical.

The meaningful comparison is between constant-dollar CHIP and a re-inflated
nominal CHIP — the latter should track the GDP deflator closely if the
underlying real CHIP is stable.

## Methodology

1. Compute CHIP using the standard deflated pipeline
2. Compute CHIP without deflation (nominal wages)
3. Verify the algebraic cancellation: deflated == nominal
4. Compare re-inflated nominal series against GDP deflator
5. Quantify correlation and divergence

## Status

**Absorbed.** The core finding of this study — that deflation cancels
algebraically in the CHIP formula — was discovered and documented during the
`timeseries` study. See `studies/timeseries/FINDINGS.md` §"Deflation Cancels
in the CHIP Formula" and §"H1: Nominal CHIP Tracks Inflation."

The timeseries study demonstrated that:
- Nominal and deflated CHIP are mathematically identical
- Nominal CHIP must be constructed by re-inflating constant-dollar CHIP
- The nominal series tracks the GDP deflator by construction

If a formal correlation coefficient or regression is desired, it can be added
as a small extension to the timeseries study rather than a separate study.
No further implementation is planned here.

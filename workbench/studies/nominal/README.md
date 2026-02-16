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

**Scaffold.** Implementation pending. The timeseries study already demonstrates
the cancellation finding; this study would formalize the H1 test.

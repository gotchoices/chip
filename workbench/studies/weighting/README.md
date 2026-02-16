# Aggregation Weighting Methods

## Research Question

How sensitive is the global CHIP estimate to the choice of aggregation weights?
The original study uses GDP-weighted averaging — does switching to labor-force
weighting, freedom-index weighting, or simple unweighted averaging materially
change the result?

This study supports the analysis in `docs/weighting-analysis.md`.

## Hypothesis

GDP-weighting gives disproportionate influence to large rich economies (USA,
EU, Japan), which tend to have higher wages. We expect:

- **Labor-weighted** CHIP to be *lower* (developing countries with large
  workforces pull the average down)
- **Unweighted** CHIP to be *lower still* (each country counts equally,
  removing the rich-country bias)
- **Freedom-weighted** to fall between GDP-weighted and unweighted (the
  freedom index partly correlates with GDP but penalizes less-free economies)

If all methods converge to a similar range, the CHIP estimate is robust
to weighting choice. If they diverge significantly, the choice of weights
is a first-order methodological decision.

## Methodology

1. Compute country-level CHIP values using the standard Cobb-Douglas pipeline
2. Apply four weighting schemes:
   - GDP-weighted (original study method)
   - Labor-force weighted (weight by total employment)
   - Freedom-weighted (GDP x Heritage/Fraser freedom index)
   - Unweighted (simple mean across countries)
3. Compare resulting CHIP values
4. Analyze country contribution breakdown for each method
5. Sensitivity analysis: how much does the result change?

## Status

**Scaffold.** Implementation pending. The `lib/aggregate.py` module already
supports GDP-weighted, labor-weighted, and unweighted methods. Freedom index
data source integration is planned.

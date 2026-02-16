# Data Coverage Analysis

## Research Question

Which countries have consistent data across which time periods, and what does
this mean for the reliability of our CHIP estimates? Where are the gaps, and
how should they influence country selection for other studies?

## Hypothesis

We expect significant variation in data availability across countries and time
periods. ILOSTAT coverage is likely sparse before 2000 and may have gaps for
developing nations. PWT coverage should be broader (more countries) but ends
at 2019. The intersection of all required sources will be substantially smaller
than any individual source.

Countries excluded by the original study (Nepal, Pakistan, Sri Lanka, Bangladesh,
Egypt, Jordan, Palestine) are expected to fall in the "fair" or "sparse" quality
tiers, supporting the original exclusion decision.

## Methodology

1. Fetch all data sources (ILOSTAT employment, wages, hours; PWT; FRED deflator)
2. Normalize column names across sources
3. Analyze per-source coverage: countries, year ranges, row counts
4. Compute overlap: countries present in all sources vs subsets
5. Identify "CHIP-viable" countries (those with employment + wages + PWT)
6. Categorize data quality tiers by years of coverage per country
7. Generate recommendations for country selection and year range

## Status

**Complete.** Produces a comprehensive markdown report with coverage tables,
quality tiers (excellent/good/fair/sparse), and recommendations.

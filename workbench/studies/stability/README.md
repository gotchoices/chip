# Update Stability & Vintage Comparison

## Research Question

How stable is the CHIP estimate across data vintages? When a new PWT release
revises historical national accounts and PPP benchmarks, do previously
published CHIP values shift materially?

This study directly addresses **Design Goals 4, 6, and 7** from the project
README: accepting real changes while quantifying them, continuity between
updates, and stable methodology.

## Scope Reduction (February 2026)

The original design included four phases. After the `production` study was
completed, two of the four hypotheses were substantially answered:

- **CPI correction distribution (original H3):** Production found correction
  std ~6.4%, 53% within ±5%, corrections mean-reverting. No need to re-test.
- **Real CHIP stability (original H4):** Both timeseries and production
  confirmed real CHIP is approximately stable ($0.12 std in stable panel,
  ±10% over a decade). Formal decomposition into inflation/composition/real
  components would be academically tidy but does not change any operational
  decision — we already use the stable panel and trailing windows to address
  composition noise.

What remains unique to this study:

### H1 (Vintage stability) — Primary focus

Recalculating CHIP for 2000–2019 using PWT 11.0 instead of PWT 10.0 changes
individual year values by less than 5%, and the overall mean by less than 3%.
Historical CHIP values are approximately "settled" across PWT releases.

This is operationally important: when PWT 12.0 eventually drops, we need to
know whether to expect historical values to shift (requiring republication)
or whether they are effectively locked in.

### H2 (Composition dominance) — Deferred

Formal decomposition of year-over-year changes into inflation, composition,
and real components. Lower priority since the practical response (use the
stable panel) is already implemented. May be revisited if the `weighting`
study reveals surprising sensitivity to country set.

## Background

### Natural Experiment: PWT 10.0 → 11.0

We have a concrete vintage test. The version-aware fetcher (`lib/fetcher.py`)
can retrieve both PWT 10.0 (1950–2019) and PWT 11.0 (1950–2023)
independently. PWT 11.0 incorporates the ICP 2021 PPP revision, updated
national accounts, and 2 additional countries. For the 2000–2019 overlap,
any difference in CHIP values is attributable entirely to data revisions —
the methodology is identical.

The timeseries study produced a PWT 10.0 series. The production study
produced a PWT 11.0 series. This study compares them directly.

## Methodology

1. Run the full CHIP pipeline on PWT 10.0 for 2000–2019 (re-run or extract
   from timeseries study outputs).
2. Run the identical pipeline on PWT 11.0 for 2000–2019.
3. For each overlapping year, compute:
   - Absolute and percentage difference in global CHIP
   - Direction (did the revision push CHIP up or down?)
   - Country-level: which countries/years shifted most?
4. Compute summary statistics: mean absolute revision, max revision, bias.
5. Assess whether the ICP 2021 PPP revision introduced a systematic bias.
6. Produce vintage stability table, scatter plot, and summary.

## Expected Outputs

- Vintage stability table (PWT 10.0 vs 11.0 CHIP by year, 2000–2019)
- Scatter plot: 10.0 CHIP vs 11.0 CHIP with identity line
- Country-level revision heatmap (which countries moved most?)
- Summary statistics for Design Goal 6 validation
- FINDINGS.md with hypothesis assessment and implications

## Dependencies

- `timeseries` study (completed — PWT 10.0 series)
- `production` study (completed — PWT 11.0 series)
- `lib/pipeline.py` for core CHIP estimation
- Both PWT 10.0 and 11.0 via `fetcher.get_pwt(version=...)`

## Status

**Scaffold — reduced scope.** The vintage comparison (H1) is the primary
remaining deliverable. Change decomposition (H2) deferred. CPI correction
analysis and real-CHIP stability were answered by the production study.

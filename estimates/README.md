# CHIP Estimates — Production Pipeline

This folder contains the operational CHIP estimator.  It produces the
official CHIP value and country multipliers that are published to MyCHIPs
and chipcentral.net.

Unlike `workbench/` (which is for research and exploration), this pipeline
is **deterministic and conservative**: same data in, same numbers out.  All
methodology decisions were made in the workbench studies and are locked
down here.

---

## Overview

The pipeline operates on a **two-tier model**:

| Tier | Script | Cadence | Trigger | What it does |
|------|--------|---------|---------|--------------|
| **Recalculation** | `recalculate.py` | Annual (or when new source data arrives) | Human-initiated | Full pipeline: fetch latest data, estimate CHIP, produce multipliers, update base parameters |
| **Extrapolation** | `extrapolate.py` | Monthly | Automated (cron) | Lightweight: apply latest CPI to the base value, publish updated nominal CHIP |

Both scripts **append** to a cumulative output ledger (`output/chip_history.json`).
Each entry is timestamped and tagged with its method (recalculation vs.
extrapolation).  This ledger is the queryable endpoint — anything that
needs the current CHIP value reads the latest entry.

---

## Locked-In Methodology

These parameters are fixed based on workbench study findings.  Changes
require re-running the relevant study and documenting the justification.

| Parameter | Value | Source |
|-----------|-------|--------|
| Production function | Cobb-Douglas with distortion factor (θ) | Original study, validated in `baseline` |
| PWT version | 11.0 (update when new version releases) | `stability` study |
| Trailing window | 5 years | `production` study |
| Aggregation | GDP-weighted | `weighting` study |
| Extrapolation index | US CPI-U (FRED series CPIAUCSL) | `production` study |
| Imputation | MICE-style linear regression | `baseline` study |
| Wage averaging | Simple mean across occupation codes | `baseline` study |

---

## Scripts

### `recalculate.py` — Annual Full Recalculation

**When to run:** When new source data becomes available (typically a new
ILOSTAT wage release or a new PWT version), or at least once per year.

**What it does:**

1. Fetches the latest data from ILOSTAT, PWT, and FRED (using
   `workbench.lib.fetcher`, cache is bypassed for recalculation).
2. Runs the full CHIP pipeline: normalize → clean → impute → estimate →
   aggregate using the locked-in methodology above.
3. Computes the GDP-weighted global CHIP value (5-year trailing window,
   re-inflated to the latest available year's nominal dollars).
4. Computes per-country multipliers (country CHIP / global CHIP).
5. Appends a `recalculation` entry to `output/chip_history.json`.
6. Writes the current base parameters to `output/base_params.json` (used
   by the extrapolator).
7. Writes human-readable summary to `output/latest_recalculation.md`.

**Human review:** After running, the operator should review:
- Did the CHIP value change significantly from the previous recalculation?
  (The `production` study found typical revisions of ±5–10%.)
- Did the country count change?  (A sudden drop may indicate a data source
  issue.)
- Are there anomalous country multipliers?  (The `stability` study found
  that individual countries can shift 50%+ across PWT vintages.)

If anomalies are found, the operator can adjust `config.yaml` (e.g., pin
a specific PWT version, exclude a problematic country) and re-run.

### `extrapolate.py` — Monthly CPI Extrapolation

**When to run:** Monthly, after the BLS releases updated CPI data
(typically mid-month for the prior month).  Can be automated via cron.

**What it does:**

1. Reads the base parameters from `output/base_params.json` (produced by
   the last recalculation).
2. Fetches the latest US CPI-U from FRED.
3. Computes the CPI ratio from the base year to the current month.
4. Multiplies the base CHIP value by this ratio to produce the current
   nominal CHIP estimate.
5. Appends an `extrapolation` entry to `output/chip_history.json`.
6. Writes `output/latest.json` — a simple file containing the current
   CHIP value, suitable for serving via a static endpoint or API.

**No human review needed** unless the CPI data itself is anomalous.

### `publish.py` — Format for API Consumption

**What it does:**

1. Reads `output/chip_history.json` and `output/latest.json`.
2. Produces API-ready output files:
   - `output/api/current.json` — current global CHIP and date.
   - `output/api/multipliers.json` — per-country multipliers from the
     latest recalculation.
   - `output/api/history.json` — full time series of CHIP values.
3. These files can be served as static JSON by any web server (nginx,
   GitHub Pages, S3) or consumed by a future dynamic API.

---

## Output Files

All outputs are written to `output/`.

```
output/
├── chip_history.json        # Cumulative ledger (append-only)
├── base_params.json         # Parameters from last recalculation
├── latest.json              # Current CHIP value (overwritten each run)
├── latest_recalculation.md  # Human-readable summary of last recalculation
├── multipliers.csv          # Per-country multipliers (latest)
└── api/                     # API-ready formatted output
    ├── current.json
    ├── multipliers.json
    └── history.json
```

### `chip_history.json` Format

The history ledger is an array of entries, each recording one estimate:

```json
[
  {
    "date": "2026-03-15",
    "method": "recalculation",
    "chip_usd": 3.17,
    "base_year": 2022,
    "pwt_version": "11.0",
    "window_years": 5,
    "n_countries": 85,
    "notes": "Annual recalculation with PWT 11.0 data through 2022"
  },
  {
    "date": "2026-04-15",
    "method": "extrapolation",
    "chip_usd": 3.21,
    "base_chip": 3.17,
    "base_date": "2026-03-15",
    "cpi_ratio": 1.0126,
    "cpi_date": "2026-03-01",
    "notes": "Monthly CPI extrapolation"
  }
]
```

### `latest.json` Format

A single object, always overwritten with the most current estimate:

```json
{
  "chip_usd": 3.21,
  "date": "2026-04-15",
  "method": "extrapolation",
  "base_chip": 3.17,
  "base_date": "2026-03-15",
  "next_recalculation": "When new ILOSTAT/PWT data is available"
}
```

### `base_params.json` Format

Written by `recalculate.py`, read by `extrapolate.py`:

```json
{
  "chip_constant_2017": 2.68,
  "chip_nominal": 3.17,
  "base_year": 2022,
  "deflator_base_year": 2017,
  "cpi_reference_date": "2022-12-01",
  "cpi_reference_value": 296.797,
  "pwt_version": "11.0",
  "window_years": 5,
  "n_countries": 85,
  "recalculation_date": "2026-03-15"
}
```

---

## Operational Workflow

### Initial Setup (Once)

1. Run `recalculate.py` to produce the first base value and multipliers.
2. Review output.  Adjust `config.yaml` if needed.  Re-run.
3. Set up a monthly cron job for `extrapolate.py`.
4. Point the chipcentral.net endpoint at `output/api/current.json`
   (or run `publish.py` after each extrapolation).

### Monthly (Automated)

```
# Cron entry (15th of each month, after BLS CPI release)
15 10 15 * * cd /path/to/chip/estimates && python extrapolate.py && python publish.py
```

### Annual (Human-Initiated)

1. Check whether new ILOSTAT or PWT data has been released.
2. If yes: clear the fetcher cache for the relevant datasets, then run:
   ```
   python recalculate.py
   ```
3. Review the output summary (`output/latest_recalculation.md`).
4. If the recalculated value differs significantly from the extrapolated
   value (the "snap"), note the magnitude and direction.
5. Run `publish.py` to update the API files.
6. The next monthly `extrapolate.py` run will automatically use the new
   base parameters.

### When a New PWT Version Releases

1. Update `config.yaml` to reference the new version.
2. If `workbench/lib/fetcher.py` needs a new URL entry, add it.
3. Run `recalculate.py`.
4. Compare to the previous version's estimate.  The `stability` study
   found mean revisions of ~4% for mature years, so modest changes are
   expected and normal.
5. Document the version change in the `notes` field of the history entry.

---

## Configuration

### `config.yaml`

```yaml
# Production CHIP estimator — locked methodology.
# Change only with justification documented in notes.

data:
  pwt_version: "11.0"

pipeline:
  year_start: 1992
  year_end: 2023
  window_years: 5
  weighting: "gdp"
  min_countries: 5
  min_coverage_pct: 0.70
  enable_imputation: true
  wage_averaging: "simple"

extrapolation:
  index: "cpi_u"           # FRED series CPIAUCSL
  deflator_base_year: 2017
```

---

## Relationship to Workbench

This pipeline **imports from `workbench/lib/`** but does not live inside
the workbench.  The relationship is:

- `workbench/lib/` — shared library (fetcher, pipeline, aggregate, etc.)
- `workbench/studies/` — research investigations that informed methodology
- `estimates/` — operational pipeline that uses the library with fixed parameters

If a methodology question arises (e.g., "should we switch to a 3-year
window?"), the answer is found by running a workbench study, not by
experimenting in the estimates pipeline.

---

## Snap-Back and Corrections

When a recalculation produces a base value that differs from the most
recent extrapolation, a "snap" occurs.  The `production` study found that
these corrections are typically ±5–10%.  Design choices to manage snaps:

1. **Recalculate promptly** when new data arrives (don't wait for a
   calendar date).  This reduces anticipation effects.
2. **Log the snap magnitude** in `chip_history.json` for transparency.
3. **No phase-in** by default — the new base value takes effect
   immediately.  A gradual phase-in (linear over 30 days) can be
   implemented in `publish.py` if market feedback warrants it.

See `docs/inflation-tracking.md` Section 7.4 for analysis of market
dynamics around recalculations.

---

*Created: 2026-02-09*

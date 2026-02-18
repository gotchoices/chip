# CHIP Estimates — Production Pipeline

This folder contains the operational CHIP estimator.  It produces the
official CHIP value and country multipliers that are published to MyCHIPs
and chipcentral.net.

Unlike `workbench/` (which is for research and exploration), this pipeline
is **deterministic and conservative**: same data in, same numbers out.  All
methodology decisions were made in the workbench studies and are locked
down here.

---

## How It Works

The pipeline operates on a **two-tier model**:

| Tier | Script | Cadence | Trigger | What it does |
|------|--------|---------|---------|--------------|
| **Recalculation** | `recalculate.py` | Annual | Human-initiated | Full pipeline: fetch latest data, estimate CHIP, produce multipliers, update base parameters |
| **Extrapolation** | `extrapolate.py` | Monthly | Cron job on server | Lightweight: apply latest CPI to the base value, update nominal CHIP |

Both scripts write to `output/chip_history.json` — a cumulative ledger
of every estimate.  The file `output/latest.json` always contains the
most current value.  The `publish.py` script formats these into
API-ready JSON under `output/api/`.

**Idempotent by default:** Runs are deduplicated by `(effective_date,
method)`.  If a matching entry already exists in the history, it is
skipped.  Use `--replace` to overwrite an existing entry.  To fix a
bad entry: delete it from `chip_history.json`, re-run, and the gap is
filled automatically.

**Deployment model:** The `output/` directory is tracked in git.
The production server hosts a checkout of this repo, and the website
serves files directly from `output/api/`.  Updates reach the server
via `git pull`.

---

## Operational Runbook

### Initial Setup (Once)

These steps establish the pipeline on a new server.

1. Clone the repo to the production server:
   ```
   git clone <repo-url> /srv/chip
   ```

2. Install Python dependencies (same as workbench):
   ```
   cd /srv/chip/workbench && pip install -e .
   ```

3. Create `secrets.toml` in the project root with your FRED API key:
   ```toml
   [fred]
   api_key = "your-key-here"
   ```

4. Run the first recalculation from your dev machine:
   ```
   cd estimates
   python recalculate.py --force-refresh --notes "Initial pipeline run"
   python publish.py
   ```

5. Review `output/latest_recalculation.md`.  If results look right,
   commit and push:
   ```
   git add output/
   git commit -m "Initial CHIP estimate"
   git push
   ```

6. On the server, pull and verify:
   ```
   cd /srv/chip && git pull
   ```

7. Point your web server at `estimates/output/api/current.json` (e.g.,
   an nginx alias or symlink).

8. Set up the monthly cron job (see below).

### Annual Recalculation (Human-Initiated)

Run this when new source data is available (new ILOSTAT wages or a new
PWT version), or at least once per year.

```
# On your dev machine:

# 1. Pull latest
git pull

# 2. Run recalculation (--force-refresh fetches fresh data)
cd estimates
python recalculate.py --force-refresh --notes "Annual 2026 recalculation"

# 3. Review the summary
#    Look at: CHIP value, country count, snap magnitude, multipliers
cat output/latest_recalculation.md

# 4. If something looks wrong, adjust config.yaml and re-run.
#    If it looks right, publish and commit:
python publish.py

git add output/
git commit -m "Annual CHIP recalculation — PWT 11.0, $X.XX nominal"
git push

# 5. On the production server:
ssh server 'cd /srv/chip && git pull'
```

**What to check:**
- Did the CHIP value change significantly from the previous recalculation?
  (The `production` study found typical revisions of ±5–10%.)
- Did the country count change?  A sudden drop may indicate a data source
  issue.
- Are there anomalous country multipliers?  (The `stability` study found
  that individual countries can shift 50%+ across PWT vintages.)

If anomalies are found, adjust `config.yaml` (e.g., pin a PWT version,
exclude a problematic country) and re-run before committing.

### Monthly Extrapolation (Automated via Cron)

A cron job on the production server runs the extrapolator monthly.  It
fetches the latest CPI-U from FRED and applies it to the base CHIP value.

**Cron entry** (weekly is fine — the script is a no-op when CPI hasn't
updated.  BLS typically releases new CPI mid-month):

```cron
0 10 * * 1 cd /srv/chip/estimates && python extrapolate.py && python publish.py
```

When new CPI data is available, the script writes a new entry and
updates `output/latest.json` and `output/api/current.json` in place.
The website picks up the change immediately (it reads from the local
filesystem).  When no new CPI data exists, the run is a silent no-op.

**Git sync:** The monthly extrapolation outputs accumulate on the server
between annual recalculations.  They are captured in git at the next
annual pull:

```
# At the next annual recalculation, on the server first:
cd /srv/chip
git add estimates/output/
git commit -m "Monthly extrapolations since last recalculation"
git push

# Then on dev machine, pull before recalculating:
git pull
```

Alternatively, a second cron entry can auto-commit monthly if desired:

```cron
30 10 16 * * cd /srv/chip && git add estimates/output/ && git commit -m "Monthly CHIP extrapolation" && git push
```

### Backfilling Historical Data

To populate the history ledger with retrospective estimates (as if the
pipeline had been running for years), use `--target-year` and
`--effective-date`:

```bash
# Backfill annual recalculations for 2005–2023
for year in $(seq 2005 2023); do
    python recalculate.py \
        --target-year $year \
        --effective-date "$((year+1))-01-01" \
        --notes "Backfill for data year $year"
done

# Then publish
python publish.py
```

Each entry gets `effective_date` set to the historical date and
`calculated_date` set to today.  The two dates make it transparent
which entries were produced in real time vs. reconstructed.

**Note:** This uses PWT 11.0 for all years (the best data available now).
Historical entries from before PWT 11.0 existed (pre-2024) would have
been slightly different if calculated live with PWT 10.0.  The stability
study found ~4% mean revision between PWT versions for mature years.

The pipeline only needs to fetch data once — subsequent `--target-year`
runs reuse the cache.

### When a New PWT Version Releases

1. Update `config.yaml`:
   - Set `pwt_version` to the new version (e.g., `"12.0"`)
   - Update `pwt_base_year` if the new version rebases (e.g., 2021)
   - Update `year_end` to the new version's latest year

2. If `workbench/lib/fetcher.py` needs a new URL entry, add it.

3. Run `recalculate.py --force-refresh`.

4. Compare to the previous version's estimate.  The `stability` study
   found mean revisions of ~4% for mature years, so modest changes are
   expected and normal.

5. Document the version change in the `--notes` flag.

---

## Locked-In Methodology

These parameters are fixed based on workbench study findings.  Changes
require re-running the relevant study and documenting the justification.

| Parameter | Value | Source |
|-----------|-------|--------|
| Production function | Cobb-Douglas with distortion factor (θ) | Original study, validated in `baseline` |
| PWT version | 11.0 (update when new version releases) | `stability` study |
| PWT base year | 2017 (constant-dollar reference, set by PWT) | PWT 11.0 documentation |
| Trailing window | 5 years | `production` study |
| Aggregation | GDP-weighted | `weighting` study |
| Extrapolation index | US CPI-U (FRED series CPIAUCSL) | `production` study |
| Imputation | MICE-style linear regression | `baseline` study |
| Wage averaging | Simple mean across occupation codes | `baseline` study |

---

## Scripts

### `recalculate.py` — Annual Full Recalculation

**What it does:**

1. Fetches the latest data from ILOSTAT, PWT, and FRED (using
   `workbench/lib/fetcher`; pass `--force-refresh` to bypass cache).
2. Runs the full CHIP pipeline: normalize → clean → impute → estimate →
   aggregate using the locked-in methodology above.
3. Computes the GDP-weighted global CHIP value (5-year trailing window,
   re-inflated to the latest available year's nominal dollars).
4. Computes per-country multipliers (country CHIP / global CHIP).
5. Fetches the latest CPI-U value as a reference point for the
   extrapolator.
6. Writes all output files (see Output Files below).

**CLI:**
```
python recalculate.py [--force-refresh] [--notes "reason for run"]
python recalculate.py --target-year 2018 --effective-date 2019-01-01
```

### `extrapolate.py` — Monthly CPI Extrapolation

**What it does:**

1. Reads `output/base_params.json` (produced by the last recalculation).
2. Fetches the latest US CPI-U from FRED.
3. Computes: `CHIP_now = CHIP_base × (CPI_now / CPI_base)`.
4. Appends an entry to `output/chip_history.json`.
5. Overwrites `output/latest.json`.

**CLI:**
```
python extrapolate.py [--effective-date YYYY-MM-DD] [--notes "optional note"]
```

**No-op when nothing changed:** If the latest CPI observation date is
the same as the last extrapolation's, the script exits cleanly without
writing.  This means the cron can run daily or weekly — it only produces
a new entry when BLS publishes fresh CPI data (typically mid-month).
Use `--replace` to force a write regardless.

**No human review needed** unless the CPI data itself is anomalous.

### `publish.py` — Format for API Consumption

**What it does:**

1. Reads the internal output files.
2. Produces API-ready JSON under `output/api/`:
   - `current.json` — current global CHIP and date
   - `multipliers.json` — per-country multipliers
   - `history.json` — full time series

**CLI:**
```
python publish.py
```

---

## Output Files

All outputs are written to `output/`.  These are **tracked in git** and
served directly by the production web server.

```
output/
├── chip_history.json        # Cumulative ledger (append-only)
├── base_params.json         # Parameters from last recalculation
├── latest.json              # Current CHIP value (overwritten each run)
├── latest_recalculation.md  # Human-readable summary of last recalculation
├── multipliers.csv          # Per-country multipliers (latest)
└── api/                     # API-ready formatted output
    ├── current.json         # ← Primary endpoint for MyCHIPs / chipcentral
    ├── multipliers.json     # ← Per-country multipliers
    └── history.json         # ← Full estimate time series
```

### `chip_history.json` Format

The history ledger is an array of entries, each recording one estimate:

```json
[
  {
    "effective_date": "2026-03-15",
    "calculated_date": "2026-03-15",
    "method": "recalculation",
    "chip_usd": 3.17,
    "base_year": 2022,
    "pwt_base_year": 2017,
    "pwt_version": "11.0",
    "window_years": 5,
    "n_countries": 85,
    "notes": "Annual recalculation with PWT 11.0 data through 2022"
  },
  {
    "effective_date": "2026-04-15",
    "calculated_date": "2026-04-15",
    "method": "extrapolation",
    "chip_usd": 3.21,
    "base_chip": 3.17,
    "base_effective_date": "2026-03-15",
    "cpi_ratio": 1.0126,
    "cpi_date": "2026-03-01",
    "notes": "Monthly CPI extrapolation"
  },
  {
    "effective_date": "2011-01-01",
    "calculated_date": "2026-02-17",
    "method": "recalculation",
    "chip_usd": 2.14,
    "base_year": 2010,
    "notes": "Backfill for data year 2010"
  }
]
```

### `latest.json` Format

A single object, always overwritten with the most current estimate:

```json
{
  "chip_usd": 3.21,
  "effective_date": "2026-04-15",
  "calculated_date": "2026-04-15",
  "method": "extrapolation",
  "base_chip": 3.17,
  "base_effective_date": "2026-03-15",
  "next_recalculation": "When new ILOSTAT/PWT data is available"
}
```

### `base_params.json` Format

Written by `recalculate.py`, read by `extrapolate.py`:

```json
{
  "chip_constant": 2.68,
  "chip_nominal": 3.17,
  "base_year": 2022,
  "pwt_base_year": 2017,
  "cpi_reference_date": "2022-12-01",
  "cpi_reference_value": 296.797,
  "pwt_version": "11.0",
  "window_years": 5,
  "n_countries": 85,
  "effective_date": "2026-03-15",
  "calculated_date": "2026-03-15"
}
```

---

## Configuration

### `config.yaml`

```yaml
data:
  pwt_version: "11.0"
  pwt_base_year: 2017       # PWT's constant-dollar reference year

pipeline:
  year_start: 1992
  year_end: 2023            # Latest year in PWT 11.0
  window_years: 5
  weighting: "gdp"
  min_countries: 5
  min_coverage_pct: 0.70
  enable_imputation: true
  wage_averaging: "simple"

extrapolation:
  index: "cpi_u"            # FRED series CPIAUCSL
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

*Created: 2026-02-09 · Updated: 2026-02-17*

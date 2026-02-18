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
| **Extrapolation** | `extrapolate.py` | Weekly cron | Automated | Lightweight: apply latest CPI to the base value, update nominal CHIP |

Both scripts write directly to `output/`.  Consumers (the website, API
clients) read these files in place:

- **`latest.json`** — current CHIP value (the primary endpoint)
- **`chip_history.json`** — full chronological ledger of all estimates
- **`multipliers.csv`** — per-country multipliers from the latest recalculation
- **`base_params.json`** — parameters linking recalculation to extrapolation

**Idempotent by default:** Runs are deduplicated by `(effective_date,
method)`.  If a matching entry already exists in the history, it is
skipped.  Use `--replace` to overwrite an existing entry.  To fix a
bad entry: delete it from `chip_history.json`, re-run, and the gap is
filled automatically.

**Deployment model:** The `output/` directory is tracked in git.
The production server hosts a checkout of this repo, and the website
reads files directly from `output/`.  Updates reach the server via
`git pull`.

---

## Operational Runbook

### Initial Setup (Once)

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

7. Point your web server at the output files (e.g., nginx alias to
   `estimates/output/latest.json`).

8. Set up the weekly cron job (see below).

### Annual Recalculation (Human-Initiated)

Run this when new source data is available (new ILOSTAT wages or a new
PWT version), or at least once per year.

```
# On your dev machine:

# 1. Pull latest (captures any extrapolations from the server)
git pull

# 2. Run recalculation (--force-refresh fetches fresh data)
cd estimates
python recalculate.py --force-refresh --notes "Annual 2026 recalculation"

# 3. Review the summary
#    Look at: CHIP value, country count, snap magnitude, multipliers
cat output/latest_recalculation.md

# 4. If something looks wrong, adjust config.yaml and re-run.
#    If it looks right, commit:
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

A cron job on the production server runs the extrapolator.  It fetches
the latest CPI-U from FRED and applies it to the base CHIP value.

**Cron entry** (weekly is fine — the script is a no-op when CPI hasn't
updated.  BLS typically releases new CPI mid-month):

```cron
0 10 * * 1 cd /srv/chip/estimates && python extrapolate.py
```

When new CPI data is available, the script writes a new history entry
and updates `latest.json`.  The website picks up the change immediately.
When no new CPI data exists, the run is a silent no-op.

**Git sync:** Extrapolation outputs accumulate on the server between
annual recalculations.  They are captured in git at the next annual
cycle:

```
# At the next annual recalculation, on the server first:
cd /srv/chip
git add estimates/output/
git commit -m "Monthly extrapolations since last recalculation"
git push

# Then on dev machine, pull before recalculating:
git pull
```

### Backfilling Historical Data

To populate the history ledger with retrospective estimates, use
`--target-year` and `--effective-date`:

```bash
for year in $(seq 2000 2022); do
    python recalculate.py \
        --target-year $year \
        --effective-date "$((year+1))-01-01" \
        --notes "Backfill for data year $year"
done
```

Each entry gets `effective_date` set to the historical date and
`calculated_date` set to today.  Existing entries are skipped
automatically.

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
6. Updates all output files directly.

**CLI:**
```
python recalculate.py [--force-refresh] [--replace] [--notes "reason"]
python recalculate.py --target-year 2018 --effective-date 2019-01-01
```

### `extrapolate.py` — Monthly CPI Extrapolation

**What it does:**

1. Reads `output/base_params.json` (produced by the last recalculation).
2. Fetches the latest US CPI-U from FRED.
3. If the CPI observation date hasn't changed since the last
   extrapolation, exits without writing (no-op).
4. Computes: `CHIP_now = CHIP_base × (CPI_now / CPI_base)`.
5. Updates `chip_history.json` and `latest.json`.

**CLI:**
```
python extrapolate.py [--effective-date YYYY-MM-DD] [--replace] [--notes "..."]
```

---

## Output Files

All outputs live in `output/` and are **tracked in git**.  The production
web server reads them directly — no separate publish step.

```
output/
├── chip_history.json        # Chronological ledger of all estimates
├── base_params.json         # Parameters from last recalculation
├── latest.json              # Current CHIP value (primary endpoint)
├── latest_recalculation.md  # Human-readable review summary
└── multipliers.csv          # Per-country multipliers (latest only)
```

### `chip_history.json`

Chronological array of every recalculation and extrapolation:

```json
[
  {
    "effective_date": "2023-01-01",
    "calculated_date": "2026-02-17",
    "method": "recalculation",
    "chip_usd": 3.27,
    "chip_constant": 2.77,
    "base_year": 2022,
    "pwt_version": "11.0",
    "window_years": 5,
    "n_countries": 46,
    "notes": "Backfill for data year 2022"
  },
  {
    "effective_date": "2026-02-17",
    "calculated_date": "2026-02-17",
    "method": "extrapolation",
    "chip_usd": 3.27,
    "base_chip": 3.27,
    "base_effective_date": "2023-01-01",
    "cpi_ratio": 1.0,
    "cpi_date": "2026-01-01",
    "notes": "First extrapolation from 2022 base"
  }
]
```

### `latest.json`

The primary endpoint.  Always contains the most current CHIP value:

```json
{
  "chip_usd": 3.27,
  "effective_date": "2026-02-17",
  "calculated_date": "2026-02-17",
  "method": "extrapolation",
  "base_chip": 3.27,
  "base_effective_date": "2023-01-01",
  "next_recalculation": "When new ILOSTAT/PWT data is available"
}
```

### `base_params.json`

Written by `recalculate.py`, read by `extrapolate.py`:

```json
{
  "chip_constant": 2.77,
  "chip_nominal": 3.27,
  "base_year": 2022,
  "pwt_base_year": 2017,
  "cpi_reference_date": "2026-01-01",
  "cpi_reference_value": 326.588,
  "pwt_version": "11.0",
  "window_years": 5,
  "n_countries": 46,
  "effective_date": "2023-01-01",
  "calculated_date": "2026-02-17"
}
```

### `multipliers.csv`

Per-country CHIP multipliers from the latest recalculation.
A multiplier of 1.0 means the country matches the global CHIP:

```
country,chip_value,multiplier
PAN,6.01,2.17
CHE,5.96,2.15
...
USA,3.56,1.28
...
BOL,0.14,0.05
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
   immediately.

See `docs/inflation-tracking.md` Section 7.4 for analysis of market
dynamics around recalculations.

---

*Created: 2026-02-09 · Updated: 2026-02-17*

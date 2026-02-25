# CHIP Estimates Pipeline

Production pipeline for computing, publishing, and maintaining the official
CHIP value.  Separates **annual recalculation** (full data pipeline, tracked
in git) from **monthly extrapolation** (lightweight CPI update, server-local).

## Architecture

```
estimates/
├── config.yaml               # Locked methodology parameters
├── recalculate.py             # Annual: full pipeline → chip_estimates.json
├── extrapolate.py             # Monthly: CPI update → extrapolation.json
├── README.md
└── output/
    ├── chip_estimates.json    # ← TRACKED IN GIT (annual estimates)
    ├── latest_recalculation.md# ← TRACKED IN GIT (human review)
    ├── extrapolation.json     # ← LOCAL ONLY (server cache)
    └── logs/                  # ← LOCAL ONLY (transient)
```

## How It Works

### Two-Tier Model

| | Annual Recalculation | Monthly Extrapolation |
|---|---|---|
| **Script** | `recalculate.py` | `extrapolate.py` |
| **Trigger** | Human, when new ILOSTAT/PWT data releases | Cron, weekly or monthly |
| **Input** | ILOSTAT wages, PWT, GDP deflator | `chip_estimates.json` + FRED CPI-U |
| **Output** | `chip_estimates.json` (append) | `extrapolation.json` (overwrite) |
| **In git?** | Yes | No |
| **Formula** | Full Cobb-Douglas MPL pipeline | `CHIP_base × (CPI_now / CPI_base)` |
| **Complexity** | ~2 minutes, needs workbench venv | ~2 seconds, needs only requests |

### Data Flow

```
                                   ┌──────────────┐
  ILOSTAT + PWT + Deflator ──────► │recalculate.py│
                                   └──────┬───────┘
                                          │
                                          ▼
                                chip_estimates.json  ◄── git tracked
                                          │
                        ┌─────────────────┤
                        │ git push        │ git pull (on server)
                        ▼                 ▼
                      GitHub        ┌─────────────┐
                                    │extrapolate.py│ ◄── cron
                                    └──────┬──────┘
                                           │
                                           ▼
                                    extrapolation.json  ◄── server local
                                           │
                                           ▼
                                    chipcentral.net
```

## Output Files

### `chip_estimates.json` (git-tracked)

The authoritative record of annual CHIP estimates.  Array of entries, sorted
chronologically.  Each entry is self-contained — it includes everything the
extrapolator needs plus the country multipliers.

```json
[
  {
    "effective_date": "2023-01-01",
    "calculated_date": "2026-02-24",
    "chip_usd": 3.2688,
    "chip_constant": 2.7712,
    "base_year": 2022,
    "pwt_base_year": 2017,
    "pwt_version": "11.0",
    "window_years": 5,
    "n_countries": 46,
    "cpi_reference_date": "2026-01-01",
    "cpi_reference_value": 326.588,
    "multipliers": [
      {"country": "PAN", "chip_usd": 6.0113, "multiplier": 2.1695},
      {"country": "CHE", "chip_usd": 5.9634, "multiplier": 2.1522}
    ],
    "notes": "Recalculation with PWT 11.0 data through 2022"
  }
]
```

Key fields:
- **`effective_date`**: When this estimate applies (typically Jan 1 of the year after the data year).
- **`calculated_date`**: When the computation actually ran (reveals backfills).
- **`chip_usd`**: Nominal CHIP in US dollars — the headline number.
- **`cpi_reference_date`** / **`cpi_reference_value`**: The CPI-U snapshot the extrapolator uses as its baseline.
- **`multipliers`**: Per-country CHIP values and their ratio to the global constant-dollar average.

### `extrapolation.json` (server-local)

Current extrapolated CHIP value.  Overwritten on each run.  This is what the
chipcentral.net website reads to show "today's CHIP value."

```json
{
  "chip_usd": 3.3521,
  "effective_date": "2026-02-24",
  "calculated_date": "2026-02-24",
  "method": "extrapolation",
  "base_chip": 3.2688,
  "base_effective_date": "2023-01-01",
  "cpi_ratio": 1.025467,
  "cpi_date": "2026-01-01",
  "cpi_value": 334.987
}
```

### `latest_recalculation.md` (git-tracked)

Human-readable summary of the most recent recalculation run, with a review
checklist.  Updated every time `recalculate.py` runs.


## Operational Runbook

### Initial Setup

```bash
cd chip
source workbench/.venv/bin/activate
pip install -r workbench/requirements.txt   # if needed
```

### Annual Recalculation (human-initiated)

Run when new ILOSTAT/PWT data is available (typically once per year):

```bash
# From the chip/ root, with workbench venv active
python estimates/recalculate.py --notes "Annual update with 2023 data"

# Review the output
cat estimates/output/latest_recalculation.md

# If satisfied, commit and push
git add estimates/output/chip_estimates.json estimates/output/latest_recalculation.md
git commit -m "CHIP recalculation: 2024 estimate"
git push
```

To force a fresh data download (bypassing cache):

```bash
python estimates/recalculate.py --force-refresh --notes "Fresh data pull"
```

### Monthly Extrapolation (server cron)

On the production server, after pulling the latest repo:

```bash
cd /path/to/chip
git pull
python estimates/extrapolate.py
```

The website reads `estimates/output/extrapolation.json` for the current value.

Example cron entry (weekly, Monday at 3 AM):
```
0 3 * * 1 cd /path/to/chip && git pull && python estimates/extrapolate.py >> /var/log/chip-extrapolate.log 2>&1
```

### Backfilling Historical Data

To recreate historical estimates retroactively:

```bash
for year in $(seq 2000 2022); do
    python estimates/recalculate.py \
        --target-year $year \
        --effective-date "$((year+1))-01-01" \
        --notes "Backfill for data year $year"
done
```

The `effective_date` vs `calculated_date` in each entry makes backfills
transparent — consumers can see that a "2010-01-01" estimate was actually
computed on "2026-02-24".

### Correcting an Estimate

To overwrite an existing entry (e.g., after discovering a data issue):

```bash
python estimates/recalculate.py --target-year 2022 \
    --effective-date 2023-01-01 --replace \
    --notes "Corrected: fixed country exclusion list"
```

### New PWT Version

When a new PWT version releases:

1. Update `config.yaml` → `pwt_version`
2. Optionally update `year_end` if coverage increased
3. Run `recalculate.py --force-refresh`
4. Expect a "snap" — compare with the previous value in `latest_recalculation.md`


## Idempotency

Both scripts are safe to re-run:

- **`recalculate.py`**: Checks for an existing entry by `effective_date`.
  Skips if already present.  Use `--replace` to overwrite.
- **`extrapolate.py`**: Checks whether CPI data or the base estimate has
  changed since the last run.  No-ops if nothing is new.  Use `--replace`
  to force a write.


## Configuration

`config.yaml` locks the methodology so results are reproducible:

```yaml
data:
  pwt_version: "11.0"
  pwt_base_year: 2017       # PWT's constant-dollar reference year

pipeline:
  year_start: 1992
  year_end: 2023
  window_years: 5
  weighting: gdp
  enable_imputation: true
  wage_averaging: simple
  min_countries: 5

extrapolation:
  cpi_u: CPIAUCSL
```

Changes to these parameters should be treated as methodology changes and
documented in the commit message.


## What Consumers See

### chipcentral.net (or any client)

The website needs two things:

1. **Current CHIP value**: Read `extrapolation.json` → `chip_usd`
   (Falls back to `chip_estimates.json` → last entry → `chip_usd` if
   no extrapolation cache exists yet.)

2. **Country multipliers**: Read `chip_estimates.json` → last entry → `multipliers`

3. **Historical series**: Read `chip_estimates.json` → all entries
   (annual granularity, suitable for a chart or table)


## Future Enhancements

- **Historical multipliers per entry**: Already embedded — each entry in
  `chip_estimates.json` includes multipliers for that year.
- **Trend analysis**: Country multiplier trends across years.
- **Automated server pull**: Webhook on GitHub push to trigger `git pull`
  and re-extrapolation on the production server.

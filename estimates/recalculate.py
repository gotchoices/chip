#!/usr/bin/env python3
"""
CHIP Recalculation — Annual Full Pipeline

Runs the complete CHIP estimation pipeline using locked-in methodology
from the workbench studies.  Appends results to chip_estimates.json —
the authoritative record of annual CHIP values, tracked in git.

Each entry includes the global CHIP value, per-country multipliers, and
the CPI reference point needed by the extrapolator.

For backfilling historical data, use --target-year and --effective-date:

    for year in $(seq 2000 2022); do
        python recalculate.py --target-year $year \\
            --effective-date "$((year+1))-01-01" \\
            --notes "Backfill for data year $year"
    done

Usage:
    python recalculate.py [--force-refresh] [--replace] [--notes "..."]
    python recalculate.py --target-year 2018 --effective-date 2019-01-01
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Path setup — import from workbench/lib/
# ---------------------------------------------------------------------------
ESTIMATES_DIR = Path(__file__).parent
PROJECT_ROOT = ESTIMATES_DIR.parent
WORKBENCH_ROOT = PROJECT_ROOT / "workbench"
sys.path.insert(0, str(WORKBENCH_ROOT))

from lib.logging_config import setup_logging, get_logger
from lib import fetcher, normalize, pipeline

logger = get_logger(__name__)

OUTPUT_DIR = ESTIMATES_DIR / "output"
ESTIMATES_FILE = OUTPUT_DIR / "chip_estimates.json"


# =============================================================================
# CONFIGURATION
# =============================================================================

def load_estimates_config():
    """Load config.yaml from estimates/ directory."""
    config_path = ESTIMATES_DIR / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing {config_path}")

    import yaml
    with open(config_path) as f:
        return yaml.safe_load(f)


# =============================================================================
# CORE PIPELINE
# =============================================================================

def run_chip_pipeline(data, deflator_df, cfg):
    """Run the full CHIP estimation pipeline."""
    pipe_cfg = cfg.get("pipeline", {})
    result = pipeline.prepare_labor_data(
        data=data,
        year_start=pipe_cfg.get("year_start", 1992),
        year_end=pipe_cfg.get("year_end", 2023),
        deflator_df=deflator_df,
        include_countries=None,
        enable_imputation=pipe_cfg.get("enable_imputation", True),
        wage_averaging_method=pipe_cfg.get("wage_averaging", "simple"),
    )
    _, _, est_data = pipeline.estimate_chip(
        result["est_data"],
        enable_imputation=pipe_cfg.get("enable_imputation", True),
    )
    return est_data


def aggregate_by_year(est_data, weighting="gdp"):
    """Aggregate CHIP to a single value per year across countries."""
    rows = []
    for year, ydf in est_data.groupby("year"):
        if len(ydf) == 0:
            continue
        if weighting == "gdp":
            total_gdp = ydf["rgdpna"].sum()
            if total_gdp > 0:
                chip = (ydf["chip_value"] * ydf["rgdpna"]).sum() / total_gdp
            else:
                chip = ydf["chip_value"].mean()
        else:
            chip = ydf["chip_value"].mean()

        rows.append({
            "year": int(year),
            "chip_value": chip,
            "n_countries": len(ydf),
        })

    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def trailing_window_chip(ts_constant, deflator, window_size, target_year):
    """
    Compute the trailing-window nominal CHIP for a specific target year.

    Averages CHIP from [target_year - window + 1, ..., target_year],
    re-inflating each to target_year dollars.
    """
    chip_by_year = dict(zip(ts_constant["year"], ts_constant["chip_value"]))
    defl_by_year = dict(zip(deflator["year"], deflator["deflator"]))

    target_defl = defl_by_year.get(target_year)
    if target_defl is None or target_defl == 0:
        return None

    window_years = [y for y in chip_by_year
                    if target_year - window_size + 1 <= y <= target_year]
    if not window_years:
        return None

    reinflated = []
    for wy in sorted(window_years):
        chip_const = chip_by_year.get(wy)
        if chip_const is not None:
            reinflated.append(chip_const * target_defl / 100.0)

    if not reinflated:
        return None

    return float(np.mean(reinflated))


def compute_country_multipliers(est_data, global_chip, target_year):
    """Compute per-country CHIP multiplier for the target year."""
    year_data = est_data[est_data["year"] == target_year].copy()
    if len(year_data) == 0:
        return []

    df = year_data[["country", "chip_value"]].copy()
    df["multiplier"] = df["chip_value"] / global_chip
    df = df.sort_values("multiplier", ascending=False).reset_index(drop=True)

    return [
        {
            "country": row["country"],
            "chip_usd": round(float(row["chip_value"]), 4),
            "multiplier": round(float(row["multiplier"]), 4),
        }
        for _, row in df.iterrows()
    ]


# =============================================================================
# ESTIMATES FILE I/O
# =============================================================================

def load_estimates():
    """Load chip_estimates.json, returning an empty list if absent."""
    if ESTIMATES_FILE.exists():
        with open(ESTIMATES_FILE) as f:
            return json.load(f)
    return []


def save_estimates(estimates):
    """Write chip_estimates.json, sorted by effective_date."""
    estimates.sort(key=lambda e: e.get("effective_date", ""))
    with open(ESTIMATES_FILE, "w") as f:
        json.dump(estimates, f, indent=2, default=str)
    logger.info(f"Wrote {ESTIMATES_FILE} ({len(estimates)} entries)")


def upsert_estimate(entry, replace=False):
    """
    Insert an estimate if not already present.

    Dedup key: effective_date.  Returns True if written, False if skipped.
    """
    estimates = load_estimates()
    eff = entry.get("effective_date")

    existing_idx = None
    for i, e in enumerate(estimates):
        if e.get("effective_date") == eff:
            existing_idx = i
            break

    if existing_idx is not None:
        if not replace:
            logger.info(
                f"Estimate already exists for {eff} — skipping. "
                f"Use --replace to overwrite."
            )
            return False
        logger.info(f"Replacing estimate for {eff}")
        estimates[existing_idx] = entry
    else:
        estimates.append(entry)

    save_estimates(estimates)
    return True


def get_previous_chip():
    """Get the chip_usd from the latest estimate, or None."""
    estimates = load_estimates()
    if not estimates:
        return None
    return estimates[-1].get("chip_usd")


# =============================================================================
# SUMMARY REPORT
# =============================================================================

def write_summary_report(entry, prev_chip, output_dir):
    """Write human-readable summary of the recalculation."""
    lines = [
        f"# CHIP Recalculation — {date.today().isoformat()}",
        "",
        "## Global CHIP Value",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Nominal CHIP ({entry['base_year']}) | **${entry['chip_usd']:.2f}/hr** |",
        f"| Constant CHIP ({entry['pwt_base_year']}$) | ${entry['chip_constant']:.2f}/hr |",
        f"| Countries | {entry['n_countries']} |",
        "| Method | GDP-weighted, 5-year trailing window |",
        "",
    ]

    if prev_chip is not None:
        pct = (entry["chip_usd"] - prev_chip) / prev_chip * 100
        lines.extend([
            "## Comparison to Previous",
            "",
            "| | Previous | Current | Change |",
            "|--|----------|---------|--------|",
            f"| Nominal CHIP | ${prev_chip:.2f} | ${entry['chip_usd']:.2f} | {pct:+.1f}% |",
            "",
            f"**Snap magnitude:** {abs(pct):.1f}%",
            "",
        ])

    mults = entry.get("multipliers", [])
    if mults:
        lines.extend([
            "## Country Multipliers (Top 10 / Bottom 5)",
            "",
            "| Country | CHIP ($/hr) | Multiplier |",
            "|---------|------------|------------|",
        ])
        for m in mults[:10]:
            lines.append(
                f"| {m['country']} | ${m['chip_usd']:.2f} | "
                f"{m['multiplier']:.2f}x |"
            )
        if len(mults) > 15:
            lines.append("| ... | ... | ... |")
        for m in mults[-5:]:
            lines.append(
                f"| {m['country']} | ${m['chip_usd']:.2f} | "
                f"{m['multiplier']:.2f}x |"
            )
        lines.append("")

    lines.extend([
        "## Review Checklist",
        "",
        "- [ ] CHIP value within expected range?",
        "- [ ] Country count stable?",
        "- [ ] No anomalous multipliers?",
        "- [ ] Ready to push?",
        "",
    ])

    path = output_dir / "latest_recalculation.md"
    with open(path, "w") as f:
        f.write("\n".join(lines))
    logger.info(f"Wrote {path}")


# =============================================================================
# CPI REFERENCE
# =============================================================================

def _fetch_cpi_reference():
    """Fetch the latest CPI-U value from FRED."""
    import requests
    from io import StringIO

    series_id = "CPIAUCSL"
    api_key = _load_fred_api_key()

    if api_key:
        url = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}&api_key={api_key}&file_type=json"
            f"&sort_order=desc&limit=1"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        obs = resp.json()["observations"][0]
        return {"date": obs["date"], "value": float(obs["value"])}
    else:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        df.columns = ["date", "value"]
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        last = df.iloc[-1]
        return {"date": str(last["date"]), "value": float(last["value"])}


def _load_fred_api_key():
    """Load FRED API key from secrets.toml."""
    secrets_path = PROJECT_ROOT / "secrets.toml"
    if not secrets_path.exists():
        return None
    try:
        import tomli
        with open(secrets_path, "rb") as f:
            secrets = tomli.load(f)
        return secrets.get("fred", {}).get("api_key")
    except Exception:
        return None


# =============================================================================
# MAIN
# =============================================================================

def recalculate(force_refresh=False, target_year=None, effective_date=None,
                replace=False, notes=""):
    """Run the full CHIP recalculation."""
    cfg = load_estimates_config()
    pipe_cfg = cfg.get("pipeline", {})
    data_cfg = cfg.get("data", {})

    pwt_version = data_cfg.get("pwt_version", "11.0")
    pwt_base_year = data_cfg.get("pwt_base_year", 2017)
    window_years = pipe_cfg.get("window_years", 5)

    eff_date = effective_date or date.today().isoformat()
    calc_date = date.today().isoformat()

    # ------------------------------------------------------------------
    # Step 1: Fetch data
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 1: Fetching data")
    logger.info("=" * 60)

    if force_refresh:
        logger.info("Force refresh: bypassing cache")

    data = fetcher.get_all(
        use_cache=not force_refresh,
        pwt_version=pwt_version,
    )
    for name, df in data.items():
        logger.info(f"  {name}: {len(df):,} rows")

    deflator_df = normalize.normalize_deflator(
        data["deflator"], base_year=pwt_base_year
    )

    # ------------------------------------------------------------------
    # Step 2: Run pipeline
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 2: Running CHIP estimation pipeline")
    logger.info("=" * 60)

    est_data = run_chip_pipeline(data, deflator_df, cfg)
    logger.info(f"Pipeline: {len(est_data)} obs, "
                f"{est_data['country'].nunique()} countries")

    # ------------------------------------------------------------------
    # Step 3: Aggregate time series
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 3: Aggregating to annual series")
    logger.info("=" * 60)

    ts_constant = aggregate_by_year(est_data, weighting="gdp")

    min_countries = pipe_cfg.get("min_countries", 5)
    ts_constant = ts_constant[ts_constant["n_countries"] >= min_countries]

    valid_years = sorted(ts_constant["year"].tolist())
    logger.info(f"Series: {len(valid_years)} years "
                f"({min(valid_years)}–{max(valid_years)})")

    # ------------------------------------------------------------------
    # Step 4: Trailing-window CHIP
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info(f"Step 4: Computing {window_years}-year trailing-window CHIP")
    logger.info("=" * 60)

    if target_year is not None:
        if target_year not in valid_years:
            raise ValueError(
                f"--target-year {target_year} not in available years "
                f"({min(valid_years)}–{max(valid_years)})"
            )
        logger.info(f"Using explicit target year: {target_year}")
    else:
        target_year = max(valid_years)

    chip_nominal = trailing_window_chip(
        ts_constant, deflator_df, window_years, target_year
    )

    chip_by_year = dict(zip(ts_constant["year"], ts_constant["chip_value"]))
    window_vals = [chip_by_year[y] for y in valid_years
                   if target_year - window_years + 1 <= y <= target_year
                   and y in chip_by_year]
    chip_constant = float(np.mean(window_vals)) if window_vals else None

    n_countries = int(ts_constant[ts_constant["year"] == target_year]["n_countries"].iloc[0])

    logger.info(f"Target year: {target_year}")
    logger.info(f"Constant CHIP ({pwt_base_year}$): ${chip_constant:.2f}")
    logger.info(f"Nominal CHIP ({target_year}$): ${chip_nominal:.2f}")
    logger.info(f"Countries: {n_countries}")

    # ------------------------------------------------------------------
    # Step 5: Country multipliers
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 5: Computing country multipliers")
    logger.info("=" * 60)

    multipliers = compute_country_multipliers(
        est_data, chip_constant, target_year
    )
    logger.info(f"Multipliers for {len(multipliers)} countries")

    # ------------------------------------------------------------------
    # Step 6: Fetch CPI reference point
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 6: Fetching CPI reference for extrapolator")
    logger.info("=" * 60)

    cpi_ref = _fetch_cpi_reference()
    logger.info(f"CPI reference: {cpi_ref['value']:.3f} "
                f"as of {cpi_ref['date']}")

    # ------------------------------------------------------------------
    # Step 7: Write estimate
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 7: Writing estimate")
    logger.info("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    prev_chip = get_previous_chip()

    entry = {
        "effective_date": eff_date,
        "calculated_date": calc_date,
        "chip_usd": round(chip_nominal, 4),
        "chip_constant": round(chip_constant, 4),
        "base_year": target_year,
        "pwt_base_year": pwt_base_year,
        "pwt_version": pwt_version,
        "window_years": window_years,
        "n_countries": n_countries,
        "cpi_reference_date": cpi_ref["date"],
        "cpi_reference_value": round(cpi_ref["value"], 3),
        "multipliers": multipliers,
        "notes": notes or f"Recalculation with PWT {pwt_version} "
                          f"data through {target_year}",
    }

    inserted = upsert_estimate(entry, replace=replace)

    # Summary report (always written for review)
    write_summary_report(entry, prev_chip, OUTPUT_DIR)

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("RECALCULATION COMPLETE")
    logger.info(f"  Global CHIP: ${chip_nominal:.2f}/hr ({target_year} nominal)")
    logger.info(f"  Countries: {n_countries}, Multipliers: {len(multipliers)}")
    if not inserted:
        logger.info("  (estimate already existed — skipped)")
    logger.info("=" * 60)

    return {
        "chip_nominal": chip_nominal,
        "chip_constant": chip_constant,
        "target_year": target_year,
        "n_countries": n_countries,
        "n_multipliers": len(multipliers),
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CHIP Annual Recalculation",
        epilog=(
            "Backfill example:\n"
            "  for year in $(seq 2000 2022); do\n"
            '    python recalculate.py --target-year $year '
            '--effective-date "$((year+1))-01-01"\n'
            "  done"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force-refresh", action="store_true",
        help="Bypass data cache and fetch fresh from all sources"
    )
    parser.add_argument(
        "--target-year", type=int, default=None,
        help="Override trailing-window target year (for backfill)"
    )
    parser.add_argument(
        "--effective-date", type=str, default=None,
        help="Effective date for this estimate (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--replace", action="store_true",
        help="Overwrite an existing estimate for the same effective date"
    )
    parser.add_argument(
        "--notes", type=str, default="",
        help="Notes to include in the estimate entry"
    )
    args = parser.parse_args()

    global logger
    logger = setup_logging("recalculate", output_dir=OUTPUT_DIR)

    logger.info("CHIP Recalculation Pipeline")
    logger.info(f"Date: {date.today().isoformat()}")
    if args.target_year:
        logger.info(f"Target year override: {args.target_year}")
    if args.effective_date:
        logger.info(f"Effective date override: {args.effective_date}")

    try:
        result = recalculate(
            force_refresh=args.force_refresh,
            target_year=args.target_year,
            effective_date=args.effective_date,
            replace=args.replace,
            notes=args.notes,
        )
        logger.info("Success")
    except Exception as e:
        logger.error(f"Recalculation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

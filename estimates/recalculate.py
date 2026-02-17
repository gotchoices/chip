#!/usr/bin/env python3
"""
CHIP Recalculation — Annual Full Pipeline

Runs the complete CHIP estimation pipeline using locked-in methodology
from the workbench studies.  Produces:

  - Global GDP-weighted CHIP value (5-year trailing window, nominal)
  - Per-country multipliers
  - Base parameters for the monthly extrapolator
  - Append to chip_history.json

Intended to be run by a human operator when new source data is available
(typically annually, or when a new PWT version releases).

Usage:
    python recalculate.py [--force-refresh] [--notes "reason for run"]
"""

import argparse
import json
import sys
from datetime import datetime, date
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


# =============================================================================
# CONFIGURATION (from config.yaml, with defaults from production study)
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
    """
    Run the full CHIP estimation pipeline.

    Returns per-country-year DataFrame with chip_value, rgdpna, etc.
    """
    pipe_cfg = cfg.get("pipeline", {})
    year_start = pipe_cfg.get("year_start", 1992)
    year_end = pipe_cfg.get("year_end", 2023)
    enable_imputation = pipe_cfg.get("enable_imputation", True)
    wage_averaging = pipe_cfg.get("wage_averaging", "simple")

    result = pipeline.prepare_labor_data(
        data=data,
        year_start=year_start,
        year_end=year_end,
        deflator_df=deflator_df,
        include_countries=None,
        enable_imputation=enable_imputation,
        wage_averaging_method=wage_averaging,
    )
    _, _, est_data = pipeline.estimate_chip(
        result["est_data"],
        enable_imputation=enable_imputation,
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
    """
    Compute per-country CHIP multiplier for the target year.

    multiplier = country_chip / global_chip
    """
    year_data = est_data[est_data["year"] == target_year].copy()
    if len(year_data) == 0:
        return pd.DataFrame()

    df = year_data[["country", "chip_value"]].copy()
    df["multiplier"] = df["chip_value"] / global_chip
    df = df.sort_values("multiplier", ascending=False).reset_index(drop=True)
    return df


# =============================================================================
# OUTPUT HELPERS
# =============================================================================

def append_history(entry, output_dir):
    """Append an entry to chip_history.json."""
    history_path = output_dir / "chip_history.json"
    if history_path.exists():
        with open(history_path) as f:
            history = json.load(f)
    else:
        history = []

    history.append(entry)

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2, default=str)

    logger.info(f"Appended to {history_path} (now {len(history)} entries)")


def write_base_params(params, output_dir):
    """Write base_params.json for the extrapolator."""
    path = output_dir / "base_params.json"
    with open(path, "w") as f:
        json.dump(params, f, indent=2, default=str)
    logger.info(f"Wrote {path}")


def write_latest(entry, output_dir):
    """Write latest.json with current CHIP value."""
    path = output_dir / "latest.json"
    with open(path, "w") as f:
        json.dump(entry, f, indent=2, default=str)
    logger.info(f"Wrote {path}")


def write_summary_report(chip_nominal, chip_constant, target_year,
                         n_countries, multipliers_df, prev_chip,
                         output_dir):
    """Write human-readable summary of the recalculation."""
    lines = [
        f"# CHIP Recalculation — {date.today().isoformat()}",
        "",
        "## Global CHIP Value",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Nominal CHIP ({target_year}) | **${chip_nominal:.2f}/hr** |",
        f"| Constant CHIP (2017$) | ${chip_constant:.2f}/hr |",
        f"| Countries | {n_countries} |",
        f"| Method | GDP-weighted, 5-year trailing window |",
        "",
    ]

    if prev_chip is not None:
        pct = (chip_nominal - prev_chip) / prev_chip * 100
        lines.extend([
            "## Comparison to Previous",
            "",
            f"| | Previous | Current | Change |",
            f"|--|----------|---------|--------|",
            f"| Nominal CHIP | ${prev_chip:.2f} | ${chip_nominal:.2f} | {pct:+.1f}% |",
            "",
            f"**Snap magnitude:** {abs(pct):.1f}%",
            "",
        ])

    if len(multipliers_df) > 0:
        lines.extend([
            "## Country Multipliers (Top 10 / Bottom 5)",
            "",
            "| Country | CHIP ($/hr) | Multiplier |",
            "|---------|------------|------------|",
        ])
        top = multipliers_df.head(10)
        bot = multipliers_df.tail(5)
        for _, row in top.iterrows():
            lines.append(
                f"| {row['country']} | ${row['chip_value']:.2f} | "
                f"{row['multiplier']:.2f}x |"
            )
        lines.append("| ... | ... | ... |")
        for _, row in bot.iterrows():
            lines.append(
                f"| {row['country']} | ${row['chip_value']:.2f} | "
                f"{row['multiplier']:.2f}x |"
            )
        lines.append("")

    lines.extend([
        "## Review Checklist",
        "",
        "- [ ] CHIP value within expected range?",
        "- [ ] Country count stable?",
        "- [ ] No anomalous multipliers?",
        "- [ ] Ready to publish?",
        "",
    ])

    path = output_dir / "latest_recalculation.md"
    with open(path, "w") as f:
        f.write("\n".join(lines))
    logger.info(f"Wrote {path}")


# =============================================================================
# MAIN
# =============================================================================

def recalculate(force_refresh=False, notes=""):
    """Run the full CHIP recalculation."""
    cfg = load_estimates_config()
    pipe_cfg = cfg.get("pipeline", {})
    data_cfg = cfg.get("data", {})
    extrap_cfg = cfg.get("extrapolation", {})

    pwt_version = data_cfg.get("pwt_version", "11.0")
    window_years = pipe_cfg.get("window_years", 5)
    year_end = pipe_cfg.get("year_end", 2023)
    deflator_base_year = extrap_cfg.get("deflator_base_year", 2017)

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
        data["deflator"], base_year=deflator_base_year
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

    # Filter to years with enough countries
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

    target_year = max(valid_years)
    chip_nominal = trailing_window_chip(
        ts_constant, deflator_df, window_years, target_year
    )

    # Also get the constant-dollar value for base_params
    chip_by_year = dict(zip(ts_constant["year"], ts_constant["chip_value"]))
    window_vals = [chip_by_year[y] for y in valid_years
                   if target_year - window_years + 1 <= y <= target_year
                   and y in chip_by_year]
    chip_constant = float(np.mean(window_vals)) if window_vals else None

    n_countries = int(ts_constant[ts_constant["year"] == target_year]["n_countries"].iloc[0])

    logger.info(f"Target year: {target_year}")
    logger.info(f"Constant CHIP (2017$): ${chip_constant:.2f}")
    logger.info(f"Nominal CHIP ({target_year}$): ${chip_nominal:.2f}")
    logger.info(f"Countries: {n_countries}")

    # ------------------------------------------------------------------
    # Step 5: Country multipliers
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 5: Computing country multipliers")
    logger.info("=" * 60)

    multipliers_df = compute_country_multipliers(
        est_data, chip_constant, target_year
    )
    logger.info(f"Multipliers for {len(multipliers_df)} countries")
    if len(multipliers_df) > 0:
        logger.info(f"  Range: {multipliers_df['multiplier'].min():.2f}x "
                     f"to {multipliers_df['multiplier'].max():.2f}x")

    # ------------------------------------------------------------------
    # Step 6: Fetch CPI reference point for extrapolator
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 6: Fetching CPI reference for extrapolator")
    logger.info("=" * 60)

    cpi_ref = _fetch_cpi_reference()
    logger.info(f"CPI reference: {cpi_ref['value']:.3f} "
                f"as of {cpi_ref['date']}")

    # ------------------------------------------------------------------
    # Step 7: Write outputs
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("Step 7: Writing outputs")
    logger.info("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Check previous value for snap comparison
    prev_chip = _get_previous_chip()

    # History entry
    history_entry = {
        "date": date.today().isoformat(),
        "method": "recalculation",
        "chip_usd": round(chip_nominal, 4),
        "chip_constant_2017": round(chip_constant, 4),
        "base_year": target_year,
        "pwt_version": pwt_version,
        "window_years": window_years,
        "n_countries": n_countries,
        "notes": notes or f"Recalculation with PWT {pwt_version} "
                          f"data through {target_year}",
    }

    if prev_chip is not None:
        snap_pct = (chip_nominal - prev_chip) / prev_chip * 100
        history_entry["snap_from"] = round(prev_chip, 4)
        history_entry["snap_pct"] = round(snap_pct, 2)

    append_history(history_entry, OUTPUT_DIR)

    # Base params for extrapolator
    base_params = {
        "chip_constant_2017": round(chip_constant, 4),
        "chip_nominal": round(chip_nominal, 4),
        "base_year": target_year,
        "deflator_base_year": deflator_base_year,
        "cpi_reference_date": cpi_ref["date"],
        "cpi_reference_value": round(cpi_ref["value"], 3),
        "pwt_version": pwt_version,
        "window_years": window_years,
        "n_countries": n_countries,
        "recalculation_date": date.today().isoformat(),
    }
    write_base_params(base_params, OUTPUT_DIR)

    # Latest value
    latest = {
        "chip_usd": round(chip_nominal, 4),
        "date": date.today().isoformat(),
        "method": "recalculation",
        "base_year": target_year,
        "pwt_version": pwt_version,
        "next_recalculation": "When new ILOSTAT/PWT data is available",
    }
    write_latest(latest, OUTPUT_DIR)

    # Multipliers CSV
    if len(multipliers_df) > 0:
        mult_path = OUTPUT_DIR / "multipliers.csv"
        multipliers_df.to_csv(mult_path, index=False)
        logger.info(f"Wrote {mult_path}")

    # Human-readable summary
    write_summary_report(
        chip_nominal, chip_constant, target_year, n_countries,
        multipliers_df, prev_chip, OUTPUT_DIR
    )

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("RECALCULATION COMPLETE")
    logger.info(f"  Global CHIP: ${chip_nominal:.2f}/hr ({target_year} nominal)")
    logger.info(f"  Countries: {n_countries}")
    logger.info(f"  Base params written for extrapolator")
    logger.info("=" * 60)

    return {
        "chip_nominal": chip_nominal,
        "chip_constant": chip_constant,
        "target_year": target_year,
        "n_countries": n_countries,
        "multipliers": multipliers_df,
    }


# =============================================================================
# CPI REFERENCE
# =============================================================================

def _fetch_cpi_reference():
    """
    Fetch the latest CPI-U value from FRED for the extrapolator.

    Returns dict with 'date' and 'value'.
    """
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


def _get_previous_chip():
    """Read the previous CHIP value from latest.json if it exists."""
    path = OUTPUT_DIR / "latest.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("chip_usd")
    except Exception:
        return None


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CHIP Annual Recalculation"
    )
    parser.add_argument(
        "--force-refresh", action="store_true",
        help="Bypass data cache and fetch fresh from all sources"
    )
    parser.add_argument(
        "--notes", type=str, default="",
        help="Notes to include in the history entry"
    )
    args = parser.parse_args()

    global logger
    logger = setup_logging("recalculate", output_dir=OUTPUT_DIR)

    logger.info("CHIP Recalculation Pipeline")
    logger.info(f"Date: {date.today().isoformat()}")

    try:
        result = recalculate(
            force_refresh=args.force_refresh,
            notes=args.notes,
        )
        logger.info("Success")
    except Exception as e:
        logger.error(f"Recalculation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

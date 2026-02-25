#!/usr/bin/env python3
"""
CHIP Extrapolation — CPI Update

Lightweight script that applies the latest CPI-U data to the base CHIP
value from chip_estimates.json.  Writes to a local cache file
(extrapolation.json) that is NOT tracked in git.

Designed to run on the production server via cron.  No-ops when:
  - No new CPI data is available since the last run
  - The base estimate hasn't changed

Usage:
    python extrapolate.py [--replace] [--notes "optional note"]

Requires:
    output/chip_estimates.json  (tracked in git, produced by recalculate.py)
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
ESTIMATES_DIR = Path(__file__).parent
PROJECT_ROOT = ESTIMATES_DIR.parent
OUTPUT_DIR = ESTIMATES_DIR / "output"
ESTIMATES_FILE = OUTPUT_DIR / "chip_estimates.json"
EXTRAPOLATION_FILE = OUTPUT_DIR / "extrapolation.json"

# Import workbench logging if available; fall back to stdlib
WORKBENCH_ROOT = PROJECT_ROOT / "workbench"
sys.path.insert(0, str(WORKBENCH_ROOT))

try:
    from lib.logging_config import setup_logging, get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger(__name__)

    def setup_logging(name, output_dir=None):
        return logger


# =============================================================================
# CPI FETCH
# =============================================================================

def fetch_latest_cpi():
    """Fetch the most recent CPI-U observation from FRED."""
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
# ESTIMATES FILE
# =============================================================================

def load_latest_estimate():
    """
    Load the most recent entry from chip_estimates.json.

    Returns the entry dict, or raises FileNotFoundError.
    """
    if not ESTIMATES_FILE.exists():
        raise FileNotFoundError(
            f"No estimates file at {ESTIMATES_FILE}.  "
            f"Run recalculate.py first."
        )
    with open(ESTIMATES_FILE) as f:
        estimates = json.load(f)
    if not estimates:
        raise ValueError("chip_estimates.json is empty")
    return estimates[-1]


# =============================================================================
# LOCAL CACHE
# =============================================================================

def load_cache():
    """Load the local extrapolation cache, or None if absent."""
    if not EXTRAPOLATION_FILE.exists():
        return None
    try:
        with open(EXTRAPOLATION_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(data):
    """Write the local extrapolation cache."""
    with open(EXTRAPOLATION_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Wrote {EXTRAPOLATION_FILE}")


# =============================================================================
# EXTRAPOLATION
# =============================================================================

def extrapolate(replace=False, notes=""):
    """
    Compute current nominal CHIP via CPI extrapolation.

    Formula:
        CHIP_now = CHIP_base × (CPI_now / CPI_base)

    Reads the base from chip_estimates.json (the latest entry).
    Writes to extrapolation.json (local cache, not in git).

    No-ops when CPI hasn't changed and base estimate hasn't changed,
    unless --replace is set.
    """
    # Load the latest annual estimate
    estimate = load_latest_estimate()
    base_chip = estimate["chip_usd"]
    base_cpi_value = estimate["cpi_reference_value"]
    base_cpi_date = estimate["cpi_reference_date"]
    base_eff_date = estimate["effective_date"]

    logger.info(f"Base estimate: ${base_chip:.4f} (effective {base_eff_date})")
    logger.info(f"Base CPI: {base_cpi_value:.3f} ({base_cpi_date})")

    # Fetch current CPI
    cpi_now = fetch_latest_cpi()
    logger.info(f"Current CPI: {cpi_now['value']:.3f} ({cpi_now['date']})")

    # Check if anything has changed since last extrapolation
    if not replace:
        cache = load_cache()
        if cache:
            same_cpi = cache.get("cpi_date") == cpi_now["date"]
            same_base = cache.get("base_effective_date") == base_eff_date
            if same_cpi and same_base:
                logger.info(
                    f"No change: CPI still {cpi_now['date']}, "
                    f"base still {base_eff_date}. Nothing to do."
                )
                return None

    # Extrapolate
    cpi_ratio = cpi_now["value"] / base_cpi_value
    chip_now = base_chip * cpi_ratio

    logger.info(f"CPI ratio: {cpi_ratio:.6f}")
    logger.info(f"Extrapolated CHIP: ${chip_now:.4f}")

    # Write local cache
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "chip_usd": round(chip_now, 4),
        "effective_date": date.today().isoformat(),
        "calculated_date": date.today().isoformat(),
        "method": "extrapolation",
        "base_chip": round(base_chip, 4),
        "base_effective_date": base_eff_date,
        "cpi_ratio": round(cpi_ratio, 6),
        "cpi_date": cpi_now["date"],
        "cpi_value": round(cpi_now["value"], 3),
        "notes": notes or "CPI extrapolation",
    }

    save_cache(cache_data)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("EXTRAPOLATION COMPLETE")
    logger.info(f"  CHIP: ${chip_now:.4f}/hr")
    logger.info(f"  CPI: {cpi_now['value']:.3f} ({cpi_now['date']})")
    logger.info(f"  Ratio vs base: {cpi_ratio:.6f}")
    logger.info("=" * 60)

    return cache_data


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CHIP CPI Extrapolation"
    )
    parser.add_argument(
        "--replace", action="store_true",
        help="Force update even if nothing has changed"
    )
    parser.add_argument(
        "--notes", type=str, default="",
        help="Notes to include in the cache entry"
    )
    args = parser.parse_args()

    global logger
    logger = setup_logging("extrapolate", output_dir=OUTPUT_DIR)

    logger.info("CHIP CPI Extrapolation")
    logger.info(f"Date: {date.today().isoformat()}")

    try:
        result = extrapolate(
            replace=args.replace,
            notes=args.notes,
        )
        if result is None:
            logger.info("No update needed")
        else:
            logger.info("Success")
    except Exception as e:
        logger.error(f"Extrapolation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

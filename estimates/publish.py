#!/usr/bin/env python3
"""
CHIP Publish — Format Outputs for API Consumption

Reads the internal output files and produces API-ready JSON files that
can be served by any static web server or consumed by a dynamic API.

Usage:
    python publish.py

Reads:
    output/latest.json
    output/base_params.json
    output/chip_history.json
    output/multipliers.csv

Writes:
    output/api/current.json      — current global CHIP value
    output/api/multipliers.json  — per-country multipliers
    output/api/history.json      — full time series
"""

import csv
import json
import sys
from datetime import date
from pathlib import Path

ESTIMATES_DIR = Path(__file__).parent
OUTPUT_DIR = ESTIMATES_DIR / "output"
API_DIR = OUTPUT_DIR / "api"

# Import workbench logging if available; fall back to stdlib
WORKBENCH_ROOT = ESTIMATES_DIR.parent / "workbench"
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
# PUBLISHERS
# =============================================================================

def publish_current():
    """
    Produce output/api/current.json — the primary endpoint.

    Contains the current CHIP value and metadata about how it was derived.
    Consumers (MyCHIPs, chipcentral.net, etc.) read this file.
    """
    latest_path = OUTPUT_DIR / "latest.json"
    if not latest_path.exists():
        raise FileNotFoundError(
            f"No {latest_path} found.  Run recalculate.py or extrapolate.py first."
        )

    with open(latest_path) as f:
        latest = json.load(f)

    # Read base params for additional context
    params_path = OUTPUT_DIR / "base_params.json"
    params = {}
    if params_path.exists():
        with open(params_path) as f:
            params = json.load(f)

    current = {
        "chip_usd": latest["chip_usd"],
        "effective_date": latest.get("effective_date", latest.get("date")),
        "calculated_date": latest.get("calculated_date", latest.get("date")),
        "method": latest["method"],
        "currency": "USD",
        "unit": "per hour",
        "description": "Value of one CHIP in US dollars",
        "base": {
            "chip_usd": params.get("chip_nominal"),
            "year": params.get("base_year"),
            "pwt_version": params.get("pwt_version"),
            "effective_date": params.get("effective_date",
                                         params.get("recalculation_date")),
            "n_countries": params.get("n_countries"),
            "window_years": params.get("window_years"),
        },
        "published": date.today().isoformat(),
    }

    # Add extrapolation details if applicable
    if latest.get("method") == "extrapolation":
        current["extrapolation"] = {
            "cpi_ratio": latest.get("cpi_ratio"),
            "cpi_date": latest.get("cpi_date"),
        }

    path = API_DIR / "current.json"
    with open(path, "w") as f:
        json.dump(current, f, indent=2)
    logger.info(f"Wrote {path}")
    return current


def publish_multipliers():
    """
    Produce output/api/multipliers.json — per-country CHIP multipliers.

    A multiplier of 1.0 means the country matches the global CHIP.
    >1 means workers are paid above the global CHIP; <1 means below.
    """
    csv_path = OUTPUT_DIR / "multipliers.csv"
    if not csv_path.exists():
        logger.warning(f"No {csv_path} found — skipping multipliers")
        return None

    params_path = OUTPUT_DIR / "base_params.json"
    params = {}
    if params_path.exists():
        with open(params_path) as f:
            params = json.load(f)

    # Read CSV
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "country": row["country"],
                "chip_usd": round(float(row["chip_value"]), 4),
                "multiplier": round(float(row["multiplier"]), 4),
            })

    multipliers = {
        "global_chip_usd": params.get("chip_nominal"),
        "base_year": params.get("base_year"),
        "pwt_version": params.get("pwt_version"),
        "effective_date": params.get("effective_date",
                                     params.get("recalculation_date")),
        "n_countries": len(rows),
        "countries": rows,
        "published": date.today().isoformat(),
    }

    path = API_DIR / "multipliers.json"
    with open(path, "w") as f:
        json.dump(multipliers, f, indent=2)
    logger.info(f"Wrote {path} ({len(rows)} countries)")
    return multipliers


def publish_history():
    """
    Produce output/api/history.json — full time series of CHIP values.

    Each entry is either a 'recalculation' or 'extrapolation' with
    the CHIP value and date.
    """
    history_path = OUTPUT_DIR / "chip_history.json"
    if not history_path.exists():
        logger.warning(f"No {history_path} found — skipping history")
        return None

    with open(history_path) as f:
        raw = json.load(f)

    # Simplify for the API: just the essential fields
    entries = []
    for entry in raw:
        entries.append({
            "effective_date": entry.get("effective_date", entry.get("date")),
            "calculated_date": entry.get("calculated_date", entry.get("date")),
            "chip_usd": entry["chip_usd"],
            "method": entry["method"],
        })

    history = {
        "entries": entries,
        "count": len(entries),
        "first_date": entries[0]["effective_date"] if entries else None,
        "last_date": entries[-1]["effective_date"] if entries else None,
        "published": date.today().isoformat(),
    }

    path = API_DIR / "history.json"
    with open(path, "w") as f:
        json.dump(history, f, indent=2)
    logger.info(f"Wrote {path} ({len(entries)} entries)")
    return history


# =============================================================================
# MAIN
# =============================================================================

def publish():
    """Run all publishers."""
    API_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Publishing API files")

    current = publish_current()
    logger.info(f"  current.json: CHIP = ${current['chip_usd']}")

    multipliers = publish_multipliers()
    if multipliers:
        logger.info(f"  multipliers.json: {multipliers['n_countries']} countries")

    history = publish_history()
    if history:
        logger.info(f"  history.json: {history['count']} entries")

    logger.info("Publish complete")


def main():
    global logger
    logger = setup_logging("publish", output_dir=OUTPUT_DIR)

    logger.info("CHIP Publish")
    logger.info(f"Date: {date.today().isoformat()}")

    try:
        publish()
    except Exception as e:
        logger.error(f"Publish failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

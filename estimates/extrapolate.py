#!/usr/bin/env python3
"""
CHIP Extrapolation — Monthly CPI Update

Lightweight script that applies the latest CPI-U data to the base CHIP
value produced by the last recalculation.  Produces an updated nominal
CHIP estimate and appends it to the history ledger.

Designed to run unattended (e.g., monthly cron).

Usage:
    python extrapolate.py [--notes "optional note"]

Requires:
    output/base_params.json  (produced by recalculate.py)
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
    """
    Fetch the most recent CPI-U observation from FRED.

    Returns dict with 'date' (str) and 'value' (float).
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


# =============================================================================
# EXTRAPOLATION LOGIC
# =============================================================================

def load_base_params():
    """Load base_params.json from the last recalculation."""
    path = OUTPUT_DIR / "base_params.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No base parameters found at {path}.  "
            f"Run recalculate.py first."
        )
    with open(path) as f:
        return json.load(f)


def upsert_history(entry, output_dir, replace=False):
    """
    Insert an entry into chip_history.json if not already present.

    Dedup key: (effective_date, method).  If a matching entry exists:
      - replace=False (default): skip, return False.
      - replace=True: overwrite the existing entry, return True.

    Entries are kept sorted by effective_date.
    """
    history_path = output_dir / "chip_history.json"
    if history_path.exists():
        with open(history_path) as f:
            history = json.load(f)
    else:
        history = []

    key = (entry.get("effective_date"), entry.get("method"))

    existing_idx = None
    for i, h in enumerate(history):
        if (h.get("effective_date"), h.get("method")) == key:
            existing_idx = i
            break

    if existing_idx is not None:
        if not replace:
            logger.info(
                f"Entry already exists for {key[1]} on {key[0]} — skipping. "
                f"Use --replace to overwrite."
            )
            return False
        logger.info(f"Replacing existing entry for {key[1]} on {key[0]}")
        history[existing_idx] = entry
    else:
        history.append(entry)

    history.sort(key=lambda h: h.get("effective_date", ""))

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2, default=str)

    action = "Replaced" if existing_idx is not None else "Added"
    logger.info(f"{action} entry in {history_path} (now {len(history)} entries)")
    return True


def _last_extrapolation_cpi_date():
    """
    Return the cpi_date from the most recent extrapolation entry in
    chip_history.json, or None if no extrapolation entries exist.
    """
    history_path = OUTPUT_DIR / "chip_history.json"
    if not history_path.exists():
        return None
    try:
        with open(history_path) as f:
            history = json.load(f)
        for entry in reversed(history):
            if entry.get("method") == "extrapolation":
                return entry.get("cpi_date")
    except Exception:
        pass
    return None


def extrapolate(effective_date=None, replace=False, notes=""):
    """
    Compute current nominal CHIP via CPI extrapolation.

    Formula:
        CHIP_now = CHIP_base × (CPI_now / CPI_base)

    where CHIP_base and CPI_base are from the last recalculation.

    Args:
        effective_date: The date this estimate is "for" (YYYY-MM-DD string).
                        If None, defaults to today.
        replace: If True, overwrite an existing history entry with the same
                 (effective_date, method) key.
        notes: Free-text annotation for the history entry.
    """
    eff_date = effective_date or date.today().isoformat()
    calc_date = date.today().isoformat()

    # Load base
    params = load_base_params()
    base_chip = params["chip_nominal"]
    base_cpi_value = params["cpi_reference_value"]
    base_cpi_date = params["cpi_reference_date"]
    base_eff_date = params.get("effective_date", params.get("recalculation_date"))

    logger.info(f"Base CHIP: ${base_chip:.4f} (effective {base_eff_date})")
    logger.info(f"Base CPI: {base_cpi_value:.3f} ({base_cpi_date})")

    # Fetch current CPI
    cpi_now = fetch_latest_cpi()
    logger.info(f"Current CPI: {cpi_now['value']:.3f} ({cpi_now['date']})")

    # Check if CPI has actually updated since last extrapolation
    if not replace:
        last_cpi_date = _last_extrapolation_cpi_date()
        if last_cpi_date and cpi_now["date"] == last_cpi_date:
            logger.info(
                f"No new CPI data (still {cpi_now['date']}). "
                f"Nothing to do. Use --replace to force."
            )
            return None

    # Extrapolate
    cpi_ratio = cpi_now["value"] / base_cpi_value
    chip_now = base_chip * cpi_ratio

    logger.info(f"CPI ratio: {cpi_ratio:.6f}")
    logger.info(f"Extrapolated CHIP: ${chip_now:.4f}")

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Append to history
    history_entry = {
        "effective_date": eff_date,
        "calculated_date": calc_date,
        "method": "extrapolation",
        "chip_usd": round(chip_now, 4),
        "base_chip": round(base_chip, 4),
        "base_effective_date": base_eff_date,
        "cpi_ratio": round(cpi_ratio, 6),
        "cpi_date": cpi_now["date"],
        "cpi_value": round(cpi_now["value"], 3),
        "notes": notes or "Monthly CPI extrapolation",
    }

    inserted = upsert_history(history_entry, OUTPUT_DIR, replace=replace)

    if not inserted:
        logger.info("History entry skipped (duplicate). "
                     "latest.json still updated.")

    # Overwrite latest.json
    latest = {
        "chip_usd": round(chip_now, 4),
        "effective_date": eff_date,
        "calculated_date": calc_date,
        "method": "extrapolation",
        "base_chip": round(base_chip, 4),
        "base_effective_date": base_eff_date,
        "cpi_ratio": round(cpi_ratio, 6),
        "cpi_date": cpi_now["date"],
        "next_recalculation": "When new ILOSTAT/PWT data is available",
    }
    latest_path = OUTPUT_DIR / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(latest, f, indent=2, default=str)
    logger.info(f"Wrote {latest_path}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("EXTRAPOLATION COMPLETE")
    logger.info(f"  CHIP: ${chip_now:.4f}/hr")
    logger.info(f"  CPI: {cpi_now['value']:.3f} ({cpi_now['date']})")
    logger.info(f"  Ratio vs base: {cpi_ratio:.6f}")
    logger.info("=" * 60)

    return {
        "chip_usd": chip_now,
        "cpi_ratio": cpi_ratio,
        "cpi_date": cpi_now["date"],
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="CHIP Monthly CPI Extrapolation"
    )
    parser.add_argument(
        "--effective-date", type=str, default=None,
        help="Effective date for this estimate (YYYY-MM-DD). "
             "Defaults to today."
    )
    parser.add_argument(
        "--replace", action="store_true",
        help="Overwrite an existing history entry with the same "
             "effective date. Without this flag, duplicates are skipped."
    )
    parser.add_argument(
        "--notes", type=str, default="",
        help="Notes to include in the history entry"
    )
    args = parser.parse_args()

    global logger
    logger = setup_logging("extrapolate", output_dir=OUTPUT_DIR)

    logger.info("CHIP CPI Extrapolation")
    logger.info(f"Date: {date.today().isoformat()}")

    try:
        result = extrapolate(
            effective_date=args.effective_date,
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

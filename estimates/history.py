#!/usr/bin/env python3
"""
CHIP History Viewer

Human-readable summary of chip_estimates.json.

Usage:
    python history.py                  # Global CHIP table
    python history.py --country CHE    # Switzerland's multiplier over time
    python history.py --country all    # All countries for latest year
    python history.py --csv            # Machine-readable output
"""

import argparse
import json
import sys
from pathlib import Path

ESTIMATES_FILE = Path(__file__).parent / "output" / "chip_estimates.json"


def load_estimates():
    if not ESTIMATES_FILE.exists():
        print(f"No estimates file at {ESTIMATES_FILE}", file=sys.stderr)
        print("Run recalculate.py first.", file=sys.stderr)
        sys.exit(1)
    with open(ESTIMATES_FILE) as f:
        return json.load(f)


def show_global(estimates, csv_mode=False):
    """Display the global CHIP summary table."""
    if csv_mode:
        print("effective_date,base_year,chip_usd,chip_constant,n_countries,n_multipliers")
        for e in estimates:
            n_mult = len(e.get("multipliers", []))
            print(f"{e['effective_date']},{e['base_year']},"
                  f"{e['chip_usd']},{e['chip_constant']},"
                  f"{e['n_countries']},{n_mult}")
        return

    header = (f"{'Date':>12}  {'Year':>4}  {'CHIP $':>8}  "
              f"{'Const $':>8}  {'Countries':>9}  {'Chg':>7}")
    print(header)
    print("-" * len(header))

    prev = None
    for e in estimates:
        chip = e["chip_usd"]
        if prev is not None:
            pct = (chip - prev) / prev * 100
            chg = f"{pct:+6.1f}%"
        else:
            chg = "     —"
        print(f"{e['effective_date']:>12}  {e['base_year']:>4}  "
              f"${chip:>7.4f}  ${e['chip_constant']:>7.4f}  "
              f"{e['n_countries']:>9}  {chg}")
        prev = chip

    print()
    latest = estimates[-1]
    print(f"Latest: ${latest['chip_usd']:.4f}/hr nominal "
          f"({latest['base_year']}), "
          f"{latest['n_countries']} countries")


def show_country(estimates, country_code, csv_mode=False):
    """Display a single country's multiplier history."""
    code = country_code.upper()

    if csv_mode:
        print("effective_date,base_year,country,chip_usd,multiplier")

    header_printed = False
    found_any = False

    for e in estimates:
        mults = e.get("multipliers", [])
        match = next((m for m in mults if m["country"].upper() == code), None)
        if match is None:
            continue
        found_any = True

        if csv_mode:
            print(f"{e['effective_date']},{e['base_year']},"
                  f"{match['country']},{match['chip_usd']},"
                  f"{match['multiplier']}")
        else:
            if not header_printed:
                hdr = (f"{'Date':>12}  {'Year':>4}  "
                       f"{'CHIP $':>8}  {'Mult':>6}  {'Global $':>8}")
                print(f"Country: {code}")
                print(hdr)
                print("-" * len(hdr))
                header_printed = True
            print(f"{e['effective_date']:>12}  {e['base_year']:>4}  "
                  f"${match['chip_usd']:>7.4f}  "
                  f"{match['multiplier']:>5.2f}x  "
                  f"${e['chip_usd']:>7.4f}")

    if not found_any:
        print(f"Country '{code}' not found in any estimate.", file=sys.stderr)
        print("Use --country all to see available codes.", file=sys.stderr)
        sys.exit(1)


def show_all_countries(estimates, csv_mode=False):
    """Display all country multipliers for the latest estimate."""
    latest = estimates[-1]
    mults = latest.get("multipliers", [])

    if csv_mode:
        print("country,chip_usd,multiplier")
        for m in mults:
            print(f"{m['country']},{m['chip_usd']},{m['multiplier']}")
        return

    print(f"Country multipliers — {latest['effective_date']} "
          f"(base year {latest['base_year']}, "
          f"global ${latest['chip_usd']:.4f})")
    print()

    header = f"{'#':>3}  {'Country':>8}  {'CHIP $':>8}  {'Multiplier':>10}"
    print(header)
    print("-" * len(header))
    for i, m in enumerate(mults, 1):
        print(f"{i:>3}  {m['country']:>8}  "
              f"${m['chip_usd']:>7.4f}  "
              f"{m['multiplier']:>9.4f}x")

    print()
    print(f"{len(mults)} countries")


def main():
    parser = argparse.ArgumentParser(
        description="View CHIP estimate history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python history.py                  # Global summary\n"
            "  python history.py --country USA    # US multiplier over time\n"
            "  python history.py --country all    # All countries (latest)\n"
            "  python history.py --csv            # CSV output\n"
        ),
    )
    parser.add_argument(
        "--country", type=str, default=None,
        help="Show multiplier history for a country code, or 'all' for "
             "the full table from the latest estimate"
    )
    parser.add_argument(
        "--csv", action="store_true",
        help="Output in CSV format"
    )
    args = parser.parse_args()

    estimates = load_estimates()

    if args.country is None:
        show_global(estimates, csv_mode=args.csv)
    elif args.country.lower() == "all":
        show_all_countries(estimates, csv_mode=args.csv)
    else:
        show_country(estimates, args.country, csv_mode=args.csv)


if __name__ == "__main__":
    main()

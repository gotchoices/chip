#!/usr/bin/env python3
"""
Test Nominal vs Deflated CHIP Computation

Purpose:
    Compare CHIP values computed with and without deflation.
    Tests hypothesis from inflation-tracking.md that nominal CHIP
    naturally tracks currency inflation.

Methodology:
    1. Compute CHIP using original deflator-based approach
    2. Compute CHIP without deflation (nominal)
    3. Compare results across time periods
    
Outputs:
    - Side-by-side comparison table
    - Time series of both measures
    - Analysis of divergence

Usage:
    python scripts/test_nominal_chip.py [--years 2010-2020]
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import fetcher, normalize, clean, models, aggregate, output
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Compare nominal vs deflated CHIP values."""
    
    print("=" * 60)
    print("Nominal vs Deflated CHIP Comparison")
    print("=" * 60)
    print()
    
    # Fetch data
    print("Fetching data...")
    data = fetcher.get_all()
    
    # Prepare datasets
    print("Preparing data...")
    employment = normalize.normalize_ilostat(data["employment"], "employment")
    wages = normalize.normalize_ilostat(data["wages"], "wage")
    pwt = normalize.normalize_pwt(data["pwt"])
    deflator = normalize.normalize_deflator(data["deflator"])
    
    # Clean and filter
    employment = clean.harmonize_countries(employment)
    wages = clean.harmonize_countries(wages)
    employment = clean.exclude_countries(employment)
    wages = clean.exclude_countries(wages)
    
    # Filter to unskilled
    wages_unskilled = clean.filter_unskilled(wages)
    
    # TODO: Merge datasets and compute CHIP
    # This is a stub - needs full implementation
    
    print("\n## Test Results")
    print("-" * 40)
    print("(Implementation pending - this is a scaffold)")
    print()
    print("Expected output:")
    print("| Year | Deflated CHIP | Nominal CHIP | Difference |")
    print("|------|---------------|--------------|------------|")
    print("| 2010 | $X.XX         | $X.XX        | +X%        |")
    print("| ...  | ...           | ...          | ...        |")
    
    print("\n" + "=" * 60)
    print("Test complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()

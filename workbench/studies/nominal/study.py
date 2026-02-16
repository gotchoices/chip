#!/usr/bin/env python3
"""
Nominal vs Deflated CHIP Comparison

Formal test of H1: does nominal CHIP track currency inflation?
See README.md for research question, hypothesis, and methodology.
"""

import sys
from pathlib import Path

# Study and workbench paths
STUDY_DIR = Path(__file__).parent
WORKBENCH_ROOT = STUDY_DIR.parent.parent
sys.path.insert(0, str(WORKBENCH_ROOT))

from lib import fetcher, normalize, clean, models, aggregate, output
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Output directory for this study
OUTPUT_DIR = STUDY_DIR / "output"


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

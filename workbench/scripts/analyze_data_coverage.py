#!/usr/bin/env python3
"""
Analyze Data Coverage

Purpose:
    Examine which countries have consistent data across which time periods.
    Identify data quality issues and gaps.
    
Outputs:
    - Country coverage summary (years available, completeness)
    - Data quality flags
    - Recommendations for country exclusions

Usage:
    python scripts/analyze_data_coverage.py [--output reports/coverage.md]
"""

import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import fetcher, normalize, clean, output
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Analyze data coverage across sources."""
    
    print("=" * 60)
    print("CHIP Data Coverage Analysis")
    print("=" * 60)
    print()
    
    # Fetch data
    print("Fetching data...")
    data = fetcher.get_all()
    
    # Analyze ILOSTAT employment coverage
    print("\n## Employment Data Coverage")
    print("-" * 40)
    emp = normalize.normalize_ilostat(data["employment"], "employment")
    emp_coverage = clean.get_country_coverage(emp)
    print(f"Countries with data: {len(emp_coverage)}")
    print(f"Year range: {emp_coverage['year_min'].min()} - {emp_coverage['year_max'].max()}")
    print("\nTop 10 by coverage:")
    print(emp_coverage.head(10).to_string(index=False))
    
    # Analyze wage coverage
    print("\n## Wage Data Coverage")
    print("-" * 40)
    wages = normalize.normalize_ilostat(data["wages"], "wage")
    wage_coverage = clean.get_country_coverage(wages)
    print(f"Countries with data: {len(wage_coverage)}")
    print(f"Year range: {wage_coverage['year_min'].min()} - {wage_coverage['year_max'].max()}")
    
    # Analyze PWT coverage
    print("\n## Penn World Tables Coverage")
    print("-" * 40)
    pwt = normalize.normalize_pwt(data["pwt"])
    pwt_coverage = clean.get_country_coverage(pwt, country_col="country")
    print(f"Countries with data: {len(pwt_coverage)}")
    print(f"Year range: {pwt_coverage['year_min'].min()} - {pwt_coverage['year_max'].max()}")
    
    # Find countries with complete data in all sources
    print("\n## Countries with Complete Data")
    print("-" * 40)
    
    # Get sets of countries
    emp_countries = set(emp_coverage["country"].unique()) if "country" in emp_coverage.columns else set()
    wage_countries = set(wage_coverage["country"].unique()) if "country" in wage_coverage.columns else set()
    pwt_countries = set(pwt_coverage["country"].unique()) if "country" in pwt_coverage.columns else set()
    
    if emp_countries and wage_countries and pwt_countries:
        complete = emp_countries & wage_countries & pwt_countries
        print(f"Countries in all three sources: {len(complete)}")
        print("\nSample countries:")
        for c in sorted(list(complete))[:20]:
            print(f"  - {c}")
    else:
        print("Unable to compare - different country identifier formats")
    
    # Identify quality issues
    print("\n## Data Quality Flags")
    print("-" * 40)
    
    # Countries with very few years
    sparse = emp_coverage[emp_coverage["n_years"] < 3]
    if len(sparse) > 0:
        print(f"\nCountries with < 3 years of employment data: {len(sparse)}")
        print(sparse["country"].tolist()[:10])
    
    # Save detailed report
    print("\n" + "=" * 60)
    print("Analysis complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()

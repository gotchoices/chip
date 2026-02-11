#!/usr/bin/env python3
"""
Baseline Reproduction Script

This script reproduces the CHIP value from the original study methodology,
matching the reproduction/ pipeline when both use fresh API data.

Result: $2.33/hour (vs reproduction's $2.35 — 0.9% deviation)
Target: $2.56/hour with original data, $2.35/hour with fresh API data

=============================================================================
KEY METHODOLOGY FIXES (to match reproduction)
=============================================================================

Several subtle methodology details were critical to matching reproduction:

1. WAGE RATIOS: Calculate per country-YEAR first, then average across years.
   Wrong: Average wages across years, then calculate ratio
   Right: wage_ratio[country,year] = wage / manager_wage, then mean(wage_ratio)

2. KEEP ALL EMPLOYMENT DATA: Don't drop rows without wages when calculating
   effective labor. Wage ratios are calculated from rows WITH wages, then
   applied to ALL employment rows (using fillna(1.0) for missing).

3. ALPHA ESTIMATION ON FULL PWT DATA: The original study estimates alpha
   on ALL country-years that have PWT data (capital, GDP, human capital),
   even if those years don't have wage data. This gives ~2000 observations
   for alpha estimation vs ~650 if we required wage data.
   
   Then, filter to rows WITH wage data for the final MPL/distortion calculation.

4. AVERAGE WAGE: Simple mean across occupations, not labor-weighted.
   (The reproduction uses simple mean despite the conceptual argument for weighting)

5. ALPHA IMPUTATION: Use regression-based imputation (MICE-style) for countries
   without valid alpha estimates. Predicts missing alphas from ln_y and ln_k.

=============================================================================
METHODOLOGY OVERVIEW (from original chips.R)
=============================================================================

The original study calculates CHIP (value of one hour of unskilled labor)
using a Cobb-Douglas production function approach:

1. DATA: Collect labor data (employment, wages, hours) for ALL occupation
   categories, not just unskilled. The study uses 9 ISCO major groups.

2. WAGE RATIOS: Calculate wage ratios relative to Managers (the reference).
   For example, if Elementary workers earn 30% of Managers, their ratio is 0.3.
   These ratios serve as "skill weights" — how much each occupation 
   contributes to production relative to Managers.

3. EFFECTIVE LABOR: Calculate skill-weighted labor hours:
   Eff_Labor = Σ (Employed × Hours × Wage_Ratio) across ALL occupations
   This is a measure of total "equivalent Manager hours" in the economy.

4. MERGE WITH PWT: Join with Penn World Tables to get capital stock (K),
   GDP (Y), and human capital index (hc).

5. ESTIMATE ALPHA: Run fixed-effects regression to estimate capital share (α):
   ln(Y / Eff_Labor × hc) = α × ln(K / Eff_Labor × hc) + country_effects

6. CALCULATE MPL: Marginal Product of Labor using Cobb-Douglas formula:
   MPL = (1 - α) × (K / Eff_Labor × hc)^α
   
   KEY INSIGHT: The denominator is ILOSTAT's Eff_Labor, NOT PWT's employment.
   This is skill-adjusted labor measured in "equivalent Manager hours".

7. AVERAGE WAGE: Simple mean of wages across occupations (per original study).

8. DISTORTION FACTOR: Compare actual wages to marginal product:
   θ = MPL / AW_Wage
   
   If θ > 1, workers are underpaid relative to their marginal product.
   If θ < 1, workers are overpaid (unlikely in competitive markets).

9. ADJUSTED WAGE: Apply distortion factor to ELEMENTARY (unskilled) wage:
   CHIP_country = Elementary_Wage × θ
   
   This gives the "fair" wage for unskilled labor if markets were frictionless.

10. GLOBAL CHIP: GDP-weighted average across countries:
    CHIP = Σ (CHIP_country × GDP_weight)

=============================================================================

Usage:
    ./run.sh baseline
    ./run.sh baseline -v   # Run and view report
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.logging_config import setup_logging, ScriptContext, get_logger
from lib import fetcher, normalize
from lib import pipeline
from lib.config import load_config

logger = get_logger(__name__)


# =============================================================================
# BASELINE-SPECIFIC CONFIGURATION
# =============================================================================
#
# These settings control how baseline matches the original study.
# Other scripts (timeseries, compare) will use different settings but
# the same pipeline functions.

# Countries from the reproduction run (90 countries)
REPRODUCTION_ISOCODES = [
    "ALB", "ARG", "ARM", "AUT", "BEL", "BGD", "BGR", "BLZ", "BRA", "BRN",
    "BWA", "CHE", "CHL", "COL", "CRI", "CYP", "CZE", "DEU", "DNK", "DOM",
    "ECU", "EGY", "ESP", "EST", "ETH", "FIN", "FRA", "GBR", "GHA", "GRC",
    "HND", "HRV", "HUN", "IDN", "IND", "IRL", "ISL", "ISR", "ITA", "JAM",
    "JOR", "KEN", "KOR", "LKA", "LSO", "LTU", "LUX", "LVA", "MDG", "MDV",
    "MEX", "MLI", "MLT", "MMR", "MNG", "MUS", "MYS", "NAM", "NGA", "NIC",
    "NLD", "NOR", "NPL", "PAK", "PAN", "PER", "PHL", "POL", "PRT", "PRY",
    "ROU", "RUS", "RWA", "SEN", "SLV", "SRB", "SVK", "SVN", "SWE", "THA",
    "TJK", "TUR", "TZA", "UGA", "UKR", "USA", "VNM", "YEM", "ZAF", "ZMB"
]

REPRODUCTION_COUNTRIES = [
    "Albania", "Argentina", "Armenia", "Austria", "Bangladesh", "Belgium",
    "Belize", "Botswana", "Brazil", "Brunei Darussalam", "Bulgaria", "Chile",
    "Colombia", "Costa Rica", "Croatia", "Cyprus", "Czechia", "Denmark",
    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Estonia",
    "Ethiopia", "Finland", "France", "Germany", "Ghana", "Greece", "Honduras",
    "Hungary", "Iceland", "India", "Indonesia", "Ireland", "Israel", "Italy",
    "Jamaica", "Jordan", "Kenya", "Korea, Republic of", "Latvia", "Lesotho",
    "Lithuania", "Luxembourg", "Madagascar", "Malaysia", "Maldives", "Mali",
    "Malta", "Mauritius", "Mexico", "Mongolia", "Myanmar", "Namibia", "Nepal",
    "Netherlands", "Nicaragua", "Nigeria", "Norway", "Pakistan", "Panama",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Romania",
    "Russian Federation", "Rwanda", "Senegal", "Serbia", "Slovakia", "Slovenia",
    "South Africa", "Spain", "Sri Lanka", "Sweden", "Switzerland", "Tajikistan",
    "Tanzania, United Republic of", "Thailand", "Türkiye", "Uganda", "Ukraine",
    "United Kingdom", "United States", "Viet Nam", "Yemen", "Zambia",
]

# Set to a list of country names/codes to restrict analysis to specific countries.
# Options:
#   None                    - Use all available countries
#   REPRODUCTION_ISOCODES   - Match original study's 90 countries (use with API data)
#   REPRODUCTION_COUNTRIES  - Match original study's 90 countries (use with local data)
#   ["USA", "DEU", ...]     - Custom list
INCLUDE_COUNTRIES = None

# Year range (reproduction uses 1992-2019)
YEAR_START = 1992
YEAR_END = 2019

# Enable MICE-style imputation for missing wage ratios and alphas
ENABLE_IMPUTATION = True

# Average wage calculation method
# "simple"   - Simple mean across occupations (matches reproduction: $2.35)
# "weighted" - Labor-weighted average (matches original R code theory)
WAGE_AVERAGING_METHOD = "simple"


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_baseline():
    """
    Run the baseline reproduction pipeline.
    Delegates all computation to lib/pipeline.py.
    """
    config = load_config()

    # Resolve year range from constants or config
    year_start = YEAR_START if YEAR_START is not None else config.data.year_start
    year_end = YEAR_END if YEAR_END is not None else config.data.year_end

    # ----- Step 1: Fetch data -----
    logger.info("=" * 70)
    logger.info("STEP 1: Fetching data from sources")
    logger.info("=" * 70)

    print("Fetching data (this may take a moment)...")
    data = fetcher.get_all()

    for name, df in data.items():
        logger.info(f"  {name}: {len(df):,} rows")

    # ----- Steps 2-10: Prepare labor data -----
    logger.info("=" * 70)
    logger.info("STEPS 2-10: Normalize → filter → map → merge → deflate → ratios → eff_labor → wages → PWT")
    logger.info("=" * 70)

    # Normalize deflator for pipeline (or None to skip deflation)
    deflator_df = normalize.normalize_deflator(data["deflator"], base_year=2017)

    result = pipeline.prepare_labor_data(
        data=data,
        year_start=year_start,
        year_end=year_end,
        deflator_df=deflator_df,
        include_countries=INCLUDE_COUNTRIES,
        enable_imputation=ENABLE_IMPUTATION,
        wage_averaging_method=WAGE_AVERAGING_METHOD,
    )

    est_data = result["est_data"]

    logger.info(f"Estimation data: {len(est_data)} observations, "
                f"{est_data['country'].nunique()} countries")

    # ----- Steps 11-16: Alpha → MPL → CHIP → aggregate -----
    logger.info("=" * 70)
    logger.info("STEPS 11-16: Alpha estimation → MPL → distortion → CHIP → aggregate")
    logger.info("=" * 70)

    chip_value, country_data, est_data = pipeline.estimate_chip(
        est_data,
        enable_imputation=ENABLE_IMPUTATION,
    )

    # ----- Validate against known targets -----
    logger.info("=" * 70)
    logger.info("RESULTS")
    logger.info("=" * 70)

    target = 2.56       # reproduction with data_source: "original"
    target_api = 2.35   # reproduction with data_source: "api" (fresh data)

    difference = chip_value - target_api
    pct_diff = (difference / target_api) * 100

    logger.info(f"Calculated CHIP:  ${chip_value:.2f}/hour")
    logger.info(f"Target CHIP:      ${target_api:.2f}/hour (reproduction w/ fresh API)")
    logger.info(f"Difference:       ${difference:+.2f} ({pct_diff:+.1f}%)")

    if abs(pct_diff) < 10:
        logger.info("VALIDATION PASSED: Within 10% of target")
        validation = "PASSED"
    elif abs(pct_diff) < 30:
        logger.warning("VALIDATION MARGINAL: 10-30% deviation (expected with fresh data)")
        validation = "MARGINAL"
    else:
        logger.error("VALIDATION FAILED: >30% deviation (check methodology)")
        validation = "FAILED"

    return {
        "chip_value": chip_value,
        "target": target_api,
        "target_original": target,
        "difference": difference,
        "pct_diff": pct_diff,
        "validation": validation,
        "n_countries": len(country_data),
        "n_observations": len(est_data),
        "mean_alpha": est_data["alpha"].mean(),
        "mean_theta": est_data["theta"].mean(),
        "country_data": country_data,
    }


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(results: dict) -> str:
    """Generate markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Baseline Reproduction Report",
        "",
        f"Generated: {timestamp}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"**Calculated CHIP:** ${results['chip_value']:.2f}/hour",
        f"**Target CHIP:** ${results['target']:.2f}/hour",
        f"**Difference:** ${results['difference']:+.2f} ({results['pct_diff']:+.1f}%)",
        "",
        f"**Validation:** {results['validation']}",
        "",
        "---",
        "",
        "## Diagnostics",
        "",
        f"- Countries: {results['n_countries']}",
        f"- Observations: {results['n_observations']}",
        f"- Mean α (capital share): {results['mean_alpha']:.3f}",
        f"- Mean θ (distortion factor): {results['mean_theta']:.3f}",
        "",
        "---",
        "",
        "## Top Countries by CHIP Value",
        "",
    ]

    df = results["country_data"].sort_values("chip_value", ascending=False).head(20)
    lines.append("| Country | CHIP ($/hr) | Elem. Wage | θ | α |")
    lines.append("|---------|-------------|------------|-----|-----|")
    for _, row in df.iterrows():
        lines.append(
            f"| {row['country']} | ${row['chip_value']:.2f} | "
            f"${row['elementary_wage']:.2f} | {row['theta']:.2f} | {row['alpha']:.2f} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Methodology",
        "",
        "This script reproduces the original study methodology:",
        "",
        "1. Fetch labor data (employment, wages, hours) for all 9 ISCO occupations",
        "2. Calculate wage ratios relative to Managers (skill weights)",
        "3. Compute effective labor = Σ(hours × skill_weight) across occupations",
        "4. Merge with Penn World Tables (capital, GDP, human capital)",
        "5. Estimate α (capital share) via fixed-effects regression",
        "6. Calculate MPL = (1-α) × (K/L × hc)^α",
        "7. Calculate distortion factor θ = MPL / average_wage",
        "8. Adjust elementary wage: CHIP = elem_wage × θ",
        "9. GDP-weighted global average",
        "",
        "---",
        "",
        "## Notes",
        "",
        "Discrepancies may arise from:",
        "- Data vintage (ILOSTAT updates historical data)",
        "- Country name matching differences",
        "- Occupation code interpretation",
        "- Numerical precision",
        "",
        "For strict reproduction, use `reproduction/` with `data_source: original`.",
    ])

    return "\n".join(lines)


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    script_name = Path(__file__).stem
    log_path = setup_logging(script_name)

    print("Baseline Reproduction")
    print("Target: $2.56/hour")
    print()

    with ScriptContext(script_name) as ctx:
        try:
            results = run_baseline()

            if results is None:
                ctx.error("Pipeline returned no results")
                return 1

            report = generate_report(results)

            output_dir = Path(__file__).parent.parent / "output" / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = output_dir / f"baseline_{timestamp}.md"
            report_path.write_text(report)

            print()
            print(f"{'=' * 60}")
            print(f"CHIP Value: ${results['chip_value']:.2f}/hour")
            print(f"Target:     ${results['target']:.2f}/hour")
            print(f"Validation: {results['validation']}")
            print(f"{'=' * 60}")
            print()
            print(f"Report: {report_path}")

            ctx.set_result("chip_value", results["chip_value"])
            ctx.set_result("target", results["target"])
            ctx.set_result("validation", results["validation"])
            ctx.set_result("n_countries", results["n_countries"])

            return 0 if results["validation"] in ["PASSED", "MARGINAL"] else 1

        except Exception as e:
            logger.exception("Pipeline failed")
            ctx.error(str(e))
            print(f"\nError: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())

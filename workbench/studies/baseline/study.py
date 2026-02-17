#!/usr/bin/env python3
"""
Baseline Reproduction Script

Reproduces the original CHIP estimate using the Cobb-Douglas methodology.
See README.md for research question, hypothesis, and methodology overview.

=============================================================================
IMPLEMENTATION NOTES
=============================================================================

Several subtle details were critical to matching the reproduction/ pipeline:

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
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

# Study and workbench paths
STUDY_DIR = Path(__file__).parent
WORKBENCH_ROOT = STUDY_DIR.parent.parent
sys.path.insert(0, str(WORKBENCH_ROOT))

from lib.logging_config import setup_logging, ScriptContext, get_logger
from lib import fetcher, normalize
from lib import pipeline
from lib.config import load_config

logger = get_logger(__name__)

# Output directory for this study
OUTPUT_DIR = STUDY_DIR / "output"


# =============================================================================
# BASELINE-SPECIFIC CONFIGURATION
# =============================================================================
#
# These settings control how baseline matches the original study.
# Other studies (timeseries, weighting) will use different settings but
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
    config = load_config(study_dir=STUDY_DIR)

    # Resolve year range from constants or config
    year_start = YEAR_START if YEAR_START is not None else config.data.year_start
    year_end = YEAR_END if YEAR_END is not None else config.data.year_end

    # ----- Step 1: Fetch data -----
    logger.info("=" * 70)
    logger.info("STEP 1: Fetching data from sources")
    logger.info("=" * 70)

    logger.info("Fetching data (this may take a moment)...")
    data = fetcher.get_all(pwt_version=config.data.pwt_version)

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
    global logger
    script_name = Path(__file__).parent.name
    output_dir = OUTPUT_DIR
    logger = setup_logging(script_name, output_dir=output_dir)

    logger.info("Baseline Reproduction — Target: $2.56/hour")

    with ScriptContext(script_name, output_dir=output_dir) as ctx:
        try:
            results = run_baseline()

            if results is None:
                ctx.error("Pipeline returned no results")
                return 1

            report = generate_report(results)

            reports_dir = output_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"baseline_{timestamp}.md"
            report_path.write_text(report)

            logger.info("=" * 60)
            logger.info(f"CHIP Value: ${results['chip_value']:.2f}/hour")
            logger.info(f"Target:     ${results['target']:.2f}/hour")
            logger.info(f"Validation: {results['validation']}")
            logger.info("=" * 60)
            logger.info(f"Report: {report_path}")

            ctx.set_result("chip_value", results["chip_value"])
            ctx.set_result("target", results["target"])
            ctx.set_result("validation", results["validation"])
            ctx.set_result("n_countries", results["n_countries"])

            return 0 if results["validation"] in ["PASSED", "MARGINAL"] else 1

        except Exception as e:
            logger.exception("Pipeline failed")
            ctx.error(str(e))
            return 1


if __name__ == "__main__":
    sys.exit(main())

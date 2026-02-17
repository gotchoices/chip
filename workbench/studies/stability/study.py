#!/usr/bin/env python3
"""
Vintage Stability Study

Compares CHIP estimates computed with PWT 10.0 vs PWT 11.0 for the
overlapping period (2000–2019) to quantify how much a PWT revision
changes historical CHIP values.

See README.md for research question, hypothesis, and methodology.
"""

import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

STUDY_DIR = Path(__file__).parent
WORKBENCH_ROOT = STUDY_DIR.parent.parent
sys.path.insert(0, str(WORKBENCH_ROOT))

from lib.logging_config import setup_logging, ScriptContext, get_logger
from lib import fetcher, normalize, pipeline

logger = get_logger(__name__)

OUTPUT_DIR = STUDY_DIR / "output"


# =============================================================================
# CONFIGURATION
# =============================================================================

YEAR_START = 2000
YEAR_END = 2019          # Last year in PWT 10.0
SERIES_MIN_COUNTRIES = 5
ENABLE_IMPUTATION = True
WAGE_AVERAGING_METHOD = "simple"


# =============================================================================
# PIPELINE
# =============================================================================

def run_chip_for_version(pwt_version):
    """
    Run the full CHIP pipeline for a given PWT version.

    Returns per-year GDP-weighted CHIP series and per-country-year est_data.
    """
    logger.info(f"Running pipeline with PWT {pwt_version}")

    data = fetcher.get_all(pwt_version=pwt_version)
    deflator_df = normalize.normalize_deflator(data["deflator"])

    result = pipeline.prepare_labor_data(
        data=data,
        year_start=YEAR_START,
        year_end=YEAR_END,
        deflator_df=deflator_df,
        include_countries=None,
        enable_imputation=ENABLE_IMPUTATION,
        wage_averaging_method=WAGE_AVERAGING_METHOD,
    )
    _, _, est_data = pipeline.estimate_chip(
        result["est_data"],
        enable_imputation=ENABLE_IMPUTATION,
    )

    logger.info(f"  PWT {pwt_version}: {len(est_data)} obs, "
                f"{est_data['country'].nunique()} countries")

    # Aggregate to per-year GDP-weighted CHIP
    rows = []
    for year, ydf in est_data.groupby("year"):
        if len(ydf) < SERIES_MIN_COUNTRIES:
            continue
        total_gdp = ydf["rgdpna"].sum()
        if total_gdp > 0:
            w = ydf["rgdpna"] / total_gdp
            chip = (ydf["chip_value"] * w).sum()
        else:
            chip = ydf["chip_value"].mean()
        rows.append({
            "year": int(year),
            "chip_value": chip,
            "n_countries": len(ydf),
        })

    ts = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    ts["pwt_version"] = pwt_version

    logger.info(f"  Series: {len(ts)} years, "
                f"mean CHIP ${ts['chip_value'].mean():.2f}")

    return ts, est_data


def compare_vintages(ts_10, ts_11):
    """
    Compare per-year CHIP values between two PWT vintages.

    Returns a comparison DataFrame with per-year differences.
    """
    comp = ts_10[["year", "chip_value", "n_countries"]].merge(
        ts_11[["year", "chip_value", "n_countries"]],
        on="year",
        suffixes=("_10", "_11"),
    )

    comp["abs_diff"] = comp["chip_value_11"] - comp["chip_value_10"]
    comp["pct_diff"] = (comp["abs_diff"] / comp["chip_value_10"]) * 100

    return comp


def compare_countries(est_10, est_11):
    """
    Compare country-level CHIP values across vintages.

    Aggregates to country mean over overlapping years, then computes
    per-country differences.
    """
    # Find overlapping years
    years_10 = set(est_10["year"].unique())
    years_11 = set(est_11["year"].unique())
    overlap_years = years_10 & years_11

    # Aggregate to country means over overlap years
    sub_10 = est_10[est_10["year"].isin(overlap_years)]
    sub_11 = est_11[est_11["year"].isin(overlap_years)]

    mean_10 = sub_10.groupby("country")["chip_value"].mean().reset_index()
    mean_11 = sub_11.groupby("country")["chip_value"].mean().reset_index()

    mean_10.columns = ["country", "chip_10"]
    mean_11.columns = ["country", "chip_11"]

    comp = mean_10.merge(mean_11, on="country", how="inner")
    comp["abs_diff"] = comp["chip_11"] - comp["chip_10"]
    comp["pct_diff"] = (comp["abs_diff"] / comp["chip_10"]) * 100

    comp = comp.sort_values("pct_diff", ascending=False).reset_index(drop=True)

    return comp


# =============================================================================
# PLOTS
# =============================================================================

def generate_plots(comparison, country_comp, ts_10, ts_11, output_dir):
    """Generate all study plots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    plot_paths = []

    # ---- Plot 1: CHIP time series overlay ----
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(ts_10["year"], ts_10["chip_value"], "o-", color="#2196F3",
            label="PWT 10.0", linewidth=2, markersize=5)
    ax.plot(ts_11["year"], ts_11["chip_value"], "s-", color="#F44336",
            label="PWT 11.0", linewidth=2, markersize=5)
    ax.set_xlabel("Year")
    ax.set_ylabel("CHIP ($/hour, constant 2017$)")
    ax.set_title("CHIP Time Series: PWT 10.0 vs 11.0")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = plots_dir / "vintage_overlay.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    plot_paths.append(path)
    logger.info(f"  Plot 1: {path.name}")

    # ---- Plot 2: Scatter — 10.0 vs 11.0 per year ----
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(comparison["chip_value_10"], comparison["chip_value_11"],
               c="#4CAF50", s=60, edgecolors="white", zorder=3)
    # Identity line
    lims = [
        min(comparison["chip_value_10"].min(), comparison["chip_value_11"].min()) * 0.9,
        max(comparison["chip_value_10"].max(), comparison["chip_value_11"].max()) * 1.1,
    ]
    ax.plot(lims, lims, "k--", alpha=0.5, label="Identity (no change)")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("CHIP with PWT 10.0 ($/hr)")
    ax.set_ylabel("CHIP with PWT 11.0 ($/hr)")
    ax.set_title("Vintage Stability: Per-Year CHIP")
    ax.legend()
    ax.grid(alpha=0.3)

    # Annotate selected years
    for _, row in comparison.iterrows():
        yr = int(row["year"])
        if yr in [2000, 2005, 2010, 2015, 2019]:
            ax.annotate(str(yr),
                        (row["chip_value_10"], row["chip_value_11"]),
                        textcoords="offset points", xytext=(8, -5),
                        fontsize=8)

    fig.tight_layout()
    path = plots_dir / "vintage_scatter.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    plot_paths.append(path)
    logger.info(f"  Plot 2: {path.name}")

    # ---- Plot 3: Percentage difference by year ----
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#4CAF50" if d >= 0 else "#F44336" for d in comparison["pct_diff"]]
    ax.bar(comparison["year"], comparison["pct_diff"], color=colors,
           edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhline(5, color="gray", linestyle=":", alpha=0.5, label="±5% threshold")
    ax.axhline(-5, color="gray", linestyle=":", alpha=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Percentage Change (%)")
    ax.set_title("CHIP Revision: PWT 10.0 → 11.0 (% change by year)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = plots_dir / "vintage_pct_diff.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    plot_paths.append(path)
    logger.info(f"  Plot 3: {path.name}")

    # ---- Plot 4: Country-level revision distribution ----
    if len(country_comp) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(country_comp["pct_diff"], bins=30, color="#9C27B0",
                edgecolor="white", alpha=0.8)
        ax.axvline(0, color="red", linestyle="--", linewidth=2,
                   label="No change")
        mean_pct = country_comp["pct_diff"].mean()
        ax.axvline(mean_pct, color="orange", linestyle=":",
                   linewidth=1.5, label=f"Mean: {mean_pct:+.1f}%")
        ax.set_xlabel("Country-level CHIP Change (%)")
        ax.set_ylabel("Number of Countries")
        ax.set_title("Distribution of Country-Level CHIP Revisions (PWT 10.0 → 11.0)")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        path = plots_dir / "country_revision_dist.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        plot_paths.append(path)
        logger.info(f"  Plot 4: {path.name}")

    return plot_paths


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_stability():
    """Execute the vintage stability study."""

    # ------------------------------------------------------------------
    # Phase 1: Run pipeline with both PWT versions
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 1: Computing CHIP with PWT 10.0")
    logger.info("=" * 70)
    ts_10, est_10 = run_chip_for_version("10.0")

    logger.info("=" * 70)
    logger.info("PHASE 1b: Computing CHIP with PWT 11.0")
    logger.info("=" * 70)
    ts_11, est_11 = run_chip_for_version("11.0")

    # ------------------------------------------------------------------
    # Phase 2: Compare vintages
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 2: Vintage comparison")
    logger.info("=" * 70)

    comparison = compare_vintages(ts_10, ts_11)

    logger.info(f"Overlapping years: {len(comparison)}")
    logger.info(f"Mean CHIP (10.0): ${comparison['chip_value_10'].mean():.2f}")
    logger.info(f"Mean CHIP (11.0): ${comparison['chip_value_11'].mean():.2f}")
    logger.info(f"Mean revision: {comparison['pct_diff'].mean():+.1f}%")
    logger.info(f"Mean |revision|: {comparison['pct_diff'].abs().mean():.1f}%")
    logger.info(f"Max |revision|: {comparison['pct_diff'].abs().max():.1f}%")
    logger.info(f"Std of revision: {comparison['pct_diff'].std():.1f}%")

    within_3 = (comparison["pct_diff"].abs() <= 3).sum()
    within_5 = (comparison["pct_diff"].abs() <= 5).sum()
    logger.info(f"Within ±3%: {within_3}/{len(comparison)} years")
    logger.info(f"Within ±5%: {within_5}/{len(comparison)} years")

    # H1 assessment
    mean_abs_revision = comparison["pct_diff"].abs().mean()
    overall_mean_diff = abs(comparison["chip_value_11"].mean() -
                           comparison["chip_value_10"].mean()) / \
                        comparison["chip_value_10"].mean() * 100
    h1_individual = comparison["pct_diff"].abs().max() < 5
    h1_mean = overall_mean_diff < 3
    logger.info(f"\nH1 assessment:")
    logger.info(f"  Individual years < 5%? {h1_individual} (max={comparison['pct_diff'].abs().max():.1f}%)")
    logger.info(f"  Overall mean < 3%? {h1_mean} (diff={overall_mean_diff:.1f}%)")

    # ------------------------------------------------------------------
    # Phase 3: Country-level comparison
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 3: Country-level revision analysis")
    logger.info("=" * 70)

    country_comp = compare_countries(est_10, est_11)
    logger.info(f"Countries in both vintages: {len(country_comp)}")
    logger.info(f"Mean country revision: {country_comp['pct_diff'].mean():+.1f}%")
    logger.info(f"Std of country revisions: {country_comp['pct_diff'].std():.1f}%")

    logger.info("\nLargest upward revisions:")
    for _, row in country_comp.head(5).iterrows():
        logger.info(f"  {row['country']:6s}: ${row['chip_10']:.2f} → "
                     f"${row['chip_11']:.2f} ({row['pct_diff']:+.1f}%)")

    logger.info("Largest downward revisions:")
    for _, row in country_comp.tail(5).iterrows():
        logger.info(f"  {row['country']:6s}: ${row['chip_10']:.2f} → "
                     f"${row['chip_11']:.2f} ({row['pct_diff']:+.1f}%)")

    # ------------------------------------------------------------------
    # Save outputs
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("Saving outputs")
    logger.info("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_dir = OUTPUT_DIR / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    comparison.to_csv(csv_dir / "vintage_comparison.csv", index=False)
    country_comp.to_csv(csv_dir / "country_revisions.csv", index=False)
    ts_10.to_csv(csv_dir / "series_pwt10.csv", index=False)
    ts_11.to_csv(csv_dir / "series_pwt11.csv", index=False)

    logger.info(f"  Saved CSVs to {csv_dir}")

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    logger.info("Generating plots")

    plot_paths = generate_plots(comparison, country_comp, ts_10, ts_11, OUTPUT_DIR)

    return {
        "comparison": comparison,
        "country_comp": country_comp,
        "ts_10": ts_10,
        "ts_11": ts_11,
        "plot_paths": plot_paths,
    }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    global logger
    script_name = Path(__file__).parent.name
    logger = setup_logging(script_name, output_dir=OUTPUT_DIR)

    logger.info("Vintage Stability Study — PWT 10.0 vs 11.0")
    logger.info(f"Overlap period: {YEAR_START}–{YEAR_END}")

    with ScriptContext(script_name, output_dir=OUTPUT_DIR) as ctx:
        try:
            results = run_stability()

            if results is None:
                ctx.error("Pipeline returned no results")
                return 1

            comp = results["comparison"]
            cc = results["country_comp"]

            logger.info("=" * 60)
            logger.info("SUMMARY")
            logger.info("=" * 60)
            logger.info(f"  Overlapping years: {len(comp)}")
            logger.info(f"  Mean |revision|: {comp['pct_diff'].abs().mean():.1f}%")
            logger.info(f"  Max |revision|:  {comp['pct_diff'].abs().max():.1f}%")
            logger.info(f"  Countries compared: {len(cc)}")
            logger.info(f"  Plots: {len(results['plot_paths'])}")
            logger.info("=" * 60)

            ctx.set_result("n_overlap_years", len(comp))
            ctx.set_result("mean_abs_revision_pct", float(comp["pct_diff"].abs().mean()))
            ctx.set_result("max_abs_revision_pct", float(comp["pct_diff"].abs().max()))
            ctx.set_result("mean_revision_pct", float(comp["pct_diff"].mean()))
            ctx.set_result("n_countries_compared", len(cc))

            return 0

        except Exception as e:
            logger.exception("Study failed")
            ctx.error(str(e))
            return 1


if __name__ == "__main__":
    sys.exit(main())

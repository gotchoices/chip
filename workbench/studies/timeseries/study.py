#!/usr/bin/env python3
"""
Time Series Discovery Script

Builds year-by-year CHIP time series under various assumptions.
See README.md for research question, hypotheses (H1-H3), and methodology.

=============================================================================
IMPLEMENTATION NOTES
=============================================================================

Deflation cancels in the CHIP formula: both elementary_wage and average_wage
are scaled identically, so the deflator drops out of theta = MPL / avg_wage.
To produce a meaningful nominal series, we RE-INFLATE the constant-dollar
CHIP: CHIP_nominal(Y) = CHIP_constant(Y) × deflator(Y) / deflator(2017).

Configuration constants below control year range, minimum country thresholds,
stable-panel membership, and weighting method.
"""

import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# Study and workbench paths
STUDY_DIR = Path(__file__).parent
WORKBENCH_ROOT = STUDY_DIR.parent.parent
sys.path.insert(0, str(WORKBENCH_ROOT))

from lib.logging_config import setup_logging, ScriptContext, get_logger
from lib import fetcher, normalize, pipeline
from lib.config import load_config

logger = get_logger(__name__)

# Output directory for this study
OUTPUT_DIR = STUDY_DIR / "output"


# =============================================================================
# CONFIGURATION
# =============================================================================

YEAR_START = 1992
YEAR_END = 2019

# Minimum number of countries in a year to include that year in the series.
# Years with fewer countries are dropped as unreliable noise.
SERIES_MIN_COUNTRIES = 5

# Minimum fraction of included years a country must have data to be "stable panel".
# Applied AFTER trimming years below SERIES_MIN_COUNTRIES.
MIN_COVERAGE_PCT = 0.70

# Weighting method for global aggregation per year
WEIGHTING = "gdp"

# Pipeline settings (same as baseline for comparability)
ENABLE_IMPUTATION = True
WAGE_AVERAGING_METHOD = "simple"


# =============================================================================
# PER-YEAR AGGREGATION
# =============================================================================

def aggregate_by_year(est_data: pd.DataFrame,
                      weighting: str = "gdp") -> pd.DataFrame:
    """
    Aggregate CHIP to a single value per year across countries.

    Unlike the baseline (which pools years per country, then GDP-weights),
    here we weight within each year directly.

    Returns DataFrame with: year, chip_value, n_countries, chip_mean,
                            chip_median, chip_std, mean_elem_wage, mean_theta
    """
    rows = []

    for year, ydf in est_data.groupby("year"):
        if len(ydf) == 0:
            continue

        if weighting == "gdp":
            total_gdp = ydf["rgdpna"].sum()
            if total_gdp > 0:
                w = ydf["rgdpna"] / total_gdp
                chip = (ydf["chip_value"] * w).sum()
            else:
                chip = ydf["chip_value"].mean()
        elif weighting == "labor":
            total_labor = ydf["eff_labor"].sum()
            if total_labor > 0:
                w = ydf["eff_labor"] / total_labor
                chip = (ydf["chip_value"] * w).sum()
            else:
                chip = ydf["chip_value"].mean()
        elif weighting == "unweighted":
            chip = ydf["chip_value"].mean()
        else:
            raise ValueError(f"Unknown weighting: {weighting}")

        rows.append({
            "year": int(year),
            "chip_value": chip,
            "n_countries": len(ydf),
            "chip_mean": ydf["chip_value"].mean(),
            "chip_median": ydf["chip_value"].median(),
            "chip_std": ydf["chip_value"].std() if len(ydf) > 1 else 0.0,
            "mean_elem_wage": ydf["elementary_wage"].mean(),
            "mean_theta": ydf["theta"].mean(),
        })

    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def trim_sparse_years(ts: pd.DataFrame, min_countries: int) -> pd.DataFrame:
    """Drop years with fewer than min_countries contributing."""
    before = len(ts)
    ts = ts[ts["n_countries"] >= min_countries].reset_index(drop=True)
    dropped = before - len(ts)
    if dropped > 0:
        logger.info(f"Trimmed {dropped} years with < {min_countries} countries")
    return ts


def create_nominal_series(ts_constant: pd.DataFrame,
                          deflator: pd.DataFrame) -> pd.DataFrame:
    """
    Re-inflate constant-dollar CHIP to nominal dollars.

    CHIP_nominal(Y) = CHIP_constant(Y) × deflator(Y) / deflator(base_year)

    The deflator is normalized so base_year=2017 → deflator=100.
    Dividing by 100 gives the price-level ratio relative to 2017.
    """
    ts = ts_constant.copy()
    ts = ts.merge(deflator[["year", "deflator"]], on="year", how="left")

    # deflator column is percentage with 2017 = 100
    ts["chip_value"] = ts["chip_value"] * (ts["deflator"] / 100.0)

    # Clean up
    ts = ts.drop(columns=["deflator"], errors="ignore")
    return ts


def rolling_average(ts: pd.DataFrame, window: int) -> pd.DataFrame:
    """Apply rolling average to a time series DataFrame."""
    result = ts.copy()
    result["chip_value"] = (
        result["chip_value"]
        .rolling(window, center=True, min_periods=1)
        .mean()
    )
    result["window"] = window
    return result


# =============================================================================
# STABLE PANEL IDENTIFICATION
# =============================================================================

def identify_stable_panel(est_data: pd.DataFrame,
                          valid_years: set,
                          min_coverage_pct: float) -> tuple:
    """
    Identify countries with consistent data across the valid years.

    Args:
        est_data: per-country-year DataFrame
        valid_years: set of years that passed the min-countries threshold
        min_coverage_pct: fraction of valid_years a country must cover

    Returns:
        (list of stable countries, full coverage DataFrame)
    """
    n_years = len(valid_years)
    if n_years == 0:
        return [], pd.DataFrame()

    coverage = est_data.groupby("country")["year"].apply(
        lambda y: len(set(y) & valid_years)
    ).reset_index()
    coverage.columns = ["country", "n_years"]
    coverage["pct"] = coverage["n_years"] / n_years
    coverage = coverage.sort_values("pct", ascending=False).reset_index(drop=True)

    stable = coverage[coverage["pct"] >= min_coverage_pct]["country"].tolist()

    logger.info(f"Stable panel: {len(stable)} of {len(coverage)} countries "
                f"with >= {min_coverage_pct:.0%} coverage over {n_years} valid years")

    return stable, coverage


# =============================================================================
# PLOTTING
# =============================================================================

def generate_plots(series: dict, deflator: pd.DataFrame, output_dir: Path) -> list:
    """Generate discovery plots and save to output_dir/plots/."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available — skipping plots")
        return []

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    # --- Plot 1: Four-panel comparison ---
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    fig.suptitle("CHIP Time Series — Discovery Comparison", fontsize=14, fontweight="bold")

    panel_keys = [
        ("all_constant", "All Countries — Constant 2017$"),
        ("all_nominal", "All Countries — Nominal $"),
        ("panel_constant", "Stable Panel — Constant 2017$"),
        ("panel_nominal", "Stable Panel — Nominal $"),
    ]

    for ax, (key, title) in zip(axes.flat, panel_keys):
        if key in series:
            ts = series[key]
            ax.plot(ts["year"], ts["chip_value"], "o-", markersize=3,
                    linewidth=1.5, label="CHIP")

            for w in [3, 5]:
                rkey = f"{key}_r{w}"
                if rkey in series:
                    rts = series[rkey]
                    ax.plot(rts["year"], rts["chip_value"], "--", linewidth=1,
                            alpha=0.7, label=f"{w}yr avg")

            ax.set_title(title, fontsize=11)
            ax.set_ylabel("$/hour")
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8)

            n_min = int(ts["n_countries"].min())
            n_max = int(ts["n_countries"].max())
            ax.annotate(f"n={n_min}–{n_max}", xy=(0.02, 0.95),
                        xycoords="axes fraction", fontsize=8, va="top", color="gray")
        else:
            ax.set_title(title + " (no data)", fontsize=11, color="gray")
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes, color="gray")

    plt.tight_layout()
    path = plots_dir / "timeseries_4panel.png"
    plt.savefig(path, dpi=150)
    plt.close()
    saved.append(path)

    # --- Plot 2: Nominal CHIP index vs GDP deflator index ---
    if "all_nominal" in series and len(deflator) > 0 and "deflator" in deflator.columns:
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle("Nominal CHIP vs US GDP Deflator (Indexed)", fontsize=14, fontweight="bold")

        ts = series["all_nominal"]
        # Index both series to first year = 100
        base_chip = ts.iloc[0]["chip_value"]
        defl_base = deflator[deflator["year"] == ts.iloc[0]["year"]]["deflator"].values

        if base_chip > 0 and len(defl_base) > 0 and defl_base[0] > 0:
            chip_idx = ts["chip_value"] / base_chip * 100
            defl_merge = deflator[deflator["year"].isin(ts["year"].values)]
            defl_idx = defl_merge["deflator"] / defl_base[0] * 100

            ax.plot(ts["year"], chip_idx, "o-", color="steelblue", markersize=3,
                    linewidth=1.5, label="Nominal CHIP (indexed)")
            ax.plot(defl_merge["year"], defl_idx, "s-", color="firebrick", markersize=3,
                    linewidth=1.5, label="US GDP Deflator (indexed)")

            ax.set_xlabel("Year")
            ax.set_ylabel("Index (first year = 100)")
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            path = plots_dir / "nominal_vs_deflator.png"
            plt.savefig(path, dpi=150)
            plt.close()
            saved.append(path)

    # --- Plot 3: Country count over time ---
    if "all_constant" in series:
        fig, ax = plt.subplots(figsize=(12, 4))
        ts = series["all_constant"]
        ax.bar(ts["year"], ts["n_countries"], color="steelblue", alpha=0.7)
        ax.set_xlabel("Year")
        ax.set_ylabel("Countries")
        ax.set_title("Countries Contributing CHIP Data per Year (after trimming)")
        ax.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()
        path = plots_dir / "country_count.png"
        plt.savefig(path, dpi=150)
        plt.close()
        saved.append(path)

    # --- Plot 4: Constant vs Nominal side-by-side ---
    if "all_constant" in series and "all_nominal" in series:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle("Constant vs Nominal CHIP — All Countries", fontsize=14, fontweight="bold")

        tc = series["all_constant"]
        tn = series["all_nominal"]

        ax1.plot(tc["year"], tc["chip_value"], "o-", color="steelblue", markersize=3)
        ax1.set_title("Constant 2017$")
        ax1.set_ylabel("$/hour")
        ax1.set_xlabel("Year")
        ax1.grid(True, alpha=0.3)

        ax2.plot(tn["year"], tn["chip_value"], "o-", color="darkorange", markersize=3)
        ax2.set_title("Nominal (re-inflated)")
        ax2.set_ylabel("$/hour")
        ax2.set_xlabel("Year")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        path = plots_dir / "constant_vs_nominal.png"
        plt.savefig(path, dpi=150)
        plt.close()
        saved.append(path)

    for p in saved:
        logger.info(f"Saved plot: {p}")

    return saved


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(series: dict,
                    stable_countries: list,
                    coverage_df: pd.DataFrame,
                    deflator: pd.DataFrame,
                    plot_paths: list,
                    config_info: dict) -> str:
    """Generate comprehensive markdown discovery report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Time Series Discovery Report",
        "",
        f"Generated: {timestamp}",
        "",
        "---",
        "",
        "## Key Finding: Deflation Cancels in CHIP Formula",
        "",
        "CHIP = elementary_wage x (MPL / average_wage). Since deflation scales both",
        "wages equally, the deflator cancels out. CHIP is the same whether you deflate",
        "or not. To create a meaningful nominal series, we RE-INFLATE the constant-dollar",
        "CHIP by the GDP deflator: `CHIP_nominal(Y) = CHIP_constant(Y) x deflator(Y)/100`.",
        "",
        "---",
        "",
        "## Configuration",
        "",
        f"- **Year range:** {config_info['year_start']}–{config_info['year_end']}",
        f"- **Min countries per year:** {config_info['series_min_countries']}",
        f"- **Weighting:** {config_info['weighting']}",
        f"- **Stable panel threshold:** {config_info['min_coverage_pct']:.0%} of valid years",
        f"- **Imputation:** {'enabled' if config_info['enable_imputation'] else 'disabled'}",
        f"- **Wage averaging:** {config_info['wage_averaging_method']}",
        "",
    ]

    # --- Summary table ---
    lines.extend([
        "---",
        "",
        "## Summary",
        "",
        "| Configuration | Mean CHIP | Min | Max | Trend | Countries |",
        "|---------------|-----------|-----|-----|-------|-----------|",
    ])

    for key, label in [
        ("all_constant", "All, Constant 2017$"),
        ("all_nominal", "All, Nominal $"),
        ("panel_constant", "Panel, Constant 2017$"),
        ("panel_nominal", "Panel, Nominal $"),
    ]:
        if key in series:
            ts = series[key]
            mean_chip = ts["chip_value"].mean()
            min_chip = ts["chip_value"].min()
            max_chip = ts["chip_value"].max()
            n_min = int(ts["n_countries"].min())
            n_max = int(ts["n_countries"].max())

            early = ts.head(3)["chip_value"].mean()
            late = ts.tail(3)["chip_value"].mean()
            trend = f"{((late - early) / early) * 100:+.0f}%" if early > 0 else "n/a"

            lines.append(
                f"| {label} | ${mean_chip:.2f} | ${min_chip:.2f} | ${max_chip:.2f} "
                f"| {trend} | {n_min}–{n_max} |"
            )

    lines.append("")

    # --- Year-by-year tables ---
    for key, label in [
        ("all_constant", "All Countries — Constant 2017$"),
        ("all_nominal", "All Countries — Nominal $"),
        ("panel_constant", "Stable Panel — Constant 2017$"),
        ("panel_nominal", "Stable Panel — Nominal $"),
    ]:
        if key in series:
            ts = series[key]
            lines.extend([
                "---",
                "",
                f"## {label}",
                "",
                "| Year | CHIP ($/hr) | Countries | Std Dev | Elem Wage | Theta |",
                "|------|-------------|-----------|---------|-----------|-------|",
            ])
            for _, row in ts.iterrows():
                std = f"${row['chip_std']:.2f}" if row['chip_std'] > 0 else "—"
                lines.append(
                    f"| {int(row['year'])} | ${row['chip_value']:.2f} "
                    f"| {int(row['n_countries'])} | {std} "
                    f"| ${row.get('mean_elem_wage', 0):.2f} "
                    f"| {row.get('mean_theta', 0):.2f} |"
                )
            lines.append("")

    # --- Stable panel ---
    lines.extend([
        "---",
        "",
        "## Stable Panel Countries",
        "",
        f"Countries with data in >= {config_info['min_coverage_pct']:.0%} of valid years: "
        f"**{len(stable_countries)}**",
        "",
    ])

    if len(stable_countries) > 0:
        lines.append(", ".join(sorted(stable_countries)))
        lines.append("")

    if len(coverage_df) > 0:
        lines.extend([
            "### Coverage Distribution",
            "",
            "| Coverage | Countries |",
            "|----------|-----------|",
        ])
        for threshold in [1.0, 0.9, 0.8, 0.7, 0.5, 0.25]:
            n = len(coverage_df[coverage_df["pct"] >= threshold])
            lines.append(f"| >= {threshold:.0%} | {n} |")
        lines.append("")

    # --- Plots ---
    if plot_paths:
        lines.extend([
            "---",
            "",
            "## Plots",
            "",
            "Saved to `output/plots/`:",
            "",
        ])
        for p in plot_paths:
            lines.append(f"- `{p.name}`")
        lines.append("")

    # --- Auto-observations ---
    lines.extend([
        "---",
        "",
        "## Preliminary Observations",
        "",
    ])

    if "all_nominal" in series and "all_constant" in series:
        nom = series["all_nominal"]
        con = series["all_constant"]

        nom_early = nom.head(3)["chip_value"].mean()
        nom_late = nom.tail(3)["chip_value"].mean()
        con_early = con.head(3)["chip_value"].mean()
        con_late = con.tail(3)["chip_value"].mean()

        if nom_early > 0 and con_early > 0:
            nom_change = ((nom_late - nom_early) / nom_early) * 100
            con_change = ((con_late - con_early) / con_early) * 100

            lines.append(f"- Nominal CHIP changed **{nom_change:+.1f}%** from early to late period")
            lines.append(f"- Constant CHIP changed **{con_change:+.1f}%** from early to late period")

            if nom_change > con_change + 10:
                lines.append("- **Supports H1**: Nominal CHIP rises faster than constant, "
                             "consistent with inflation tracking")
            lines.append("")

    if "panel_constant" in series and "all_constant" in series:
        panel_std = series["panel_constant"]["chip_value"].std()
        all_std = series["all_constant"]["chip_value"].std()

        if all_std > 0:
            change = ((panel_std - all_std) / all_std) * 100
            if change < 0:
                lines.append(f"- Stable panel reduces CHIP volatility by **{abs(change):.0f}%** "
                             f"(std: ${all_std:.2f} -> ${panel_std:.2f})")
                lines.append("- **Supports H2**: Composition effects are a major source of volatility")
            else:
                lines.append(f"- Stable panel is **{change:.0f}% more volatile** than full set "
                             f"(std: ${all_std:.2f} -> ${panel_std:.2f})")
                lines.append("- Panel volatility may reflect fewer countries smoothing outliers")
            lines.append("")

    # --- Next steps ---
    lines.extend([
        "---",
        "",
        "## Next Steps",
        "",
        "1. If nominal CHIP tracks inflation -> proceed to formal H1 testing",
        "2. If stable panel is smoother -> use it as default country set",
        "3. If rolling average helps -> adopt 3yr or 5yr window for production",
        "4. Compare GDP vs labor vs unweighted (change WEIGHTING constant)",
        "5. Investigate anomalous years / country-count changes",
        "",
    ])

    return "\n".join(lines)


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_timeseries():
    """
    Run the time series discovery pipeline.

    1. Run the shared pipeline once (deflation doesn't matter for raw CHIP)
    2. Aggregate to per-year constant-dollar CHIP
    3. Trim sparse years
    4. Identify stable panel from remaining years
    5. Create nominal series by re-inflating with GDP deflator
    6. Generate comparison plots
    """
    config = load_config(study_dir=STUDY_DIR)

    year_start = YEAR_START
    year_end = YEAR_END

    # ------------------------------------------------------------------
    # Step 1: Fetch data
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("STEP 1: Fetching data")
    logger.info("=" * 70)

    logger.info("Fetching data (this may take a moment)...")
    data = fetcher.get_all()

    for name, df in data.items():
        logger.info(f"  {name}: {len(df):,} rows")

    # ------------------------------------------------------------------
    # Step 2: Run pipeline (constant dollars)
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("STEP 2: Running CHIP pipeline (all countries, constant 2017$)")
    logger.info("=" * 70)

    # Deflation doesn't affect CHIP (cancels in the ratio), but we apply
    # it anyway to keep wages in consistent units for diagnostics.
    deflator_df = normalize.normalize_deflator(data["deflator"], base_year=2017)

    result = pipeline.prepare_labor_data(
        data=data,
        year_start=year_start,
        year_end=year_end,
        deflator_df=deflator_df,
        include_countries=None,
        enable_imputation=ENABLE_IMPUTATION,
        wage_averaging_method=WAGE_AVERAGING_METHOD,
    )

    _, _, est_data = pipeline.estimate_chip(
        result["est_data"],
        enable_imputation=ENABLE_IMPUTATION,
    )

    logger.info(f"Pipeline produced {len(est_data)} country-year observations, "
                f"{est_data['country'].nunique()} countries")

    # ------------------------------------------------------------------
    # Step 3: Aggregate by year (constant dollars)
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("STEP 3: Aggregating to per-year CHIP values")
    logger.info("=" * 70)

    ts_all_raw = aggregate_by_year(est_data, weighting=WEIGHTING)
    logger.info(f"Raw time series: {len(ts_all_raw)} years, "
                f"country range {int(ts_all_raw['n_countries'].min())}–"
                f"{int(ts_all_raw['n_countries'].max())}")

    # Trim sparse years
    ts_all_constant = trim_sparse_years(ts_all_raw, SERIES_MIN_COUNTRIES)

    if len(ts_all_constant) == 0:
        raise ValueError(f"No years with >= {SERIES_MIN_COUNTRIES} countries!")

    valid_years = set(ts_all_constant["year"].astype(int).tolist())
    logger.info(f"After trimming: {len(ts_all_constant)} years "
                f"({min(valid_years)}–{max(valid_years)})")

    # ------------------------------------------------------------------
    # Step 4: Create nominal series (re-inflated)
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("STEP 4: Creating nominal (re-inflated) series")
    logger.info("=" * 70)

    ts_all_nominal = create_nominal_series(ts_all_constant, deflator_df)
    logger.info(f"Nominal series: mean ${ts_all_nominal['chip_value'].mean():.2f}, "
                f"range ${ts_all_nominal['chip_value'].min():.2f}–"
                f"${ts_all_nominal['chip_value'].max():.2f}")

    # ------------------------------------------------------------------
    # Step 5: Identify stable panel
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("STEP 5: Identifying stable panel")
    logger.info("=" * 70)

    stable_countries, coverage_df = identify_stable_panel(
        est_data, valid_years, MIN_COVERAGE_PCT
    )

    if len(stable_countries) < 3:
        logger.warning(f"Only {len(stable_countries)} countries in panel at "
                       f"{MIN_COVERAGE_PCT:.0%}. Trying 50%...")
        stable_countries, coverage_df = identify_stable_panel(
            est_data, valid_years, 0.50
        )

    # ------------------------------------------------------------------
    # Step 6: Build stable-panel series
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("STEP 6: Building stable-panel time series")
    logger.info("=" * 70)

    series = {
        "all_constant": ts_all_constant,
        "all_nominal": ts_all_nominal,
    }

    if len(stable_countries) > 0:
        # Only include years that passed the min-countries filter for all-countries
        est_panel = est_data[
            (est_data["country"].isin(stable_countries)) &
            (est_data["year"].isin(valid_years))
        ]
        ts_panel_constant = aggregate_by_year(est_panel, weighting=WEIGHTING)
        ts_panel_constant = trim_sparse_years(ts_panel_constant, 3)
        ts_panel_nominal = create_nominal_series(ts_panel_constant, deflator_df)

        series["panel_constant"] = ts_panel_constant
        series["panel_nominal"] = ts_panel_nominal

        logger.info(f"Panel: {est_panel['country'].nunique()} countries, "
                    f"{len(ts_panel_constant)} years")
    else:
        logger.warning("No stable panel could be formed")

    # ------------------------------------------------------------------
    # Step 7: Rolling averages
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("STEP 7: Computing rolling averages")
    logger.info("=" * 70)

    for key in list(series.keys()):
        for window in [3, 5]:
            series[f"{key}_r{window}"] = rolling_average(series[key], window)

    # ------------------------------------------------------------------
    # Step 8: Plots
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("STEP 8: Generating plots")
    logger.info("=" * 70)

    plot_paths = generate_plots(series, deflator_df, OUTPUT_DIR)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("RESULTS SUMMARY")
    logger.info("=" * 70)

    for key, label in [("all_constant", "All/Constant"),
                       ("all_nominal", "All/Nominal"),
                       ("panel_constant", "Panel/Constant"),
                       ("panel_nominal", "Panel/Nominal")]:
        if key in series:
            ts = series[key]
            logger.info(f"  {label}: mean=${ts['chip_value'].mean():.2f}, "
                        f"range=[${ts['chip_value'].min():.2f}, ${ts['chip_value'].max():.2f}], "
                        f"n={int(ts['n_countries'].min())}–{int(ts['n_countries'].max())}")

    return {
        "series": series,
        "stable_countries": stable_countries,
        "coverage_df": coverage_df,
        "deflator_series": deflator_df,
        "plot_paths": plot_paths,
        "config_info": {
            "year_start": year_start,
            "year_end": year_end,
            "series_min_countries": SERIES_MIN_COUNTRIES,
            "weighting": WEIGHTING,
            "min_coverage_pct": MIN_COVERAGE_PCT,
            "enable_imputation": ENABLE_IMPUTATION,
            "wage_averaging_method": WAGE_AVERAGING_METHOD,
        },
    }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    script_name = Path(__file__).parent.name
    output_dir = OUTPUT_DIR
    log_path = setup_logging(script_name, output_dir=output_dir)

    logger.info(f"Time Series Discovery — Range: {YEAR_START}–{YEAR_END}")

    with ScriptContext(script_name, output_dir=output_dir) as ctx:
        try:
            results = run_timeseries()

            if results is None:
                ctx.error("Pipeline returned no results")
                return 1

            report = generate_report(
                series=results["series"],
                stable_countries=results["stable_countries"],
                coverage_df=results["coverage_df"],
                deflator=results["deflator_series"],
                plot_paths=results["plot_paths"],
                config_info=results["config_info"],
            )

            reports_dir = output_dir / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"timeseries_{timestamp}.md"
            report_path.write_text(report)

            ts_con = results["series"].get("all_constant")
            ts_nom = results["series"].get("all_nominal")

            logger.info("=" * 60)
            if ts_con is not None:
                logger.info(f"Constant CHIP (mean): ${ts_con['chip_value'].mean():.2f}/hour")
            if ts_nom is not None:
                logger.info(f"Nominal CHIP  (mean): ${ts_nom['chip_value'].mean():.2f}/hour")
            logger.info(f"Stable panel: {len(results['stable_countries'])} countries")
            logger.info(f"Plots: {len(results['plot_paths'])} saved")
            logger.info("=" * 60)
            logger.info(f"Report: {report_path}")

            ctx.set_result("n_years", len(ts_con) if ts_con is not None else 0)
            ctx.set_result("n_stable_countries", len(results["stable_countries"]))
            ctx.set_result("mean_constant_chip",
                           float(ts_con["chip_value"].mean()) if ts_con is not None else None)
            ctx.set_result("mean_nominal_chip",
                           float(ts_nom["chip_value"].mean()) if ts_nom is not None else None)

            return 0

        except Exception as e:
            logger.exception("Pipeline failed")
            ctx.error(str(e))
            return 1


if __name__ == "__main__":
    sys.exit(main())

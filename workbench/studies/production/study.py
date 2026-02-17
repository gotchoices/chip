#!/usr/bin/env python3
"""
Production Methodology Study

Tests trailing-window CHIP estimation, PWT bridge strategies, and CPI
extrapolation accuracy to determine the best methodology for producing
current-year CHIP values.

See README.md for research question, hypotheses, and methodology.
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
from lib.config import load_config

logger = get_logger(__name__)

OUTPUT_DIR = STUDY_DIR / "output"


# =============================================================================
# CONFIGURATION
# =============================================================================

YEAR_START = 1992
YEAR_END = 2023       # PWT 11.0 extends to 2023
SERIES_MIN_COUNTRIES = 5
MIN_COVERAGE_PCT = 0.70
WEIGHTING = "gdp"
ENABLE_IMPUTATION = True
WAGE_AVERAGING_METHOD = "simple"

# Trailing window sizes to test
WINDOW_SIZES = [1, 3, 5]

# Bridge test: hold PWT constant at this year, estimate later years
# Override in config.yaml with data.bridge_freeze_year
BRIDGE_FREEZE_YEAR_DEFAULT = 2020

# CPI extrapolation: test from this range forward
EXTRAP_BASE_YEARS = range(2005, 2022)


# =============================================================================
# CORE PIPELINE (shared with timeseries)
# =============================================================================

def aggregate_by_year(est_data, weighting="gdp"):
    """Aggregate CHIP to a single value per year across countries."""
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
        else:
            chip = ydf["chip_value"].mean()

        rows.append({
            "year": int(year),
            "chip_value": chip,
            "n_countries": len(ydf),
            "chip_std": ydf["chip_value"].std() if len(ydf) > 1 else 0.0,
            "mean_elem_wage": ydf["elementary_wage"].mean(),
            "mean_theta": ydf["theta"].mean(),
            "mean_alpha": ydf["alpha"].mean(),
        })
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def trim_sparse_years(ts, min_countries):
    """Drop years with fewer than min_countries contributing."""
    before = len(ts)
    ts = ts[ts["n_countries"] >= min_countries].reset_index(drop=True)
    dropped = before - len(ts)
    if dropped > 0:
        logger.info(f"Trimmed {dropped} years with < {min_countries} countries")
    return ts


def create_nominal_series(ts_constant, deflator):
    """Re-inflate constant-dollar CHIP to nominal dollars."""
    ts = ts_constant.copy()
    ts = ts.merge(deflator[["year", "deflator"]], on="year", how="left")
    ts["chip_value"] = ts["chip_value"] * (ts["deflator"] / 100.0)
    ts = ts.drop(columns=["deflator"], errors="ignore")
    return ts


def identify_stable_panel(est_data, valid_years, min_coverage_pct):
    """Identify countries with consistent data across valid years."""
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
    logger.info(f"Stable panel: {len(stable)} countries with >= {min_coverage_pct:.0%} "
                f"coverage over {n_years} valid years")
    return stable, coverage


# =============================================================================
# PHASE 1: EXTENDED SERIES
# =============================================================================

def run_base_pipeline(data, deflator_df, year_start, year_end):
    """Run the full CHIP pipeline and return per-country-year data."""
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
    return est_data


# =============================================================================
# PHASE 2: TRAILING WINDOW
# =============================================================================

def trailing_window_series(ts_constant, deflator, window_size):
    """
    Compute a trailing-window CHIP series.

    For each target year Y, average CHIP from years [Y-w+1, ..., Y],
    re-inflating each to year-Y dollars.

    Returns DataFrame with year, chip_value (nominal in year-Y dollars).
    """
    rows = []
    years = sorted(ts_constant["year"].values)
    chip_by_year = dict(zip(ts_constant["year"], ts_constant["chip_value"]))
    defl_by_year = dict(zip(deflator["year"], deflator["deflator"]))

    for target_year in years:
        window_years = [y for y in years
                        if target_year - window_size + 1 <= y <= target_year]
        if len(window_years) == 0:
            continue

        target_defl = defl_by_year.get(target_year)
        if target_defl is None or target_defl == 0:
            continue

        reinflated = []
        for wy in window_years:
            chip_const = chip_by_year.get(wy)
            if chip_const is None:
                continue
            # Re-inflate from constant 2017$ to target-year dollars
            reinflated.append(chip_const * target_defl / 100.0)

        if len(reinflated) > 0:
            rows.append({
                "year": int(target_year),
                "chip_value": np.mean(reinflated),
                "window_years_used": len(reinflated),
                "window_size": window_size,
            })

    return pd.DataFrame(rows)


def compare_windows(ts_constant, deflator, window_sizes):
    """Compute trailing-window series for multiple window sizes and compare."""
    results = {}
    for ws in window_sizes:
        tw = trailing_window_series(ts_constant, deflator, ws)
        if len(tw) > 0:
            results[ws] = tw
            yoy_changes = tw["chip_value"].pct_change().dropna()
            logger.info(f"Window {ws}yr: mean=${tw['chip_value'].mean():.2f}, "
                        f"yoy_std={yoy_changes.std()*100:.1f}%, "
                        f"n_years={len(tw)}")
    return results


# =============================================================================
# PHASE 3: PWT BRIDGE
# =============================================================================

def _build_bridge_pwt(pwt_df, freeze_year, year_end, method="freeze", trend_years=5):
    """
    Build a modified PWT dataset that extrapolates beyond freeze_year.

    Methods:
        "freeze" — copy freeze_year values to all later years
        "slope"  — extrapolate each country's numeric columns using the
                   average annual growth rate over the last trend_years
    """
    pwt_pre = pwt_df[pwt_df["year"] <= freeze_year].copy()
    freeze_data = pwt_df[pwt_df["year"] == freeze_year].copy()

    if len(freeze_data) == 0:
        return None

    if method == "freeze":
        bridge_rows = []
        for bridge_year in range(freeze_year + 1, year_end + 1):
            year_copy = freeze_data.copy()
            year_copy["year"] = bridge_year
            bridge_rows.append(year_copy)
        return pd.concat([pwt_pre] + bridge_rows, ignore_index=True)

    elif method == "slope":
        # Compute per-country annual growth rates from recent history
        trend_start = freeze_year - trend_years
        trend_data = pwt_df[
            (pwt_df["year"] >= trend_start) & (pwt_df["year"] <= freeze_year)
        ].copy()

        # Numeric columns to extrapolate (the key macro variables)
        extrap_cols = ["rgdpna", "rnna", "emp", "hc"]
        extrap_cols = [c for c in extrap_cols if c in pwt_df.columns]

        country_col = "countrycode" if "countrycode" in pwt_df.columns else "country"

        growth_rates = {}
        for country, cdf in trend_data.groupby(country_col):
            if len(cdf) < 2:
                growth_rates[country] = {c: 0.0 for c in extrap_cols}
                continue
            cdf = cdf.sort_values("year")
            rates = {}
            for col in extrap_cols:
                vals = cdf[col].dropna()
                if len(vals) >= 2 and vals.iloc[0] > 0:
                    total_growth = vals.iloc[-1] / vals.iloc[0]
                    n_periods = len(vals) - 1
                    rates[col] = total_growth ** (1.0 / n_periods) - 1.0
                else:
                    rates[col] = 0.0
            growth_rates[country] = rates

        bridge_rows = []
        for bridge_year in range(freeze_year + 1, year_end + 1):
            year_copy = freeze_data.copy()
            year_copy["year"] = bridge_year
            years_ahead = bridge_year - freeze_year
            for col in extrap_cols:
                year_copy[col] = year_copy.apply(
                    lambda r: r[col] * (1.0 + growth_rates.get(
                        r[country_col], {}
                    ).get(col, 0.0)) ** years_ahead,
                    axis=1,
                )
            bridge_rows.append(year_copy)

        return pd.concat([pwt_pre] + bridge_rows, ignore_index=True)

    else:
        raise ValueError(f"Unknown bridge method: {method}")


def test_pwt_bridge(data, deflator_df, freeze_year, year_end):
    """
    Test PWT bridge strategies: freeze vs slope extrapolation.
    Compares both to truth (full PWT data).

    Returns dict with truth, freeze bridge, slope bridge, and comparisons.
    """
    # Truth: full pipeline with all PWT data
    logger.info(f"Computing truth (full PWT through {year_end})...")
    est_truth = run_base_pipeline(data, deflator_df, YEAR_START, year_end)
    ts_truth = aggregate_by_year(est_truth, weighting=WEIGHTING)
    ts_truth = trim_sparse_years(ts_truth, SERIES_MIN_COUNTRIES)

    pwt_df = data["pwt"].copy()

    results = {
        "ts_truth": ts_truth,
        "freeze_year": freeze_year,
        "methods": {},
    }

    for method in ["freeze", "slope"]:
        logger.info(f"Computing bridge ({method}, frozen at {freeze_year})...")
        bridge_pwt = _build_bridge_pwt(pwt_df, freeze_year, year_end, method=method)

        if bridge_pwt is None:
            logger.warning(f"No PWT data for freeze year {freeze_year}")
            continue

        data_bridge = dict(data)
        data_bridge["pwt"] = bridge_pwt

        est_bridge = run_base_pipeline(data_bridge, deflator_df, YEAR_START, year_end)
        ts_bridge = aggregate_by_year(est_bridge, weighting=WEIGHTING)
        ts_bridge = trim_sparse_years(ts_bridge, SERIES_MIN_COUNTRIES)

        post_freeze = ts_truth[ts_truth["year"] > freeze_year].copy()
        bridge_post = ts_bridge[ts_bridge["year"] > freeze_year].copy()

        if len(post_freeze) > 0 and len(bridge_post) > 0:
            comparison = post_freeze[["year", "chip_value"]].merge(
                bridge_post[["year", "chip_value"]],
                on="year", suffixes=("_truth", f"_{method}")
            )
            comparison["diff"] = comparison[f"chip_value_{method}"] - comparison["chip_value_truth"]
            comparison["pct_diff"] = (comparison["diff"] / comparison["chip_value_truth"]) * 100
        else:
            comparison = pd.DataFrame()

        results["methods"][method] = {
            "ts_bridge": ts_bridge,
            "comparison": comparison,
        }

    return results


# =============================================================================
# PHASE 4: CPI EXTRAPOLATION
# =============================================================================

def test_cpi_extrapolation(ts_constant, deflator, base_years):
    """
    Test CPI extrapolation: for each base year, extrapolate CHIP forward
    and compare to the actual calculated value.

    Extrapolation: CHIP_nominal(Y+1) = CHIP_constant(Y) * deflator(Y+1)/100
    Actual: CHIP_nominal(Y+1) = CHIP_constant(Y+1) * deflator(Y+1)/100

    The correction is driven entirely by the change in real CHIP.
    """
    chip_by_year = dict(zip(ts_constant["year"], ts_constant["chip_value"]))
    defl_by_year = dict(zip(deflator["year"], deflator["deflator"]))

    rows = []
    for base_year in base_years:
        target_year = base_year + 1
        chip_base = chip_by_year.get(base_year)
        chip_target = chip_by_year.get(target_year)
        defl_target = defl_by_year.get(target_year)

        if chip_base is None or chip_target is None or defl_target is None:
            continue

        # Extrapolated nominal: assume real CHIP doesn't change
        extrap_nominal = chip_base * defl_target / 100.0
        # Actual nominal
        actual_nominal = chip_target * defl_target / 100.0

        correction = actual_nominal - extrap_nominal
        correction_pct = (correction / extrap_nominal) * 100 if extrap_nominal != 0 else 0

        rows.append({
            "base_year": int(base_year),
            "target_year": int(target_year),
            "chip_const_base": chip_base,
            "chip_const_target": chip_target,
            "extrap_nominal": extrap_nominal,
            "actual_nominal": actual_nominal,
            "correction": correction,
            "correction_pct": correction_pct,
        })

    return pd.DataFrame(rows)


# =============================================================================
# PLOTTING
# =============================================================================

def generate_plots(ts_constant, ts_nominal, window_results, bridge_result,
                   extrap_df, deflator, output_dir):
    """Generate production methodology plots."""
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

    # --- Plot 1: Extended series (constant + nominal) ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("CHIP Time Series — PWT 11.0 (2000–2023)", fontsize=14, fontweight="bold")

    ax1.plot(ts_constant["year"], ts_constant["chip_value"], "o-",
             color="steelblue", markersize=3, linewidth=1.5)
    ax1.set_title("Constant 2017$")
    ax1.set_ylabel("$/hour")
    ax1.set_xlabel("Year")
    ax1.grid(True, alpha=0.3)

    ax2.plot(ts_nominal["year"], ts_nominal["chip_value"], "o-",
             color="darkorange", markersize=3, linewidth=1.5)
    ax2.set_title("Nominal (re-inflated)")
    ax2.set_ylabel("$/hour")
    ax2.set_xlabel("Year")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    path = plots_dir / "extended_series.png"
    plt.savefig(path, dpi=150)
    plt.close()
    saved.append(path)

    # --- Plot 2: Trailing window comparison ---
    if window_results:
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.suptitle("Trailing Window Comparison (Nominal $/hr)", fontsize=14, fontweight="bold")
        colors = {1: "steelblue", 3: "darkorange", 5: "seagreen"}

        for ws, tw in sorted(window_results.items()):
            ax.plot(tw["year"], tw["chip_value"], "o-", markersize=3,
                    linewidth=1.5, color=colors.get(ws, "gray"),
                    label=f"{ws}-year window")

        ax.set_xlabel("Year")
        ax.set_ylabel("Nominal CHIP ($/hr)")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        path = plots_dir / "trailing_windows.png"
        plt.savefig(path, dpi=150)
        plt.close()
        saved.append(path)

    # --- Plot 3: Bridge comparison (freeze vs slope) ---
    if bridge_result and bridge_result.get("methods"):
        fy = bridge_result["freeze_year"]
        tt = bridge_result["ts_truth"]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(f"PWT Bridge Test (frozen at {fy})",
                     fontsize=14, fontweight="bold")

        ax1.plot(tt["year"], tt["chip_value"], "o-", color="steelblue",
                 markersize=3, linewidth=1.5, label="Full PWT (truth)")

        colors = {"freeze": "firebrick", "slope": "seagreen"}
        labels = {"freeze": f"Freeze at {fy}", "slope": f"Slope from {fy}"}

        for method, mdata in bridge_result["methods"].items():
            tb = mdata["ts_bridge"]
            ax1.plot(tb["year"], tb["chip_value"], "s--",
                     color=colors.get(method, "gray"), markersize=3,
                     linewidth=1.5, label=labels.get(method, method))

        ax1.axvline(x=fy, color="gray", linestyle=":", alpha=0.5)
        ax1.set_title("Constant CHIP ($/hr)")
        ax1.set_ylabel("$/hour")
        ax1.set_xlabel("Year")
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)

        bar_width = 0.35
        for i, (method, mdata) in enumerate(bridge_result["methods"].items()):
            comp = mdata["comparison"]
            if len(comp) > 0:
                offset = (i - 0.5) * bar_width
                ax2.bar(comp["year"] + offset, comp["pct_diff"],
                        width=bar_width, alpha=0.7,
                        color=colors.get(method, "gray"),
                        label=labels.get(method, method))

        ax2.axhline(y=0, color="black", linewidth=0.5)
        ax2.set_title("Bridge Error (% vs truth)")
        ax2.set_ylabel("% difference")
        ax2.set_xlabel("Year")
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()
        path = plots_dir / "bridge_test.png"
        plt.savefig(path, dpi=150)
        plt.close()
        saved.append(path)

    # --- Plot 4: CPI extrapolation corrections ---
    if len(extrap_df) > 0:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle("CPI Extrapolation Accuracy", fontsize=14, fontweight="bold")

        ax1.bar(extrap_df["target_year"], extrap_df["correction_pct"],
                color="steelblue", alpha=0.7)
        ax1.axhline(y=0, color="black", linewidth=0.5)
        ax1.set_title("Year-over-Year Correction (%)")
        ax1.set_ylabel("Correction (%)")
        ax1.set_xlabel("Target Year")
        ax1.grid(True, alpha=0.3, axis="y")

        ax2.hist(extrap_df["correction_pct"], bins=15, color="steelblue",
                 alpha=0.7, edgecolor="white")
        ax2.axvline(x=0, color="black", linewidth=0.5)
        ax2.set_title("Distribution of Corrections")
        ax2.set_xlabel("Correction (%)")
        ax2.set_ylabel("Count")
        ax2.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()
        path = plots_dir / "cpi_extrapolation.png"
        plt.savefig(path, dpi=150)
        plt.close()
        saved.append(path)

    # --- Plot 5: Country count over time ---
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(ts_constant["year"], ts_constant["n_countries"], color="steelblue", alpha=0.7)
    ax.set_xlabel("Year")
    ax.set_ylabel("Countries")
    ax.set_title("Countries Contributing CHIP Data per Year (PWT 11.0)")
    ax.grid(True, alpha=0.3, axis="y")
    plt.tight_layout()
    path = plots_dir / "country_count.png"
    plt.savefig(path, dpi=150)
    plt.close()
    saved.append(path)

    for p in saved:
        logger.info(f"Saved plot: {p}")
    return saved


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(ts_constant, ts_nominal, stable_countries, coverage_df,
                    window_results, bridge_result, extrap_df, plot_paths,
                    config_info):
    """Generate production methodology report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Production Methodology Report",
        "",
        f"Generated: {timestamp}",
        "",
        "---",
        "",
        "## Configuration",
        "",
        f"- **PWT version:** {config_info.get('pwt_version', 'default')}",
        f"- **Year range:** {config_info['year_start']}–{config_info['year_end']}",
        f"- **Min countries/year:** {config_info['series_min_countries']}",
        f"- **Weighting:** {config_info['weighting']}",
        f"- **Window sizes tested:** {config_info['window_sizes']}",
        f"- **Bridge freeze year:** {config_info['bridge_freeze_year']}",
        "",
    ]

    # --- Phase 1: Extended series ---
    lines.extend([
        "---",
        "",
        "## Phase 1: Extended Series (PWT 11.0)",
        "",
        "| Year | Constant CHIP | Nominal CHIP | Countries | Mean Alpha |",
        "|------|---------------|--------------|-----------|------------|",
    ])
    merged = ts_constant[["year", "chip_value", "n_countries", "mean_alpha"]].merge(
        ts_nominal[["year", "chip_value"]], on="year", suffixes=("_const", "_nom")
    )
    for _, row in merged.iterrows():
        lines.append(
            f"| {int(row['year'])} | ${row['chip_value_const']:.2f} | "
            f"${row['chip_value_nom']:.2f} | {int(row['n_countries'])} | "
            f"{row['mean_alpha']:.3f} |"
        )
    lines.append("")

    # Stable panel
    lines.extend([
        f"**Stable panel:** {len(stable_countries)} countries with >= "
        f"{config_info['min_coverage_pct']:.0%} coverage",
        "",
    ])
    if stable_countries:
        lines.append(", ".join(sorted(stable_countries)))
        lines.append("")

    # --- Phase 2: Trailing windows ---
    lines.extend([
        "---",
        "",
        "## Phase 2: Trailing Window Comparison",
        "",
        "| Window | Mean Nominal | YoY Std | Smoothness Rank |",
        "|--------|-------------|---------|-----------------|",
    ])

    window_stats = {}
    for ws in sorted(window_results.keys()):
        tw = window_results[ws]
        yoy = tw["chip_value"].pct_change().dropna()
        yoy_std = yoy.std() * 100
        window_stats[ws] = {"mean": tw["chip_value"].mean(), "yoy_std": yoy_std}

    ranked = sorted(window_stats.items(), key=lambda x: x[1]["yoy_std"])
    for rank, (ws, stats) in enumerate(ranked, 1):
        lines.append(
            f"| {ws}-year | ${stats['mean']:.2f} | {stats['yoy_std']:.1f}% | {rank} |"
        )
    lines.append("")

    if ranked:
        best_ws = ranked[0][0]
        lines.append(f"**Recommended window: {best_ws}-year** (lowest year-over-year volatility)")
        lines.append("")

    # --- Phase 3: Bridge ---
    if bridge_result and bridge_result.get("methods"):
        fy = bridge_result["freeze_year"]
        lines.extend([
            "---",
            "",
            f"## Phase 3: PWT Bridge (frozen at {fy})",
            "",
        ])

        # Build a combined comparison table
        header_cols = ["Year", "Truth"]
        methods_with_data = {}
        for method, mdata in bridge_result["methods"].items():
            if len(mdata["comparison"]) > 0:
                methods_with_data[method] = mdata["comparison"]
                header_cols.extend([method.capitalize(), f"{method.capitalize()} Err"])

        if methods_with_data:
            lines.append("| " + " | ".join(header_cols) + " |")
            lines.append("|" + "|".join(["------"] * len(header_cols)) + "|")

            # Get all years from truth
            all_years = set()
            for comp in methods_with_data.values():
                all_years.update(comp["year"].astype(int).tolist())

            for year in sorted(all_years):
                row_parts = [f"{year}"]
                # Truth value from first method's comparison
                first_comp = list(methods_with_data.values())[0]
                truth_row = first_comp[first_comp["year"] == year]
                if len(truth_row) > 0:
                    row_parts.append(f"${truth_row.iloc[0]['chip_value_truth']:.2f}")
                else:
                    row_parts.append("—")

                for method, comp in methods_with_data.items():
                    mrow = comp[comp["year"] == year]
                    if len(mrow) > 0:
                        val_col = f"chip_value_{method}"
                        row_parts.append(f"${mrow.iloc[0][val_col]:.2f}")
                        row_parts.append(f"{mrow.iloc[0]['pct_diff']:+.1f}%")
                    else:
                        row_parts.extend(["—", "—"])

                lines.append("| " + " | ".join(row_parts) + " |")

            lines.append("")

            # Summary stats per method
            for method, comp in methods_with_data.items():
                mae = comp["pct_diff"].abs().mean()
                max_err = comp["pct_diff"].abs().max()
                lines.append(f"**{method.capitalize()} bridge:** "
                             f"mean |error| = {mae:.1f}%, max = {max_err:.1f}%")
            lines.append("")

            # Recommendation
            best_method = min(methods_with_data.keys(),
                              key=lambda m: methods_with_data[m]["pct_diff"].abs().mean())
            best_mae = methods_with_data[best_method]["pct_diff"].abs().mean()
            lines.append(f"**Recommended: {best_method} bridge** ({best_mae:.1f}% mean error)")
            lines.append("")

    # --- Phase 4: CPI extrapolation ---
    if len(extrap_df) > 0:
        lines.extend([
            "---",
            "",
            "## Phase 4: CPI Extrapolation Accuracy",
            "",
            "| Base Year | Target | Extrapolated | Actual | Correction |",
            "|-----------|--------|-------------|--------|------------|",
        ])
        for _, row in extrap_df.iterrows():
            lines.append(
                f"| {int(row['base_year'])} | {int(row['target_year'])} | "
                f"${row['extrap_nominal']:.2f} | ${row['actual_nominal']:.2f} | "
                f"{row['correction_pct']:+.1f}% |"
            )
        lines.extend([
            "",
            f"**Mean correction:** {extrap_df['correction_pct'].mean():+.1f}%",
            f"**Std of corrections:** {extrap_df['correction_pct'].std():.1f}%",
            f"**Max absolute correction:** {extrap_df['correction_pct'].abs().max():.1f}%",
            "",
        ])
        within_5 = (extrap_df['correction_pct'].abs() <= 5).sum()
        total = len(extrap_df)
        lines.append(
            f"**{within_5}/{total} corrections** ({within_5/total*100:.0f}%) are within ±5%."
        )
        lines.append("")

    # --- Plots ---
    if plot_paths:
        lines.extend([
            "---",
            "",
            "## Plots",
            "",
        ])
        for p in plot_paths:
            lines.append(f"- `{p.name}`")
        lines.append("")

    # --- Current CHIP Estimate ---
    lines.extend([
        "---",
        "",
        "## Current CHIP Estimate",
        "",
    ])

    # Latest year with full data
    last_year = int(ts_constant["year"].max())
    last_const = ts_constant[ts_constant["year"] == last_year]["chip_value"].values[0]
    last_nom = ts_nominal[ts_nominal["year"] == last_year]["chip_value"].values[0]

    # 5-year trailing window value
    if 5 in window_results and len(window_results[5]) > 0:
        tw5 = window_results[5]
        tw5_last = tw5[tw5["year"] == last_year]
        if len(tw5_last) > 0:
            tw5_value = tw5_last.iloc[0]["chip_value"]
        else:
            tw5_value = tw5.iloc[-1]["chip_value"]
        tw5_year = int(tw5.iloc[-1]["year"])
    else:
        tw5_value = last_nom
        tw5_year = last_year

    lines.extend([
        f"**Latest calculated year:** {last_year}",
        f"- Single-year constant: ${last_const:.2f}/hr",
        f"- Single-year nominal: ${last_nom:.2f}/hr",
        f"- 5-year trailing nominal: ${tw5_value:.2f}/hr (at {tw5_year})",
        "",
        "To estimate current CHIP, multiply the trailing-window value by",
        "cumulative CPI growth since the last calculated year:",
        "",
        "```",
        f"CHIP_current = ${tw5_value:.2f} × (CPI_today / CPI_{tw5_year})",
        "```",
        "",
        f"For reference: chipcentral.net reports $3.18 (based on original study",
        f"$2.53 × CPI adjustment). Our {last_year} single-year nominal is ${last_nom:.2f}.",
        "",
    ])

    # --- Recommendations ---
    lines.extend([
        "---",
        "",
        "## Preliminary Recommendations",
        "",
    ])

    if ranked:
        best_ws = ranked[0][0]
        lines.append(f"1. Use a **{best_ws}-year trailing window** for production estimates.")

    if bridge_result and bridge_result.get("methods"):
        best_method = None
        best_mae = 999
        for method, mdata in bridge_result["methods"].items():
            if len(mdata["comparison"]) > 0:
                mae = mdata["comparison"]["pct_diff"].abs().mean()
                if mae < best_mae:
                    best_mae = mae
                    best_method = method
        if best_method:
            lines.append(f"2. Use **{best_method} bridge** for years beyond PWT "
                         f"(mean error {best_mae:.1f}%).")

    if len(extrap_df) > 0:
        std = extrap_df['correction_pct'].std()
        lines.append(f"3. CPI extrapolation correction std: {std:.1f}% — "
                     f"{'acceptable' if std < 5 else 'acceptable for interim estimates'}.")

    lines.append(f"4. Latest nominal CHIP ({last_year}): **${last_nom:.2f}/hr**. "
                 f"Extrapolate with CPI for current value.")
    lines.append("")

    return "\n".join(lines)


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_production():
    """Run the full production methodology study."""
    config = load_config(study_dir=STUDY_DIR)
    pwt_version = config.data.pwt_version
    bridge_freeze_year = config.data.bridge_freeze_year or BRIDGE_FREEZE_YEAR_DEFAULT

    # ------------------------------------------------------------------
    # Step 1: Fetch data (PWT 11.0 by default)
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 0: Fetching data")
    logger.info("=" * 70)

    data = fetcher.get_all(pwt_version=pwt_version)
    for name, df in data.items():
        logger.info(f"  {name}: {len(df):,} rows")

    deflator_df = normalize.normalize_deflator(data["deflator"], base_year=2017)

    # ------------------------------------------------------------------
    # Phase 1: Extended series
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 1: Running pipeline (PWT 11.0, full range)")
    logger.info("=" * 70)

    est_data = run_base_pipeline(data, deflator_df, YEAR_START, YEAR_END)
    logger.info(f"Pipeline: {len(est_data)} obs, {est_data['country'].nunique()} countries")

    ts_constant = aggregate_by_year(est_data, weighting=WEIGHTING)
    ts_constant = trim_sparse_years(ts_constant, SERIES_MIN_COUNTRIES)

    valid_years = set(ts_constant["year"].astype(int).tolist())
    logger.info(f"Series: {len(ts_constant)} years ({min(valid_years)}–{max(valid_years)})")

    ts_nominal = create_nominal_series(ts_constant, deflator_df)

    # Stable panel
    stable_countries, coverage_df = identify_stable_panel(
        est_data, valid_years, MIN_COVERAGE_PCT
    )

    logger.info(f"Constant mean: ${ts_constant['chip_value'].mean():.2f}")
    logger.info(f"Nominal mean: ${ts_nominal['chip_value'].mean():.2f}")

    # ------------------------------------------------------------------
    # Phase 2: Trailing windows
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 2: Trailing window comparison")
    logger.info("=" * 70)

    window_results = compare_windows(ts_constant, deflator_df, WINDOW_SIZES)

    # ------------------------------------------------------------------
    # Phase 3: PWT bridge
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info(f"PHASE 3: PWT bridge (freeze at {bridge_freeze_year})")
    logger.info("=" * 70)

    bridge_result = test_pwt_bridge(data, deflator_df, bridge_freeze_year, YEAR_END)

    if bridge_result and bridge_result.get("methods"):
        for method, mdata in bridge_result["methods"].items():
            comp = mdata["comparison"]
            if len(comp) > 0:
                logger.info(f"Bridge ({method}): {len(comp)} years")
                logger.info(f"  Mean |error|: {comp['pct_diff'].abs().mean():.1f}%")
                logger.info(f"  Max |error|: {comp['pct_diff'].abs().max():.1f}%")
            else:
                logger.warning(f"Bridge ({method}): no comparison data")
    else:
        logger.warning("Bridge test produced no results")

    # ------------------------------------------------------------------
    # Phase 4: CPI extrapolation
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 4: CPI extrapolation accuracy")
    logger.info("=" * 70)

    extrap_df = test_cpi_extrapolation(ts_constant, deflator_df, EXTRAP_BASE_YEARS)

    if len(extrap_df) > 0:
        logger.info(f"Extrapolation tests: {len(extrap_df)}")
        logger.info(f"  Mean correction: {extrap_df['correction_pct'].mean():+.1f}%")
        logger.info(f"  Std correction: {extrap_df['correction_pct'].std():.1f}%")
        within_5 = (extrap_df['correction_pct'].abs() <= 5).sum()
        logger.info(f"  Within ±5%: {within_5}/{len(extrap_df)}")
    else:
        logger.warning("No extrapolation comparisons available")

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("Generating plots")
    logger.info("=" * 70)

    plot_paths = generate_plots(
        ts_constant, ts_nominal, window_results, bridge_result,
        extrap_df, deflator_df, OUTPUT_DIR
    )

    config_info = {
        "pwt_version": pwt_version or "default",
        "year_start": YEAR_START,
        "year_end": YEAR_END,
        "series_min_countries": SERIES_MIN_COUNTRIES,
        "min_coverage_pct": MIN_COVERAGE_PCT,
        "weighting": WEIGHTING,
        "window_sizes": WINDOW_SIZES,
        "bridge_freeze_year": bridge_freeze_year,
    }

    return {
        "ts_constant": ts_constant,
        "ts_nominal": ts_nominal,
        "stable_countries": stable_countries,
        "coverage_df": coverage_df,
        "window_results": window_results,
        "bridge_result": bridge_result,
        "extrap_df": extrap_df,
        "plot_paths": plot_paths,
        "config_info": config_info,
    }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    global logger
    script_name = Path(__file__).parent.name
    logger = setup_logging(script_name, output_dir=OUTPUT_DIR)

    logger.info(f"Production Methodology Study — PWT 11.0, {YEAR_START}–{YEAR_END}")

    with ScriptContext(script_name, output_dir=OUTPUT_DIR) as ctx:
        try:
            results = run_production()

            if results is None:
                ctx.error("Pipeline returned no results")
                return 1

            report = generate_report(
                ts_constant=results["ts_constant"],
                ts_nominal=results["ts_nominal"],
                stable_countries=results["stable_countries"],
                coverage_df=results["coverage_df"],
                window_results=results["window_results"],
                bridge_result=results["bridge_result"],
                extrap_df=results["extrap_df"],
                plot_paths=results["plot_paths"],
                config_info=results["config_info"],
            )

            reports_dir = OUTPUT_DIR / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"production_{timestamp}.md"
            report_path.write_text(report)

            tc = results["ts_constant"]
            tn = results["ts_nominal"]

            logger.info("=" * 60)
            logger.info(f"Constant CHIP mean: ${tc['chip_value'].mean():.2f}/hr")
            logger.info(f"Nominal CHIP mean:  ${tn['chip_value'].mean():.2f}/hr")
            logger.info(f"Stable panel: {len(results['stable_countries'])} countries")
            logger.info(f"Plots: {len(results['plot_paths'])} saved")
            logger.info(f"Report: {report_path}")
            logger.info("=" * 60)

            ctx.set_result("n_years", len(tc))
            ctx.set_result("mean_constant_chip", float(tc["chip_value"].mean()))
            ctx.set_result("mean_nominal_chip", float(tn["chip_value"].mean()))
            ctx.set_result("n_stable_countries", len(results["stable_countries"]))

            if results["bridge_result"] and results["bridge_result"].get("methods"):
                for method, mdata in results["bridge_result"]["methods"].items():
                    comp = mdata["comparison"]
                    if len(comp) > 0:
                        ctx.set_result(f"bridge_{method}_mean_error_pct",
                                       float(comp["pct_diff"].abs().mean()))

            if len(results["extrap_df"]) > 0:
                ctx.set_result("extrap_correction_std_pct",
                               float(results["extrap_df"]["correction_pct"].std()))

            return 0

        except Exception as e:
            logger.exception("Pipeline failed")
            ctx.error(str(e))
            return 1


if __name__ == "__main__":
    sys.exit(main())

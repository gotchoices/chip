#!/usr/bin/env python3
"""
Aggregation Weighting Method Comparison

Tests sensitivity of global CHIP to five aggregation weighting schemes:
GDP, labor-force, freedom, HDI, and unweighted.  Produces country-specific
multipliers for the recommended scheme.

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
from lib import fetcher, normalize, pipeline, aggregate
from lib.config import load_config

logger = get_logger(__name__)

OUTPUT_DIR = STUDY_DIR / "output"


# =============================================================================
# CONFIGURATION
# =============================================================================

YEAR_START = 2000
YEAR_END = 2022         # Last full year in PWT 11.0
FOCUS_YEAR = 2022       # Primary year for cross-sectional comparison
WINDOW_YEARS = range(2018, 2023)  # 5-year trailing window for averages
ENABLE_IMPUTATION = True
WAGE_AVERAGING_METHOD = "simple"


# =============================================================================
# PIPELINE: COUNTRY-LEVEL CHIP VALUES
# =============================================================================

def run_chip_pipeline(data, deflator_df):
    """Run the CHIP pipeline and return per-country-year estimation data."""
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
    return est_data


def aggregate_country_chip(est_data, years):
    """
    Aggregate to one row per country, averaging over the given years.

    Returns DataFrame with: country, chip_value, elementary_wage, theta,
    alpha, mpl, gdp, employment, n_years.
    """
    subset = est_data[est_data["year"].isin(years)].copy()
    logger.info(f"Aggregating over years {min(years)}-{max(years)}: "
                f"{len(subset)} obs, {subset['country'].nunique()} countries")

    agg_spec = {
        "chip_value": "mean",
        "elementary_wage": "mean",
        "theta": "mean",
        "alpha": "mean",
        "mpl": "mean",
        "rgdpna": "mean",
    }

    # Include employment if available (from PWT merge)
    emp_col = None
    for candidate in ["employment", "emp"]:
        if candidate in subset.columns:
            emp_col = candidate
            agg_spec[candidate] = "mean"
            break

    agg_spec["year"] = "count"

    country_data = subset.groupby("country").agg(agg_spec).reset_index()

    # Standardize column names
    rename = {"rgdpna": "gdp", "year": "n_years"}
    if emp_col and emp_col != "employment":
        rename[emp_col] = "employment"
    country_data = country_data.rename(columns=rename)

    logger.info(f"Aggregated to {len(country_data)} countries")
    return country_data


# =============================================================================
# MERGE EXTERNAL INDICES
# =============================================================================

def _build_name_to_iso_map():
    """
    Build a country-name → ISO-3166 mapping using PWT as the bridge.
    PWT has both 'countrycode' (ISO) and 'country' (full name).
    """
    pwt_raw = fetcher.get_pwt()
    name_map = {}

    # PWT column names before normalization
    code_col = "countrycode" if "countrycode" in pwt_raw.columns else "isocode"
    name_col = "country"

    if code_col not in pwt_raw.columns or name_col not in pwt_raw.columns:
        return name_map

    for _, row in pwt_raw[[code_col, name_col]].drop_duplicates().iterrows():
        iso = str(row[code_col]).strip().upper()
        name = str(row[name_col]).strip().lower()
        if iso and name and len(iso) == 3:
            name_map[name] = iso

    # Heritage-specific name variants that differ from PWT
    heritage_aliases = {
        "the bahamas": "BHS",
        "bahamas": "BHS",
        "brunei": "BRN",
        "brunei darussalam": "BRN",
        "burma": "MMR",
        "myanmar": "MMR",
        "cabo verde": "CPV",
        "cape verde": "CPV",
        "congo, dem. rep.": "COD",
        "congo, democratic republic of the": "COD",
        "democratic republic of congo": "COD",
        "congo, rep.": "COG",
        "congo, republic of": "COG",
        "republic of congo": "COG",
        "côte d'ivoire": "CIV",
        "cote d'ivoire": "CIV",
        "ivory coast": "CIV",
        "czech republic": "CZE",
        "czechia": "CZE",
        "eswatini": "SWZ",
        "swaziland": "SWZ",
        "iran": "IRN",
        "iran, islamic republic of": "IRN",
        "korea, south": "KOR",
        "south korea": "KOR",
        "korea, republic of": "KOR",
        "korea, north": "PRK",
        "north korea": "PRK",
        "korea, dem. people's rep.": "PRK",
        "kyrgyz republic": "KGZ",
        "kyrgyzstan": "KGZ",
        "lao p.d.r.": "LAO",
        "laos": "LAO",
        "micronesia": "FSM",
        "north macedonia": "MKD",
        "russia": "RUS",
        "russian federation": "RUS",
        "são tomé and príncipe": "STP",
        "sao tome and principe": "STP",
        "slovak republic": "SVK",
        "slovakia": "SVK",
        "syria": "SYR",
        "taiwan": "TWN",
        "timor-leste": "TLS",
        "east timor": "TLS",
        "türkiye": "TUR",
        "turkey": "TUR",
        "venezuela": "VEN",
        "vietnam": "VNM",
        "viet nam": "VNM",
        "yemen": "YEM",
    }

    for alias, iso in heritage_aliases.items():
        if alias not in name_map:
            name_map[alias] = iso

    return name_map


def merge_freedom_scores(country_data):
    """Merge Heritage Foundation freedom scores onto country data."""
    try:
        freedom = fetcher.get_freedom_index()
    except Exception as e:
        logger.warning(f"Could not fetch freedom index: {e}")
        return country_data

    # Build name → ISO mapping using PWT + manual aliases
    name_to_iso = _build_name_to_iso_map()

    # Convert Heritage names to ISO codes
    freedom = freedom.copy()
    freedom["iso_mapped"] = freedom["country"].str.lower().str.strip().map(name_to_iso)

    # Build ISO → freedom_score lookup
    iso_scores = dict(zip(
        freedom["iso_mapped"].dropna(),
        freedom.loc[freedom["iso_mapped"].notna(), "freedom_score"]
    ))

    country_data = country_data.copy()
    country_data["freedom_score"] = country_data["country"].map(iso_scores)

    matched = country_data["freedom_score"].notna().sum()
    total = len(country_data)
    logger.info(f"Freedom scores: matched {matched}/{total} countries "
                f"({matched/total:.0%})")

    if matched < total:
        unmatched = country_data[country_data["freedom_score"].isna()]["country"].tolist()
        logger.debug(f"  Unmatched: {unmatched[:10]}")

    return country_data


def merge_hdi_scores(country_data, target_year=FOCUS_YEAR):
    """Merge UNDP HDI scores onto country data."""
    try:
        hdi = fetcher.get_hdi()
    except Exception as e:
        logger.warning(f"Could not fetch HDI data: {e}")
        return country_data

    # Use target year data, falling back to nearest available year
    hdi_year = hdi[hdi["year"] == target_year]
    if len(hdi_year) == 0:
        available_years = sorted(hdi["year"].unique())
        closest = min(available_years, key=lambda y: abs(y - target_year))
        logger.warning(f"No HDI data for {target_year}, using {closest}")
        hdi_year = hdi[hdi["year"] == closest]

    # Primary match: ISO code (our pipeline uses 3-letter ISO codes)
    iso_lookup = {}
    if "isocode" in hdi_year.columns:
        iso_lookup = dict(zip(
            hdi_year["isocode"].str.upper().str.strip(),
            hdi_year["hdi"]
        ))

    country_data = country_data.copy()
    country_data["hdi"] = country_data["country"].str.upper().str.strip().map(iso_lookup)

    matched = country_data["hdi"].notna().sum()
    total = len(country_data)
    logger.info(f"HDI scores: matched {matched}/{total} countries "
                f"({matched/total:.0%})")

    return country_data


# =============================================================================
# WEIGHTING COMPARISON
# =============================================================================

def run_all_weightings(country_data):
    """
    Apply all five weighting schemes and return results.

    Returns:
        dict mapping scheme name -> AggregateResult
    """
    results = {}

    # 1. GDP-weighted (original method)
    try:
        results["gdp_weighted"] = aggregate.gdp_weighted(country_data)
    except Exception as e:
        logger.warning(f"GDP-weighted failed: {e}")

    # 2. Labor-force weighted
    if "employment" in country_data.columns:
        try:
            results["labor_weighted"] = aggregate.labor_weighted(country_data)
        except Exception as e:
            logger.warning(f"Labor-weighted failed: {e}")
    else:
        logger.warning("No employment column — skipping labor-weighted")

    # 3. Unweighted
    try:
        results["unweighted"] = aggregate.unweighted(country_data)
    except Exception as e:
        logger.warning(f"Unweighted failed: {e}")

    # 4. Freedom-weighted
    if "freedom_score" in country_data.columns and country_data["freedom_score"].notna().any():
        try:
            results["freedom_weighted"] = aggregate.freedom_weighted(country_data)
        except Exception as e:
            logger.warning(f"Freedom-weighted failed: {e}")
    else:
        logger.warning("No freedom scores — skipping freedom-weighted")

    # 5. HDI-weighted
    if "hdi" in country_data.columns and country_data["hdi"].notna().any():
        try:
            results["hdi_weighted"] = aggregate.hdi_weighted(country_data)
        except Exception as e:
            logger.warning(f"HDI-weighted failed: {e}")
    else:
        logger.warning("No HDI scores — skipping HDI-weighted")

    return results


def build_comparison_table(results):
    """Build a summary comparison table from weighting results."""
    rows = []
    for name, r in results.items():
        rows.append({
            "scheme": name,
            "chip_value": r.chip_value,
            "n_countries": r.n_countries,
            "top_contributor": r.metadata.get("top_contributor", ""),
            "top_pct": r.metadata.get("top_contribution_pct", 0),
        })

    df = pd.DataFrame(rows).sort_values("chip_value", ascending=False)
    return df


def compute_country_multipliers(country_data, global_chip, scheme_name):
    """
    Compute per-country multiplier = country_chip / global_chip.

    A multiplier of 1.0 means the country matches the global average.
    Values >1 mean workers are paid above the global CHIP; <1 means below.
    """
    df = country_data[["country", "chip_value"]].copy()
    df["multiplier"] = df["chip_value"] / global_chip
    df["scheme"] = scheme_name
    df = df.sort_values("multiplier", ascending=False).reset_index(drop=True)
    return df


# =============================================================================
# PLOTS
# =============================================================================

def generate_plots(comparison_df, results, country_data, multipliers, output_dir):
    """Generate all study plots."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    plot_paths = []

    # ---- Plot 1: CHIP by weighting scheme (bar chart) ----
    fig, ax = plt.subplots(figsize=(10, 6))
    schemes = comparison_df["scheme"].values
    values = comparison_df["chip_value"].values
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]
    bars = ax.bar(range(len(schemes)), values, color=colors[:len(schemes)])
    ax.set_xticks(range(len(schemes)))
    ax.set_xticklabels([s.replace("_", "\n") for s in schemes], fontsize=9)
    ax.set_ylabel("Global CHIP ($/hour)")
    ax.set_title("CHIP Value by Weighting Scheme")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"${val:.2f}", ha="center", va="bottom", fontsize=10,
                fontweight="bold")
    ax.set_ylim(0, max(values) * 1.15)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = plots_dir / "chip_by_scheme.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    plot_paths.append(path)
    logger.info(f"  Plot 1: {path.name}")

    # ---- Plot 2: Top-10 contributors for each scheme ----
    n_schemes = len(results)
    fig, axes = plt.subplots(1, min(n_schemes, 5), figsize=(4 * min(n_schemes, 5), 8),
                              sharey=False)
    if n_schemes == 1:
        axes = [axes]

    for idx, (name, r) in enumerate(results.items()):
        if idx >= 5:
            break
        ax = axes[idx]
        top10 = r.contributions.head(10).copy()
        top10 = top10.sort_values("contribution", ascending=True)
        ax.barh(range(len(top10)), top10["weight"] * 100, color=colors[idx])
        ax.set_yticks(range(len(top10)))
        ax.set_yticklabels(top10["country"].values, fontsize=8)
        ax.set_xlabel("Weight %")
        ax.set_title(name.replace("_", "\n"), fontsize=9)

    fig.suptitle("Top 10 Country Weights by Scheme", fontsize=12, y=1.02)
    fig.tight_layout()
    path = plots_dir / "top10_by_scheme.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    plot_paths.append(path)
    logger.info(f"  Plot 2: {path.name}")

    # ---- Plot 3: Country multiplier distribution ----
    fig, ax = plt.subplots(figsize=(10, 6))
    m = multipliers["multiplier"].values
    ax.hist(m, bins=30, color="#2196F3", edgecolor="white", alpha=0.8)
    ax.axvline(1.0, color="red", linestyle="--", linewidth=2, label="Global average (1.0)")
    ax.set_xlabel("Country Multiplier (country CHIP / global CHIP)")
    ax.set_ylabel("Number of Countries")
    ax.set_title("Distribution of Country Multipliers (GDP-weighted)")
    ax.legend()

    median_m = np.median(m)
    ax.axvline(median_m, color="orange", linestyle=":", linewidth=1.5,
               label=f"Median: {median_m:.2f}")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = plots_dir / "multiplier_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    plot_paths.append(path)
    logger.info(f"  Plot 3: {path.name}")

    # ---- Plot 4: Top/bottom 15 country multipliers ----
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))

    top15 = multipliers.head(15).copy().sort_values("multiplier", ascending=True)
    ax1.barh(range(len(top15)), top15["multiplier"], color="#4CAF50")
    ax1.set_yticks(range(len(top15)))
    ax1.set_yticklabels(top15["country"], fontsize=9)
    ax1.set_xlabel("Multiplier")
    ax1.set_title("Top 15 — Above Global Average")
    ax1.axvline(1.0, color="red", linestyle="--", alpha=0.5)

    bot15 = multipliers.tail(15).copy().sort_values("multiplier", ascending=False)
    ax2.barh(range(len(bot15)), bot15["multiplier"], color="#F44336")
    ax2.set_yticks(range(len(bot15)))
    ax2.set_yticklabels(bot15["country"], fontsize=9)
    ax2.set_xlabel("Multiplier")
    ax2.set_title("Bottom 15 — Below Global Average")
    ax2.axvline(1.0, color="red", linestyle="--", alpha=0.5)

    fig.suptitle("Country CHIP Multipliers (GDP-weighted)", fontsize=12)
    fig.tight_layout()
    path = plots_dir / "multiplier_top_bottom.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    plot_paths.append(path)
    logger.info(f"  Plot 4: {path.name}")

    return plot_paths


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(comparison_df, results, country_data, multipliers,
                    plot_paths, config_info):
    """Generate Markdown report."""
    lines = []
    lines.append("# Aggregation Weighting Study — Report")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"\nPWT version: {config_info.get('pwt_version', '11.0')}")
    lines.append(f"Focus year: {config_info.get('focus_year', FOCUS_YEAR)}")
    lines.append(f"Window: {config_info.get('window', '2018-2022')}")
    lines.append(f"Countries in pipeline: {len(country_data)}")

    # Comparison table
    lines.append("\n## Weighting Scheme Comparison\n")
    lines.append("| Scheme | CHIP ($/hr) | Countries | Top Contributor | Top Weight |")
    lines.append("|--------|------------|-----------|-----------------|------------|")
    for _, row in comparison_df.iterrows():
        lines.append(
            f"| {row['scheme']} | ${row['chip_value']:.2f} | "
            f"{row['n_countries']} | {row['top_contributor']} | "
            f"{row['top_pct']:.1f}% |"
        )

    # Sensitivity
    chip_vals = comparison_df["chip_value"].dropna()
    if len(chip_vals) > 1:
        lines.append("\n## Sensitivity Analysis\n")
        lines.append(f"- Range: ${chip_vals.min():.2f} – ${chip_vals.max():.2f}")
        lines.append(f"- Spread: ${chip_vals.max() - chip_vals.min():.2f} "
                      f"({(chip_vals.max() - chip_vals.min()) / chip_vals.mean() * 100:.1f}%)")
        lines.append(f"- Mean across schemes: ${chip_vals.mean():.2f}")
        lines.append(f"- Coefficient of variation: {chip_vals.std() / chip_vals.mean() * 100:.1f}%")

    # Country multipliers
    lines.append("\n## Country Multipliers (GDP-weighted)\n")
    lines.append("A multiplier of 1.0 = global average. Above 1.0 = workers paid "
                 "more than global CHIP; below 1.0 = paid less.\n")
    lines.append("| Rank | Country | CHIP ($/hr) | Multiplier |")
    lines.append("|------|---------|------------|------------|")
    for rank, (_, row) in enumerate(multipliers.iterrows(), 1):
        lines.append(
            f"| {rank} | {row['country']} | "
            f"${row['chip_value']:.2f} | {row['multiplier']:.2f} |"
        )

    # Plots
    if plot_paths:
        lines.append("\n## Plots\n")
        for p in plot_paths:
            lines.append(f"- `{p.name}`")

    return "\n".join(lines)


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_weighting():
    """Execute the weighting study."""

    # Load config
    config_path = STUDY_DIR / "config.yaml"
    config = load_config(config_path) if config_path.exists() else load_config()
    pwt_version = getattr(config.data, "pwt_version", None) or "11.0"

    logger.info(f"PWT version: {pwt_version}")
    logger.info(f"Year range: {YEAR_START}–{YEAR_END}, focus: {FOCUS_YEAR}")

    # ------------------------------------------------------------------
    # Fetch data
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("Fetching data sources")
    logger.info("=" * 70)

    data = fetcher.get_all(pwt_version=pwt_version)
    deflator_df = normalize.normalize_deflator(data["deflator"])

    # ------------------------------------------------------------------
    # Phase 1: Run CHIP pipeline
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 1: Running CHIP pipeline")
    logger.info("=" * 70)

    est_data = run_chip_pipeline(data, deflator_df)
    logger.info(f"Pipeline: {len(est_data)} obs, "
                f"{est_data['country'].nunique()} countries, "
                f"years {est_data['year'].min()}-{est_data['year'].max()}")

    # Aggregate to country level over window years
    country_data = aggregate_country_chip(est_data, WINDOW_YEARS)

    # ------------------------------------------------------------------
    # Phase 2: Merge external indices
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 2: Merging freedom and HDI scores")
    logger.info("=" * 70)

    country_data = merge_freedom_scores(country_data)
    country_data = merge_hdi_scores(country_data, target_year=FOCUS_YEAR)

    # Log merge summary
    logger.info(f"Final country data: {len(country_data)} countries")
    for col in ["gdp", "employment", "freedom_score", "hdi"]:
        if col in country_data.columns:
            n = country_data[col].notna().sum()
            logger.info(f"  {col}: {n}/{len(country_data)} non-null")

    # ------------------------------------------------------------------
    # Phase 3: Apply all weighting schemes
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 3: Weighting comparison")
    logger.info("=" * 70)

    results = run_all_weightings(country_data)
    comparison_df = build_comparison_table(results)

    logger.info("\nWeighting comparison:")
    for _, row in comparison_df.iterrows():
        logger.info(f"  {row['scheme']:20s}: ${row['chip_value']:.2f}/hr "
                     f"({row['n_countries']} countries)")

    # Sensitivity
    chip_vals = comparison_df["chip_value"].dropna()
    if len(chip_vals) > 1:
        spread = chip_vals.max() - chip_vals.min()
        cv = chip_vals.std() / chip_vals.mean() * 100
        logger.info(f"\n  Spread: ${spread:.2f} ({spread/chip_vals.mean()*100:.1f}%)")
        logger.info(f"  CV: {cv:.1f}%")

    # ------------------------------------------------------------------
    # Phase 4: Country multipliers
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("PHASE 4: Country multipliers")
    logger.info("=" * 70)

    # Use GDP-weighted as reference (original methodology)
    if "gdp_weighted" in results:
        global_chip = results["gdp_weighted"].chip_value
        multipliers = compute_country_multipliers(
            country_data, global_chip, "gdp_weighted"
        )
        logger.info(f"GDP-weighted global CHIP: ${global_chip:.2f}/hr")
        logger.info(f"Multiplier range: {multipliers['multiplier'].min():.2f} – "
                     f"{multipliers['multiplier'].max():.2f}")
        logger.info(f"Median multiplier: {multipliers['multiplier'].median():.2f}")

        # Top and bottom 5
        logger.info("\nTop 5 multipliers:")
        for _, row in multipliers.head(5).iterrows():
            logger.info(f"  {row['country']:30s}: {row['multiplier']:.2f} "
                         f"(${row['chip_value']:.2f}/hr)")
        logger.info("Bottom 5 multipliers:")
        for _, row in multipliers.tail(5).iterrows():
            logger.info(f"  {row['country']:30s}: {row['multiplier']:.2f} "
                         f"(${row['chip_value']:.2f}/hr)")
    else:
        global_chip = chip_vals.mean()
        multipliers = compute_country_multipliers(
            country_data, global_chip, "mean_all_schemes"
        )

    # ------------------------------------------------------------------
    # Save outputs
    # ------------------------------------------------------------------
    logger.info("=" * 70)
    logger.info("Saving outputs")
    logger.info("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # CSV exports
    csv_dir = OUTPUT_DIR / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)

    comparison_df.to_csv(csv_dir / "scheme_comparison.csv", index=False)
    multipliers.to_csv(csv_dir / "country_multipliers.csv", index=False)
    country_data.to_csv(csv_dir / "country_data.csv", index=False)

    logger.info(f"  Saved CSVs to {csv_dir}")

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    logger.info("Generating plots")

    plot_paths = generate_plots(
        comparison_df, results, country_data, multipliers, OUTPUT_DIR
    )

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    config_info = {
        "pwt_version": pwt_version,
        "focus_year": FOCUS_YEAR,
        "window": f"{min(WINDOW_YEARS)}-{max(WINDOW_YEARS)}",
    }

    report = generate_report(
        comparison_df, results, country_data, multipliers,
        plot_paths, config_info
    )

    reports_dir = OUTPUT_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"weighting_{timestamp}.md"
    report_path.write_text(report)

    logger.info(f"  Report: {report_path}")

    return {
        "comparison_df": comparison_df,
        "results": results,
        "country_data": country_data,
        "multipliers": multipliers,
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

    logger.info("Aggregation Weighting Method Comparison")
    logger.info(f"PWT 11.0, {YEAR_START}–{YEAR_END}")

    with ScriptContext(script_name, output_dir=OUTPUT_DIR) as ctx:
        try:
            results = run_weighting()

            if results is None:
                ctx.error("Pipeline returned no results")
                return 1

            comp = results["comparison_df"]
            mult = results["multipliers"]

            logger.info("=" * 60)
            logger.info("SUMMARY")
            logger.info("=" * 60)
            for _, row in comp.iterrows():
                logger.info(f"  {row['scheme']:20s}: ${row['chip_value']:.2f}")
            logger.info(f"  Countries with multipliers: {len(mult)}")
            logger.info(f"  Plots: {len(results['plot_paths'])}")
            logger.info("=" * 60)

            ctx.set_result("n_schemes", len(comp))
            ctx.set_result("n_countries", len(mult))
            for _, row in comp.iterrows():
                ctx.set_result(f"chip_{row['scheme']}", float(row["chip_value"]))

            return 0

        except Exception as e:
            logger.exception("Study failed")
            ctx.error(str(e))
            return 1


if __name__ == "__main__":
    sys.exit(main())

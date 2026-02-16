#!/usr/bin/env python3
"""
Analyze Data Coverage

Purpose:
    Examine which countries have consistent data across which time periods.
    Identify data quality issues and gaps.
    
Outputs:
    - Markdown report with coverage analysis
    - JSON summary with key metrics

Usage:
    ./run.sh coverage
    ./run.sh coverage -v    # Run and view report
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.logging_config import ScriptContext
from lib import fetcher, normalize, clean

# Output directory
REPORTS_DIR = Path(__file__).parent.parent / "output" / "reports"


def _get_country_col(df):
    """Find the best country identifier column."""
    # Prefer isocode, fall back to country
    if "isocode" in df.columns:
        return "isocode"
    elif "country" in df.columns:
        return "country"
    elif "ref_area" in df.columns:
        return "ref_area"
    else:
        # Last resort: find any column with country-like data
        for col in df.columns:
            if "country" in col.lower() or "area" in col.lower():
                return col
        raise ValueError(f"No country column found. Available: {list(df.columns)}")


def analyze_source_coverage(data: dict, ctx) -> dict:
    """Analyze coverage for each data source."""
    
    coverage = {}
    
    # Employment
    ctx.log("Analyzing employment data...")
    emp = normalize.normalize_ilostat(data["employment"], "employment")
    emp_col = _get_country_col(emp)
    ctx.log(f"  Employment using column: {emp_col}")
    coverage["employment"] = {
        "df": emp,
        "country_col": emp_col,
        "countries": set(emp[emp_col].dropna().unique()),
        "years": set(emp["year"].dropna().astype(int).unique()),
        "rows": len(emp),
    }
    
    # Wages
    ctx.log("Analyzing wage data...")
    wages = normalize.normalize_ilostat(data["wages"], "wage")
    wage_col = _get_country_col(wages)
    ctx.log(f"  Wages using column: {wage_col}")
    coverage["wages"] = {
        "df": wages,
        "country_col": wage_col,
        "countries": set(wages[wage_col].dropna().unique()),
        "years": set(wages["year"].dropna().astype(int).unique()),
        "rows": len(wages),
    }
    
    # Hours
    ctx.log("Analyzing hours data...")
    hours = normalize.normalize_ilostat(data["hours"], "hours")
    hours_col = _get_country_col(hours)
    ctx.log(f"  Hours using column: {hours_col}")
    coverage["hours"] = {
        "df": hours,
        "country_col": hours_col,
        "countries": set(hours[hours_col].dropna().unique()),
        "years": set(hours["year"].dropna().astype(int).unique()),
        "rows": len(hours),
    }
    
    # PWT
    ctx.log("Analyzing PWT data...")
    pwt = normalize.normalize_pwt(data["pwt"])
    pwt_col = _get_country_col(pwt)
    ctx.log(f"  PWT using column: {pwt_col}")
    coverage["pwt"] = {
        "df": pwt,
        "country_col": pwt_col,
        "countries": set(pwt[pwt_col].dropna().unique()),
        "years": set(pwt["year"].dropna().astype(int).unique()),
        "rows": len(pwt),
    }
    
    return coverage


def analyze_overlap(coverage: dict, ctx) -> dict:
    """Analyze country overlap across sources."""
    
    ctx.log("Analyzing country overlap...")
    
    # Check if all sources use the same identifier type
    cols_used = {name: info["country_col"] for name, info in coverage.items()}
    unique_cols = set(cols_used.values())
    if len(unique_cols) > 1:
        ctx.warning(f"Mixed identifier types: {cols_used}")
        ctx.warning("Overlap analysis may be inaccurate - need to harmonize identifiers")
    
    emp_countries = coverage["employment"]["countries"]
    wage_countries = coverage["wages"]["countries"]
    hours_countries = coverage["hours"]["countries"]
    pwt_countries = coverage["pwt"]["countries"]
    
    # Log sample identifiers to help debug
    ctx.log(f"  Sample emp: {list(emp_countries)[:3]}")
    ctx.log(f"  Sample wage: {list(wage_countries)[:3]}")
    ctx.log(f"  Sample pwt: {list(pwt_countries)[:3]}")
    
    # Core overlap: countries in ALL sources
    all_sources = emp_countries & wage_countries & hours_countries & pwt_countries
    
    # Minimal for CHIP: employment + wages + PWT
    chip_viable = emp_countries & wage_countries & pwt_countries
    
    ctx.log(f"  Overlap (all sources): {len(all_sources)}")
    ctx.log(f"  CHIP-viable: {len(chip_viable)}")
    
    return {
        "all_sources": all_sources,
        "chip_viable": chip_viable,
        "missing_wages": emp_countries - wage_countries,
        "missing_pwt": emp_countries - pwt_countries,
        "identifier_types": cols_used,
    }


def analyze_temporal(coverage: dict) -> dict:
    """Analyze temporal coverage."""
    
    emp_years = coverage["employment"]["years"]
    wage_years = coverage["wages"]["years"]
    pwt_years = coverage["pwt"]["years"]
    
    common_years = emp_years & wage_years & pwt_years
    
    return {
        "emp_years": emp_years,
        "wage_years": wage_years,
        "pwt_years": pwt_years,
        "common_years": common_years,
        "recommended_range": (max(2000, min(common_years)), min(2019, max(common_years))) if common_years else None,
    }


def analyze_quality(coverage: dict, overlap: dict, ctx) -> dict:
    """Analyze data quality by country."""
    
    ctx.log("Analyzing data quality...")
    
    emp_df = coverage["employment"]["df"]
    emp_col = coverage["employment"]["country_col"]
    viable = overlap["chip_viable"]
    
    # Filter to viable countries
    emp_viable = emp_df[emp_df[emp_col].isin(viable)]
    
    # Count years per country
    years_per_country = emp_viable.groupby(emp_col)["year"].nunique()
    
    # Categorize
    return {
        "excellent": set(years_per_country[years_per_country >= 15].index),
        "good": set(years_per_country[(years_per_country >= 8) & (years_per_country < 15)].index),
        "fair": set(years_per_country[(years_per_country >= 3) & (years_per_country < 8)].index),
        "sparse": set(years_per_country[years_per_country < 3].index),
        "years_per_country": years_per_country.to_dict(),
    }


def generate_markdown_report(coverage: dict, overlap: dict, temporal: dict, quality: dict) -> str:
    """Generate markdown report content."""
    
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Header
    lines.append("# Data Coverage Analysis")
    lines.append("")
    lines.append(f"Generated: {timestamp}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Data Source Summary
    lines.append("## 📊 Data Source Summary")
    lines.append("")
    lines.append("| Source | Countries | Year Range | Rows |")
    lines.append("|--------|-----------|------------|------|")
    
    for name, info in coverage.items():
        years = sorted(info["years"])
        year_range = f"{min(years)}–{max(years)}" if years else "N/A"
        lines.append(f"| {name.upper()} | {len(info['countries'])} | {year_range} | {info['rows']:,} |")
    
    lines.append("")
    
    # Country Overlap
    lines.append("## 🔗 Country Overlap Analysis")
    lines.append("")
    lines.append("For CHIP estimation, we need:")
    lines.append("- Employment data (ILOSTAT)")
    lines.append("- Wage data (ILOSTAT)")
    lines.append("- Macro data (Penn World Tables)")
    lines.append("")
    lines.append("| Category | Count | Status |")
    lines.append("|----------|-------|--------|")
    lines.append(f"| In ALL sources | {len(overlap['all_sources'])} | ✓ Full coverage |")
    lines.append(f"| CHIP-viable (emp+wage+PWT) | {len(overlap['chip_viable'])} | ✓ Can estimate CHIP |")
    lines.append(f"| Missing wage data | {len(overlap['missing_wages'])} | ⚠ Excluded |")
    lines.append(f"| Missing PWT data | {len(overlap['missing_pwt'])} | ⚠ Excluded |")
    lines.append("")
    
    # List viable countries
    lines.append(f"### CHIP-Viable Countries ({len(overlap['chip_viable'])})")
    lines.append("")
    countries_sorted = sorted(overlap["chip_viable"])
    # Format in columns
    for i in range(0, len(countries_sorted), 6):
        row = ", ".join(countries_sorted[i:i+6])
        lines.append(f"{row}")
    lines.append("")
    
    # Year Coverage
    lines.append("## 📅 Year Coverage")
    lines.append("")
    lines.append("| Source | Year Range | # Years |")
    lines.append("|--------|------------|---------|")
    
    for name, years in [
        ("Employment", temporal["emp_years"]),
        ("Wages", temporal["wage_years"]),
        ("PWT", temporal["pwt_years"]),
        ("**Common (all)**", temporal["common_years"]),
    ]:
        if years:
            sorted_years = sorted(years)
            lines.append(f"| {name} | {min(sorted_years)}–{max(sorted_years)} | {len(years)} |")
        else:
            lines.append(f"| {name} | N/A | 0 |")
    
    lines.append("")
    
    if temporal["recommended_range"]:
        start, end = temporal["recommended_range"]
        lines.append(f"**Recommended analysis range: {start}–{end}**")
        lines.append("")
        lines.append("*(Common coverage, PWT available, recent data)*")
        lines.append("")
    
    # Data Quality Tiers
    lines.append("## 📈 Data Quality Tiers")
    lines.append("")
    lines.append("| Tier | Criteria | Countries | Recommendation |")
    lines.append("|------|----------|-----------|----------------|")
    lines.append(f"| 🟢 Excellent | 15+ years | {len(quality['excellent'])} | Use for all analyses |")
    lines.append(f"| 🔵 Good | 8–14 years | {len(quality['good'])} | Use for most analyses |")
    lines.append(f"| 🟡 Fair | 3–7 years | {len(quality['fair'])} | Use with caution |")
    lines.append(f"| 🔴 Sparse | < 3 years | {len(quality['sparse'])} | Consider excluding |")
    lines.append("")
    
    # List excellent countries with years
    if quality["excellent"]:
        lines.append("### Excellent Coverage Countries")
        lines.append("")
        lines.append("| Country | Years of Data |")
        lines.append("|---------|---------------|")
        for country in sorted(quality["excellent"])[:30]:
            years = quality["years_per_country"].get(country, 0)
            lines.append(f"| {country} | {years} |")
        if len(quality["excellent"]) > 30:
            lines.append(f"| ... | ({len(quality['excellent']) - 30} more) |")
        lines.append("")
    
    # Recommendations
    lines.append("## 💡 Recommendations")
    lines.append("")
    
    n_viable = len(overlap["chip_viable"])
    n_excellent = len(quality["excellent"])
    
    lines.append(f"1. **Country selection:** Use {n_excellent} 'excellent' countries for robust estimates, ")
    lines.append(f"   or all {n_viable} viable countries for broader coverage.")
    lines.append("")
    
    if temporal["recommended_range"]:
        start, end = temporal["recommended_range"]
        lines.append(f"2. **Year range:** Analyze {start}–{end} for best coverage. ")
        lines.append(f"   Note: PWT ends at 2019, limiting recent-year analysis.")
        lines.append("")
    
    n_sparse = len(quality["sparse"])
    if n_sparse > 0:
        lines.append(f"3. **Quality:** Consider excluding {n_sparse} countries with < 3 years of data.")
        lines.append("")
    
    lines.append("4. **Original study:** Excluded Nepal, Pakistan, Sri Lanka, Bangladesh, Egypt, Jordan, Palestine ")
    lines.append("   due to data quality concerns. Review if these appear in 'fair' or 'sparse' tiers.")
    lines.append("")
    
    # Summary box
    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **{n_viable}** countries viable for CHIP estimation")
    lines.append(f"- **{n_excellent}** excellent, **{len(quality['good'])}** good, **{len(quality['fair'])}** fair, **{n_sparse}** sparse")
    if temporal["recommended_range"]:
        lines.append(f"- **Recommended range:** {temporal['recommended_range'][0]}–{temporal['recommended_range'][1]}")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Analyze data coverage across sources."""
    
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with ScriptContext("coverage", log_to_file=True) as ctx:
        
        # Fetch data
        ctx.log("Fetching data from sources...")
        ctx.log("Loading data (this may take a moment on first run)...")
        data = fetcher.get_all()
        ctx.log(f"Fetched {len(data)} datasets")
        
        # Analyze
        ctx.log("Analyzing coverage...")
        coverage = analyze_source_coverage(data, ctx)
        overlap = analyze_overlap(coverage, ctx)
        temporal = analyze_temporal(coverage)
        quality = analyze_quality(coverage, overlap, ctx)
        
        # Store results
        ctx.set_result("viable_countries", len(overlap["chip_viable"]))
        ctx.set_result("all_source_countries", len(overlap["all_sources"]))
        ctx.set_result("excellent_countries", len(quality["excellent"]))
        ctx.set_result("sparse_countries", len(quality["sparse"]))
        if temporal["recommended_range"]:
            ctx.set_result("recommended_start", temporal["recommended_range"][0])
            ctx.set_result("recommended_end", temporal["recommended_range"][1])
        
        # Generate report
        ctx.log("Generating report...")
        report_content = generate_markdown_report(coverage, overlap, temporal, quality)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORTS_DIR / f"coverage_{timestamp}.md"
        with open(report_path, "w") as f:
            f.write(report_content)
        
        ctx.log(f"Report saved: {report_path}")
        ctx.log(f"Viable countries: {len(overlap['chip_viable'])}")
        ctx.log(f"Excellent quality: {len(quality['excellent'])}")
        if temporal["recommended_range"]:
            ctx.log(f"Recommended years: {temporal['recommended_range'][0]}–{temporal['recommended_range'][1]}")


if __name__ == "__main__":
    main()

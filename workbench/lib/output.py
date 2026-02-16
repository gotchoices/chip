"""
Output Generation

Utilities for generating reports, tables, and visualizations.

Capabilities:
    - Markdown reports with embedded tables
    - CSV/JSON data export
    - Summary statistics
    - Basic visualizations (matplotlib/plotly)

Design Principles:
    - Output formats are configurable
    - Reports are self-contained and reproducible
    - Include metadata (timestamp, parameters, data sources)

Public API:
    generate_report(results, path, format="md") -> Path
    to_table(df, format="markdown") -> str
    plot_chip_by_country(df, output_path) -> Path
    plot_time_series(df, output_path) -> Path
    summarize(results) -> dict
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# Default output directory (workbench-level fallback)
_DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "output"

# Active output directory (can be set per-study via set_output_dir)
_output_dir = _DEFAULT_OUTPUT_DIR


def set_output_dir(path: Path):
    """Set the output directory for subsequent calls."""
    global _output_dir
    _output_dir = Path(path)


def get_output_dir() -> Path:
    """Get the current output directory."""
    return _output_dir


def _ensure_output_dir(subdir: str = None) -> Path:
    """Ensure output directory exists."""
    path = _output_dir
    if subdir:
        path = path / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


# =============================================================================
# Report Generation
# =============================================================================

def generate_report(results: dict,
                    title: str = "CHIP Analysis Report",
                    output_path: Path = None,
                    format: str = "md") -> Path:
    """
    Generate a comprehensive analysis report.
    
    Args:
        results: Dict containing analysis results
            Expected keys: chip_value, model_name, parameters, diagnostics
        title: Report title
        output_path: Where to save (default: auto-generated)
        format: Output format ("md", "json", "html")
        
    Returns:
        Path to generated report
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = _ensure_output_dir("reports") / f"report_{timestamp}.{format}"
    
    if format == "md":
        content = _generate_markdown_report(results, title)
    elif format == "json":
        content = json.dumps(results, indent=2, default=str)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    with open(output_path, "w") as f:
        f.write(content)
    
    logger.info(f"Report saved to: {output_path}")
    return output_path


def _generate_markdown_report(results: dict, title: str) -> str:
    """Generate markdown report content."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        f"# {title}",
        "",
        f"Generated: {timestamp}",
        "",
        "---",
        "",
    ]
    
    # Main result
    if "chip_value" in results:
        lines.extend([
            "## CHIP Value",
            "",
            f"**${results['chip_value']:.2f}/hour**",
            "",
        ])
    
    # Model info
    if "model_name" in results:
        lines.extend([
            "## Model",
            "",
            f"Method: {results['model_name']}",
            "",
        ])
    
    # Parameters
    if "parameters" in results:
        lines.extend([
            "## Parameters",
            "",
            "| Parameter | Value |",
            "|-----------|-------|",
        ])
        for k, v in results["parameters"].items():
            lines.append(f"| {k} | {v} |")
        lines.append("")
    
    # Diagnostics
    if "diagnostics" in results:
        lines.extend([
            "## Diagnostics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ])
        for k, v in results["diagnostics"].items():
            if isinstance(v, float):
                lines.append(f"| {k} | {v:.4f} |")
            else:
                lines.append(f"| {k} | {v} |")
        lines.append("")
    
    # Country breakdown if available
    if "chip_by_country" in results:
        df = results["chip_by_country"]
        if isinstance(df, pd.DataFrame) and len(df) > 0:
            lines.extend([
                "## Country Breakdown",
                "",
                to_table(df.head(20)),
                "",
                f"*Showing top 20 of {len(df)} countries*",
                "",
            ])
    
    return "\n".join(lines)


# =============================================================================
# Table Formatting
# =============================================================================

def to_table(df: pd.DataFrame, format: str = "markdown") -> str:
    """
    Convert DataFrame to formatted table.
    
    Args:
        df: DataFrame to format
        format: Output format ("markdown", "csv", "latex")
        
    Returns:
        Formatted table as string
    """
    if format == "markdown":
        return df.to_markdown(index=False)
    elif format == "csv":
        return df.to_csv(index=False)
    elif format == "latex":
        return df.to_latex(index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")


# =============================================================================
# Data Export
# =============================================================================

def save_csv(df: pd.DataFrame, 
             name: str,
             subdir: str = "data") -> Path:
    """
    Save DataFrame to CSV.
    
    Args:
        df: DataFrame to save
        name: Base name for file (without extension)
        subdir: Subdirectory within output folder
        
    Returns:
        Path to saved file
    """
    path = _ensure_output_dir(subdir) / f"{name}.csv"
    df.to_csv(path, index=False)
    logger.info(f"Saved CSV: {path}")
    return path


def save_json(data: dict,
              name: str,
              subdir: str = "data") -> Path:
    """
    Save dict to JSON.
    
    Args:
        data: Dict to save
        name: Base name for file
        subdir: Subdirectory
        
    Returns:
        Path to saved file
    """
    path = _ensure_output_dir(subdir) / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved JSON: {path}")
    return path


# =============================================================================
# Visualization (Placeholder)
# =============================================================================

def plot_chip_by_country(df: pd.DataFrame,
                         chip_col: str = "chip_value",
                         country_col: str = "country",
                         output_path: Path = None,
                         top_n: int = 30) -> Path:
    """
    Create bar chart of CHIP values by country.
    
    Args:
        df: DataFrame with country-level CHIP values
        chip_col: Column with CHIP values
        country_col: Column with country names
        output_path: Where to save plot
        top_n: Number of countries to show
        
    Returns:
        Path to saved plot
    """
    try:
        import matplotlib.pyplot as plt
        
        # Sort and select top N
        plot_df = df.nlargest(top_n, chip_col)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.barh(plot_df[country_col], plot_df[chip_col])
        ax.set_xlabel("CHIP Value ($/hour)")
        ax.set_title(f"CHIP Value by Country (Top {top_n})")
        ax.invert_yaxis()
        
        if output_path is None:
            output_path = _ensure_output_dir("plots") / "chip_by_country.png"
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        logger.info(f"Saved plot: {output_path}")
        return output_path
        
    except ImportError:
        logger.warning("matplotlib not available for plotting")
        return None


def plot_time_series(df: pd.DataFrame,
                     value_col: str = "chip_value",
                     time_col: str = "year",
                     output_path: Path = None) -> Path:
    """
    Create time series plot of CHIP values.
    
    Args:
        df: DataFrame with time series data
        value_col: Column with values
        time_col: Column with time periods
        output_path: Where to save plot
        
    Returns:
        Path to saved plot
    """
    try:
        import matplotlib.pyplot as plt
        
        # Aggregate by time period
        ts = df.groupby(time_col)[value_col].mean().reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(ts[time_col], ts[value_col], marker='o')
        ax.set_xlabel("Year")
        ax.set_ylabel("CHIP Value ($/hour)")
        ax.set_title("CHIP Value Over Time")
        ax.grid(True, alpha=0.3)
        
        if output_path is None:
            output_path = _ensure_output_dir("plots") / "chip_time_series.png"
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        logger.info(f"Saved plot: {output_path}")
        return output_path
        
    except ImportError:
        logger.warning("matplotlib not available for plotting")
        return None


# =============================================================================
# Summary Statistics
# =============================================================================

def summarize(results: dict) -> dict:
    """
    Generate summary statistics from analysis results.
    
    Args:
        results: Analysis results dict
        
    Returns:
        Summary dict with key statistics
    """
    summary = {
        "timestamp": datetime.now().isoformat(),
    }
    
    if "chip_value" in results:
        summary["chip_value"] = results["chip_value"]
    
    if "model_name" in results:
        summary["model"] = results["model_name"]
    
    if "diagnostics" in results:
        summary.update(results["diagnostics"])
    
    if "chip_by_country" in results:
        df = results["chip_by_country"]
        if isinstance(df, pd.DataFrame):
            summary["n_countries"] = len(df)
            summary["chip_mean"] = df["chip_value"].mean()
            summary["chip_median"] = df["chip_value"].median()
            summary["chip_std"] = df["chip_value"].std()
    
    return summary

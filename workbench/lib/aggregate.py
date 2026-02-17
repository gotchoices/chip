"""
Global Aggregation

Methods for combining country-level CHIP values into a global estimate.

Available Weighting Schemes:
    - GDP-weighted: Weight by economic output (original study approach)
    - Labor-force weighted: Weight by number of workers
    - Freedom-weighted: Weight by Heritage Foundation economic freedom index
    - HDI-weighted: Weight by UNDP Human Development Index (standard of living)
    - Unweighted: Simple average across countries

Design Principles:
    - Each weighting scheme is a separate function
    - Functions return both the aggregate value and component breakdown
    - Easy to compare different weighting approaches

Public API:
    gdp_weighted(df, gdp_col="gdp") -> AggregateResult
    labor_weighted(df, labor_col="employment") -> AggregateResult
    freedom_weighted(df, freedom_col="freedom_score") -> AggregateResult
    hdi_weighted(df, hdi_col="hdi") -> AggregateResult
    unweighted(df) -> AggregateResult
    
    compare_weightings(df) -> pd.DataFrame  # Side-by-side comparison
"""

import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AggregateResult:
    """Standard output for aggregation methods."""
    chip_value: float              # Global CHIP value
    weighting_scheme: str          # Name of weighting method
    contributions: pd.DataFrame    # Country contributions to final value
    n_countries: int               # Number of countries included
    metadata: dict                 # Additional statistics


# =============================================================================
# Weighting Schemes
# =============================================================================

def gdp_weighted(df: pd.DataFrame,
                 chip_col: str = "chip_value",
                 gdp_col: str = "gdp") -> AggregateResult:
    """
    Calculate GDP-weighted global CHIP value.
    
    This is the original study approach. Countries with larger
    economies have more influence on the global average.
    
    Args:
        df: DataFrame with country-level CHIP values and GDP
        chip_col: Column with CHIP values
        gdp_col: Column with GDP values
        
    Returns:
        AggregateResult with global CHIP value
    """
    df = df.copy()
    
    if chip_col not in df.columns or gdp_col not in df.columns:
        raise ValueError(f"Required columns: {chip_col}, {gdp_col}")
    
    # Remove missing values
    df = df.dropna(subset=[chip_col, gdp_col])
    
    # Calculate weights
    total_gdp = df[gdp_col].sum()
    df["weight"] = df[gdp_col] / total_gdp
    
    # Weighted average
    chip_value = (df[chip_col] * df["weight"]).sum()
    
    # Contributions
    df["contribution"] = df[chip_col] * df["weight"]
    contributions = df[["country", chip_col, gdp_col, "weight", "contribution"]].copy()
    contributions = contributions.sort_values("contribution", ascending=False)
    
    metadata = {
        "total_gdp": total_gdp,
        "top_contributor": contributions.iloc[0]["country"],
        "top_contribution_pct": contributions.iloc[0]["weight"] * 100,
    }
    
    logger.info(f"GDP-weighted CHIP: ${chip_value:.2f}/hour "
                f"({len(df)} countries)")
    
    return AggregateResult(
        chip_value=chip_value,
        weighting_scheme="gdp_weighted",
        contributions=contributions,
        n_countries=len(df),
        metadata=metadata,
    )


def labor_weighted(df: pd.DataFrame,
                   chip_col: str = "chip_value",
                   labor_col: str = "employment") -> AggregateResult:
    """
    Calculate labor-force weighted global CHIP value.
    
    Countries with more workers have more influence.
    
    Args:
        df: DataFrame with country-level CHIP values and employment
        chip_col: Column with CHIP values
        labor_col: Column with employment/labor force
        
    Returns:
        AggregateResult with global CHIP value
    """
    df = df.copy()
    
    if chip_col not in df.columns or labor_col not in df.columns:
        raise ValueError(f"Required columns: {chip_col}, {labor_col}")
    
    df = df.dropna(subset=[chip_col, labor_col])
    
    # Calculate weights
    total_labor = df[labor_col].sum()
    df["weight"] = df[labor_col] / total_labor
    
    # Weighted average
    chip_value = (df[chip_col] * df["weight"]).sum()
    
    # Contributions
    df["contribution"] = df[chip_col] * df["weight"]
    contributions = df[["country", chip_col, labor_col, "weight", "contribution"]].copy()
    contributions = contributions.sort_values("contribution", ascending=False)
    
    metadata = {
        "total_labor": total_labor,
        "top_contributor": contributions.iloc[0]["country"],
        "top_contribution_pct": contributions.iloc[0]["weight"] * 100,
    }
    
    logger.info(f"Labor-weighted CHIP: ${chip_value:.2f}/hour "
                f"({len(df)} countries)")
    
    return AggregateResult(
        chip_value=chip_value,
        weighting_scheme="labor_weighted",
        contributions=contributions,
        n_countries=len(df),
        metadata=metadata,
    )


def freedom_weighted(df: pd.DataFrame,
                     chip_col: str = "chip_value",
                     freedom_col: str = "freedom_score",
                     gdp_col: str = "gdp") -> AggregateResult:
    """
    Calculate freedom-adjusted weighted CHIP value.
    
    Combines GDP weighting with economic freedom scores.
    More economically free countries are given higher weight,
    reflecting the CHIP ideal of a frictionless global economy.
    
    Args:
        df: DataFrame with CHIP values, GDP, and freedom scores
        chip_col: Column with CHIP values
        freedom_col: Column with economic freedom scores (0-100)
        gdp_col: Column with GDP values
        
    Returns:
        AggregateResult with global CHIP value
    """
    df = df.copy()
    
    required = [chip_col, freedom_col, gdp_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Required columns: {required}")
    
    df = df.dropna(subset=required)
    
    # Normalize freedom scores to 0-1 range
    df["freedom_norm"] = df[freedom_col] / 100.0
    
    # Combined weight: GDP × freedom score
    df["raw_weight"] = df[gdp_col] * df["freedom_norm"]
    total_weight = df["raw_weight"].sum()
    df["weight"] = df["raw_weight"] / total_weight
    
    # Weighted average
    chip_value = (df[chip_col] * df["weight"]).sum()
    
    # Contributions
    df["contribution"] = df[chip_col] * df["weight"]
    contributions = df[["country", chip_col, gdp_col, freedom_col, "weight", "contribution"]].copy()
    contributions = contributions.sort_values("contribution", ascending=False)
    
    metadata = {
        "mean_freedom_score": df[freedom_col].mean(),
        "top_contributor": contributions.iloc[0]["country"],
        "top_contribution_pct": contributions.iloc[0]["weight"] * 100,
    }
    
    logger.info(f"Freedom-weighted CHIP: ${chip_value:.2f}/hour "
                f"({len(df)} countries)")
    
    return AggregateResult(
        chip_value=chip_value,
        weighting_scheme="freedom_weighted",
        contributions=contributions,
        n_countries=len(df),
        metadata=metadata,
    )


def unweighted(df: pd.DataFrame,
               chip_col: str = "chip_value") -> AggregateResult:
    """
    Calculate simple unweighted average CHIP value.
    
    All countries contribute equally regardless of size.
    
    Args:
        df: DataFrame with country-level CHIP values
        chip_col: Column with CHIP values
        
    Returns:
        AggregateResult with global CHIP value
    """
    df = df.copy()
    
    if chip_col not in df.columns:
        raise ValueError(f"Required column: {chip_col}")
    
    df = df.dropna(subset=[chip_col])
    
    # Equal weights
    n = len(df)
    df["weight"] = 1.0 / n
    
    # Simple average
    chip_value = df[chip_col].mean()
    
    # Contributions
    df["contribution"] = df[chip_col] * df["weight"]
    contributions = df[["country", chip_col, "weight", "contribution"]].copy()
    contributions = contributions.sort_values("contribution", ascending=False)
    
    metadata = {
        "chip_std": df[chip_col].std(),
        "chip_min": df[chip_col].min(),
        "chip_max": df[chip_col].max(),
    }
    
    logger.info(f"Unweighted CHIP: ${chip_value:.2f}/hour "
                f"({len(df)} countries)")
    
    return AggregateResult(
        chip_value=chip_value,
        weighting_scheme="unweighted",
        contributions=contributions,
        n_countries=n,
        metadata=metadata,
    )


def hdi_weighted(df: pd.DataFrame,
                 chip_col: str = "chip_value",
                 hdi_col: str = "hdi") -> AggregateResult:
    """
    Calculate HDI-weighted global CHIP value.

    Countries with higher Human Development Index (standard of living)
    receive more weight, reflecting the premise that developed economies
    better approximate the free-market wage equilibrium.

    Args:
        df: DataFrame with country-level CHIP values and HDI scores
        chip_col: Column with CHIP values
        hdi_col: Column with HDI values (0-1 scale)

    Returns:
        AggregateResult with global CHIP value
    """
    df = df.copy()

    if chip_col not in df.columns or hdi_col not in df.columns:
        raise ValueError(f"Required columns: {chip_col}, {hdi_col}")

    df = df.dropna(subset=[chip_col, hdi_col])

    # Calculate weights (HDI is 0-1, directly usable as weight)
    total_hdi = df[hdi_col].sum()
    df["weight"] = df[hdi_col] / total_hdi

    # Weighted average
    chip_value = (df[chip_col] * df["weight"]).sum()

    # Contributions
    df["contribution"] = df[chip_col] * df["weight"]
    contributions = df[["country", chip_col, hdi_col, "weight", "contribution"]].copy()
    contributions = contributions.sort_values("contribution", ascending=False)

    metadata = {
        "mean_hdi": df[hdi_col].mean(),
        "top_contributor": contributions.iloc[0]["country"],
        "top_contribution_pct": contributions.iloc[0]["weight"] * 100,
    }

    logger.info(f"HDI-weighted CHIP: ${chip_value:.2f}/hour "
                f"({len(df)} countries)")

    return AggregateResult(
        chip_value=chip_value,
        weighting_scheme="hdi_weighted",
        contributions=contributions,
        n_countries=len(df),
        metadata=metadata,
    )


# =============================================================================
# Comparison
# =============================================================================

def compare_weightings(df: pd.DataFrame,
                       chip_col: str = "chip_value",
                       gdp_col: str = "gdp",
                       labor_col: str = "employment",
                       freedom_col: str = "freedom_score",
                       hdi_col: str = "hdi") -> pd.DataFrame:
    """
    Compare CHIP values across different weighting schemes.
    
    Returns DataFrame with:
        - scheme: Weighting scheme name
        - chip_value: Global CHIP value
        - n_countries: Number of countries included
        - notes: Any issues or caveats
    """
    results = []
    
    # Always calculate unweighted
    try:
        r = unweighted(df, chip_col)
        results.append({
            "scheme": r.weighting_scheme,
            "chip_value": r.chip_value,
            "n_countries": r.n_countries,
            "notes": "",
        })
    except Exception as e:
        results.append({"scheme": "unweighted", "chip_value": None, "notes": str(e)})
    
    # GDP-weighted
    if gdp_col in df.columns:
        try:
            r = gdp_weighted(df, chip_col, gdp_col)
            results.append({
                "scheme": r.weighting_scheme,
                "chip_value": r.chip_value,
                "n_countries": r.n_countries,
                "notes": "",
            })
        except Exception as e:
            results.append({"scheme": "gdp_weighted", "chip_value": None, "notes": str(e)})
    
    # Labor-weighted
    if labor_col in df.columns:
        try:
            r = labor_weighted(df, chip_col, labor_col)
            results.append({
                "scheme": r.weighting_scheme,
                "chip_value": r.chip_value,
                "n_countries": r.n_countries,
                "notes": "",
            })
        except Exception as e:
            results.append({"scheme": "labor_weighted", "chip_value": None, "notes": str(e)})
    
    # Freedom-weighted
    if freedom_col in df.columns:
        try:
            r = freedom_weighted(df, chip_col, freedom_col, gdp_col)
            results.append({
                "scheme": r.weighting_scheme,
                "chip_value": r.chip_value,
                "n_countries": r.n_countries,
                "notes": "",
            })
        except Exception as e:
            results.append({"scheme": "freedom_weighted", "chip_value": None, "notes": str(e)})
    
    # HDI-weighted
    if hdi_col in df.columns:
        try:
            r = hdi_weighted(df, chip_col, hdi_col)
            results.append({
                "scheme": r.weighting_scheme,
                "chip_value": r.chip_value,
                "n_countries": r.n_countries,
                "notes": "",
            })
        except Exception as e:
            results.append({"scheme": "hdi_weighted", "chip_value": None, "notes": str(e)})
    
    return pd.DataFrame(results)

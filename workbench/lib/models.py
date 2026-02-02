"""
Estimation Models

Various economic models for CHIP estimation.

Available Models:
    - Cobb-Douglas: Original study approach using production function
    - Direct wage: Simple wage averaging with PPP adjustment
    - CES: Constant Elasticity of Substitution (planned)
    - Stochastic frontier: Efficiency-based approach (planned)

Design Principles:
    - Each model is a function that takes cleaned data and returns estimates
    - Models return standardized output for easy comparison
    - Models log their assumptions and intermediate calculations

Public API:
    cobb_douglas(df, **params) -> ModelResult
    direct_wage(df, **params) -> ModelResult
    
    ModelResult:
        - chip_by_country: DataFrame with country-level CHIP values
        - parameters: dict of estimated parameters
        - diagnostics: dict of model diagnostics
"""

import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelResult:
    """Standard output format for all estimation models."""
    chip_by_country: pd.DataFrame  # Country-level CHIP values
    parameters: dict               # Estimated model parameters
    diagnostics: dict              # Model diagnostics and fit statistics
    model_name: str                # Name of the model used


# =============================================================================
# Cobb-Douglas Production Function
# =============================================================================

def cobb_douglas(df: pd.DataFrame,
                 estimate_alpha: bool = True,
                 default_alpha: float = 0.33,
                 use_fixed_effects: bool = True) -> ModelResult:
    """
    Estimate CHIP using Cobb-Douglas production function.
    
    This replicates the original study methodology:
    1. Estimate capital share (α) from labor share data
    2. Calculate Marginal Product of Labor (MPL)
    3. Calculate distortion factor (θ = MPL / wage)
    4. Derive distortion-free wage = wage × θ
    
    Args:
        df: Cleaned DataFrame with columns:
            - country, year
            - gdp, capital, employment (from PWT)
            - wage (unskilled wage from ILOSTAT)
            - human_capital (optional)
        estimate_alpha: If True, estimate α from data; else use default
        default_alpha: Capital share to use if not estimating
        use_fixed_effects: If True, use country fixed effects
        
    Returns:
        ModelResult with country-level CHIP values
    """
    df = df.copy()
    required = ["country", "year", "gdp", "capital", "employment", "wage"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Step 1: Estimate or set alpha (capital share)
    if estimate_alpha and "labor_share" in df.columns:
        # α = 1 - labor_share
        # Use fixed effects regression if requested
        if use_fixed_effects:
            alpha_by_country = _estimate_alpha_fe(df)
            df = df.merge(alpha_by_country, on="country", how="left")
            df["alpha"] = df["alpha"].fillna(default_alpha)
        else:
            df["alpha"] = 1 - df["labor_share"].fillna(1 - default_alpha)
    else:
        df["alpha"] = default_alpha
        logger.info(f"Using default alpha = {default_alpha}")
    
    # Step 2: Calculate efficient labor (L_s = L * h)
    if "human_capital" in df.columns:
        df["efficient_labor"] = df["employment"] * df["human_capital"]
    else:
        df["efficient_labor"] = df["employment"]
        logger.warning("No human capital data; using raw employment")
    
    # Step 3: Calculate MPL
    # MPL = (1 - α) * Y / L_s
    df["mpl"] = (1 - df["alpha"]) * df["gdp"] / df["efficient_labor"]
    
    # Step 4: Calculate distortion factor
    # θ = MPL / wage
    df["theta"] = df["mpl"] / df["wage"]
    
    # Step 5: Calculate distortion-free wage (CHIP value)
    # CHIP = wage * θ = MPL
    df["chip_value"] = df["wage"] * df["theta"]
    
    # Aggregate by country
    chip_by_country = df.groupby("country").agg({
        "chip_value": "mean",
        "theta": "mean",
        "alpha": "mean",
        "mpl": "mean",
        "wage": "mean",
        "gdp": "sum",
        "year": ["min", "max", "count"],
    }).reset_index()
    
    # Flatten column names
    chip_by_country.columns = [
        "country", "chip_value", "theta", "alpha", "mpl", "wage", 
        "total_gdp", "year_min", "year_max", "n_years"
    ]
    
    # Diagnostics
    diagnostics = {
        "n_countries": len(chip_by_country),
        "n_observations": len(df),
        "mean_alpha": df["alpha"].mean(),
        "mean_theta": df["theta"].mean(),
        "chip_mean": chip_by_country["chip_value"].mean(),
        "chip_std": chip_by_country["chip_value"].std(),
    }
    
    parameters = {
        "estimate_alpha": estimate_alpha,
        "default_alpha": default_alpha,
        "use_fixed_effects": use_fixed_effects,
    }
    
    logger.info(f"Cobb-Douglas: {diagnostics['n_countries']} countries, "
                f"mean CHIP = ${diagnostics['chip_mean']:.2f}")
    
    return ModelResult(
        chip_by_country=chip_by_country,
        parameters=parameters,
        diagnostics=diagnostics,
        model_name="cobb_douglas"
    )


def _estimate_alpha_fe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate country-specific capital shares using fixed effects.
    
    Uses the relationship: α = 1 - labor_share
    with country fixed effects to get stable estimates.
    """
    try:
        from linearmodels.panel import PanelOLS
        
        # Prepare panel data
        panel = df.set_index(["country", "year"])
        
        # Estimate with fixed effects
        # log(Y/L) = α * log(K/L) + country_fe
        panel["log_yl"] = np.log(panel["gdp"] / panel["employment"])
        panel["log_kl"] = np.log(panel["capital"] / panel["employment"])
        
        model = PanelOLS(panel["log_yl"], panel[["log_kl"]], entity_effects=True)
        result = model.fit()
        
        # Extract country effects and derive alpha
        alpha_global = result.params["log_kl"]
        
        alpha_by_country = pd.DataFrame({
            "country": df["country"].unique(),
            "alpha": alpha_global,
        })
        
        logger.info(f"Estimated global alpha = {alpha_global:.3f}")
        return alpha_by_country
        
    except ImportError:
        logger.warning("linearmodels not available; using mean labor share")
        alpha_by_country = df.groupby("country")["labor_share"].mean().reset_index()
        alpha_by_country["alpha"] = 1 - alpha_by_country["labor_share"]
        return alpha_by_country[["country", "alpha"]]


# =============================================================================
# Direct Wage Method
# =============================================================================

def direct_wage(df: pd.DataFrame,
                use_ppp: bool = True,
                hours_per_month: float = 173.33) -> ModelResult:
    """
    Estimate CHIP using direct wage averaging.
    
    A simpler approach that bypasses production function estimation:
    1. Take unskilled wages directly from ILOSTAT
    2. Convert to hourly rate
    3. Adjust for PPP if requested
    4. Average across countries
    
    Args:
        df: Cleaned DataFrame with columns:
            - country, year
            - wage (monthly unskilled wage)
            - Optional: ppp_factor for adjustment
        use_ppp: If True, adjust wages by PPP factor
        hours_per_month: Standard hours for monthly→hourly conversion
        
    Returns:
        ModelResult with country-level CHIP values
    """
    df = df.copy()
    
    if "wage" not in df.columns:
        raise ValueError("Missing required column: wage")
    
    # Convert to hourly
    df["hourly_wage"] = df["wage"] / hours_per_month
    
    # Apply PPP adjustment if available and requested
    if use_ppp and "ppp_factor" in df.columns:
        df["chip_value"] = df["hourly_wage"] * df["ppp_factor"]
    else:
        df["chip_value"] = df["hourly_wage"]
        if use_ppp:
            logger.warning("PPP adjustment requested but ppp_factor not available")
    
    # Aggregate by country
    chip_by_country = df.groupby("country").agg({
        "chip_value": "mean",
        "hourly_wage": "mean",
        "year": ["min", "max", "count"],
    }).reset_index()
    
    chip_by_country.columns = [
        "country", "chip_value", "hourly_wage",
        "year_min", "year_max", "n_years"
    ]
    
    diagnostics = {
        "n_countries": len(chip_by_country),
        "n_observations": len(df),
        "chip_mean": chip_by_country["chip_value"].mean(),
        "chip_std": chip_by_country["chip_value"].std(),
        "use_ppp": use_ppp,
    }
    
    parameters = {
        "use_ppp": use_ppp,
        "hours_per_month": hours_per_month,
    }
    
    logger.info(f"Direct wage: {diagnostics['n_countries']} countries, "
                f"mean CHIP = ${diagnostics['chip_mean']:.2f}")
    
    return ModelResult(
        chip_by_country=chip_by_country,
        parameters=parameters,
        diagnostics=diagnostics,
        model_name="direct_wage"
    )


# =============================================================================
# Placeholder for Future Models
# =============================================================================

def ces_production(df: pd.DataFrame, **params) -> ModelResult:
    """
    Constant Elasticity of Substitution production function.
    
    TODO: Implement CES model
    """
    raise NotImplementedError("CES model not yet implemented")


def stochastic_frontier(df: pd.DataFrame, **params) -> ModelResult:
    """
    Stochastic frontier analysis for efficiency-based estimation.
    
    TODO: Implement SFA model
    """
    raise NotImplementedError("Stochastic frontier model not yet implemented")

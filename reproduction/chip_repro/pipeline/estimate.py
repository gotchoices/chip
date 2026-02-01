"""
Estimation module for CHIP valuation.

Implements:
- Cobb-Douglas production function estimation with country fixed effects
- Marginal product of labor calculation
- Distortion factor computation
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger("chip.estimate")


class Estimator:
    """Estimates production function parameters and distortion factors."""
    
    def __init__(self, config: dict):
        """
        Initialize the estimator.
        
        Args:
            config: Configuration dictionary with estimation parameters
        """
        self.config = config
        self.estimation = config.get("estimation", {})
        
        self._alpha_estimates: pd.DataFrame | None = None
        self._valid_alpha_count = 0
    
    def estimate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Estimate country-specific capital shares (alpha).
        
        Uses the production function:
            ln(y) = alpha * ln(k) + epsilon
        
        where y = Y/L (output per worker) and k = K/L (capital per worker)
        
        Args:
            data: Cleaned and merged dataset
        
        Returns:
            DataFrame with country-level alpha estimates
        """
        logger.info("Estimating Cobb-Douglas production function...")
        
        # Prepare data for estimation
        est_data = self._prepare_estimation_data(data)
        
        # Estimate alpha for each country using OLS
        alphas = self._estimate_country_alphas(est_data)
        
        # Filter valid alphas (between 0 and 1)
        alphas = self._filter_valid_alphas(alphas)
        
        # Impute missing alphas
        alphas = self._impute_missing_alphas(alphas, est_data)
        
        self._alpha_estimates = alphas
        
        return alphas
    
    def calculate_mpl(self, data: pd.DataFrame, alphas: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate marginal product of labor and distortion factors.
        
        MPL = (1 - alpha) * (K / L)^alpha
        
        Distortion Factor = MPL / wage
        
        Args:
            data: Cleaned dataset
            alphas: Country-level alpha estimates
        
        Returns:
            DataFrame with MPL and distortion factors
        """
        logger.info("Calculating marginal product of labor...")
        
        # Merge alphas with data
        df = data.merge(alphas, on="country", how="left")
        
        # Calculate capital per effective worker
        df["k_per_l"] = df["rnna"] / df["effective_labor"]
        
        # Adjust for human capital
        if "hc" in df.columns:
            df["k_per_l_hc"] = df["k_per_l"] * df["hc"]
        else:
            df["k_per_l_hc"] = df["k_per_l"]
        
        # Calculate MPL using preferred specification (effective labor, national prices)
        # MPL = (1 - alpha) * k^alpha
        df["mpl"] = (1 - df["alpha"]) * np.power(df["k_per_l_hc"], df["alpha"])
        
        # Calculate average weighted wage
        df["avg_wage"] = df["wage_real"]
        
        # Calculate distortion factor (theta)
        # theta = MPL / wage
        df["distortion_factor"] = df["mpl"] / df["avg_wage"]
        
        # Calculate adjusted elementary wage
        # This is the CHIP value before global aggregation
        df["adjusted_wage"] = df["elementary_wage"] * df["distortion_factor"]
        
        # Filter valid observations
        df = df.dropna(subset=["mpl", "distortion_factor", "adjusted_wage"])
        
        logger.info(f"Calculated MPL for {len(df)} observations across {df['country'].nunique()} countries")
        
        return df
    
    def get_valid_alpha_count(self) -> int:
        """Return count of countries with valid alpha estimates."""
        return self._valid_alpha_count
    
    def _prepare_estimation_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for production function estimation."""
        df = data.copy()
        
        # Need: output (rgdpna or cgdpo), capital (rnna or cn), labor
        required_cols = ["country", "year", "effective_labor"]
        
        # Check for capital and output measures
        has_national = "rgdpna" in df.columns and "rnna" in df.columns
        has_ppp = "cgdpo" in df.columns and "cn" in df.columns
        
        if not has_national and not has_ppp:
            raise ValueError("Missing required capital/output columns")
        
        # Filter to observations with required data
        if has_national:
            df = df.dropna(subset=["rgdpna", "rnna", "effective_labor", "hc"])
        
        # Calculate log variables for estimation
        # Use effective labor adjusted by human capital
        if "hc" in df.columns:
            df["L_eff"] = df["effective_labor"] * df["hc"]
        else:
            df["L_eff"] = df["effective_labor"]
        
        # Output per effective worker
        if "rgdpna" in df.columns:
            df["y"] = df["rgdpna"] / df["L_eff"]
            df["ln_y"] = np.log(df["y"])
        
        # Capital per effective worker  
        if "rnna" in df.columns:
            df["k"] = df["rnna"] / df["L_eff"]
            df["ln_k"] = np.log(df["k"])
        
        # Filter valid observations
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna(subset=["ln_y", "ln_k"])
        
        logger.info(f"Estimation data: {len(df)} observations, {df['country'].nunique()} countries")
        
        return df
    
    def _estimate_country_alphas(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Estimate alpha for each country using OLS with country fixed effects.
        
        For each country j:
            ln(y_jt) = alpha_j * ln(k_jt) + epsilon_jt
        """
        results = []
        
        for country in data["country"].unique():
            country_data = data[data["country"] == country]
            
            if len(country_data) < 3:  # Need minimum observations
                continue
            
            try:
                # Simple OLS: ln(y) = alpha * ln(k)
                # Using numpy for simplicity (statsmodels would be more robust)
                X = country_data["ln_k"].values
                y = country_data["ln_y"].values
                
                # Add constant for intercept
                X_with_const = np.column_stack([np.ones(len(X)), X])
                
                # OLS estimation: beta = (X'X)^-1 X'y
                beta = np.linalg.lstsq(X_with_const, y, rcond=None)[0]
                alpha = beta[1]  # Coefficient on ln(k)
                
                results.append({
                    "country": country,
                    "alpha_raw": alpha,
                    "n_obs": len(country_data),
                })
                
            except Exception as e:
                logger.debug(f"Estimation failed for {country}: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def _filter_valid_alphas(self, alphas: pd.DataFrame) -> pd.DataFrame:
        """Filter alpha estimates to economically valid range (0, 1)."""
        alpha_min = self.estimation.get("alpha_min", 0.0)
        alpha_max = self.estimation.get("alpha_max", 1.0)
        
        # Mark valid alphas
        alphas["alpha_valid"] = (
            (alphas["alpha_raw"] > alpha_min) & 
            (alphas["alpha_raw"] < alpha_max)
        )
        
        # Set invalid alphas to NaN
        alphas["alpha"] = alphas["alpha_raw"].where(alphas["alpha_valid"], np.nan)
        
        valid_count = alphas["alpha_valid"].sum()
        total_count = len(alphas)
        
        self._valid_alpha_count = valid_count
        logger.info(f"Valid alpha estimates: {valid_count}/{total_count} countries")
        
        return alphas
    
    def _impute_missing_alphas(
        self, 
        alphas: pd.DataFrame, 
        est_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Impute missing alpha values using regression."""
        
        missing_mask = alphas["alpha"].isna()
        n_missing = missing_mask.sum()
        
        if n_missing == 0:
            return alphas
        
        logger.info(f"Imputing {n_missing} missing alpha values...")
        
        method = self.estimation.get("imputation_method", "mean")
        
        if method == "mean":
            # Simple mean imputation
            mean_alpha = alphas["alpha"].mean()
            alphas.loc[missing_mask, "alpha"] = mean_alpha
            
        elif method == "regression":
            # Use available alphas to predict missing ones
            # Based on country characteristics from the data
            
            # Get average characteristics per country
            country_chars = est_data.groupby("country").agg({
                "ln_y": "mean",
                "ln_k": "mean",
            }).reset_index()
            
            alphas_with_chars = alphas.merge(country_chars, on="country", how="left")
            
            # Fit regression on countries with valid alpha
            valid_data = alphas_with_chars[~missing_mask].dropna()
            
            if len(valid_data) >= 10:
                X = valid_data[["ln_y", "ln_k"]].values
                y = valid_data["alpha"].values
                
                X_const = np.column_stack([np.ones(len(X)), X])
                beta = np.linalg.lstsq(X_const, y, rcond=None)[0]
                
                # Predict for missing
                missing_data = alphas_with_chars[missing_mask]
                X_missing = missing_data[["ln_y", "ln_k"]].values
                X_missing_const = np.column_stack([np.ones(len(X_missing)), X_missing])
                
                predicted = X_missing_const @ beta
                
                # Clip to valid range
                predicted = np.clip(predicted, 0.01, 0.99)
                
                alphas.loc[missing_mask, "alpha"] = predicted
            else:
                # Fall back to mean
                mean_alpha = alphas["alpha"].mean()
                alphas.loc[missing_mask, "alpha"] = mean_alpha
        
        return alphas

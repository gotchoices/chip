"""
Aggregation module for CHIP valuation.

Aggregates country-level adjusted wages to a global CHIP value
using various weighting schemes.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger("chip.aggregate")


class Aggregator:
    """Aggregates country-level values to global CHIP estimate."""
    
    def __init__(self, config: dict):
        """
        Initialize the aggregator.
        
        Args:
            config: Configuration dictionary with aggregation parameters
        """
        self.config = config
        self.agg_config = config.get("aggregation", {})
        
        self.primary_weight = self.agg_config.get("primary_weight", "gdp")
        self.alternative_weights = self.agg_config.get("alternative_weights", [])
    
    def aggregate(self, data: pd.DataFrame) -> dict[str, Any]:
        """
        Aggregate country-level data to global CHIP value.
        
        Args:
            data: DataFrame with country-level MPL and adjusted wages
        
        Returns:
            Dictionary with CHIP values under different weighting schemes
        """
        logger.info("Aggregating to global CHIP value...")
        
        # Aggregate to country means (average across years)
        country_data = self._aggregate_to_country(data)
        
        # Calculate weights
        country_data = self._calculate_weights(country_data)
        
        # Calculate CHIP under each weighting scheme
        results = {}
        
        # Primary weighting
        results[f"chip_{self.primary_weight}"] = self._weighted_average(
            country_data, 
            f"weight_{self.primary_weight}"
        )
        
        # Alternative weightings
        for weight_type in self.alternative_weights:
            if f"weight_{weight_type}" in country_data.columns:
                results[f"chip_{weight_type}"] = self._weighted_average(
                    country_data,
                    f"weight_{weight_type}"
                )
        
        # Add summary statistics
        results["n_countries"] = len(country_data)
        results["n_observations"] = len(data)
        
        # Country-level stats
        results["chip_min"] = country_data["adjusted_wage"].min()
        results["chip_max"] = country_data["adjusted_wage"].max()
        results["chip_median"] = country_data["adjusted_wage"].median()
        
        # Log results
        logger.info(f"CHIP (GDP-weighted): ${results.get('chip_gdp', 0):.2f}/hour")
        if "chip_labor" in results:
            logger.info(f"CHIP (Labor-weighted): ${results['chip_labor']:.2f}/hour")
        logger.info(f"Range: ${results['chip_min']:.2f} - ${results['chip_max']:.2f}")
        
        return results
    
    def _aggregate_to_country(self, data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate time series data to country-level means."""
        
        # Apply time weighting filter/weights
        data = self._apply_time_weighting(data)
        
        # Group by country and calculate (weighted) means
        if "time_weight" in data.columns:
            # Weighted aggregation
            country_data = self._weighted_country_agg(data)
        else:
            # Simple mean aggregation
            agg_funcs = {
                "adjusted_wage": "mean",
                "elementary_wage": "mean",
                "distortion_factor": "mean",
                "mpl": "mean",
                "labor_hours": "mean",
                "effective_labor": "mean",
            }
            
            # Add GDP/output columns if present
            for col in ["rgdpna", "cgdpo"]:
                if col in data.columns:
                    agg_funcs[col] = "mean"
            
            country_data = data.groupby("country").agg(agg_funcs).reset_index()
        
        # Keep ISO codes if available
        if "isocode" in data.columns:
            iso_map = data.groupby("country")["isocode"].first()
            country_data = country_data.merge(
                iso_map.reset_index(), 
                on="country", 
                how="left"
            )
        
        return country_data
    
    def _apply_time_weighting(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply time weighting strategy to filter or weight observations."""
        method = self.agg_config.get("time_weighting", "all_years")
        
        if method == "all_years":
            # Original methodology: use all years equally
            return data
        
        elif method == "recent_only":
            # Use only the most recent year per country
            idx = data.groupby("country")["year"].idxmax()
            return data.loc[idx].copy()
        
        elif method == "rolling":
            # Use only last N years
            window = self.agg_config.get("rolling_window_years", 5)
            max_year = data["year"].max()
            min_year = max_year - window + 1
            logger.info(f"Using rolling window: {min_year}-{max_year}")
            return data[data["year"] >= min_year].copy()
        
        elif method == "exponential":
            # Exponential decay weighting
            half_life = self.agg_config.get("half_life_years", 3)
            max_year = data["year"].max()
            data = data.copy()
            # Weight = 0.5^((max_year - year) / half_life)
            data["time_weight"] = np.power(0.5, (max_year - data["year"]) / half_life)
            logger.info(f"Applied exponential weighting (half-life: {half_life} years)")
            return data
        
        else:
            logger.warning(f"Unknown time_weighting method: {method}, using all_years")
            return data
    
    def _weighted_country_agg(self, data: pd.DataFrame) -> pd.DataFrame:
        """Aggregate to country level using time weights."""
        result_rows = []
        
        for country, group in data.groupby("country"):
            weights = group["time_weight"]
            weight_sum = weights.sum()
            
            row = {"country": country}
            for col in ["adjusted_wage", "elementary_wage", "distortion_factor", 
                        "mpl", "labor_hours", "effective_labor", "rgdpna", "cgdpo"]:
                if col in group.columns:
                    row[col] = (group[col] * weights).sum() / weight_sum
            
            result_rows.append(row)
        
        return pd.DataFrame(result_rows)
    
    def _calculate_weights(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate weighting factors for each country."""
        df = data.copy()
        
        # GDP weight (using rgdpna as primary, cgdpo as fallback)
        gdp_col = "rgdpna" if "rgdpna" in df.columns else "cgdpo"
        if gdp_col in df.columns:
            total_gdp = df[gdp_col].sum()
            df["weight_gdp"] = df[gdp_col] / total_gdp
        else:
            logger.warning("No GDP column found; using equal weights")
            df["weight_gdp"] = 1 / len(df)
        
        # Labor weight (using labor hours)
        if "labor_hours" in df.columns:
            total_labor = df["labor_hours"].sum()
            df["weight_labor"] = df["labor_hours"] / total_labor
        else:
            df["weight_labor"] = 1 / len(df)
        
        # Unweighted (equal)
        df["weight_unweighted"] = 1 / len(df)
        
        # Labor productivity weight
        if "rgdpna" in df.columns and "labor_hours" in df.columns:
            df["labor_productivity"] = df["rgdpna"] / df["labor_hours"]
            total_lprod = df["labor_productivity"].sum()
            df["weight_productivity"] = df["labor_productivity"] / total_lprod
        
        return df
    
    def _weighted_average(self, data: pd.DataFrame, weight_col: str) -> float:
        """Calculate weighted average of adjusted wages."""
        if weight_col not in data.columns:
            logger.warning(f"Weight column {weight_col} not found; using equal weights")
            return data["adjusted_wage"].mean()
        
        # Filter to valid observations
        valid = data.dropna(subset=["adjusted_wage", weight_col])
        
        if len(valid) == 0:
            logger.error("No valid observations for aggregation")
            return 0.0
        
        # Normalize weights
        weights = valid[weight_col] / valid[weight_col].sum()
        
        # Weighted average
        chip_value = (valid["adjusted_wage"] * weights).sum()
        
        return chip_value
    
    def get_country_contributions(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Get contribution of each country to the global CHIP value.
        
        Useful for understanding which countries drive the result.
        """
        # Count years per country
        year_counts = data.groupby("country")["year"].agg(["min", "max", "count"])
        year_counts.columns = ["year_min", "year_max", "n_years"]
        year_counts = year_counts.reset_index()
        
        country_data = self._aggregate_to_country(data)
        country_data = self._calculate_weights(country_data)
        
        # Add year info
        country_data = country_data.merge(year_counts, on="country", how="left")
        
        # Calculate contribution to global CHIP
        country_data["contribution_gdp"] = (
            country_data["adjusted_wage"] * country_data["weight_gdp"]
        )
        
        # Sort by CHIP value (adjusted_wage)
        country_data = country_data.sort_values("adjusted_wage", ascending=False)
        
        # Select and rename columns for clarity
        output_cols = ["country"]
        if "isocode" in country_data.columns:
            output_cols.append("isocode")
        output_cols.extend([
            "adjusted_wage",      # CHIP value for this country
            "elementary_wage",    # Raw unskilled wage
            "distortion_factor",  # MPL/wage correction
            "weight_gdp",         # GDP weight in global average
            "contribution_gdp",   # This country's contribution to global CHIP
            "n_years",            # Number of years of data
            "year_min",           # Earliest year
            "year_max",           # Latest year
        ])
        
        # Only include columns that exist
        output_cols = [c for c in output_cols if c in country_data.columns]
        
        return country_data[output_cols]

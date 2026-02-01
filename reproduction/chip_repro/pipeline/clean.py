"""
Data cleaning module for CHIP valuation.

Handles:
- ISCO occupation code standardization
- Country name harmonization between ILOSTAT and PWT
- Outlier removal per configuration
- Merging of employment, wages, hours data
- Construction of effective labor units
"""

import logging
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger("chip.clean")


class DataCleaner:
    """Cleans and merges raw data for CHIP estimation."""
    
    def __init__(self, config: dict):
        """
        Initialize the data cleaner.
        
        Args:
            config: Configuration dictionary with exclusions and mappings
        """
        self.config = config
        self.exclusions = config.get("exclusions", {})
        self.occupations = config.get("occupations", {})
        self.dates = config.get("dates", {})
        
        self._exclusion_count = 0
    
    def process(self, raw_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Process and merge all raw datasets.
        
        Args:
            raw_data: Dictionary of raw DataFrames from fetch step
        
        Returns:
            Merged and cleaned DataFrame ready for estimation
        """
        # Clean individual datasets
        employment = self._clean_ilostat(raw_data["employment"], "employment")
        wages = self._clean_ilostat(raw_data["wages"], "wages")
        hours = self._clean_ilostat(raw_data["hours"], "hours")
        pwt = self._clean_pwt(raw_data["pwt"])
        deflator = self._clean_deflator(raw_data["deflator"])
        
        # Standardize occupation codes
        employment = self._standardize_occupations(employment)
        wages = self._standardize_occupations(wages)
        hours = self._standardize_occupations(hours)
        
        # Merge labor data
        labor_data = self._merge_labor_data(employment, wages, hours)
        
        # Apply deflator to wages
        labor_data = self._deflate_wages(labor_data, deflator)
        
        # Apply exclusions
        labor_data = self._apply_exclusions(labor_data)
        
        # Calculate wage ratios (skill weights)
        wage_ratios = self._calculate_wage_ratios(labor_data)
        
        # Calculate effective labor
        labor_data = self._calculate_effective_labor(labor_data, wage_ratios)
        
        # Merge with PWT
        merged = self._merge_with_pwt(labor_data, pwt)
        
        logger.info(f"Final dataset: {len(merged)} observations, {merged['country'].nunique()} countries")
        
        return merged
    
    def get_exclusion_count(self) -> int:
        """Return the number of observations excluded."""
        return self._exclusion_count
    
    def _clean_ilostat(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Clean ILOSTAT data to standard format."""
        df = df.copy()
        
        # The ILOSTAT data has various column naming conventions
        # Standardize to: country, year, sex, skill, value
        
        # Identify columns
        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if "ref_area" in col_lower or col_lower == "country":
                col_map[col] = "country"
            elif "time" in col_lower or "year" in col_lower:
                col_map[col] = "year"
            elif "sex" in col_lower:
                col_map[col] = "sex"
            elif "classif1" in col_lower or "ocu" in col_lower or "skill" in col_lower:
                col_map[col] = "skill"
            elif "obs_value" in col_lower or "value" in col_lower:
                col_map[col] = "value"
            elif "classif2" in col_lower and data_type == "wages":
                col_map[col] = "currency"
        
        df = df.rename(columns=col_map)
        
        # Filter to total sex (not male/female breakdown)
        if "sex" in df.columns:
            sex_filter = df["sex"].str.contains("Total|SEX_T", case=False, na=False)
            df = df[sex_filter]
        
        # Ensure year is numeric
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
        
        # Apply date range filter
        start_year = self.dates.get("start_year", 1970)
        end_year = self.dates.get("end_year", 2025)
        if "year" in df.columns:
            df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
        
        # Rename value column based on data type
        value_name = {"employment": "employed", "wages": "wage", "hours": "hours"}
        if "value" in df.columns:
            df = df.rename(columns={"value": value_name.get(data_type, "value")})
        
        return df
    
    def _clean_pwt(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean Penn World Tables data."""
        df = df.copy()
        
        # Standardize column names
        df.columns = df.columns.str.lower()
        
        # Rename for consistency
        rename_map = {
            "countrycode": "isocode",
            "country": "country",
        }
        df = df.rename(columns=rename_map)
        
        # Filter to required years
        start_year = self.dates.get("start_year", 1970)
        end_year = self.dates.get("end_year", 2025)
        df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
        
        # Harmonize country names to match ILOSTAT
        df = self._harmonize_country_names(df)
        
        # Drop rows where capital and GDP are both missing
        df = df.dropna(subset=["cn", "rnna"], how="all")
        
        return df
    
    def _clean_deflator(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean GDP deflator data."""
        df = df.copy()
        
        # Calculate deflator index relative to base year
        base_year = self.dates.get("deflator_base_year", 2017)
        
        base_value = df.loc[df["year"] == base_year, "deflator"].values
        if len(base_value) > 0:
            df["deflator_index"] = df["deflator"] / base_value[0]
        else:
            logger.warning(f"Base year {base_year} not found in deflator data")
            df["deflator_index"] = 1.0
        
        return df[["year", "deflator", "deflator_index"]]
    
    def _standardize_occupations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map ISCO occupation codes to standardized names."""
        if "skill" not in df.columns:
            return df
        
        df = df.copy()
        
        # Build mapping from config
        isco_map = {}
        for isco_version in ["isco08", "isco88", "isco68"]:
            version_map = self.occupations.get(isco_version, {})
            isco_map.update(version_map)
        
        # Also handle text descriptions
        text_map = {
            "1. Managers": "Managers",
            "Legislators, senior officials and managers": "Managers",
            "2. Professionals": "Professionals",
            "3. Technicians and associate professionals": "Technicians",
            "4. Clerical support workers": "Clerks",
            "4. Clerks": "Clerks",
            "5. Service and sales workers": "Salesmen",
            "6. Skilled agricultural, forestry and fishery workers": "Agforestry",
            "7. Craft and related trades workers": "Craftsmen",
            "8. Plant and machine operators, and assemblers": "Operators",
            "9. Elementary occupations": "Elementary",
        }
        
        # Apply mapping
        def map_occupation(skill_str):
            if pd.isna(skill_str):
                return None
            
            skill_str = str(skill_str)
            
            # Try direct code match
            if skill_str in isco_map:
                return isco_map[skill_str]
            
            # Try text match
            for pattern, name in text_map.items():
                if pattern.lower() in skill_str.lower():
                    return name
            
            # Exclude totals, armed forces, not classified
            exclude_patterns = ["Total", "Armed", "X.", "0."]
            for pattern in exclude_patterns:
                if pattern.lower() in skill_str.lower():
                    return None
            
            return None
        
        df["occupation"] = df["skill"].apply(map_occupation)
        df = df.dropna(subset=["occupation"])
        
        return df
    
    def _harmonize_country_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Harmonize country names between PWT and ILOSTAT conventions."""
        # These mappings come from the original R code
        name_map = {
            "Bolivia (Plurinational State of)": "Bolivia",
            "Cabo Verde": "Cape Verde",
            "Congo, Democratic Republic": "Congo, Democratic Republic of the",
            "Cote d'Ivoire": "Côte d'Ivoire",
            "Czech Republic": "Czechia",
            "China, Hong Kong SAR": "Hong Kong, China",
            "Iran (Islamic Republic of)": "Iran, Islamic Republic of",
            "Republic of Korea": "Korea, Republic of",
            "Lao People's DR": "Lao People's Democratic Republic",
            "China, Macao SAR": "Macau, China",
            "Republic of Moldova": "Moldova, Republic of",
            "State of Palestine": "Occupied Palestinian Territory",
            "St. Vincent & Grenadines": "Saint Vincent and the Grenadines",
            "Taiwan": "Taiwan, China",
            "U.R. of Tanzania: Mainland": "Tanzania, United Republic of",
            "Turkey": "Türkiye",
            "United States of America": "United States",
            "Venezuela (Bolivarian Republic of)": "Venezuela, Bolivarian Republic of",
        }
        
        df = df.copy()
        df["country"] = df["country"].replace(name_map)
        
        return df
    
    def _merge_labor_data(
        self, 
        employment: pd.DataFrame, 
        wages: pd.DataFrame, 
        hours: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge employment, wages, and hours data."""
        
        # Prepare each dataset
        emp = employment[["country", "year", "occupation", "employed"]].copy()
        
        # Wages may have currency dimension - filter to USD
        if "currency" in wages.columns:
            wages = wages[wages["currency"].str.contains("USD|U.S. dollars", case=False, na=False)]
        wage = wages[["country", "year", "occupation", "wage"]].copy()
        
        hrs = hours[["country", "year", "occupation", "hours"]].copy()
        
        # Merge
        merged = emp.merge(
            wage, 
            on=["country", "year", "occupation"], 
            how="left"
        ).merge(
            hrs,
            on=["country", "year", "occupation"],
            how="left"
        )
        
        # Default hours to 40 if missing (per original study)
        merged["hours"] = merged["hours"].fillna(40)
        
        # Calculate labor hours
        merged["labor_hours"] = merged["employed"] * merged["hours"]
        
        return merged
    
    def _deflate_wages(self, df: pd.DataFrame, deflator: pd.DataFrame) -> pd.DataFrame:
        """Apply GDP deflator to convert wages to constant dollars."""
        df = df.merge(deflator[["year", "deflator_index"]], on="year", how="left")
        
        # Deflate wages to base year dollars
        df["wage_real"] = df["wage"] / df["deflator_index"]
        
        return df
    
    def _apply_exclusions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove observations per configuration exclusions."""
        original_len = len(df)
        
        # Exclude entire countries
        excluded_countries = self.exclusions.get("countries", [])
        if excluded_countries:
            df = df[~df["country"].isin(excluded_countries)]
        
        # Exclude specific country-years
        country_years = self.exclusions.get("country_years", [])
        for cy in country_years:
            mask = (df["country"] == cy["country"]) & (df["year"] == cy["year"])
            df = df[~mask]
        
        self._exclusion_count = original_len - len(df)
        
        if self._exclusion_count > 0:
            logger.info(f"Excluded {self._exclusion_count} observations per config")
        
        return df
    
    def _calculate_wage_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate wage ratios relative to reference category (Managers)."""
        reference = self.occupations.get("reference_category", "Managers")
        
        # Get manager wages by country-year
        manager_wages = df[df["occupation"] == reference].copy()
        manager_wages = manager_wages[["country", "year", "wage_real"]].rename(
            columns={"wage_real": "manager_wage"}
        )
        
        # Merge and calculate ratio
        df = df.merge(manager_wages, on=["country", "year"], how="left")
        df["wage_ratio"] = df["wage_real"] / df["manager_wage"]
        
        # Aggregate wage ratios by country-occupation
        wage_ratios = df.groupby(["country", "occupation"])["wage_ratio"].mean().reset_index()
        
        return wage_ratios
    
    def _calculate_effective_labor(
        self, 
        df: pd.DataFrame, 
        wage_ratios: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate effective labor (skill-weighted hours)."""
        
        # Merge wage ratios
        df = df.merge(wage_ratios, on=["country", "occupation"], how="left", suffixes=("", "_avg"))
        
        # Use average wage ratio if available, otherwise use observation-level
        df["skill_weight"] = df["wage_ratio_avg"].fillna(df["wage_ratio"])
        
        # Calculate effective labor hours
        df["effective_labor"] = df["labor_hours"] * df["skill_weight"]
        
        return df
    
    def _merge_with_pwt(self, labor_data: pd.DataFrame, pwt: pd.DataFrame) -> pd.DataFrame:
        """Merge labor data with Penn World Tables."""
        
        # Aggregate labor data to country-year level
        agg_labor = labor_data.groupby(["country", "year"]).agg({
            "labor_hours": "sum",
            "effective_labor": "sum",
            "wage_real": "mean",  # Average wage
        }).reset_index()
        
        # Also get elementary wage specifically
        elementary = labor_data[labor_data["occupation"] == "Elementary"]
        elementary_wage = elementary.groupby(["country", "year"])["wage_real"].mean().reset_index()
        elementary_wage = elementary_wage.rename(columns={"wage_real": "elementary_wage"})
        
        agg_labor = agg_labor.merge(elementary_wage, on=["country", "year"], how="left")
        
        # Merge with PWT
        merged = agg_labor.merge(pwt, on=["country", "year"], how="inner")
        
        return merged

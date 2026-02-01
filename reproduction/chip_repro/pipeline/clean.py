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

from .normalize import ILOSTATNormalizer, PWTNormalizer

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
        
        # Initialize normalizers
        occupation_mapping = {}
        for isco_version in ["isco08", "isco88", "isco68"]:
            occupation_mapping.update(self.occupations.get(isco_version, {}))
        self._ilostat_normalizer = ILOSTATNormalizer(occupation_mapping)
        self._pwt_normalizer = PWTNormalizer()
    
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
        """
        Clean ILOSTAT data to standard format.
        
        Uses normalizer for column renaming only. Occupation filtering
        is done in _standardize_occupations to match original methodology.
        """
        # Use normalizer for column name standardization only
        normalized = self._ilostat_normalizer.normalize(df, data_type)
        
        # Apply date range filter
        start_year = self.dates.get("start_year", 1970)
        end_year = self.dates.get("end_year", 2025)
        if "year" in normalized.columns:
            normalized = normalized[
                (normalized["year"] >= start_year) & (normalized["year"] <= end_year)
            ]
        
        logger.debug(
            f"Cleaned {data_type}: {len(normalized)} rows, "
            f"format: {self._ilostat_normalizer.detect_format(df)}"
        )
        
        return normalized
    
    def _clean_pwt(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean Penn World Tables data using normalizer."""
        # Use normalizer for column standardization
        normalized = self._pwt_normalizer.normalize(df)
        
        # Filter to required years
        start_year = self.dates.get("start_year", 1970)
        end_year = self.dates.get("end_year", 2025)
        normalized = normalized[
            (normalized["year"] >= start_year) & (normalized["year"] <= end_year)
        ]
        
        # Harmonize country names to match ILOSTAT
        normalized = self._harmonize_country_names(normalized)
        
        # Drop rows where capital and GDP are both missing
        if "cn" in normalized.columns and "rnna" in normalized.columns:
            normalized = normalized.dropna(subset=["cn", "rnna"], how="all")
        
        return normalized
    
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
        """
        Map ISCO occupation codes/text to standardized names.
        
        This method uses the EXACT same text patterns as the original
        reproduction code to ensure we match the same occupations.
        """
        if "skill" not in df.columns:
            logger.warning("No skill column found for occupation mapping")
            return df
        
        df = df.copy()
        
        # Build mapping from config (for API data with codes like OCU_ISCO08_1)
        isco_map = {}
        for isco_version in ["isco08", "isco88", "isco68"]:
            version_map = self.occupations.get(isco_version, {})
            isco_map.update(version_map)
        
        # Text patterns for local CSV data (bulk downloads have text labels)
        # These are the EXACT patterns from the original reproduction code
        # that produced $2.56 — do not modify for reproduction fidelity
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
        
        # Apply mapping using substring matching (matches original behavior)
        def map_occupation(skill_str):
            if pd.isna(skill_str):
                return None
            
            skill_str = str(skill_str)
            
            # Try direct code match first (for API data)
            if skill_str in isco_map:
                return isco_map[skill_str]
            
            # Try text pattern match (for local CSV data)
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
        
        # Determine key column based on which has valid values
        # Normalizer sets "country" for bulk CSV, "isocode" for API
        if "country" in employment.columns and employment["country"].notna().any():
            key_col = "country"
        elif "isocode" in employment.columns and employment["isocode"].notna().any():
            key_col = "isocode"
        else:
            raise ValueError("No valid country or isocode column found in employment data")
        
        logger.debug(f"Using '{key_col}' as merge key")
        
        # Prepare each dataset
        emp_cols = [key_col, "year", "occupation", "employed"]
        emp = employment[[c for c in emp_cols if c in employment.columns]].copy()
        
        # Wages may have currency dimension - filter to USD only (per original study)
        if "currency" in wages.columns:
            # Original R code uses: filter(classif2 == "CUR_TYPE_USD")
            # Filter to USD and exclude PPP to avoid duplicates
            usd_mask = wages["currency"].str.contains(
                "USD|U\\.S\\. dollars", case=False, na=False, regex=True
            )
            ppp_mask = wages["currency"].str.contains("PPP", case=False, na=False)
            wages = wages[usd_mask & ~ppp_mask]
            logger.debug(f"Filtered to {len(wages)} USD wage observations")
        
        wage_cols = [key_col, "year", "occupation", "wage"]
        wage = wages[[c for c in wage_cols if c in wages.columns]].copy()
        
        hrs_cols = [key_col, "year", "occupation", "hours"]
        hrs = hours[[c for c in hrs_cols if c in hours.columns]].copy()
        
        # Merge
        merge_keys = [key_col, "year", "occupation"]
        merged = emp.merge(
            wage, 
            on=merge_keys, 
            how="left"
        ).merge(
            hrs,
            on=merge_keys,
            how="left"
        )
        
        # Rename isocode to country for downstream compatibility
        if key_col == "isocode":
            merged = merged.rename(columns={"isocode": "country"})
        
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
        
        # Rename wage_ratio to wage_ratio_avg before merging
        wage_ratios = wage_ratios.rename(columns={"wage_ratio": "wage_ratio_avg"})
        
        # Merge wage ratios
        df = df.merge(wage_ratios, on=["country", "occupation"], how="left")
        
        # Use average wage ratio as skill weight (default to 1.0 if missing)
        df["skill_weight"] = df["wage_ratio_avg"].fillna(1.0)
        
        # Calculate effective labor hours
        df["effective_labor"] = df["labor_hours"] * df["skill_weight"]
        
        return df
    
    def _merge_with_pwt(self, labor_data: pd.DataFrame, pwt: pd.DataFrame) -> pd.DataFrame:
        """Merge labor data with Penn World Tables."""
        
        # labor_data["country"] is actually ISO codes when from API
        # PWT has both "country" (name) and "isocode" (code)
        
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
        
        # Determine if we're using ISO codes or country names
        # If agg_labor["country"] values are 3-letter codes, use isocode matching
        sample_country = agg_labor["country"].iloc[0] if len(agg_labor) > 0 else ""
        use_isocode = len(str(sample_country)) == 3 and str(sample_country).isupper()
        
        if use_isocode and "isocode" in pwt.columns:
            # Match on ISO codes
            agg_labor = agg_labor.rename(columns={"country": "isocode"})
            merged = agg_labor.merge(pwt, on=["isocode", "year"], how="inner")
        else:
            # Match on country names
            merged = agg_labor.merge(pwt, on=["country", "year"], how="inner")
        
        logger.debug(f"PWT merge: {len(agg_labor)} labor obs -> {len(merged)} merged obs")
        
        return merged

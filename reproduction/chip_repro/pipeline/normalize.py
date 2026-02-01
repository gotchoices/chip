"""
Data normalization module for CHIP valuation.

Handles format differences between data sources:
- Local CSV files (bulk download with .label suffix columns)
- ILOSTAT rplumber API (raw codes)
- Other potential future formats

IMPORTANT: This module ONLY handles column renaming and format detection.
It does NOT filter or interpret occupation codes — that is handled by
the DataCleaner's _standardize_occupations method to ensure reproduction
fidelity with the original study.
"""

import logging
from typing import Literal

import pandas as pd

logger = logging.getLogger("chip.normalize")


class ILOSTATNormalizer:
    """
    Normalize ILOSTAT data column names from various formats.
    
    Handles:
    - Bulk CSV downloads (columns with .label suffix, human-readable values)
    - rplumber API responses (raw codes without suffix)
    
    This normalizer ONLY renames columns to a standard schema.
    Occupation filtering/mapping is done separately in DataCleaner.
    """
    
    def __init__(self, occupation_mapping: dict | None = None):
        """
        Initialize normalizer.
        
        Args:
            occupation_mapping: Dict mapping ISCO codes to standard names
                               (used only for API format, not for reproduction)
        """
        self.occupation_mapping = occupation_mapping or {}
    
    def detect_format(self, df: pd.DataFrame) -> Literal["bulk_csv", "api", "unknown"]:
        """
        Detect the format of ILOSTAT data.
        
        Args:
            df: Raw DataFrame from ILOSTAT
            
        Returns:
            Format identifier string
        """
        columns = [c.lower() for c in df.columns]
        
        # Bulk CSV has .label suffix on columns
        if any(".label" in c for c in columns):
            return "bulk_csv"
        
        # API has raw column names without suffix
        if "ref_area" in columns and "classif1" in columns:
            return "api"
        
        return "unknown"
    
    def normalize(
        self, 
        df: pd.DataFrame, 
        data_type: Literal["employment", "wages", "hours"],
        source_format: str | None = None
    ) -> pd.DataFrame:
        """
        Normalize ILOSTAT data column names to standard schema.
        
        ONLY renames columns — does NOT filter rows or map occupation codes.
        
        Args:
            df: Raw DataFrame from ILOSTAT
            data_type: Type of data (employment, wages, hours)
            source_format: Override format detection (bulk_csv, api)
            
        Returns:
            DataFrame with standardized column names
        """
        if source_format is None:
            source_format = self.detect_format(df)
        
        logger.debug(f"Normalizing {data_type} data from {source_format} format")
        
        if source_format == "bulk_csv":
            return self._normalize_bulk_csv(df, data_type)
        elif source_format == "api":
            return self._normalize_api(df, data_type)
        else:
            raise ValueError(f"Unknown ILOSTAT format: {source_format}. "
                           f"Columns: {list(df.columns)[:5]}")
    
    def _normalize_bulk_csv(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        Normalize bulk CSV download format.
        
        Only renames columns — preserves all rows for downstream processing.
        """
        df = df.copy()
        
        # Map columns (CSV has .label suffix with human-readable values)
        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if "ref_area.label" in col_lower:
                col_map[col] = "country"  # Already country names
            elif "time" in col_lower:
                col_map[col] = "year"
            elif "sex.label" in col_lower:
                col_map[col] = "sex"
            elif "classif1.label" in col_lower:
                col_map[col] = "skill"  # Raw occupation text for downstream mapping
            elif "classif2.label" in col_lower:
                col_map[col] = "currency"
            elif "obs_value" in col_lower:
                col_map[col] = "value"
        
        df = df.rename(columns=col_map)
        
        # No isocode in bulk CSV
        if "isocode" not in df.columns:
            df["isocode"] = None
        
        return self._finalize(df, data_type)
    
    def _normalize_api(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        Normalize rplumber API format.
        
        Only renames columns — preserves all rows for downstream processing.
        """
        df = df.copy()
        
        # Map columns (API has raw codes)
        col_map = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower == "ref_area":
                col_map[col] = "isocode"  # ISO codes
            elif col_lower == "time":
                col_map[col] = "year"
            elif col_lower == "sex":
                col_map[col] = "sex"
            elif col_lower == "classif1":
                col_map[col] = "skill"  # Raw occupation code for downstream mapping
            elif col_lower == "classif2":
                col_map[col] = "currency"
            elif col_lower == "obs_value":
                col_map[col] = "value"
        
        df = df.rename(columns=col_map)
        
        # API doesn't have country names
        if "country" not in df.columns:
            df["country"] = None
        
        return self._finalize(df, data_type)
    
    def _finalize(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        Apply minimal transformations common to all formats.
        
        Only handles:
        - Sex filtering (to Total only)
        - Year type conversion
        - Value column renaming
        
        Does NOT filter occupations — that's done in DataCleaner.
        """
        # Filter to total sex only (this is universal across all methodologies)
        if "sex" in df.columns:
            sex_filter = df["sex"].str.contains("Total|SEX_T", case=False, na=False)
            df = df[sex_filter]
        
        # Ensure year is numeric
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
        
        # Rename value column based on data type
        value_names = {
            "employment": "employed",
            "wages": "wage", 
            "hours": "hours"
        }
        if "value" in df.columns and data_type in value_names:
            df = df.rename(columns={"value": value_names[data_type]})
        
        return df


class PWTNormalizer:
    """Normalize Penn World Tables data."""
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize PWT data to standard schema.
        
        Args:
            df: Raw DataFrame from PWT
            
        Returns:
            Normalized DataFrame with standard column names
        """
        df = df.copy()
        
        # Standardize column names (PWT uses lowercase)
        df.columns = df.columns.str.lower()
        
        # Rename countrycode to isocode
        if "countrycode" in df.columns:
            df = df.rename(columns={"countrycode": "isocode"})
        
        return df

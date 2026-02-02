"""
Data Normalization

Standardizes column names and formats across different data sources.

Design Principles:
    - Input: Raw data from various sources (ILOSTAT API, local CSV, etc.)
    - Output: Consistent column names and formats
    - Each normalizer is idempotent (safe to call multiple times)
    - Normalizers detect format automatically when possible

Standard Column Names:
    ILOSTAT data:
        - country: Country name (string)
        - isocode: ISO 3-letter country code
        - year: Year (int)
        - occupation: Occupation description (string)
        - isco_code: ISCO code (string, e.g., "ISCO08_9")
        - employment: Number employed (float)
        - wage: Monthly earnings (float)
        - hours: Hours worked (float)
        - currency: Currency type (string: "USD", "PPP", "LCU")
    
    PWT data:
        - country: Country name
        - isocode: ISO 3-letter code
        - year: Year
        - gdp: Real GDP
        - capital: Capital stock
        - employment: Total employment
        - human_capital: Human capital index
        - labor_share: Labor share of income

Public API:
    normalize_ilostat(df, dataset_type) -> pd.DataFrame
    normalize_pwt(df) -> pd.DataFrame
    normalize_deflator(df) -> pd.DataFrame
    detect_format(df) -> str  # "ilostat_api", "ilostat_csv", "pwt", etc.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Format Detection
# =============================================================================

def detect_format(df: pd.DataFrame) -> str:
    """
    Detect the format of a DataFrame based on column names.
    
    Returns:
        One of: "ilostat_api", "ilostat_csv", "pwt", "deflator", "unknown"
    """
    cols = set(df.columns.str.lower())
    
    # ILOSTAT API format
    if "ref_area" in cols and "obs_value" in cols:
        return "ilostat_api"
    
    # ILOSTAT CSV format (with .label suffix)
    if any(".label" in c.lower() for c in df.columns):
        return "ilostat_csv"
    
    # PWT format
    if "countrycode" in cols and "rgdpna" in cols:
        return "pwt"
    
    # Deflator
    if "deflator" in cols or "usagdpdefaismei" in cols:
        return "deflator"
    
    return "unknown"


# =============================================================================
# ILOSTAT Normalization
# =============================================================================

# Column mappings for ILOSTAT API format
ILOSTAT_API_COLUMNS = {
    "ref_area": "isocode",
    "time": "year",
    "classif1": "isco_code",
    "classif2": "currency_code",
    "obs_value": "value",
    "sex": "sex",
}

# Column mappings for ILOSTAT CSV format (with .label suffix)
ILOSTAT_CSV_COLUMNS = {
    "ref_area.label": "country",
    "ref_area": "isocode",
    "time": "year",
    "classif1.label": "occupation",
    "classif1": "isco_code",
    "classif2.label": "currency",
    "classif2": "currency_code",
    "obs_value": "value",
    "sex.label": "sex",
}


def normalize_ilostat(df: pd.DataFrame, value_column: str = "value") -> pd.DataFrame:
    """
    Normalize ILOSTAT data to standard format.
    
    Args:
        df: Raw ILOSTAT DataFrame
        value_column: Name for the value column (e.g., "employment", "wage", "hours")
        
    Returns:
        DataFrame with standardized column names
    """
    df = df.copy()
    fmt = detect_format(df)
    
    if fmt == "ilostat_api":
        mapping = ILOSTAT_API_COLUMNS
    elif fmt == "ilostat_csv":
        mapping = ILOSTAT_CSV_COLUMNS
    else:
        logger.warning(f"Unknown ILOSTAT format, columns: {list(df.columns)}")
        return df
    
    # Apply column renaming
    rename_map = {}
    for old_name, new_name in mapping.items():
        if old_name in df.columns:
            rename_map[old_name] = new_name
    
    df = df.rename(columns=rename_map)
    
    # Rename 'value' to specific column name
    if "value" in df.columns and value_column != "value":
        df = df.rename(columns={"value": value_column})
    
    # Ensure year is integer
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    
    return df


# =============================================================================
# PWT Normalization
# =============================================================================

PWT_COLUMNS = {
    "countrycode": "isocode",
    "country": "country",
    "year": "year",
    "rgdpna": "gdp",
    "rkna": "capital",
    "emp": "employment",
    "hc": "human_capital",
    "labsh": "labor_share",
    "avh": "avg_hours",
    "pop": "population",
}


def normalize_pwt(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize Penn World Tables data to standard format.
    
    Args:
        df: Raw PWT DataFrame
        
    Returns:
        DataFrame with standardized column names
    """
    df = df.copy()
    
    # Apply column renaming
    rename_map = {}
    for old_name, new_name in PWT_COLUMNS.items():
        if old_name in df.columns:
            rename_map[old_name] = new_name
    
    df = df.rename(columns=rename_map)
    
    # Ensure year is integer
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    
    return df


# =============================================================================
# Deflator Normalization
# =============================================================================

def normalize_deflator(df: pd.DataFrame, base_year: int = 2017) -> pd.DataFrame:
    """
    Normalize deflator data and rebase to specified year.
    
    Args:
        df: Raw deflator DataFrame
        base_year: Year to use as base (deflator = 100)
        
    Returns:
        DataFrame with columns: year, deflator (rebased)
    """
    df = df.copy()
    
    # Standardize column names
    col_map = {
        "DATE": "date",
        "USAGDPDEFAISMEI": "deflator",
    }
    df = df.rename(columns=col_map)
    
    # Extract year if needed
    if "date" in df.columns and "year" not in df.columns:
        df["year"] = pd.to_datetime(df["date"]).dt.year
    
    # Ensure we have year and deflator
    if "year" not in df.columns or "deflator" not in df.columns:
        raise ValueError(f"Cannot normalize deflator, columns: {list(df.columns)}")
    
    # Rebase to specified year
    base_value = df.loc[df["year"] == base_year, "deflator"].values
    if len(base_value) > 0:
        df["deflator"] = df["deflator"] / base_value[0] * 100
    
    return df[["year", "deflator"]].drop_duplicates()

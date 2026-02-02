"""
Data Cleaning

Utilities for cleaning, filtering, and preprocessing data.

Design Principles:
    - Each function does one thing well
    - Functions are composable (can chain together)
    - Explicit about what gets filtered and why
    - Returns filtered data + optionally a log of what was removed

Public API:
    # Country handling
    harmonize_countries(df) -> pd.DataFrame
    exclude_countries(df, countries: list) -> pd.DataFrame
    get_country_coverage(df) -> pd.DataFrame
    
    # Occupation handling
    filter_unskilled(df) -> pd.DataFrame
    classify_skill_level(df) -> pd.DataFrame
    
    # Data quality
    filter_outliers(df, column, method="iqr") -> pd.DataFrame
    require_complete(df, columns) -> pd.DataFrame
    filter_years(df, start, end) -> pd.DataFrame
    
    # Merging
    merge_datasets(employment, wages, hours, pwt) -> pd.DataFrame
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Country Handling
# =============================================================================

# Standard country name mappings
COUNTRY_ALIASES = {
    "United States of America": "United States",
    "USA": "United States",
    "Russian Federation": "Russia",
    "Korea, Republic of": "South Korea",
    "Republic of Korea": "South Korea",
    "Korea (Republic of)": "South Korea",
    "Viet Nam": "Vietnam",
    "Türkiye": "Turkey",
    "Czechia": "Czech Republic",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
    # Add more as needed
}

# Countries excluded in original study (data quality issues)
ORIGINAL_EXCLUDED = [
    "Nepal", "Pakistan", "Sri Lanka", "Bangladesh",
    "Egypt", "Jordan", "Palestine",
    "Occupied Palestinian Territory",
]


def harmonize_countries(df: pd.DataFrame, country_col: str = "country") -> pd.DataFrame:
    """
    Standardize country names to consistent format.
    
    Args:
        df: DataFrame with country column
        country_col: Name of country column
        
    Returns:
        DataFrame with harmonized country names
    """
    df = df.copy()
    if country_col in df.columns:
        df[country_col] = df[country_col].replace(COUNTRY_ALIASES)
    return df


def exclude_countries(df: pd.DataFrame, 
                      countries: list = None,
                      country_col: str = "country") -> pd.DataFrame:
    """
    Remove specified countries from dataset.
    
    Args:
        df: DataFrame with country column
        countries: List of country names to exclude (default: original study exclusions)
        country_col: Name of country column
        
    Returns:
        DataFrame with countries removed
    """
    if countries is None:
        countries = ORIGINAL_EXCLUDED
    
    df = df.copy()
    if country_col in df.columns:
        mask = ~df[country_col].isin(countries)
        removed = len(df) - mask.sum()
        if removed > 0:
            logger.info(f"Excluded {removed} observations from {len(countries)} countries")
        df = df[mask]
    
    return df


def get_country_coverage(df: pd.DataFrame,
                         country_col: str = "country",
                         year_col: str = "year") -> pd.DataFrame:
    """
    Analyze data coverage by country.
    
    Returns DataFrame with:
        - country: Country name
        - n_years: Number of years with data
        - year_min: First year with data
        - year_max: Last year with data
        - n_obs: Total observations
    """
    coverage = df.groupby(country_col).agg({
        year_col: ["count", "min", "max", "nunique"]
    }).reset_index()
    
    coverage.columns = [country_col, "n_obs", "year_min", "year_max", "n_years"]
    return coverage.sort_values("n_years", ascending=False)


# =============================================================================
# Occupation Handling
# =============================================================================

# ISCO codes for unskilled/elementary occupations
UNSKILLED_CODES = [
    "ISCO08_9",     # ISCO-08 Major Group 9: Elementary Occupations
    "ISCO88_9",     # ISCO-88 Major Group 9
    "OCU_SKILL_L",  # Low skill level
]

# Text patterns indicating unskilled occupations
UNSKILLED_PATTERNS = [
    "elementary",
    "unskilled",
    "low skill",
    "skill level 1",
]


def filter_unskilled(df: pd.DataFrame,
                     occupation_col: str = "occupation",
                     isco_col: str = "isco_code") -> pd.DataFrame:
    """
    Filter to only unskilled/elementary occupations.
    
    Uses both ISCO codes and text pattern matching.
    
    Args:
        df: DataFrame with occupation data
        occupation_col: Column with occupation text
        isco_col: Column with ISCO code
        
    Returns:
        DataFrame filtered to unskilled occupations only
    """
    df = df.copy()
    mask = pd.Series(False, index=df.index)
    
    # Match by ISCO code
    if isco_col in df.columns:
        for code in UNSKILLED_CODES:
            mask |= df[isco_col].astype(str).str.contains(code, case=False, na=False)
    
    # Match by text pattern
    if occupation_col in df.columns:
        for pattern in UNSKILLED_PATTERNS:
            mask |= df[occupation_col].astype(str).str.contains(pattern, case=False, na=False)
    
    result = df[mask]
    logger.info(f"Filtered to {len(result)} unskilled observations ({len(result)/len(df)*100:.1f}%)")
    
    return result


def classify_skill_level(df: pd.DataFrame,
                         occupation_col: str = "occupation",
                         isco_col: str = "isco_code") -> pd.DataFrame:
    """
    Add skill level classification column.
    
    Classifies occupations into: unskilled, semi-skilled, skilled, highly-skilled
    based on ISCO major group codes.
    
    Args:
        df: DataFrame with occupation data
        
    Returns:
        DataFrame with added 'skill_level' column
    """
    df = df.copy()
    df["skill_level"] = "unknown"
    
    if isco_col not in df.columns:
        return df
    
    code_col = df[isco_col].astype(str)
    
    # ISCO major group to skill level mapping
    skill_map = {
        "1": "highly_skilled",  # Managers
        "2": "highly_skilled",  # Professionals
        "3": "skilled",         # Technicians
        "4": "semi_skilled",    # Clerical
        "5": "semi_skilled",    # Service/Sales
        "6": "semi_skilled",    # Agricultural
        "7": "semi_skilled",    # Craft workers
        "8": "semi_skilled",    # Machine operators
        "9": "unskilled",       # Elementary
    }
    
    for group, skill in skill_map.items():
        # Match ISCO08_X or ISCO88_X patterns
        mask = code_col.str.contains(f"ISCO\\d\\d_{group}", regex=True, na=False)
        df.loc[mask, "skill_level"] = skill
    
    return df


# =============================================================================
# Data Quality
# =============================================================================

def filter_outliers(df: pd.DataFrame,
                    column: str,
                    method: str = "iqr",
                    threshold: float = 1.5) -> pd.DataFrame:
    """
    Remove statistical outliers from a column.
    
    Args:
        df: DataFrame
        column: Column to check for outliers
        method: "iqr" (interquartile range) or "zscore"
        threshold: IQR multiplier or z-score threshold
        
    Returns:
        DataFrame with outliers removed
    """
    df = df.copy()
    
    if column not in df.columns:
        return df
    
    values = df[column].dropna()
    
    if method == "iqr":
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        mask = (df[column] >= lower) & (df[column] <= upper) | df[column].isna()
    
    elif method == "zscore":
        mean, std = values.mean(), values.std()
        mask = (np.abs(df[column] - mean) <= threshold * std) | df[column].isna()
    
    else:
        raise ValueError(f"Unknown outlier method: {method}")
    
    removed = len(df) - mask.sum()
    if removed > 0:
        logger.info(f"Removed {removed} outliers from {column}")
    
    return df[mask]


def require_complete(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Remove rows with missing values in required columns.
    
    Args:
        df: DataFrame
        columns: List of columns that must be non-null
        
    Returns:
        DataFrame with complete cases only
    """
    df = df.copy()
    initial = len(df)
    df = df.dropna(subset=columns)
    removed = initial - len(df)
    
    if removed > 0:
        logger.info(f"Removed {removed} rows with missing values in {columns}")
    
    return df


def filter_years(df: pd.DataFrame,
                 start: int = None,
                 end: int = None,
                 year_col: str = "year") -> pd.DataFrame:
    """
    Filter to specified year range.
    
    Args:
        df: DataFrame with year column
        start: First year to include (inclusive)
        end: Last year to include (inclusive)
        year_col: Name of year column
        
    Returns:
        DataFrame filtered to year range
    """
    df = df.copy()
    
    if year_col not in df.columns:
        return df
    
    if start is not None:
        df = df[df[year_col] >= start]
    if end is not None:
        df = df[df[year_col] <= end]
    
    return df


# =============================================================================
# Merging
# =============================================================================

def merge_datasets(employment: pd.DataFrame,
                   wages: pd.DataFrame,
                   hours: pd.DataFrame = None,
                   pwt: pd.DataFrame = None,
                   on: list = None) -> pd.DataFrame:
    """
    Merge ILOSTAT and PWT datasets.
    
    Args:
        employment: Employment by occupation
        wages: Wages by occupation
        hours: Hours worked (optional)
        pwt: Penn World Tables data (optional)
        on: Columns to merge on (default: country, year)
        
    Returns:
        Merged DataFrame
    """
    if on is None:
        on = ["country", "year"]
    
    # Start with employment
    df = employment.copy()
    
    # Merge wages
    if wages is not None:
        df = df.merge(wages, on=on + ["occupation"], how="outer", suffixes=("", "_wage"))
    
    # Merge hours
    if hours is not None:
        df = df.merge(hours, on=on + ["occupation"], how="outer", suffixes=("", "_hours"))
    
    # Merge PWT (country-year level)
    if pwt is not None:
        df = df.merge(pwt, on=on, how="left", suffixes=("", "_pwt"))
    
    return df

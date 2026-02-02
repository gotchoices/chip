"""
Data Fetcher

Retrieves data from external sources with automatic caching.

Supported Sources:
    - ILOSTAT: Employment, wages, hours worked by occupation
    - PWT (Penn World Tables): GDP, capital, labor productivity
    - FRED: US GDP deflator for inflation adjustment
    - Heritage Foundation: Economic Freedom Index (planned)

Design Principles:
    - Fetch once, cache forever (until explicitly invalidated)
    - Transparent fallback to original study data for reproduction
    - Log data vintage for reproducibility
    - Raise clear errors when data unavailable

Public API:
    get_employment() -> pd.DataFrame
    get_wages() -> pd.DataFrame
    get_hours() -> pd.DataFrame
    get_pwt() -> pd.DataFrame
    get_deflator() -> pd.DataFrame
    get_freedom_index() -> pd.DataFrame  # planned
    get_all() -> dict[str, pd.DataFrame]
"""

import pandas as pd
import requests
from io import StringIO
from pathlib import Path
import logging

from . import cache

logger = logging.getLogger(__name__)

# Original study data location (for fallback/comparison)
ORIGINAL_DATA = Path(__file__).parent.parent.parent / "original" / "Data"


# =============================================================================
# ILOSTAT Data
# =============================================================================

ILOSTAT_BASE_URL = "https://rplumber.ilo.org/data/indicator/"

ILOSTAT_DATASETS = {
    "employment": "EMP_TEMP_SEX_OCU_NB_A",
    "wages": "EAR_4MTH_SEX_OCU_CUR_NB_A",
    "hours": "HOW_TEMP_SEX_OCU_NB_A",
}


def _fetch_ilostat(dataset_id: str) -> pd.DataFrame:
    """Fetch a dataset from ILOSTAT API."""
    url = f"{ILOSTAT_BASE_URL}?id={dataset_id}&format=csv"
    logger.info(f"Fetching ILOSTAT: {dataset_id}")
    
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    
    return pd.read_csv(StringIO(response.text))


def get_employment(use_cache: bool = True) -> pd.DataFrame:
    """
    Get employment data by occupation.
    
    Returns DataFrame with columns:
        - country/ref_area: Country identifier
        - year/time: Year
        - occupation/classif1: ISCO occupation code
        - employment/obs_value: Number employed
    """
    if use_cache and cache.is_cached("employment"):
        logger.debug("Loading employment from cache")
        return pd.read_parquet(cache.get_cache_path("employment"))
    
    try:
        df = _fetch_ilostat(ILOSTAT_DATASETS["employment"])
        df.to_parquet(cache.get_cache_path("employment"))
        cache.set_metadata("employment", source="ILOSTAT API", 
                          dataset_id=ILOSTAT_DATASETS["employment"])
        return df
    except Exception as e:
        logger.warning(f"ILOSTAT API failed: {e}")
        # Fallback to original data
        fallback = ORIGINAL_DATA / "employment.csv"
        if fallback.exists():
            logger.info(f"Using fallback: {fallback}")
            return pd.read_csv(fallback)
        raise RuntimeError("Could not fetch employment data")


def get_wages(use_cache: bool = True) -> pd.DataFrame:
    """
    Get wage data by occupation.
    
    Returns DataFrame with columns:
        - country/ref_area: Country identifier
        - year/time: Year
        - occupation/classif1: ISCO occupation code
        - currency/classif2: Currency type (USD, PPP, LCU)
        - wage/obs_value: Monthly earnings
    """
    if use_cache and cache.is_cached("wages"):
        logger.debug("Loading wages from cache")
        return pd.read_parquet(cache.get_cache_path("wages"))
    
    try:
        df = _fetch_ilostat(ILOSTAT_DATASETS["wages"])
        df.to_parquet(cache.get_cache_path("wages"))
        cache.set_metadata("wages", source="ILOSTAT API",
                          dataset_id=ILOSTAT_DATASETS["wages"])
        return df
    except Exception as e:
        logger.warning(f"ILOSTAT API failed: {e}")
        fallback = ORIGINAL_DATA / "wages.csv"
        if fallback.exists():
            logger.info(f"Using fallback: {fallback}")
            return pd.read_csv(fallback)
        raise RuntimeError("Could not fetch wage data")


def get_hours(use_cache: bool = True) -> pd.DataFrame:
    """
    Get hours worked data by occupation.
    
    Returns DataFrame with columns:
        - country/ref_area: Country identifier
        - year/time: Year
        - occupation/classif1: ISCO occupation code
        - hours/obs_value: Hours worked
    """
    if use_cache and cache.is_cached("hours"):
        logger.debug("Loading hours from cache")
        return pd.read_parquet(cache.get_cache_path("hours"))
    
    try:
        df = _fetch_ilostat(ILOSTAT_DATASETS["hours"])
        df.to_parquet(cache.get_cache_path("hours"))
        cache.set_metadata("hours", source="ILOSTAT API",
                          dataset_id=ILOSTAT_DATASETS["hours"])
        return df
    except Exception as e:
        logger.warning(f"ILOSTAT API failed: {e}")
        fallback = ORIGINAL_DATA / "hoursworked.csv"
        if fallback.exists():
            logger.info(f"Using fallback: {fallback}")
            return pd.read_csv(fallback)
        raise RuntimeError("Could not fetch hours data")


# =============================================================================
# Penn World Tables
# =============================================================================

PWT_URL = "https://dataverse.nl/api/access/datafile/354098"  # PWT 10.0


def get_pwt(use_cache: bool = True) -> pd.DataFrame:
    """
    Get Penn World Tables data.
    
    Returns DataFrame with columns:
        - country/countrycode: Country identifier
        - year: Year
        - rgdpna: Real GDP (national accounts)
        - rkna: Capital stock
        - emp: Employment
        - hc: Human capital index
        - labsh: Labor share of income
    """
    if use_cache and cache.is_cached("pwt"):
        logger.debug("Loading PWT from cache")
        return pd.read_parquet(cache.get_cache_path("pwt"))
    
    try:
        logger.info("Fetching Penn World Tables 10.0")
        df = pd.read_stata(PWT_URL)
        df.to_parquet(cache.get_cache_path("pwt"))
        cache.set_metadata("pwt", source="Dataverse", version="10.0")
        return df
    except Exception as e:
        logger.warning(f"PWT fetch failed: {e}")
        fallback = ORIGINAL_DATA / "national_accounts.csv"
        if fallback.exists():
            logger.info(f"Using fallback: {fallback}")
            return pd.read_csv(fallback)
        raise RuntimeError("Could not fetch PWT data")


# =============================================================================
# FRED (Deflator)
# =============================================================================

def get_deflator(use_cache: bool = True) -> pd.DataFrame:
    """
    Get GDP deflator from FRED.
    
    Returns DataFrame with columns:
        - year: Year
        - deflator: GDP deflator value (base year = 100)
    """
    if use_cache and cache.is_cached("deflator"):
        logger.debug("Loading deflator from cache")
        return pd.read_parquet(cache.get_cache_path("deflator"))
    
    try:
        logger.info("Fetching FRED deflator")
        # Try pandas-datareader first
        import pandas_datareader.data as web
        from datetime import datetime
        
        df = web.DataReader("USAGDPDEFAISMEI", "fred", 
                           datetime(1990, 1, 1), datetime.now())
        df = df.reset_index()
        df.columns = ["date", "deflator"]
        df["year"] = df["date"].dt.year
        df = df.groupby("year")["deflator"].mean().reset_index()
        
        df.to_parquet(cache.get_cache_path("deflator"))
        cache.set_metadata("deflator", source="FRED", series="USAGDPDEFAISMEI")
        return df
    except Exception as e:
        logger.warning(f"FRED fetch failed: {e}")
        fallback = ORIGINAL_DATA / "GDPDEF.csv"
        if fallback.exists():
            logger.info(f"Using fallback: {fallback}")
            df = pd.read_csv(fallback)
            # Normalize column names
            if "DATE" in df.columns:
                df["year"] = pd.to_datetime(df["DATE"]).dt.year
                df = df.rename(columns={"USAGDPDEFAISMEI": "deflator"})
            return df[["year", "deflator"]].drop_duplicates()
        raise RuntimeError("Could not fetch deflator data")


# =============================================================================
# Economic Freedom Index (Planned)
# =============================================================================

def get_freedom_index(use_cache: bool = True) -> pd.DataFrame:
    """
    Get economic freedom index data.
    
    TODO: Implement fetching from Heritage Foundation or Fraser Institute
    
    Returns DataFrame with columns:
        - country: Country name
        - year: Year
        - freedom_score: Economic freedom score (0-100)
    """
    # Check for local file first
    local_file = ORIGINAL_DATA / "freedomindex.xlsx"
    if local_file.exists():
        logger.info(f"Loading freedom index from: {local_file}")
        return pd.read_excel(local_file)
    
    raise NotImplementedError("Freedom index API not yet implemented")


# =============================================================================
# Convenience Functions
# =============================================================================

def get_all(use_cache: bool = True) -> dict:
    """
    Fetch all standard datasets.
    
    Returns:
        dict with keys: employment, wages, hours, pwt, deflator
    """
    return {
        "employment": get_employment(use_cache),
        "wages": get_wages(use_cache),
        "hours": get_hours(use_cache),
        "pwt": get_pwt(use_cache),
        "deflator": get_deflator(use_cache),
    }


def refresh_all():
    """Force refresh of all cached data."""
    cache.invalidate()
    return get_all(use_cache=False)

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
    - Self-sufficient: workbench fetches its own data, no fallbacks
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
import time

from . import cache

logger = logging.getLogger(__name__)

# Project root for finding secrets.toml
PROJECT_ROOT = Path(__file__).parent.parent.parent


# =============================================================================
# ILOSTAT Data
# =============================================================================

ILOSTAT_BASE_URL = "https://rplumber.ilo.org/data/indicator/"

ILOSTAT_DATASETS = {
    "employment": "EMP_TEMP_SEX_OCU_NB_A",
    # CRITICAL: Use HOURLY wages (4HRL), not MONTHLY (4MTH)!
    # The original study uses hourly wages for distortion factor calculation
    "wages": "EAR_4HRL_SEX_OCU_CUR_NB_A",
    "hours": "HOW_TEMP_SEX_OCU_NB_A",
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
REQUEST_TIMEOUT = 180  # seconds


def _fetch_ilostat(dataset_id: str) -> pd.DataFrame:
    """
    Fetch a dataset from ILOSTAT API with retries.
    
    Raises:
        RuntimeError: If all retries fail
    """
    url = f"{ILOSTAT_BASE_URL}?id={dataset_id}&format=csv"
    
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Fetching ILOSTAT: {dataset_id} (attempt {attempt + 1}/{MAX_RETRIES})")
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text), low_memory=False)
            logger.info(f"  Received {len(df)} rows, {len(df.columns)} columns")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"  Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"ILOSTAT API failed after {MAX_RETRIES} attempts for {dataset_id}. "
                    f"Last error: {e}"
                )


def get_employment(use_cache: bool = True) -> pd.DataFrame:
    """
    Get employment data by occupation from ILOSTAT.
    
    Returns DataFrame with columns:
        - ref_area: ISO country code
        - time: Year
        - classif1: ISCO occupation code
        - obs_value: Number employed
    """
    if use_cache and cache.is_cached("employment"):
        logger.debug("Loading employment from cache")
        return pd.read_parquet(cache.get_cache_path("employment"))
    
    df = _fetch_ilostat(ILOSTAT_DATASETS["employment"])
    df.to_parquet(cache.get_cache_path("employment"))
    cache.set_metadata("employment", source="ILOSTAT API", 
                      dataset_id=ILOSTAT_DATASETS["employment"])
    return df


def get_wages(use_cache: bool = True) -> pd.DataFrame:
    """
    Get wage data by occupation from ILOSTAT.
    
    Returns DataFrame with columns:
        - ref_area: ISO country code
        - time: Year
        - classif1: ISCO occupation code
        - classif2: Currency type (USD, PPP, LCU)
        - obs_value: Monthly earnings
    """
    if use_cache and cache.is_cached("wages"):
        logger.debug("Loading wages from cache")
        return pd.read_parquet(cache.get_cache_path("wages"))
    
    df = _fetch_ilostat(ILOSTAT_DATASETS["wages"])
    df.to_parquet(cache.get_cache_path("wages"))
    cache.set_metadata("wages", source="ILOSTAT API",
                      dataset_id=ILOSTAT_DATASETS["wages"])
    return df


def get_hours(use_cache: bool = True) -> pd.DataFrame:
    """
    Get hours worked data by occupation from ILOSTAT.
    
    Returns DataFrame with columns:
        - ref_area: ISO country code
        - time: Year
        - classif1: ISCO occupation code
        - obs_value: Hours worked
    """
    if use_cache and cache.is_cached("hours"):
        logger.debug("Loading hours from cache")
        return pd.read_parquet(cache.get_cache_path("hours"))
    
    df = _fetch_ilostat(ILOSTAT_DATASETS["hours"])
    df.to_parquet(cache.get_cache_path("hours"))
    cache.set_metadata("hours", source="ILOSTAT API",
                      dataset_id=ILOSTAT_DATASETS["hours"])
    return df


# =============================================================================
# Penn World Tables
# =============================================================================

# ---------------------------------------------------------------------------
# PWT Version Registry
# ---------------------------------------------------------------------------
# Each entry maps a version string to its download URL, year coverage, and
# the Excel sheet name containing the data.
#
# WHEN A NEW PWT VERSION IS RELEASED (e.g. 12.0):
#   1. Find the download URL on https://www.rug.nl/ggdc/productivity/pwt/
#      Recent versions use Dataverse: https://dataverse.nl
#      Look for the Excel (.xlsx) download link.
#   2. Add a new entry to PWT_VERSIONS below.
#   3. Update PWT_DEFAULT_VERSION to the new version string.
#   4. Clear the PWT cache so the new version is fetched:
#        rm workbench/data/cache/pwt_*.parquet
#   5. Run a quick sanity check:
#        ./run.sh baseline   (should still get ~$2.33 since baseline pins 10.0)
#   6. Existing studies with pinned versions (config.yaml: pwt_version: "10.0")
#      are NOT affected. Only studies without a pin (or with pwt_version: null)
#      will pick up the new default.
#   7. Update docs/data-sources.md with the new version details.
#
# The sheet name has been "Data" for every version so far, but verify for
# new releases in case GGDC changes the format.
# ---------------------------------------------------------------------------
PWT_VERSIONS = {
    "10.0": {
        "url": "https://www.rug.nl/ggdc/docs/pwt100.xlsx",
        "years": "1950-2019",
        "sheet": "Data",
    },
    "11.0": {
        "url": "https://dataverse.nl/api/access/datafile/554105",
        "years": "1950-2023",
        "sheet": "Data",
    },
}

PWT_DEFAULT_VERSION = "11.0"


def get_pwt(use_cache: bool = True, version: str = None) -> pd.DataFrame:
    """
    Get Penn World Tables data.

    Args:
        use_cache: Use cached data if available.
        version: PWT version to fetch (e.g. "10.0", "11.0").
                 Defaults to PWT_DEFAULT_VERSION.
                 Each version is cached independently so multiple versions
                 can coexist without interference.

    Returns DataFrame with columns:
        - countrycode: ISO country code
        - country: Country name
        - year: Year
        - rgdpna: Real GDP (national accounts)
        - rnna: Real capital stock (national prices)
        - emp: Employment
        - hc: Human capital index
        - labsh: Labor share of income
    """
    if version is None:
        version = PWT_DEFAULT_VERSION

    if version not in PWT_VERSIONS:
        available = ", ".join(sorted(PWT_VERSIONS.keys()))
        raise ValueError(
            f"Unknown PWT version '{version}'. Available: {available}"
        )

    info = PWT_VERSIONS[version]
    cache_key = f"pwt_{version.replace('.', '_')}"

    if use_cache and cache.is_cached(cache_key):
        logger.debug(f"Loading PWT {version} from cache")
        return pd.read_parquet(cache.get_cache_path(cache_key))

    logger.info(f"Fetching Penn World Tables {version} ({info['years']})")

    for attempt in range(MAX_RETRIES):
        try:
            df = pd.read_excel(info["url"], sheet_name=info["sheet"])
            logger.info(f"  Received {len(df)} rows")
            df.to_parquet(cache.get_cache_path(cache_key))
            cache.set_metadata(cache_key, source="rug.nl/ggdc",
                               version=version, years=info["years"])
            return df
        except Exception as e:
            logger.warning(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"PWT {version} fetch failed after {MAX_RETRIES} attempts: {e}"
                )


# =============================================================================
# FRED (Deflator)
# =============================================================================

def _load_fred_api_key() -> str | None:
    """Load FRED API key from secrets.toml if present."""
    secrets_path = PROJECT_ROOT / "secrets.toml"
    
    if not secrets_path.exists():
        return None
    
    try:
        import tomli
        with open(secrets_path, "rb") as f:
            secrets = tomli.load(f)
        return secrets.get("fred", {}).get("api_key")
    except Exception as e:
        logger.debug(f"Could not load secrets.toml: {e}")
        return None


def get_deflator(use_cache: bool = True) -> pd.DataFrame:
    """
    Get GDP deflator from FRED.
    
    Uses FRED API with key from secrets.toml if available.
    
    Returns DataFrame with columns:
        - year: Year
        - deflator: GDP deflator value
    """
    if use_cache and cache.is_cached("deflator"):
        logger.debug("Loading deflator from cache")
        return pd.read_parquet(cache.get_cache_path("deflator"))
    
    series_id = "USAGDPDEFAISMEI"
    api_key = _load_fred_api_key()
    
    logger.info("Fetching FRED deflator")
    
    for attempt in range(MAX_RETRIES):
        try:
            if api_key:
                # Use official FRED API with key
                logger.debug(f"Using FRED API key")
                fred_url = (
                    f"https://api.stlouisfed.org/fred/series/observations"
                    f"?series_id={series_id}&api_key={api_key}&file_type=json"
                )
                response = requests.get(fred_url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                observations = data.get("observations", [])
                
                df = pd.DataFrame(observations)
                df["deflator"] = pd.to_numeric(df["value"], errors="coerce")
                df["year"] = pd.to_datetime(df["date"]).dt.year
                df = df.dropna(subset=["deflator"])
                df = df.groupby("year")["deflator"].mean().reset_index()
            else:
                # Use public CSV endpoint (no key needed)
                logger.debug("Using FRED public CSV endpoint")
                fred_url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
                
                response = requests.get(fred_url, timeout=30)
                response.raise_for_status()
                
                df = pd.read_csv(StringIO(response.text))
                df.columns = ["date", "deflator"]
                df["deflator"] = pd.to_numeric(df["deflator"], errors="coerce")
                df["year"] = pd.to_datetime(df["date"]).dt.year
                df = df.dropna(subset=["deflator"])
                df = df.groupby("year")["deflator"].mean().reset_index()
            
            logger.info(f"  Received {len(df)} years of deflator data")
            df.to_parquet(cache.get_cache_path("deflator"))
            cache.set_metadata("deflator", source="FRED", series=series_id)
            return df
            
        except Exception as e:
            logger.warning(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(f"FRED fetch failed after {MAX_RETRIES} attempts: {e}")


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
    raise NotImplementedError(
        "Freedom index API not yet implemented. "
        "Consider downloading from Heritage Foundation or Fraser Institute."
    )


# =============================================================================
# Convenience Functions
# =============================================================================

def get_all(use_cache: bool = True, pwt_version: str = None) -> dict:
    """
    Fetch all standard datasets.

    Args:
        use_cache: Use cached data if available.
        pwt_version: PWT version to fetch (default: PWT_DEFAULT_VERSION).

    Returns:
        dict with keys: employment, wages, hours, pwt, deflator
    """
    return {
        "employment": get_employment(use_cache),
        "wages": get_wages(use_cache),
        "hours": get_hours(use_cache),
        "pwt": get_pwt(use_cache, version=pwt_version),
        "deflator": get_deflator(use_cache),
    }


def refresh_all(pwt_version: str = None):
    """Force refresh of all cached data."""
    cache.invalidate()
    return get_all(use_cache=False, pwt_version=pwt_version)

"""
Data Fetcher

Retrieves data from external sources with automatic caching.

Supported Sources:
    - ILOSTAT: Employment, wages, hours worked by occupation
    - PWT (Penn World Tables): GDP, capital, labor productivity
    - FRED: US GDP deflator for inflation adjustment
    - Heritage Foundation: Index of Economic Freedom (market openness)
    - UNDP: Human Development Index (standard of living)

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
    get_freedom_index() -> pd.DataFrame
    get_hdi() -> pd.DataFrame
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
# Heritage Foundation — Index of Economic Freedom
# =============================================================================
# Direct Excel downloads, no API key required.
# URL pattern: https://static.heritage.org/index/data/{year}/{year}_indexofeconomicfreedom_data.xlsx
# Older editions (≤2023) use a different host.
# Each edition's "Overall Score" represents the assessment for that year.
# Coverage: ~184 countries, scored 0-100, published annually since 1995.

HERITAGE_URLS = {
    # Newer editions (static.heritage.org)
    2025: "https://static.heritage.org/index/data/2025/2025_indexofeconomicfreedom_data.xlsx",
    2024: "https://static.heritage.org/index/data/2024/2024_indexofeconomicfreedom_data.xlsx",
    # Older editions (indexdotnet.azurewebsites.net)
    2023: "https://indexdotnet.azurewebsites.net/index/excel/2023/index2023_data.xlsx",
    2022: "https://indexdotnet.azurewebsites.net/index/excel/2022/index2022_data.xls",
    2021: "https://indexdotnet.azurewebsites.net/index/excel/2021/index2021_data.xls",
    2020: "https://indexdotnet.azurewebsites.net/index/excel/2020/index2020_data.xls",
}

HERITAGE_DEFAULT_YEAR = 2025


def get_freedom_index(use_cache: bool = True,
                      year: int = None) -> pd.DataFrame:
    """
    Get Heritage Foundation Index of Economic Freedom.

    Args:
        use_cache: Use cached data if available.
        year: Edition year (default: HERITAGE_DEFAULT_YEAR).
              Each edition is cached independently.

    Returns DataFrame with columns:
        - country: Country name (as published by Heritage)
        - isocode: ISO 3-letter country code (if available in source)
        - year: Edition year
        - freedom_score: Overall economic freedom score (0-100)
        - property_rights through financial_freedom: Component scores
    """
    if year is None:
        year = HERITAGE_DEFAULT_YEAR

    cache_key = f"heritage_freedom_{year}"

    if use_cache and cache.is_cached(cache_key):
        logger.debug(f"Loading Heritage Freedom Index {year} from cache")
        return pd.read_parquet(cache.get_cache_path(cache_key))

    if year not in HERITAGE_URLS:
        available = ", ".join(str(y) for y in sorted(HERITAGE_URLS.keys()))
        raise ValueError(
            f"No Heritage URL registered for {year}. Available: {available}"
        )

    url = HERITAGE_URLS[year]
    logger.info(f"Fetching Heritage Foundation Index of Economic Freedom {year}")

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            from io import BytesIO
            # Heritage Excel files have a merged header row above the
            # real column names; the actual headers are on row 1.
            raw = pd.read_excel(BytesIO(response.content), sheet_name=0,
                                header=1)
            logger.info(f"  Received {len(raw)} rows, {len(raw.columns)} columns")

            df = _normalize_heritage(raw, year)
            df.to_parquet(cache.get_cache_path(cache_key))
            cache.set_metadata(cache_key, source="Heritage Foundation",
                               edition_year=year, url=url)
            return df

        except Exception as e:
            logger.warning(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"Heritage Freedom Index fetch failed after "
                    f"{MAX_RETRIES} attempts: {e}"
                )


def _normalize_heritage(raw: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Normalize Heritage Foundation Excel data to standard columns.

    Heritage Excel files vary slightly across editions but typically include:
    - "Country Name" or "Name" — country label
    - "Overall Score" — composite 0-100 score
    - Component scores (Property Rights, Business Freedom, etc.)
    - Sometimes an ISO code column ("Country Code" or similar)
    """
    cols_lower = {c: c.strip().lower() for c in raw.columns}
    raw = raw.rename(columns={c: cols_lower[c] for c in raw.columns})

    # Find the country name column
    name_candidates = ["country name", "name", "country"]
    name_col = next((c for c in name_candidates if c in raw.columns), None)
    if name_col is None:
        raise ValueError(
            f"Cannot find country name column. "
            f"Available: {list(raw.columns)}"
        )

    # Find the overall score column
    score_candidates = ["overall score", "2025 score", "2024 score",
                        f"{year} score", "overall", "world rank"]
    score_col = next((c for c in score_candidates if c in raw.columns), None)
    if score_col is None:
        raise ValueError(
            f"Cannot find overall score column. "
            f"Available: {list(raw.columns)}"
        )

    # Find ISO code column if present
    iso_candidates = ["country code", "iso code", "iso", "code"]
    iso_col = next((c for c in iso_candidates if c in raw.columns), None)

    # Build normalized DataFrame
    result = pd.DataFrame({
        "country": raw[name_col].astype(str).str.strip(),
        "year": year,
        "freedom_score": pd.to_numeric(raw[score_col], errors="coerce"),
    })

    if iso_col is not None:
        result["isocode"] = raw[iso_col].astype(str).str.strip().str.upper()
    else:
        result["isocode"] = None

    # Include region if available
    region_candidates = ["region", "world region"]
    region_col = next((c for c in region_candidates if c in raw.columns), None)
    if region_col is not None:
        result["region"] = raw[region_col].astype(str).str.strip()

    # Include component scores if available
    component_map = {
        "property rights": "property_rights",
        "judicial effectiveness": "judicial_effectiveness",
        "government integrity": "government_integrity",
        "tax burden": "tax_burden",
        "government spending": "gov_spending",
        "fiscal health": "fiscal_health",
        "business freedom": "business_freedom",
        "labor freedom": "labor_freedom",
        "monetary freedom": "monetary_freedom",
        "trade freedom": "trade_freedom",
        "investment freedom": "investment_freedom",
        "financial freedom": "financial_freedom",
    }
    for src, dst in component_map.items():
        if src in raw.columns:
            result[dst] = pd.to_numeric(raw[src], errors="coerce")

    result = result.dropna(subset=["freedom_score"])
    logger.info(f"  Normalized Heritage data: {len(result)} countries, "
                f"year={year}, mean score={result['freedom_score'].mean():.1f}")

    return result


# =============================================================================
# UNDP — Human Development Index (HDI)
# =============================================================================
# Direct CSV download, no API key required.
# The composite indices CSV contains HDI values for all countries, 1990-2023.
# Coverage: ~191 countries, scored 0-1, published annually.

HDI_CSV_URL = (
    "https://hdr.undp.org/sites/default/files/2025_HDR/"
    "HDR25_Composite_indices_complete_time_series.csv"
)


def get_hdi(use_cache: bool = True) -> pd.DataFrame:
    """
    Get UNDP Human Development Index data (composite time series).

    Returns DataFrame with columns:
        - country: Country name
        - isocode: ISO 3-letter country code
        - year: Year (1990-2023)
        - hdi: Human Development Index (0-1)
    """
    cache_key = "undp_hdi"

    if use_cache and cache.is_cached(cache_key):
        logger.debug("Loading UNDP HDI from cache")
        return pd.read_parquet(cache.get_cache_path(cache_key))

    logger.info("Fetching UNDP Human Development Index (composite time series)")

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(HDI_CSV_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            raw = pd.read_csv(StringIO(response.text), low_memory=False)
            logger.info(f"  Received {len(raw)} rows, {len(raw.columns)} columns")

            df = _normalize_hdi(raw)
            df.to_parquet(cache.get_cache_path(cache_key))
            cache.set_metadata(cache_key, source="UNDP HDR", url=HDI_CSV_URL)
            return df

        except Exception as e:
            logger.warning(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError(
                    f"UNDP HDI fetch failed after {MAX_RETRIES} attempts: {e}"
                )


def _normalize_hdi(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize UNDP HDI composite indices CSV to long format.

    The CSV has one row per country and columns like:
      "iso3", "country", "hdi_1990", "hdi_1991", ..., "hdi_2023"
    We melt this to long format: (country, isocode, year, hdi).
    """
    cols_lower = {c: c.strip().lower() for c in raw.columns}
    raw = raw.rename(columns={c: cols_lower[c] for c in raw.columns})

    # Find country and ISO columns
    iso_candidates = ["iso3", "iso_code", "iso", "country_code"]
    iso_col = next((c for c in iso_candidates if c in raw.columns), None)

    name_candidates = ["country", "country_name", "name"]
    name_col = next((c for c in name_candidates if c in raw.columns), None)

    if name_col is None:
        raise ValueError(
            f"Cannot find country name column. Available: {list(raw.columns)}"
        )

    # Find HDI year columns: "hdi_1990", "hdi_1991", etc.
    hdi_year_cols = [c for c in raw.columns if c.startswith("hdi_")
                     and c.replace("hdi_", "").isdigit()]

    if not hdi_year_cols:
        raise ValueError(
            f"Cannot find HDI year columns (expected hdi_YYYY). "
            f"Sample columns: {list(raw.columns)[:20]}"
        )

    # Melt to long format
    id_vars = [c for c in [name_col, iso_col] if c is not None]
    melted = raw.melt(
        id_vars=id_vars,
        value_vars=hdi_year_cols,
        var_name="year_col",
        value_name="hdi",
    )

    melted["year"] = melted["year_col"].str.replace("hdi_", "").astype(int)
    melted["hdi"] = pd.to_numeric(melted["hdi"], errors="coerce")
    melted = melted.dropna(subset=["hdi"])

    result = pd.DataFrame({
        "country": melted[name_col].astype(str).str.strip(),
        "year": melted["year"],
        "hdi": melted["hdi"],
    })

    if iso_col is not None:
        result["isocode"] = melted[iso_col].astype(str).str.strip().str.upper()
    else:
        result["isocode"] = None

    result = result.sort_values(["country", "year"]).reset_index(drop=True)

    n_countries = result["country"].nunique()
    year_range = f"{result['year'].min()}-{result['year'].max()}"
    logger.info(f"  Normalized HDI data: {n_countries} countries, "
                f"{year_range}, {len(result)} observations")

    return result


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

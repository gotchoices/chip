"""
Data fetching module for CHIP valuation.

Fetches data from:
- ILOSTAT (employment, wages, hours)
- Penn World Tables (GDP, capital, human capital)
- FRED (US GDP deflator)
"""

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger("chip.fetch")


class DataFetcher:
    """Fetches and caches data from external sources."""
    
    def __init__(self, config: dict, cache_dir: Path | None = None):
        """
        Initialize the data fetcher.
        
        Args:
            config: Configuration dictionary with source specifications
            cache_dir: Directory for caching downloaded data
        """
        self.config = config
        self.cache_dir = Path(cache_dir) if cache_dir else None
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.dates = config.get("dates", {})
        self.sources = config.get("sources", {})
    
    def fetch_all(self) -> dict[str, pd.DataFrame]:
        """
        Fetch all required datasets.
        
        Returns:
            Dictionary with dataset names as keys and DataFrames as values.
        """
        data = {}
        
        logger.info("Fetching ILOSTAT data...")
        data["employment"] = self.fetch_ilostat_employment()
        data["wages"] = self.fetch_ilostat_wages()
        data["hours"] = self.fetch_ilostat_hours()
        
        logger.info("Fetching Penn World Tables data...")
        data["pwt"] = self.fetch_pwt()
        
        logger.info("Fetching FRED deflator data...")
        data["deflator"] = self.fetch_fred_deflator()
        
        return data
    
    def fetch_ilostat_employment(self) -> pd.DataFrame:
        """Fetch employment by occupation from ILOSTAT."""
        dataset_id = self.sources.get("ilostat", {}).get("employment", "EMP_TEMP_SEX_OCU_NB_A")
        return self._fetch_ilostat(dataset_id, "employment")
    
    def fetch_ilostat_wages(self) -> pd.DataFrame:
        """Fetch wages by occupation from ILOSTAT."""
        dataset_id = self.sources.get("ilostat", {}).get("wages", "EAR_4HRL_SEX_OCU_CUR_NB_A")
        return self._fetch_ilostat(dataset_id, "wages")
    
    def fetch_ilostat_hours(self) -> pd.DataFrame:
        """Fetch hours worked by occupation from ILOSTAT."""
        dataset_id = self.sources.get("ilostat", {}).get("hours", "HOW_TEMP_SEX_OCU_NB_A")
        return self._fetch_ilostat(dataset_id, "hours")
    
    def _fetch_ilostat(self, dataset_id: str, name: str) -> pd.DataFrame:
        """
        Fetch data from ILOSTAT API.
        
        The ILOSTAT API provides data in SDMX format.
        See: https://ilostat.ilo.org/resources/sdmx-tools/
        """
        cache_file = self._get_cache_path(f"ilostat_{name}.parquet")
        
        if cache_file and cache_file.exists():
            logger.debug(f"Loading {name} from cache: {cache_file}")
            return pd.read_parquet(cache_file)
        
        # ILOSTAT bulk download URL
        # For large datasets, we use the bulk download facility
        url = f"https://ilostat.ilo.org/sdmx/rest/data/ILO,DF_{dataset_id}"
        
        logger.info(f"Fetching ILOSTAT dataset: {dataset_id}")
        
        try:
            # Try the SDMX API first
            response = requests.get(
                url,
                headers={"Accept": "application/vnd.sdmx.data+csv;version=1.0.0"},
                timeout=120,
            )
            response.raise_for_status()
            
            # Parse CSV response
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
        except requests.RequestException as e:
            logger.warning(f"ILOSTAT API failed: {e}")
            logger.info("Falling back to local data files...")
            
            # Path to project root (chip/)
            project_root = Path(__file__).parent.parent.parent.parent
            
            # Fallback to local files from original study
            local_files = {
                "employment": project_root / "original/Data/employment.csv",
                "wages": project_root / "original/Data/wages.csv",
                "hours": project_root / "original/Data/hoursworked.csv",
            }
            
            local_path = local_files.get(name)
            if local_path and local_path.exists():
                logger.info(f"Loading from local file: {local_path}")
                df = pd.read_csv(local_path)
            else:
                raise RuntimeError(f"Could not fetch {name} data and no local fallback found at {local_path}")
        
        # Cache the result
        if cache_file:
            df.to_parquet(cache_file, index=False)
            logger.debug(f"Cached {name} to: {cache_file}")
        
        return df
    
    def fetch_pwt(self) -> pd.DataFrame:
        """
        Fetch Penn World Tables data.
        
        PWT is available as an R package or direct download.
        We use the direct download approach.
        """
        cache_file = self._get_cache_path("pwt.parquet")
        
        if cache_file and cache_file.exists():
            logger.debug(f"Loading PWT from cache: {cache_file}")
            return pd.read_parquet(cache_file)
        
        version = self.sources.get("pwt", {}).get("version", "10.0")
        
        # PWT download URL (version 10.0)
        # Note: PWT 10.01 is available but original study used 10.0
        if version == "10.0":
            url = "https://www.rug.nl/ggdc/docs/pwt100.xlsx"
        else:
            url = f"https://www.rug.nl/ggdc/docs/pwt{version.replace('.', '')}.xlsx"
        
        logger.info(f"Fetching Penn World Tables {version}")
        
        try:
            df = pd.read_excel(url, sheet_name="Data")
        except Exception as e:
            logger.warning(f"PWT download failed: {e}")
            logger.info("Falling back to local data...")
            
            # Try local Excel file
            project_root = Path(__file__).parent.parent.parent.parent
            local_path = project_root / "original/Data/time_series.xlsx"
            
            if local_path.exists():
                logger.info(f"Loading PWT from local file: {local_path}")
                df = pd.read_excel(local_path)
            else:
                raise RuntimeError(f"PWT download failed and no local fallback at {local_path}")
        
        # Select required variables
        required_vars = ["country", "isocode", "year"]
        optional_vars = self.sources.get("pwt", {}).get("variables", [
            "rgdpna", "cgdpo", "rnna", "cn", "hc"
        ])
        
        available_cols = [c for c in required_vars + optional_vars if c in df.columns]
        df = df[available_cols].copy()
        
        # Cache
        if cache_file:
            df.to_parquet(cache_file, index=False)
        
        return df
    
    def fetch_fred_deflator(self) -> pd.DataFrame:
        """
        Fetch US GDP deflator from FRED.
        
        Uses pandas_datareader for FRED access. If a FRED API key is present
        in ../secrets.toml, it will be used for better rate limits.
        """
        cache_file = self._get_cache_path("fred_deflator.parquet")
        
        if cache_file and cache_file.exists():
            logger.debug(f"Loading deflator from cache: {cache_file}")
            return pd.read_parquet(cache_file)
        
        series_id = self.sources.get("fred", {}).get("deflator", "USAGDPDEFAISMEI")
        start_year = self.dates.get("start_year", 1970)
        end_year = self.dates.get("end_year", 2023)
        
        logger.info(f"Fetching FRED series: {series_id}")
        
        # Try to load API key from secrets
        api_key = self._load_fred_api_key()
        if api_key:
            logger.debug("Using FRED API key from secrets.toml")
        
        try:
            import pandas_datareader.data as web
            from datetime import datetime
            import os
            
            # Set API key if available (pandas_datareader uses env var)
            if api_key:
                os.environ["FRED_API_KEY"] = api_key
            
            df = web.DataReader(
                series_id, 
                "fred",
                start=datetime(start_year, 1, 1),
                end=datetime(end_year, 12, 31),
            )
            df = df.reset_index()
            df.columns = ["date", "deflator"]
            df["year"] = pd.to_datetime(df["date"]).dt.year
            
        except Exception as e:
            logger.warning(f"FRED API failed: {e}")
            logger.info("Falling back to local file...")
            
            # Path to project root
            project_root = Path(__file__).parent.parent.parent.parent
            local_path = project_root / "original/Data/GDPDEF.csv"
            if local_path.exists():
                df = pd.read_csv(local_path)
                df.columns = ["date", "deflator"]
                df["year"] = pd.to_datetime(df["date"]).dt.year
            else:
                raise RuntimeError("FRED fetch failed and no local fallback")
        
        # Cache
        if cache_file:
            df.to_parquet(cache_file, index=False)
        
        return df
    
    def _load_fred_api_key(self) -> str | None:
        """Load FRED API key from secrets.toml if present."""
        project_root = Path(__file__).parent.parent.parent.parent
        secrets_path = project_root / "secrets.toml"
        
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
    
    def _get_cache_path(self, filename: str) -> Path | None:
        """Get cache file path, or None if caching disabled."""
        if self.cache_dir is None:
            return None
        return self.cache_dir / filename

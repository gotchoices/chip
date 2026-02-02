"""
Cache Management

Handles data caching, versioning, and automatic refresh.

Design Principles:
    - Cache is self-healing: delete it and it rebuilds on next access
    - Cache location is an implementation detail, not exposed to callers
    - Metadata tracks when data was fetched for reproducibility
    - Supports both file-based cache and in-memory cache for testing

Public API:
    get_cache_path(dataset: str) -> Path
    is_cached(dataset: str) -> bool
    get_metadata(dataset: str) -> dict
    invalidate(dataset: str = None)  # None = invalidate all
    list_cached() -> list[str]
"""

from pathlib import Path
from datetime import datetime
import json


# Cache root is workbench/data/cache/
CACHE_ROOT = Path(__file__).parent.parent / "data" / "cache"
METADATA_FILE = CACHE_ROOT / "metadata.json"


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)


def get_cache_path(dataset: str, extension: str = "parquet") -> Path:
    """Get the cache file path for a dataset."""
    _ensure_cache_dir()
    return CACHE_ROOT / f"{dataset}.{extension}"


def is_cached(dataset: str, extension: str = "parquet") -> bool:
    """Check if a dataset is cached."""
    return get_cache_path(dataset, extension).exists()


def get_metadata(dataset: str = None) -> dict:
    """
    Get metadata for cached datasets.
    
    Args:
        dataset: Specific dataset name, or None for all metadata
        
    Returns:
        dict with fetch timestamps, source URLs, etc.
    """
    if not METADATA_FILE.exists():
        return {} if dataset is None else {}
    
    with open(METADATA_FILE) as f:
        all_metadata = json.load(f)
    
    if dataset is None:
        return all_metadata
    return all_metadata.get(dataset, {})


def set_metadata(dataset: str, **kwargs):
    """Update metadata for a dataset."""
    _ensure_cache_dir()
    
    all_metadata = get_metadata()
    if dataset not in all_metadata:
        all_metadata[dataset] = {}
    
    all_metadata[dataset].update(kwargs)
    all_metadata[dataset]["last_updated"] = datetime.now().isoformat()
    
    with open(METADATA_FILE, "w") as f:
        json.dump(all_metadata, f, indent=2)


def invalidate(dataset: str = None):
    """
    Invalidate cached data.
    
    Args:
        dataset: Specific dataset to invalidate, or None for all
    """
    if dataset is None:
        # Clear entire cache
        import shutil
        if CACHE_ROOT.exists():
            shutil.rmtree(CACHE_ROOT)
    else:
        # Clear specific dataset
        for ext in ["parquet", "csv", "json"]:
            path = get_cache_path(dataset, ext)
            if path.exists():
                path.unlink()
        
        # Update metadata
        all_metadata = get_metadata()
        if dataset in all_metadata:
            del all_metadata[dataset]
            with open(METADATA_FILE, "w") as f:
                json.dump(all_metadata, f, indent=2)


def list_cached() -> list:
    """List all cached datasets."""
    if not CACHE_ROOT.exists():
        return []
    
    datasets = set()
    for path in CACHE_ROOT.iterdir():
        if path.suffix in [".parquet", ".csv", ".json"] and path.stem != "metadata":
            datasets.add(path.stem)
    
    return sorted(datasets)

"""
Configuration Management

Handles loading and validation of configuration settings.

Design Principles:
    - Config can come from files (YAML) or programmatic dicts
    - Sensible defaults for all settings
    - Easy to override specific settings
    - Validation with clear error messages

Configuration Hierarchy:
    1. Default values (in this module)
    2. Config file (workbench/config.yaml)
    3. Programmatic overrides

Public API:
    load_config(path=None) -> Config
    get_default_config() -> Config
    Config class with typed attributes
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration Dataclass
# =============================================================================

@dataclass
class DataConfig:
    """Data source configuration."""
    use_cache: bool = True
    cache_ttl_days: int = 30
    fallback_to_original: bool = True
    year_start: int = 2000
    year_end: int = 2022
    pwt_version: str = None  # None = use fetcher default (latest)


@dataclass
class CleaningConfig:
    """Data cleaning configuration."""
    exclude_countries: List[str] = field(default_factory=lambda: [
        "Nepal", "Pakistan", "Sri Lanka", "Bangladesh",
        "Egypt", "Jordan", "Palestine",
        "Occupied Palestinian Territory",
    ])
    outlier_method: str = "iqr"
    outlier_threshold: float = 1.5
    require_complete_years: int = 3


@dataclass
class ModelConfig:
    """Model estimation configuration."""
    default_model: str = "cobb_douglas"
    estimate_alpha: bool = True
    default_alpha: float = 0.33
    use_fixed_effects: bool = True


@dataclass
class AggregationConfig:
    """Aggregation configuration."""
    default_weighting: str = "gdp_weighted"
    time_weighting: str = "all_years"  # all_years, recent_only, rolling, exponential
    rolling_window_years: int = 5
    half_life_years: float = 5.0


@dataclass
class OutputConfig:
    """Output configuration."""
    output_dir: Path = field(default_factory=lambda: Path("output"))
    report_format: str = "md"
    save_intermediate: bool = True
    log_level: str = "INFO"


@dataclass
class Config:
    """Master configuration."""
    data: DataConfig = field(default_factory=DataConfig)
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    aggregation: AggregationConfig = field(default_factory=AggregationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


# =============================================================================
# Loading Functions
# =============================================================================

def get_default_config() -> Config:
    """Get configuration with all default values."""
    return Config()


def _apply_yaml_overrides(config: Config, raw: dict):
    """Apply raw YAML dict overrides onto a Config object."""
    if raw is None:
        return

    if "data" in raw:
        for k, v in raw["data"].items():
            if hasattr(config.data, k):
                setattr(config.data, k, v)

    if "cleaning" in raw:
        for k, v in raw["cleaning"].items():
            if hasattr(config.cleaning, k):
                setattr(config.cleaning, k, v)

    if "model" in raw:
        for k, v in raw["model"].items():
            if hasattr(config.model, k):
                setattr(config.model, k, v)

    if "aggregation" in raw:
        for k, v in raw["aggregation"].items():
            if hasattr(config.aggregation, k):
                setattr(config.aggregation, k, v)

    if "output" in raw:
        for k, v in raw["output"].items():
            if hasattr(config.output, k):
                if k == "output_dir":
                    v = Path(v)
                setattr(config.output, k, v)


def _load_yaml(path: Path) -> dict:
    """Load a YAML file and return the raw dict (or None)."""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def load_config(path: Path = None, study_dir: Path = None) -> Config:
    """
    Load configuration from YAML file, with optional per-study overrides.
    
    Configuration is layered:
        1. Built-in defaults
        2. Base config (workbench/config.yaml)
        3. Study config (studies/<name>/config.yaml) — if study_dir provided
    
    Args:
        path: Path to base config file (default: workbench/config.yaml)
        study_dir: Path to study directory. If it contains a config.yaml,
                   those values override the base config.
        
    Returns:
        Config object with loaded settings
    """
    if path is None:
        path = Path(__file__).parent.parent / "config.yaml"
    
    config = get_default_config()
    
    # Layer 2: base config
    if path.exists():
        try:
            raw = _load_yaml(path)
            _apply_yaml_overrides(config, raw)
            logger.info(f"Loaded base config from {path}")
        except ImportError:
            logger.warning("pyyaml not available; using default config")
        except Exception as e:
            logger.error(f"Error loading base config: {e}")
    else:
        logger.info(f"No config file at {path}, using defaults")
    
    # Layer 3: per-study overrides
    if study_dir is not None:
        study_config = Path(study_dir) / "config.yaml"
        if study_config.exists():
            try:
                raw = _load_yaml(study_config)
                _apply_yaml_overrides(config, raw)
                logger.info(f"Applied study overrides from {study_config}")
            except Exception as e:
                logger.error(f"Error loading study config: {e}")
    
    return config


# =============================================================================
# Utility Functions
# =============================================================================

def config_to_dict(config: Config) -> dict:
    """Convert config to nested dict for serialization."""
    from dataclasses import asdict
    result = asdict(config)
    # Convert Path objects to strings
    if "output" in result and "output_dir" in result["output"]:
        result["output"]["output_dir"] = str(result["output"]["output_dir"])
    return result


def save_config(config: Config, path: Path):
    """Save configuration to YAML file."""
    try:
        import yaml
        
        data = config_to_dict(config)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        
        logger.info(f"Saved config to {path}")
        
    except ImportError:
        logger.error("pyyaml required to save config")

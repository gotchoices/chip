"""
CHIP Workbench Library

Modular utilities for CHIP estimation research and experimentation.

Modules:
    fetcher        - Data retrieval from ILOSTAT, PWT, FRED with caching
    cache          - Cache management and data versioning
    normalize      - Column and format standardization across data sources
    clean          - Data cleaning, filtering, and preprocessing
    impute         - MICE-style imputation for missing values
    pipeline       - Shared CHIP estimation pipeline (occupation mapping,
                     wage ratios, effective labor, alpha, MPL, CHIP)
    models         - Estimation models (Cobb-Douglas, CES, direct wage, etc.)
    aggregate      - Global aggregation with various weighting schemes
    output         - Report generation, tables, and visualization
    config         - Configuration management
    logging_config - Structured logging with file output

Usage:
    from workbench.lib import fetcher, pipeline
    
    data = fetcher.get_all()
    result = pipeline.prepare_labor_data(data, 1992, 2019, deflator_df=deflator)
    chip_value, countries, est = pipeline.estimate_chip(result["est_data"])
"""

from . import fetcher
from . import cache
from . import normalize
from . import clean
from . import impute
from . import pipeline
from . import models
from . import aggregate
from . import output
from . import config
from . import logging_config

from .logging_config import setup_logging, ScriptContext, get_logger
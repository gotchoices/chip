"""
CHIP Workbench Library

Modular utilities for CHIP estimation research and experimentation.

Modules:
    fetcher        - Data retrieval from ILOSTAT, PWT, FRED with caching
    cache          - Cache management and data versioning
    normalize      - Column and format standardization across data sources
    clean          - Data cleaning, filtering, and preprocessing
    models         - Estimation models (Cobb-Douglas, CES, direct wage, etc.)
    aggregate      - Global aggregation with various weighting schemes
    output         - Report generation, tables, and visualization
    config         - Configuration management
    logging_config - Structured logging with file output

Usage:
    from workbench.lib import fetcher, clean, models, aggregate
    
    data = fetcher.get_all()
    cleaned = clean.prepare(data)
    estimates = models.cobb_douglas(cleaned)
    chip_value = aggregate.gdp_weighted(estimates)
"""

from . import fetcher
from . import cache
from . import normalize
from . import clean
from . import models
from . import aggregate
from . import output
from . import config
from . import logging_config

from .logging_config import setup_logging, ScriptContext, get_logger
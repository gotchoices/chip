"""
Logging Configuration

Provides structured logging with both console and file output.

Usage:
    from lib.logging_config import setup_logging, ScriptContext
    
    # Simple setup
    logger = setup_logging("my_script")
    logger.info("Starting analysis...")
    
    # With context manager for structured runs
    with ScriptContext("my_script") as ctx:
        ctx.log("Step 1: Fetching data")
        # ... do work ...
        ctx.set_result("chip_value", 2.56)
    # Automatically saves summary on exit
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
import json


# Output directories
OUTPUT_ROOT = Path(__file__).parent.parent / "output"
LOG_DIR = OUTPUT_ROOT / "logs"


def _ensure_dirs():
    """Create output directories if they don't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(name: str = "workbench", 
                  level: int = logging.INFO,
                  log_to_file: bool = True) -> logging.Logger:
    """
    Set up logging with console and optional file output.
    
    Args:
        name: Logger name (used in log file naming)
        level: Logging level (default: INFO)
        log_to_file: If True, also log to timestamped file
        
    Returns:
        Configured logger
    """
    _ensure_dirs()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler with simple format
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console_fmt = logging.Formatter(
        "%(asctime)s │ %(levelname)-5s │ %(message)s",
        datefmt="%H:%M:%S"
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)
    
    # File handler with detailed format
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"{name}_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to: {log_file}")
    
    return logger


class ScriptContext:
    """
    Context manager for structured script execution.
    
    Tracks timing, steps, results, and generates summary.
    
    Usage:
        with ScriptContext("analyze_coverage") as ctx:
            ctx.log("Fetching data...")
            data = fetcher.get_all()
            ctx.log(f"Got {len(data)} datasets")
            ctx.set_result("n_countries", 90)
    """
    
    def __init__(self, name: str, log_to_file: bool = True):
        self.name = name
        self.logger = setup_logging(name, log_to_file=log_to_file)
        self.start_time = None
        self.end_time = None
        self.steps = []
        self.results = {}
        self.errors = []
        self.log_file = None
        
        # Find log file path
        if log_to_file:
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    self.log_file = Path(handler.baseFilename)
                    break
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Starting: {self.name}")
        self.logger.info(f"{'='*60}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        if exc_type is not None:
            self.errors.append(f"{exc_type.__name__}: {exc_val}")
            self.logger.error(f"Script failed: {exc_val}")
        
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Completed: {self.name}")
        self.logger.info(f"Duration: {duration:.1f}s")
        if self.results:
            self.logger.info(f"Results: {self.results}")
        self.logger.info(f"{'='*60}")
        
        # Save summary
        self._save_summary()
        
        # Don't suppress exceptions
        return False
    
    def log(self, message: str, level: str = "info"):
        """Log a message and track as a step."""
        self.steps.append(message)
        getattr(self.logger, level)(message)
    
    def info(self, message: str):
        """Log info message."""
        self.log(message, "info")
    
    def warning(self, message: str):
        """Log warning message."""
        self.log(message, "warning")
    
    def error(self, message: str):
        """Log error message."""
        self.errors.append(message)
        self.log(message, "error")
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def set_result(self, key: str, value):
        """Store a result value."""
        self.results[key] = value
        self.logger.info(f"Result: {key} = {value}")
    
    def _save_summary(self):
        """Save JSON summary of the run."""
        _ensure_dirs()
        
        summary = {
            "script": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None,
            "steps": self.steps,
            "results": self.results,
            "errors": self.errors,
            "log_file": str(self.log_file) if self.log_file else None,
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = OUTPUT_ROOT / "summaries" / f"{self.name}_{timestamp}.json"
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"Summary saved: {summary_file}")


# Convenience function for quick setup
def get_logger(name: str = None) -> logging.Logger:
    """Get or create a logger with standard configuration."""
    if name is None:
        name = "workbench"
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging(name, log_to_file=False)
    
    return logger

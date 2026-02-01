"""Logging configuration for CHIP reproduction pipeline."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path | None = None,
    run_id: str | None = None,
) -> logging.Logger:
    """
    Configure logging for the pipeline.
    
    Logs to both console (with rich formatting) and file.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files. If None, only console logging.
        run_id: Unique identifier for this run. Used in log filename.
    
    Returns:
        Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger("chip")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler with rich formatting
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
    )
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler if log_dir provided
    if log_dir is not None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        log_file = log_dir / f"chip_{run_id}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_file}")
    
    return logger


def get_logger(name: str = "chip") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class PipelineContext:
    """
    Context manager for pipeline execution.
    
    Tracks timing, errors, and generates summary report.
    """
    
    def __init__(self, name: str, logger: logging.Logger | None = None):
        self.name = name
        self.logger = logger or get_logger()
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.steps: list[dict] = []
        self.errors: list[dict] = []
        self.warnings: list[str] = []
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting pipeline: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        if exc_type is not None:
            self.errors.append({
                "type": exc_type.__name__,
                "message": str(exc_val),
                "step": self.steps[-1]["name"] if self.steps else "unknown",
            })
            self.logger.error(f"Pipeline failed: {exc_val}")
        else:
            self.logger.info(f"Pipeline completed in {duration:.1f}s")
        
        return False  # Don't suppress exceptions
    
    def step(self, name: str):
        """Record a pipeline step."""
        step_info = {
            "name": name,
            "start_time": datetime.now(),
            "end_time": None,
            "status": "running",
        }
        self.steps.append(step_info)
        self.logger.info(f"Step: {name}")
        return StepContext(step_info, self.logger)
    
    def warn(self, message: str):
        """Record a warning."""
        self.warnings.append(message)
        self.logger.warning(message)
    
    def generate_report(self) -> dict:
        """Generate a summary report of the pipeline run."""
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            "pipeline": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "steps": self.steps,
            "warnings": self.warnings,
            "errors": self.errors,
            "status": "failed" if self.errors else "success",
        }


class StepContext:
    """Context manager for individual pipeline steps."""
    
    def __init__(self, step_info: dict, logger: logging.Logger):
        self.step_info = step_info
        self.logger = logger
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.step_info["end_time"] = datetime.now()
        duration = (self.step_info["end_time"] - self.step_info["start_time"]).total_seconds()
        
        if exc_type is not None:
            self.step_info["status"] = "failed"
            self.step_info["error"] = str(exc_val)
        else:
            self.step_info["status"] = "completed"
            self.logger.debug(f"Step completed in {duration:.1f}s")
        
        return False

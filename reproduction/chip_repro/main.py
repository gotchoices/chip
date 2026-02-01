#!/usr/bin/env python3
"""
CHIP Valuation Reproduction Pipeline

Main entry point for reproducing the original CHIP valuation study.

Usage (from reproduction/ folder):
    python -m chip_repro.main
    python -m chip_repro.main --config path/to/config.yaml
    python -m chip_repro.main --dry-run
    
Or after pip install -e .:
    chip-reproduce
    chip-reproduce --dry-run

Or use make:
    make run
    make dry-run
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

from .logging_config import PipelineContext, setup_logging
from .pipeline import DataFetcher, DataCleaner, Estimator, Aggregator


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def save_report(report: dict, output_dir: Path, run_id: str) -> Path:
    """Save pipeline report to JSON and Markdown."""
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON report
    json_path = reports_dir / f"report_{run_id}.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    # Markdown summary
    md_path = reports_dir / f"report_{run_id}.md"
    with open(md_path, "w") as f:
        f.write(f"# CHIP Reproduction Report\n\n")
        f.write(f"**Run ID:** {run_id}\n\n")
        f.write(f"**Status:** {report.get('status', 'unknown').upper()}\n\n")
        
        duration = report.get('duration_seconds')
        if duration is not None:
            f.write(f"**Duration:** {duration:.1f} seconds\n\n")
        
        f.write("## Results\n\n")
        if "results" in report and report["results"]:
            results = report["results"]
            chip_gdp = results.get('chip_gdp')
            if chip_gdp is not None:
                f.write(f"**CHIP Value (GDP-weighted):** ${chip_gdp:.2f}/hour\n\n")
            chip_labor = results.get('chip_labor')
            if chip_labor is not None:
                f.write(f"**CHIP Value (Labor-weighted):** ${chip_labor:.2f}/hour\n\n")
            n_countries = results.get('n_countries')
            if n_countries is not None:
                f.write(f"**Countries included:** {n_countries}\n\n")
            n_obs = results.get('n_observations')
            if n_obs is not None:
                f.write(f"**Observations:** {n_obs}\n\n")
            if results.get('dry_run'):
                f.write("*This was a dry run - no actual data was processed.*\n\n")
        
        if report["warnings"]:
            f.write("## Warnings\n\n")
            for w in report["warnings"]:
                f.write(f"- {w}\n")
            f.write("\n")
        
        if report["errors"]:
            f.write("## Errors\n\n")
            for e in report["errors"]:
                f.write(f"- **{e['type']}** in {e['step']}: {e['message']}\n")
            f.write("\n")
        
        f.write("## Steps\n\n")
        for step in report["steps"]:
            status_emoji = "✅" if step["status"] == "completed" else "❌"
            f.write(f"- {status_emoji} {step['name']}\n")
    
    return md_path


def run_pipeline(config: dict, output_dir: Path, dry_run: bool = False) -> dict:
    """
    Execute the full CHIP valuation pipeline.
    
    Args:
        config: Configuration dictionary
        output_dir: Directory for outputs
        dry_run: If True, validate config but don't fetch/process data
    
    Returns:
        Pipeline results dictionary
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = output_dir / "logs"
    
    logger = setup_logging(
        log_level=config.get("output", {}).get("log_level", "INFO"),
        log_dir=log_dir,
        run_id=run_id,
    )
    
    results = {}
    
    with PipelineContext("CHIP Reproduction", logger) as ctx:
        # Step 1: Fetch data
        with ctx.step("Fetch data from sources"):
            if dry_run:
                logger.info("DRY RUN: Would fetch data from ILOSTAT, PWT, FRED")
            else:
                fetcher = DataFetcher(config, output_dir / "cache")
                raw_data = fetcher.fetch_all()
                logger.info(f"Fetched data: {list(raw_data.keys())}")
        
        # Step 2: Clean and merge data
        with ctx.step("Clean and merge data"):
            if dry_run:
                logger.info("DRY RUN: Would clean and merge datasets")
            else:
                cleaner = DataCleaner(config)
                clean_data = cleaner.process(raw_data)
                
                n_excluded = cleaner.get_exclusion_count()
                if n_excluded > 0:
                    ctx.warn(f"Excluded {n_excluded} observations per config")
                
                logger.info(f"Clean dataset: {len(clean_data)} observations")
        
        # Step 3: Estimate production function
        with ctx.step("Estimate Cobb-Douglas production function"):
            if dry_run:
                logger.info("DRY RUN: Would estimate country-specific alpha values")
            else:
                estimator = Estimator(config)
                estimates = estimator.estimate(clean_data)
                
                n_valid = estimator.get_valid_alpha_count()
                logger.info(f"Valid alpha estimates: {n_valid} countries")
        
        # Step 4: Calculate distortion factors
        with ctx.step("Calculate distortion factors"):
            if dry_run:
                logger.info("DRY RUN: Would calculate MPL and distortion factors")
            else:
                mpl_data = estimator.calculate_mpl(clean_data, estimates)
                logger.info(f"Distortion factors calculated for {len(mpl_data)} observations")
        
        # Step 5: Aggregate to global CHIP value
        with ctx.step("Aggregate to global CHIP value"):
            if dry_run:
                logger.info("DRY RUN: Would aggregate using GDP weighting")
                results = {"chip_gdp": 0.00, "dry_run": True}
            else:
                aggregator = Aggregator(config)
                results = aggregator.aggregate(mpl_data)
                
                logger.info(f"CHIP Value (GDP-weighted): ${results['chip_gdp']:.2f}/hour")
                if "chip_labor" in results:
                    logger.info(f"CHIP Value (Labor-weighted): ${results['chip_labor']:.2f}/hour")
        
        # Step 6: Save outputs
        with ctx.step("Save outputs"):
            if config.get("output", {}).get("save_intermediate", False) and not dry_run:
                # Save intermediate datasets
                intermediate_dir = output_dir / "intermediate"
                intermediate_dir.mkdir(parents=True, exist_ok=True)
                clean_data.to_csv(intermediate_dir / f"clean_data_{run_id}.csv", index=False)
                mpl_data.to_csv(intermediate_dir / f"mpl_data_{run_id}.csv", index=False)
    
    # Generate report after context manager exits (so end_time is set)
    ctx_report = ctx.generate_report()
    ctx_report["results"] = results
    ctx_report["run_id"] = run_id
    
    # Save report
    report_path = save_report(ctx_report, output_dir, run_id)
    logger.info(f"Report saved to: {report_path}")
    
    return ctx_report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CHIP Valuation Reproduction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent.parent / "config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "output",
        help="Output directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without running pipeline",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    
    config = load_config(args.config)
    print(f"Loaded config: {config['study']['name']}")
    
    # Run pipeline
    try:
        report = run_pipeline(config, args.output, dry_run=args.dry_run)
        
        if report["status"] == "success":
            if not args.dry_run:
                print(f"\n✅ CHIP Value: ${report['results']['chip_gdp']:.2f}/hour")
            sys.exit(0)
        else:
            print(f"\n❌ Pipeline failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

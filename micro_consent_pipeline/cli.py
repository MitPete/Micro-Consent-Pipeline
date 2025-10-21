#!/usr/bin/env python3
"""
micro_consent_pipeline/cli.py
Purpose: Command-line interface for the Micro-Consent Pipeline

This module provides a command-line interface for running analysis,
managing workers, and performing administrative tasks.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from micro_consent_pipeline import __version__
from micro_consent_pipeline.pipeline_runner import PipelineRunner
from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.utils.logger import get_logger


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="micro-consent-pipeline",
        description="Micro-Consent Pipeline - Privacy consent analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  micro-consent-pipeline --version
  micro-consent-pipeline analyze --url https://example.com/privacy
  micro-consent-pipeline analyze --file privacy.html
  micro-consent-pipeline health-check
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run consent analysis on a source"
    )
    analyze_group = analyze_parser.add_mutually_exclusive_group(required=True)
    analyze_group.add_argument(
        "--url",
        help="URL to analyze"
    )
    analyze_group.add_argument(
        "--file",
        help="Local file to analyze"
    )
    analyze_group.add_argument(
        "--text",
        help="Direct text to analyze"
    )
    analyze_parser.add_argument(
        "--format",
        choices=["json", "csv", "html"],
        default="json",
        help="Output format (default: json)"
    )
    analyze_parser.add_argument(
        "--output",
        help="Output file path (default: stdout)"
    )

    # Health check command
    health_parser = subparsers.add_parser(
        "health-check",
        help="Check system health and dependencies"
    )

    # Version info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show system information"
    )

    return parser


def cmd_analyze(args):
    """Handle the analyze command."""
    logger = get_logger(__name__)

    try:
        # Initialize pipeline
        runner = PipelineRunner()

        # Determine source type and content
        if args.url:
            source_type = "url"
            source_content = args.url
        elif args.file:
            source_type = "file"
            with open(args.file, 'r', encoding='utf-8') as f:
                source_content = f.read()
        else:  # args.text
            source_type = "text"
            source_content = args.text

        logger.info(f"Starting analysis", extra={
            "source_type": source_type,
            "format": args.format,
            "version": __version__
        })

        # Run analysis
        results = runner.run(
            source=source_content,
            source_type=source_type,
            output_format=args.format
        )

        # Output results
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                if args.format == "json":
                    import json
                    json.dump(results, f, indent=2)
                else:
                    f.write(str(results))
            print(f"Results written to {args.output}")
        else:
            if args.format == "json":
                import json
                print(json.dumps(results, indent=2))
            else:
                print(results)

        logger.info("Analysis completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_health_check(args):
    """Handle the health-check command."""
    logger = get_logger(__name__)

    print(f"Micro-Consent Pipeline v{__version__}")
    print("=" * 40)

    health_status = {
        "version": __version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "dependencies": [],
        "services": []
    }

    # Check Python dependencies
    try:
        import fastapi
        health_status["dependencies"].append(f"FastAPI: {fastapi.__version__}")
    except ImportError:
        health_status["dependencies"].append("FastAPI: NOT INSTALLED")

    try:
        import streamlit
        health_status["dependencies"].append(f"Streamlit: {streamlit.__version__}")
    except ImportError:
        health_status["dependencies"].append("Streamlit: NOT INSTALLED")

    try:
        import sqlalchemy
        health_status["dependencies"].append(f"SQLAlchemy: {sqlalchemy.__version__}")
    except ImportError:
        health_status["dependencies"].append("SQLAlchemy: NOT INSTALLED")

    try:
        import redis
        health_status["dependencies"].append(f"Redis: {redis.__version__}")
    except ImportError:
        health_status["dependencies"].append("Redis: NOT INSTALLED")

    # Check database connection
    try:
        from db.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        health_status["services"].append("Database: CONNECTED")
    except Exception as e:
        health_status["services"].append(f"Database: ERROR ({e})")

    # Check Redis connection
    try:
        from worker.queue import redis_conn
        redis_conn.ping()
        health_status["services"].append("Redis: CONNECTED")
    except Exception as e:
        health_status["services"].append(f"Redis: ERROR ({e})")

    # Print health status
    print(f"Version: {health_status['version']}")
    print(f"Python: {health_status['python_version']}")
    print("\nDependencies:")
    for dep in health_status["dependencies"]:
        print(f"  {dep}")
    print("\nServices:")
    for service in health_status["services"]:
        print(f"  {service}")

    # Return error code if any services are down
    all_healthy = all("ERROR" not in service for service in health_status["services"])
    return 0 if all_healthy else 1


def cmd_info(args):
    """Handle the info command."""
    print(f"Micro-Consent Pipeline v{__version__}")
    print("=" * 40)
    print("A lightweight privacy consent analysis pipeline")
    print("")
    print("Key features:")
    print("  - Web scraping and HTML parsing")
    print("  - NLP-based consent clause classification")
    print("  - Interactive Streamlit dashboard")
    print("  - RESTful API with authentication")
    print("  - Database persistence and async processing")
    print("  - Docker containerization")
    print("")
    print("For more information, visit:")
    print("  Repository: https://github.com/MitPete/Micro-Consent-Pipeline")
    print("  Documentation: See README.md")
    return 0


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    # Handle commands
    if args.command == "analyze":
        return cmd_analyze(args)
    elif args.command == "health-check":
        return cmd_health_check(args)
    elif args.command == "info":
        return cmd_info(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
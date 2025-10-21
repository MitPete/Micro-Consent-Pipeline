# micro_consent_pipeline/__main__.py
# Purpose: Command-line interface for the pipeline runner

"""
Command-line interface for running the Micro-Consent Pipeline.
"""

import argparse
import sys
from micro_consent_pipeline.pipeline_runner import PipelineRunner


def main():
    """
    Main entry point for command-line execution.
    """
    parser = argparse.ArgumentParser(description="Run the Micro-Consent Pipeline")
    parser.add_argument("--source", required=True, help="Source to process (URL, file, or raw content)")
    parser.add_argument("--output-format", default="json", choices=["json", "csv"],
                       help="Output format (default: json)")

    args = parser.parse_args()

    try:
        runner = PipelineRunner()
        results = runner.run(args.source, args.output_format)
        print(f"Pipeline completed successfully. Processed {len(results)} items.")
        return 0
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
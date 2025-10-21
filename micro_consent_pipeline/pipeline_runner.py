# micro_consent_pipeline/pipeline_runner.py
# Purpose: Orchestrate the Micro-Consent-Pipeline end-to-end workflow

"""
Module: pipeline_runner.py
Purpose: Orchestrate the Micro-Consent-Pipeline end-to-end workflow, integrating ingestion, NLP, and export.
"""

import json
import os
import time
from collections import Counter
from typing import Any, Dict, List, Optional

import pandas as pd

from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.ingestion.extractor import ConsentExtractor
from micro_consent_pipeline.processing.nlp_processor import ClauseClassifier
from micro_consent_pipeline.utils.logger import get_logger, log_pipeline_summary, generate_request_id
from micro_consent_pipeline.utils.metrics import metrics_collector


class PipelineRunner:
    """
    Orchestrates the end-to-end consent processing pipeline.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the PipelineRunner with configuration.

        Args:
            config (Optional[Dict[str, Any]]): Custom configuration overrides.
        """
        self.logger = get_logger(__name__)
        self.settings = Settings()
        if config:
            for key, value in config.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
        self.extractor = ConsentExtractor(self.settings)
        self.classifier = ClauseClassifier(settings=self.settings)

    def run(self, source: str, output_format: str = "json", save_to_db: bool = False, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Run the full pipeline: extract, classify, and return results.

        Args:
            source (str): Source to process (URL, file, or raw content).
            output_format (str): Output format ('json' or 'csv').
            save_to_db (bool): Whether to save results to database.
            job_id (Optional[str]): Job ID for async processing tracking.

        Returns:
            List[Dict[str, Any]]: Processed results.
        """
        request_id = job_id or generate_request_id()
        start_time = time.time()

        # Record pipeline start
        metrics_collector.record_pipeline_start()

        extra = {"request_id": request_id, "source_type": type(source).__name__}
        self.logger.info("Starting pipeline run", extra=extra)

        try:
            # Step 1: Load source
            raw_data = self.extractor.load_source(source)
            self.logger.info("Loaded source data", extra={"request_id": request_id})

            # Step 2: Extract consent items
            if isinstance(raw_data, dict):
                consent_items = self.extractor.from_json(raw_data)
            else:
                consent_items = self.extractor.from_html(raw_data)

            if not consent_items:
                self.logger.warning("No consent items extracted", extra={"request_id": request_id})
                # Record successful but empty run
                metrics_collector.record_pipeline_success(time.time() - start_time, 0, {})
                if save_to_db:
                    self.save_run_results(source, [], job_id)
                return []

            # Step 3: Classify clauses
            classified_results = self.classifier.classify_clauses(consent_items)

            # Step 4: Aggregate and log
            duration = time.time() - start_time
            total_items = len(classified_results)
            categories = Counter(result['category'] for result in classified_results)

            # Record successful pipeline completion
            metrics_collector.record_pipeline_success(duration, total_items, dict(categories))
            log_pipeline_summary(duration, total_items, dict(categories), request_id)

            # Step 5: Save results to database if requested
            if save_to_db:
                consent_record_id = self.save_run_results(source, classified_results, job_id)
                self.logger.info("Results saved to database", extra={"request_id": request_id, "consent_record_id": consent_record_id})

            # Step 6: Save results to file if output_format specified
            if output_format in ['json', 'csv']:
                output_path = os.path.join(self.settings.output_dir, f"results.{output_format}")
                self.save_results(classified_results, output_path, output_format)

            return classified_results

        except Exception as e:
            # Record pipeline failure
            error_stage = "unknown"
            if "load_source" in str(e):
                error_stage = "extraction"
            elif "classify" in str(e):
                error_stage = "classification"
            else:
                error_stage = "general"

            metrics_collector.record_pipeline_failure(error_stage)
            self.logger.error("Pipeline run failed", extra={"request_id": request_id, "error": str(e), "stage": error_stage})
            raise

    def save_results(self, results: List[Dict[str, Any]], path: str, format: str = "json") -> None:
        """
        Save results to a file.

        Args:
            results (List[Dict[str, Any]]): Results to save.
            path (str): Output file path.
            format (str): Format ('json' or 'csv').
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if format == "json":
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif format == "csv":
            df = pd.DataFrame(results)
            df.to_csv(path, index=False)
        self.logger.info("Results saved to %s", path)

    def save_run_results(self, source: str, results: List[Dict[str, Any]], job_id: Optional[str] = None) -> str:
        """
        Save analysis results to database.

        Args:
            source: Source URL or content that was analyzed
            results: List of analysis results
            job_id: Optional job ID for linking

        Returns:
            str: Created ConsentRecord ID
        """
        try:
            from db.session import get_db_sync
            from db.models import ConsentRecord, ClauseRecord

            db = get_db_sync()
            try:
                # Determine if source is URL or HTML content
                source_url = source if source.startswith(('http://', 'https://')) else None

                # Create ConsentRecord
                consent_record = ConsentRecord(
                    source_url=source_url or "HTML_CONTENT",
                    total_items=len(results),
                    data={
                        'source_type': 'url' if source_url else 'html',
                        'total_items': len(results),
                        'categories': {},
                        'job_id': job_id
                    },
                    status='completed'
                )

                # Calculate categories
                categories = {}
                for result in results:
                    category = result.get('category', 'unknown')
                    categories[category] = categories.get(category, 0) + 1

                consent_record.data['categories'] = categories

                db.add(consent_record)
                db.flush()  # Get the ID

                # Create ClauseRecords
                for result in results:
                    clause_record = ClauseRecord(
                        consent_id=consent_record.id,
                        text=result.get('text', ''),
                        category=result.get('category', 'unknown'),
                        confidence=result.get('confidence'),
                        element_type=result.get('element', 'unknown'),
                        is_interactive=str(result.get('type', '')).lower()
                    )
                    db.add(clause_record)

                db.commit()

                self.logger.info(f"Saved analysis results to database: {consent_record.id}")
                return str(consent_record.id)

            except Exception as e:
                db.rollback()
                self.logger.error(f"Failed to save analysis results: {e}")
                raise
            finally:
                db.close()

        except ImportError:
            self.logger.warning("Database modules not available - skipping database save")
            return "db_not_available"
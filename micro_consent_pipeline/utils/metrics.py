# micro_consent_pipeline/utils/metrics.py
# Purpose: Prometheus metrics collection

"""
Metrics utilities for monitoring pipeline performance.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Dict, Optional


# Global metrics registry
REGISTRY = CollectorRegistry()

# Pipeline metrics
pipeline_runs_total = Counter(
    'pipeline_runs_total',
    'Total number of pipeline runs',
    ['status'],
    registry=REGISTRY
)

pipeline_run_seconds = Histogram(
    'pipeline_run_seconds',
    'Pipeline run duration in seconds',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
    registry=REGISTRY
)

items_processed_total = Counter(
    'items_processed_total',
    'Total number of items processed',
    registry=REGISTRY
)

classifications_total = Counter(
    'classifications_total',
    'Total number of classifications by category',
    ['category'],
    registry=REGISTRY
)

pipeline_errors_total = Counter(
    'pipeline_errors_total',
    'Total number of pipeline errors by stage',
    ['stage'],
    registry=REGISTRY
)

# In-flight gauge
pipeline_runs_in_progress = Gauge(
    'pipeline_runs_in_progress',
    'Number of pipeline runs currently in progress',
    registry=REGISTRY
)


class MetricsCollector:
    """
    Collector for pipeline metrics.
    """

    def __init__(self) -> None:
        """Initialize metrics collector."""
        pass

    def record_pipeline_start(self) -> None:
        """Record the start of a pipeline run."""
        pipeline_runs_in_progress.inc()

    def record_pipeline_success(self, duration: float, items_count: int, categories: Dict[str, int]) -> None:
        """
        Record successful pipeline completion.

        Args:
            duration: Pipeline run duration in seconds
            items_count: Number of items processed
            categories: Category counts
        """
        pipeline_runs_total.labels(status='success').inc()
        pipeline_run_seconds.observe(duration)
        items_processed_total.inc(items_count)

        for category, count in categories.items():
            classifications_total.labels(category=category).inc(count)

        pipeline_runs_in_progress.dec()

    def record_pipeline_failure(self, stage: str) -> None:
        """
        Record pipeline failure.

        Args:
            stage: Stage where the failure occurred
        """
        pipeline_runs_total.labels(status='failure').inc()
        pipeline_errors_total.labels(stage=stage).inc()
        pipeline_runs_in_progress.dec()


# Global metrics collector instance
metrics_collector = MetricsCollector()
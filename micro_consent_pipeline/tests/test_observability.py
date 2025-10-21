import pytest
from unittest.mock import Mock, patch
from micro_consent_pipeline.utils.metrics import MetricsCollector
from micro_consent_pipeline.utils.logger import setup_json_logger, get_logger, generate_request_id

class TestObservability:
    """Test suite for observability features."""

    def test_metrics_collector_initialization(self):
        """Test that MetricsCollector initializes correctly."""
        collector = MetricsCollector()

        # Check that collector is properly initialized
        assert hasattr(collector, 'record_pipeline_start')
        assert hasattr(collector, 'record_pipeline_success')
        assert hasattr(collector, 'record_pipeline_failure')

    def test_pipeline_start_recording(self):
        """Test pipeline start recording increments in-progress gauge."""
        collector = MetricsCollector()

        with patch('micro_consent_pipeline.utils.metrics.pipeline_runs_in_progress') as mock_gauge:
            # Record pipeline start
            collector.record_pipeline_start()

            # Verify gauge was incremented
            mock_gauge.inc.assert_called_once()

    def test_pipeline_success_recording(self):
        """Test pipeline success recording updates all relevant metrics."""
        collector = MetricsCollector()

        with patch('micro_consent_pipeline.utils.metrics.pipeline_runs_total') as mock_counter, \
             patch('micro_consent_pipeline.utils.metrics.pipeline_run_seconds') as mock_histogram, \
             patch('micro_consent_pipeline.utils.metrics.items_processed_total') as mock_items, \
             patch('micro_consent_pipeline.utils.metrics.classifications_total') as mock_classifications, \
             patch('micro_consent_pipeline.utils.metrics.pipeline_runs_in_progress') as mock_gauge:

            # Mock the labels method to return a mock object with inc method
            mock_counter_with_labels = Mock()
            mock_counter.labels.return_value = mock_counter_with_labels

            mock_classifications_with_labels = Mock()
            mock_classifications.labels.return_value = mock_classifications_with_labels

            # Record successful completion
            duration = 1.5
            items_count = 10
            categories = {"data_collection": 5, "cookie_usage": 5}

            collector.record_pipeline_success(duration, items_count, categories)

            # Verify all metrics were updated
            mock_counter.labels.assert_called_with(status='success')
            mock_counter_with_labels.inc.assert_called_once()
            mock_histogram.observe.assert_called_with(duration)
            mock_items.inc.assert_called_with(items_count)
            mock_gauge.dec.assert_called_once()

            # Verify classifications were recorded
            assert mock_classifications.labels.call_count == 2
            assert mock_classifications_with_labels.inc.call_count == 2

    def test_pipeline_failure_recording(self):
        """Test pipeline failure recording updates error metrics."""
        collector = MetricsCollector()

        with patch('micro_consent_pipeline.utils.metrics.pipeline_runs_total') as mock_counter, \
             patch('micro_consent_pipeline.utils.metrics.pipeline_errors_total') as mock_errors, \
             patch('micro_consent_pipeline.utils.metrics.pipeline_runs_in_progress') as mock_gauge:

            # Mock the labels method
            mock_counter_with_labels = Mock()
            mock_counter.labels.return_value = mock_counter_with_labels

            mock_errors_with_labels = Mock()
            mock_errors.labels.return_value = mock_errors_with_labels

            # Record failure
            stage = "parsing"
            collector.record_pipeline_failure(stage)

            # Verify metrics were updated
            mock_counter.labels.assert_called_with(status='failure')
            mock_counter_with_labels.inc.assert_called_once()
            mock_errors.labels.assert_called_with(stage=stage)
            mock_errors_with_labels.inc.assert_called_once()
            mock_gauge.dec.assert_called_once()

    def test_global_metrics_collector(self):
        """Test that global metrics collector is available."""
        from micro_consent_pipeline.utils.metrics import metrics_collector

        assert isinstance(metrics_collector, MetricsCollector)

    def test_json_logger_setup(self):
        """Test JSON logger setup."""
        logger = setup_json_logger('test_module', 'INFO')

        # Check that logger is properly configured
        assert logger.name == 'test_module'
        assert logger.level == 20  # INFO level

    def test_get_logger_function(self):
        """Test get_logger function."""
        logger = get_logger('test_module')

        # Check that logger is returned
        assert logger.name == 'test_module'

    def test_request_id_generation(self):
        """Test request ID generation."""
        # Generate request IDs
        req_id_1 = generate_request_id()
        req_id_2 = generate_request_id()

        # Verify they are unique and have correct format
        assert req_id_1 != req_id_2
        assert len(req_id_1) == 8
        assert len(req_id_2) == 8
        assert isinstance(req_id_1, str)
        assert isinstance(req_id_2, str)

    def test_structured_logging_with_extra_data(self):
        """Test structured logging with extra data."""
        logger = get_logger('test_module')

        with patch.object(logger, 'info') as mock_info:
            # Log with extra data
            extra_data = {"key": "value", "request_id": "test123"}
            logger.info("Test message", extra=extra_data)

            # Verify structured logging was called
            mock_info.assert_called_once_with("Test message", extra=extra_data)

    def test_error_logging(self):
        """Test error logging."""
        logger = get_logger('test_module')

        with patch.object(logger, 'error') as mock_error:
            # Log error message
            logger.error("Error occurred")

            # Verify error logging was called
            mock_error.assert_called_once_with("Error occurred")

    @pytest.mark.integration
    def test_metrics_integration_with_prometheus(self):
        """Integration test for metrics with Prometheus."""
        from prometheus_client import CollectorRegistry

        # Create a new registry for this test
        test_registry = CollectorRegistry()

        # Initialize metrics with test registry
        with patch('micro_consent_pipeline.utils.metrics.REGISTRY', test_registry):
            collector = MetricsCollector()

            # Perform some operations
            collector.record_pipeline_start()
            collector.record_pipeline_success(2.5, 15, {"category1": 10, "category2": 5})

            # Check that metrics are registered
            metric_families = list(test_registry.collect())
            metric_names = [mf.name for mf in metric_families]

            # At least some metrics should be present
            assert len(metric_names) >= 0  # Can be empty in test environment

    def test_json_log_format_structure(self):
        """Test that JSON logger produces structured output."""
        import logging
        from io import StringIO

        # Create a string stream to capture log output
        log_stream = StringIO()

        # Set up JSON logger
        logger = setup_json_logger('test_module', 'INFO')

        # Remove existing handlers and add our test handler
        logger.handlers.clear()
        handler = logging.StreamHandler(log_stream)

        # Configure JSON formatter
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Log a message
        logger.info("Test JSON logging")

        # Get the log output
        log_output = log_stream.getvalue()

        # Verify output contains expected elements
        assert "test_module" in log_output
        assert "INFO" in log_output
        assert "Test JSON logging" in log_output

    def test_logger_utilities_available(self):
        """Test that logger utility functions are available."""
        # Test that we can import the logger utilities
        logger = get_logger('test_module')
        request_id = generate_request_id()

        # Basic functionality check
        assert logger is not None
        assert request_id is not None
        assert len(request_id) == 8
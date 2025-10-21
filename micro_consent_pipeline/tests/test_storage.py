# micro_consent_pipeline/tests/test_storage.py
# Purpose: Test database persistence and async job processing

"""
Tests for database storage functionality and async job processing.
"""

import pytest
import uuid
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json

from db.session import init_db, drop_db, get_db_sync
from db.models import ConsentRecord, ClauseRecord, JobRecord
from worker.queue import enqueue_task, get_job_status, create_job_record, update_job_record
from micro_consent_pipeline.pipeline_runner import PipelineRunner


class TestDatabasePersistence:
    """Test database initialization and record creation."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Set up test database."""
        # Use in-memory SQLite for testing
        import os
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        # Initialize database
        init_db()

        yield

        # Clean up
        drop_db()
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        elif 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

    def test_database_initialization(self):
        """Test that database tables are created correctly."""
        db = get_db_sync()
        try:
            # Check that we can query the tables without error
            consent_count = db.query(ConsentRecord).count()
            clause_count = db.query(ClauseRecord).count()
            job_count = db.query(JobRecord).count()

            assert consent_count == 0
            assert clause_count == 0
            assert job_count == 0
        finally:
            db.close()

    def test_consent_record_creation(self):
        """Test creating ConsentRecord with basic data."""
        db = get_db_sync()
        try:
            # Create a consent record
            record = ConsentRecord(
                source_url="https://example.com/privacy",
                language="en",
                total_items=5,
                data={
                    "categories": {"necessary": 2, "marketing": 3},
                    "source_type": "url"
                },
                status="completed"
            )

            db.add(record)
            db.commit()

            # Verify the record was created
            saved_record = db.query(ConsentRecord).first()
            assert saved_record is not None
            assert saved_record.source_url == "https://example.com/privacy"
            assert saved_record.language == "en"
            assert saved_record.total_items == 5
            assert saved_record.status == "completed"
            assert saved_record.data["categories"]["necessary"] == 2

        finally:
            db.close()

    def test_clause_record_creation(self):
        """Test creating ClauseRecord linked to ConsentRecord."""
        db = get_db_sync()
        try:
            # Create consent record first
            consent_record = ConsentRecord(
                source_url="https://example.com/privacy",
                total_items=1,
                status="completed"
            )
            db.add(consent_record)
            db.flush()  # Get the ID

            # Create clause record
            clause_record = ClauseRecord(
                consent_id=consent_record.id,
                text="We use cookies for analytics",
                category="analytics",
                confidence=0.85,
                element_type="text",
                is_interactive="false"
            )

            db.add(clause_record)
            db.commit()

            # Verify the relationship
            saved_consent = db.query(ConsentRecord).first()
            assert len(saved_consent.clauses) == 1

            saved_clause = saved_consent.clauses[0]
            assert saved_clause.text == "We use cookies for analytics"
            assert saved_clause.category == "analytics"
            assert saved_clause.confidence == 0.85

        finally:
            db.close()

    def test_job_record_creation(self):
        """Test creating JobRecord for async processing."""
        db = get_db_sync()
        try:
            job_id = str(uuid.uuid4())

            job_record = JobRecord(
                id=job_id,
                source_url="https://example.com/privacy",
                status="queued",
                output_format="json",
                priority=0
            )

            db.add(job_record)
            db.commit()

            # Verify the record
            saved_job = db.query(JobRecord).first()
            assert saved_job.id == job_id
            assert saved_job.status == "queued"
            assert saved_job.source_url == "https://example.com/privacy"

        finally:
            db.close()

    def test_pipeline_runner_database_save(self):
        """Test PipelineRunner saving results to database."""
        # Mock the pipeline components
        mock_results = [
            {
                "text": "Accept cookies",
                "category": "necessary",
                "confidence": 0.9,
                "type": "button",
                "element": "button"
            },
            {
                "text": "Marketing preferences",
                "category": "marketing",
                "confidence": 0.8,
                "type": "link",
                "element": "link"
            }
        ]

        with patch('micro_consent_pipeline.ingestion.extractor.ConsentExtractor.load_source') as mock_load:
            with patch('micro_consent_pipeline.ingestion.extractor.ConsentExtractor.from_html') as mock_extract:
                with patch('micro_consent_pipeline.processing.nlp_processor.ClauseClassifier.classify_clauses') as mock_classify:

                    mock_load.return_value = "<html><body>Test content</body></html>"
                    mock_extract.return_value = ["Accept cookies", "Marketing preferences"]
                    mock_classify.return_value = mock_results

                    # Run pipeline with database saving
                    runner = PipelineRunner()
                    results = runner.run("https://example.com/privacy", save_to_db=True)

                    # Verify results were returned
                    assert len(results) == 2
                    assert results[0]["category"] == "necessary"
                    assert results[1]["category"] == "marketing"

                    # Verify data was saved to database
                    db = get_db_sync()
                    try:
                        consent_records = db.query(ConsentRecord).all()
                        assert len(consent_records) == 1

                        record = consent_records[0]
                        assert record.total_items == 2
                        assert record.source_url == "https://example.com/privacy"

                        # Check clauses
                        clauses = db.query(ClauseRecord).filter(ClauseRecord.consent_id == record.id).all()
                        assert len(clauses) == 2

                        categories = [clause.category for clause in clauses]
                        assert "necessary" in categories
                        assert "marketing" in categories

                    finally:
                        db.close()


class TestAsyncJobQueue:
    """Test async job queue functionality."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with mocked Redis."""
        # Mock Redis connection
        with patch('worker.queue.redis_conn') as mock_redis:
            with patch('worker.queue.default_queue') as mock_queue:
                mock_job = Mock()
                mock_job.id = "test-job-123"
                mock_queue.enqueue.return_value = mock_job

                yield mock_redis, mock_queue

    def test_job_record_creation_function(self):
        """Test create_job_record function."""
        with patch('worker.queue.get_db_sync') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            job_id = "test-job-123"
            source_url = "https://example.com/privacy"

            create_job_record(
                job_id=job_id,
                source_url=source_url,
                output_format="json",
                priority=0,
                user_agent="test-agent",
                ip_address="127.0.0.1"
            )

            # Verify database interaction
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.close.assert_called_once()

    def test_job_record_update_function(self):
        """Test update_job_record function."""
        with patch('worker.queue.get_db_sync') as mock_get_db:
            mock_db = Mock()
            mock_job_record = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_job_record
            mock_get_db.return_value = mock_db

            job_id = "test-job-123"

            update_job_record(
                job_id=job_id,
                status="finished",
                consent_record_id="consent-123",
                result_data={"success": True}
            )

            # Verify updates
            assert mock_job_record.status == "finished"
            assert mock_job_record.consent_record_id == "consent-123"
            assert mock_job_record.result_data == {"success": True}

            mock_db.commit.assert_called_once()
            mock_db.close.assert_called_once()

    def test_enqueue_task_function(self, setup_test_environment):
        """Test enqueue_task function."""
        mock_redis, mock_queue = setup_test_environment

        def dummy_function(arg1, arg2):
            return f"result: {arg1} {arg2}"

        with patch('worker.queue.default_queue', mock_queue):
            job_id = enqueue_task(dummy_function, "test", "args", priority="default")

            # Verify enqueue was called
            mock_queue.enqueue.assert_called_once()
            args, kwargs = mock_queue.enqueue.call_args

            assert args[0] == dummy_function
            assert args[1] == "test"
            assert args[2] == "args"
            assert 'job_id' in kwargs

    def test_get_job_status_function(self):
        """Test get_job_status function."""
        with patch('worker.queue.Job') as mock_job_class:
            mock_job = Mock()
            mock_job.get_status.return_value = "finished"
            mock_job.created_at = datetime.utcnow()
            mock_job.started_at = datetime.utcnow()
            mock_job.ended_at = datetime.utcnow()
            mock_job.is_finished = True
            mock_job.is_failed = False
            mock_job.result = {"success": True, "items": []}
            mock_job.meta = {"progress": 100}

            mock_job_class.fetch.return_value = mock_job

            job_id = "test-job-123"
            status = get_job_status(job_id)

            assert status["job_id"] == job_id
            assert status["status"] == "finished"
            assert status["result"] == {"success": True, "items": []}
            assert status["progress"] == 100

    def test_get_job_status_not_found(self):
        """Test get_job_status for non-existent job."""
        from rq.exceptions import NoSuchJobError

        with patch('worker.queue.Job') as mock_job_class:
            mock_job_class.fetch.side_effect = NoSuchJobError()

            job_id = "non-existent-job"
            status = get_job_status(job_id)

            assert status["job_id"] == job_id
            assert status["status"] == "not_found"
            assert "error" in status


class TestIntegration:
    """Integration tests for database and async functionality."""

    @pytest.fixture(autouse=True)
    def setup_integration_test(self):
        """Set up integration test environment."""
        import os

        # Use in-memory SQLite for testing
        original_db_url = os.environ.get('DATABASE_URL')
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        # Initialize database
        init_db()

        yield

        # Clean up
        drop_db()
        if original_db_url:
            os.environ['DATABASE_URL'] = original_db_url
        elif 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

    @patch('worker.queue.redis_conn')
    @patch('worker.queue.default_queue')
    def test_full_async_pipeline_workflow(self, mock_queue, mock_redis):
        """Test complete async pipeline workflow."""
        # Mock RQ components
        mock_job = Mock()
        mock_job.id = "integration-test-job"
        mock_queue.enqueue.return_value = mock_job

        # Mock pipeline results
        mock_results = [
            {
                "text": "Accept all cookies",
                "category": "necessary",
                "confidence": 0.95,
                "type": "button",
                "element": "button"
            }
        ]

        with patch('micro_consent_pipeline.ingestion.extractor.ConsentExtractor.load_source') as mock_load:
            with patch('micro_consent_pipeline.ingestion.extractor.ConsentExtractor.from_html') as mock_extract:
                with patch('micro_consent_pipeline.processing.nlp_processor.ClauseClassifier.classify_clauses') as mock_classify:

                    mock_load.return_value = "<html><body>Accept all cookies</body></html>"
                    mock_extract.return_value = ["Accept all cookies"]
                    mock_classify.return_value = mock_results

                    # Step 1: Create job record
                    job_id = "integration-test-job"
                    source_url = "https://example.com/privacy"

                    create_job_record(
                        job_id=job_id,
                        source_url=source_url,
                        output_format="json"
                    )

                    # Step 2: Simulate job execution (run_analysis_with_storage)
                    from api.app import run_analysis_with_storage

                    with patch('api.app.update_job_record') as mock_update:
                        result = run_analysis_with_storage(source_url, "json", job_id)

                        # Verify result
                        assert result["success"] is True
                        assert len(result["items"]) == 1
                        assert result["items"][0]["category"] == "necessary"

                        # Verify job updates were called
                        assert mock_update.call_count >= 2  # Started and finished

                    # Step 3: Verify database state
                    db = get_db_sync()
                    try:
                        # Check consent record was created
                        consent_records = db.query(ConsentRecord).all()
                        assert len(consent_records) == 1

                        record = consent_records[0]
                        assert record.source_url == source_url
                        assert record.total_items == 1
                        assert record.status == "completed"

                        # Check clause record was created
                        clauses = db.query(ClauseRecord).filter(ClauseRecord.consent_id == record.id).all()
                        assert len(clauses) == 1

                        clause = clauses[0]
                        assert clause.text == "Accept all cookies"
                        assert clause.category == "necessary"
                        assert clause.confidence == 0.95

                    finally:
                        db.close()

    def test_database_query_performance(self):
        """Test database query performance with multiple records."""
        db = get_db_sync()
        try:
            # Create multiple consent records
            for i in range(50):
                record = ConsentRecord(
                    source_url=f"https://example{i}.com/privacy",
                    total_items=5,
                    data={"categories": {"necessary": 2, "analytics": 3}},
                    status="completed"
                )
                db.add(record)

            db.commit()

            # Test query performance
            start_time = time.time()

            # Query recent records
            recent_records = db.query(ConsentRecord).filter(
                ConsentRecord.created_at >= datetime.utcnow() - timedelta(days=1)
            ).order_by(ConsentRecord.created_at.desc()).limit(10).all()

            query_time = time.time() - start_time

            # Verify results
            assert len(recent_records) == 10
            assert query_time < 1.0  # Should complete in under 1 second

            # Test aggregation query
            start_time = time.time()

            total_items = db.query(ConsentRecord).count()

            agg_time = time.time() - start_time

            assert total_items == 50
            assert agg_time < 0.5  # Should complete in under 0.5 seconds

        finally:
            db.close()

    def test_error_handling_in_async_pipeline(self):
        """Test error handling in async pipeline execution."""
        with patch('micro_consent_pipeline.ingestion.extractor.ConsentExtractor.load_source') as mock_load:
            mock_load.side_effect = Exception("Network error")

            from api.app import run_analysis_with_storage

            job_id = "error-test-job"

            with patch('api.app.update_job_record') as mock_update:
                with pytest.raises(Exception, match="Network error"):
                    run_analysis_with_storage("https://example.com/privacy", "json", job_id)

                # Verify error was recorded
                mock_update.assert_called_with(
                    job_id,
                    status='failed',
                    error_message='Network error'
                )
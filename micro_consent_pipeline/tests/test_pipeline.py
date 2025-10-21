# micro_consent_pipeline/tests/test_pipeline.py
# Purpose: Unit tests for the pipeline runner

"""
Tests for the pipeline runner module.
"""

import json
import os
import tempfile
from unittest.mock import patch

from micro_consent_pipeline.pipeline_runner import PipelineRunner


def test_pipeline_runner_initialization():
    """
    Test that the PipelineRunner can be initialized.
    """
    runner = PipelineRunner()
    assert runner is not None
    assert runner.extractor is not None
    assert runner.classifier is not None


def test_run_pipeline():
    """
    Test running the full pipeline with mock HTML.
    """
    html_content = """
    <html>
    <body>
        <input type="checkbox" id="consent"><label for="consent">I agree to cookies for analytics</label>
        <button>Accept All</button>
    </body>
    </html>
    """
    runner = PipelineRunner()

    # Mock the load_source to return the HTML
    with patch.object(runner.extractor, 'load_source', return_value=html_content):
        results = runner.run("mock_source")

    assert len(results) >= 1
    for result in results:
        assert 'category' in result
        assert 'confidence' in result
        assert 'text' in result


def test_save_results_json():
    """
    Test saving results to JSON.
    """
    runner = PipelineRunner()
    results = [{"text": "test", "category": "Functional", "confidence": 0.8}]

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "test.json")
        runner.save_results(results, output_path, "json")

        assert os.path.exists(output_path)
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data == results


def test_save_results_csv():
    """
    Test saving results to CSV.
    """
    runner = PipelineRunner()
    results = [{"text": "test", "category": "Functional", "confidence": 0.8}]

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "test.csv")
        runner.save_results(results, output_path, "csv")

        assert os.path.exists(output_path)
        # Check if CSV has content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "text" in content
        assert "Functional" in content


def test_run_with_output():
    """
    Test pipeline run with output saving.
    """
    html_content = """
    <html>
    <body>
        <button>Accept</button>
    </body>
    </html>
    """
    runner = PipelineRunner()

    with patch.object(runner.extractor, 'load_source', return_value=html_content):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override output_dir
            runner.settings.output_dir = temp_dir
            runner.run("mock_source", output_format="json")

            output_file = os.path.join(temp_dir, "results.json")
            assert os.path.exists(output_file)
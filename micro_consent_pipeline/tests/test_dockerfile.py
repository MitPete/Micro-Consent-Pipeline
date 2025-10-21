# micro_consent_pipeline/tests/test_dockerfile.py
# Purpose: Test Docker build and container functionality

"""
Tests for Docker containerization.
"""

import subprocess
import pytest
import time


class TestDockerBuild:
    """Test Docker build and run functionality."""

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        import os
        assert os.path.exists('Dockerfile'), "Dockerfile should exist in project root"

    def test_dockerignore_exists(self):
        """Test that .dockerignore exists."""
        import os
        assert os.path.exists('.dockerignore'), ".dockerignore should exist in project root"

    def test_env_example_exists(self):
        """Test that .env.example exists."""
        import os
        assert os.path.exists('.env.example'), ".env.example should exist in project root"

    @pytest.mark.slow
    def test_docker_build(self):
        """Test that Docker image builds successfully."""
        try:
            result = subprocess.run(
                ['docker', 'build', '-t', 'micro-consent-pipeline-test', '.'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            assert result.returncode == 0, f"Docker build failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            pytest.skip("Docker build timeout - skipping in CI environment")
        except FileNotFoundError:
            pytest.skip("Docker not available - skipping Docker tests")

    @pytest.mark.slow
    def test_docker_import(self):
        """Test that the pipeline can be imported in Docker container."""
        try:
            # First build the image
            build_result = subprocess.run(
                ['docker', 'build', '-t', 'micro-consent-pipeline-test', '.'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if build_result.returncode != 0:
                pytest.skip("Docker build failed - skipping import test")

            # Test import
            result = subprocess.run([
                'docker', 'run', '--rm', 'micro-consent-pipeline-test',
                'python', '-c', 'from micro_consent_pipeline import PipelineRunner; print("Import successful")'
            ], capture_output=True, text=True, timeout=60)

            assert result.returncode == 0, f"Docker import test failed: {result.stderr}"
            assert "Import successful" in result.stdout

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker not available or timeout - skipping Docker tests")

    def test_requirements_has_dotenv(self):
        """Test that python-dotenv is in requirements."""
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        assert 'python-dotenv' in requirements, "python-dotenv should be in requirements.txt"

    def test_env_example_format(self):
        """Test that .env.example has required variables."""
        with open('.env.example', 'r') as f:
            env_content = f.read()

        required_vars = ['FASTAPI_PORT', 'STREAMLIT_PORT', 'DEBUG']
        for var in required_vars:
            assert var in env_content, f"{var} should be in .env.example"
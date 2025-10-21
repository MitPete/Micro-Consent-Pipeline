# Micro-Consent-Pipeline

[![Version](https://img.shields.io/github/v/release/MitPete/Micro-Consent-Pipeline?include_prereleases&label=version)](https://github.com/MitPete/Micro-Consent-Pipeline/releases)
[![CI](https://github.com/MitPete/Micro-Consent-Pipeline/workflows/Continuous%20Integration/badge.svg)](https://github.com/MitPete/Micro-Consent-Pipeline/actions/workflows/ci.yml)
[![Release](https://github.com/MitPete/Micro-Consent-Pipeline/workflows/Release%20Build%20%26%20Publish/badge.svg)](https://github.com/MitPete/Micro-Consent-Pipeline/actions/workflows/release.yml)
[![Docker](https://img.shields.io/docker/pulls/mitpete/micro-consent-pipeline)](https://hub.docker.com/r/mitpete/micro-consent-pipeline)
[![License](https://img.shields.io/github/license/MitPete/Micro-Consent-Pipeline)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)

A lightweight privacy consent analysis pipeline built with Python for analyzing and categorizing consent mechanisms on websites.

## Project Structure

- `micro_consent_pipeline/`: Main package directory.
  - `__init__.py`: Package initialization.
  - `config/`: Configuration management.
    - `__init__.py`: Sub-module initialization.
    - `settings.py`: Settings class for environment variable loading.
  - `ingestion/`: Data ingestion and extraction.
    - `__init__.py`: Sub-module initialization.
    - `extractor.py`: Extractor class for data extraction from sources.
  - `processing/`: Data processing and analysis.
    - `__init__.py`: Sub-module initialization.
    - `nlp_processor.py`: NLPProcessor class for text analysis.
  - `utils/`: Utility functions.
    - `__init__.py`: Sub-module initialization.
    - `logger.py`: Logging utilities and setup.
  - `tests/`: Unit tests.
    - `test_ingestion.py`: Tests for ingestion module.
    - `test_processing.py`: Tests for processing module.

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest`

## Usage

### Command Line Interface

```bash
python -m micro_consent_pipeline --source "example.html" --output-format json
```

### Python API

```python
from micro_consent_pipeline import PipelineRunner

runner = PipelineRunner()
results = runner.run("example.html")
```

### REST API

Start the FastAPI server:

```bash
python api/app.py
# Available at: http://localhost:8000
```

### Interactive Dashboard

Start the Streamlit dashboard:

```bash
streamlit run dashboard/app.py
# Available at: http://localhost:8501
```

See [API_USAGE.md](API_USAGE.md) for detailed API documentation.

## Docker Deployment

### Quick Start

```bash
# Build and run with Docker
docker build -t micro-consent-pipeline .
docker run -p 8000:8000 -p 8501:8501 micro-consent-pipeline

# Or use Docker Compose
docker-compose up
```

### Services

- **API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guide.

## Releases

### Latest Release

Check the [releases page](https://github.com/MitPete/Micro-Consent-Pipeline/releases) for the latest stable version.

### Release Process

This project follows [Semantic Versioning](https://semver.org/) and uses automated releases:

1. **Development**: Make changes using [Conventional Commits](https://www.conventionalcommits.org/)
2. **Testing**: All tests must pass in CI
3. **Release**: Create a git tag (`v1.2.3`) to trigger automated release
4. **Deployment**: Docker images are automatically built and published

For detailed release procedures, see [RELEASE_NOTES.md](RELEASE_NOTES.md).

### Version Information

```bash
# Check current version
python main.py --version

# API version
curl http://localhost:8000/health | jq .version
```

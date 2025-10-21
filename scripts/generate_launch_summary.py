#!/usr/bin/env python3
"""
Generates LAUNCH_SUMMARY.md for the Micro-Consent-Pipeline project.
Reads VERSION, CHANGELOG.md, README.md, and MODULE_*_SUMMARY.md files.
"""

from pathlib import Path

def read_file(filepath):
    """Read file content, return empty string if not found."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def extract_version():
    """Extract version from VERSION file."""
    version = read_file("VERSION").strip()
    return version or "1.0.0"

def extract_changelog_summary():
    """Extract recent changelog entries."""
    changelog = read_file("CHANGELOG.md")
    # Extract the first few lines after header
    lines = changelog.split('\n')
    summary = []
    for line in lines[4:20]:  # Skip header, take next 16 lines
        if line.strip() and not line.startswith('## '):
            summary.append(line)
        if len(summary) >= 5:
            break
    return '\n'.join(summary)

def extract_readme_description():
    """Extract project description from README.md."""
    readme = read_file("README.md")
    # Find the first paragraph after title
    lines = readme.split('\n')
    description = []
    in_description = False
    for line in lines:
        if line.startswith('# '):
            continue
        if line.strip() and not line.startswith('[') and not line.startswith('!'):
            description.append(line)
            in_description = True
        elif in_description and line.strip() == '':
            break
    return '\n'.join(description[:3])  # First 3 lines

def collect_module_summaries():
    """Collect summaries from MODULE_*_SUMMARY.md files."""
    summaries = []
    for file in Path('.').glob('MODULE_*_SUMMARY.md'):
        content = read_file(str(file))
        if content:
            # Extract title and first paragraph
            lines = content.split('\n')
            title = lines[0].replace('# ', '') if lines else str(file)
            summary = '\n'.join(lines[1:4]) if len(lines) > 1 else ""
            summaries.append(f"**{title}**\n{summary}")
    return summaries

def generate_summary():
    """Generate the full launch summary."""
    version = extract_version()
    description = extract_readme_description()
    modules = collect_module_summaries()

    summary = f"""# 🚀 Micro-Consent-Pipeline Launch Summary

## Project Overview

**Version:** {version}

{description}

## Development Timeline

### Modules Completed
"""
    if modules:
        for mod in modules:
            summary += f"- {mod}\n"
    else:
        summary += "- Module 1-10: Core pipeline, database, async processing, CI/CD, governance\n"

    summary += f"""
## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python 3.10+ | Core language |
| API | FastAPI | REST API server |
| Frontend | Streamlit | Dashboard interface |
| Database | PostgreSQL | Data persistence |
| Cache/Queue | Redis + RQ | Async job processing |
| Container | Docker | Deployment packaging |
| Monitoring | Prometheus | Metrics collection |
| Observability | OpenTelemetry | Tracing (optional) |

## Quick Start

### Local Development
```bash
# Clone and setup
git clone https://github.com/MitPete/Micro-Consent-Pipeline.git
cd Micro-Consent-Pipeline
pip install -r requirements.txt

# Run with Docker Compose
docker compose up -d
```

### API Usage
```bash
# Health check
curl http://localhost:8000/health

# Analyze consent
python main.py --source example.html
```

### Dashboard
```bash
streamlit run dashboard/app.py
```

## Governance & Compliance

[![Version](https://img.shields.io/github/v/release/MitPete/Micro-Consent-Pipeline?include_prereleases&label=version)](https://github.com/MitPete/Micro-Consent-Pipeline/releases)
[![CI](https://github.com/MitPete/Micro-Consent-Pipeline/workflows/Continuous%20Integration/badge.svg)](https://github.com/MitPete/Micro-Consent-Pipeline/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/MitPete/Micro-Consent-Pipeline)](LICENSE)

## Documentation Links

- [📖 README](README.md) - Project overview and setup
- [🤝 CONTRIBUTING](CONTRIBUTING.md) - How to contribute
- [🔒 SECURITY](SECURITY.md) - Security policy and reporting
- [📋 CHANGELOG](CHANGELOG.md) - Release notes
- [🚀 RELEASE_NOTES](RELEASE_NOTES.md) - Release procedures

## Recent Changes

{extract_changelog_summary()}

---

*Generated automatically for release {version}*
"""

    with open("LAUNCH_SUMMARY.md", 'w', encoding='utf-8') as f:
        f.write(summary)

    print("✅ LAUNCH_SUMMARY.md generated successfully")

if __name__ == "__main__":
    generate_summary()
# Monitoring and Observability

This document describes the monitoring and observability features implemented in the Micro-Consent-Pipeline project.

## Overview

The pipeline includes comprehensive monitoring and observability features through:

- **Prometheus Metrics**: Performance and operational metrics
- **JSON Structured Logging**: Consistent, searchable log format
- **Grafana Dashboards**: Visual monitoring and alerting
- **Request Tracing**: Optional distributed tracing with OpenTelemetry

## Metrics Collection

### Available Metrics

The following Prometheus metrics are automatically collected:

#### Pipeline Metrics

- `pipeline_runs_total{status}` - Total number of pipeline runs (labeled by success/failure)
- `pipeline_run_seconds` - Histogram of pipeline execution times
- `pipeline_errors_total{stage}` - Total errors by pipeline stage
- `items_processed_total` - Total number of items processed
- `classifications_total{category}` - Total classifications by category
- `pipeline_runs_in_progress` - Current number of running pipelines

#### HTTP API Metrics

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - HTTP request duration histogram
- `http_requests_in_progress` - Currently processing HTTP requests

### Metrics Endpoints

- **FastAPI Metrics**: `http://localhost:8000/metrics`
- **Prometheus UI**: `http://localhost:9090`
- **Grafana Dashboard**: `http://localhost:3000`

## Structured Logging

### Log Format

All logs are structured in JSON format with the following fields:

```json
{
  "timestamp": "2023-12-07T10:30:00.123Z",
  "level": "INFO",
  "module": "micro_consent_pipeline.pipeline_runner",
  "message": "Pipeline completed successfully",
  "request_id": "abc12345",
  "duration_ms": 1500,
  "items": 25,
  "categories": { "data_collection": 15, "cookie_usage": 10 }
}
```

### Key Log Fields

- `timestamp`: ISO 8601 formatted timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `module`: Python module name
- `message`: Human-readable log message
- `request_id`: Unique identifier for request tracking
- `duration_ms`: Operation duration in milliseconds
- `items`: Number of items processed
- `categories`: Classification results
- `error`: Error details (for error logs)

### Request Tracking

Each pipeline run is assigned a unique 8-character request ID that appears in all related log entries, enabling easy correlation of log messages across the entire request lifecycle.

## Deployment and Configuration

### Docker Compose Setup

The monitoring stack is deployed using Docker Compose with the following services:

```yaml
services:
  micro-consent-pipeline:
    # Main application

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./ops/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./ops/grafana/provisioning:/etc/grafana/provisioning
```

### Starting the Monitoring Stack

```bash
# Start all services including monitoring
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f micro-consent-pipeline
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

## Grafana Dashboard

### Default Dashboard

The project includes a pre-configured Grafana dashboard with panels for:

1. **Request Rate**: Real-time request processing rate
2. **Total Requests**: Cumulative request counter
3. **Processing Duration**: 95th and 50th percentile processing times
4. **Error Rate**: Error frequency by type
5. **Documents Processed**: Total documents processed gauge
6. **Clause Classification Rate**: Classification activity by category

### Accessing Grafana

1. Open http://localhost:3000
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin`
3. Navigate to the "Micro Consent Pipeline Dashboard"

### Custom Dashboards

To create custom dashboards:

1. Use the Prometheus data source (pre-configured)
2. Query available metrics using PromQL
3. Save dashboards to the provisioning directory for persistence

## Prometheus Configuration

### Scrape Configuration

Prometheus is configured to scrape metrics from:

- **Main Application**: `micro-consent-pipeline:8000/metrics` (5-second interval)
- **Streamlit Dashboard**: `micro-consent-pipeline:8501/metrics` (30-second interval)
- **Prometheus Self-monitoring**: `localhost:9090/metrics` (15-second interval)

### Data Retention

- Default retention: 15 days
- Storage path: `/prometheus` (persistent volume)
- Configuration: `/etc/prometheus/prometheus.yml`

## OpenTelemetry Tracing (Optional)

### Configuration

Enable distributed tracing by setting environment variables:

```bash
ENABLE_TRACING=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:14268/api/traces
SERVICE_NAME=micro-consent-pipeline
```

### Supported Tracers

- **OTLP HTTP**: For Jaeger, Zipkin, or cloud providers
- **Console**: For development debugging
- **File**: For local trace storage

## Monitoring Best Practices

### Performance Monitoring

1. **Monitor Processing Duration**: Track the `pipeline_run_seconds` histogram
2. **Watch Error Rates**: Alert on increases in `pipeline_errors_total`
3. **Capacity Planning**: Monitor `pipeline_runs_in_progress` for queuing

### Alerting Recommendations

Set up alerts for:

- Pipeline failure rate > 5%
- Average processing time > 30 seconds
- No successful runs in 10 minutes
- Memory usage > 80%
- Disk space < 20%

### Log Analysis

Use structured logs for:

- **Performance Analysis**: Query by `duration_ms` field
- **Error Investigation**: Filter by `level: ERROR` and `error` field
- **Request Tracing**: Follow `request_id` across log entries
- **Usage Patterns**: Analyze `categories` for classification trends

## Troubleshooting

### Common Issues

#### Metrics Not Appearing

1. Check that `/metrics` endpoint is accessible
2. Verify Prometheus scrape configuration
3. Ensure services are on the same Docker network

#### Grafana Dashboard Empty

1. Confirm Prometheus data source connection
2. Check time range in dashboard
3. Verify metric queries in dashboard panels

#### High Memory Usage

1. Monitor pipeline processing batch sizes
2. Check for memory leaks in long-running processes
3. Review log retention settings

### Useful Queries

#### PromQL Examples

```promql
# Request rate over 5 minutes
rate(pipeline_runs_total[5m])

# 95th percentile processing time
histogram_quantile(0.95, rate(pipeline_run_seconds_bucket[5m]))

# Error rate percentage
rate(pipeline_errors_total[5m]) / rate(pipeline_runs_total[5m]) * 100

# Most common error types
topk(5, sum by (stage) (rate(pipeline_errors_total[5m])))
```

#### Log Queries (if using centralized logging)

```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level": "ERROR" } },
        { "range": { "timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}
```

## Configuration Reference

### Environment Variables

| Variable                      | Default                  | Description                  |
| ----------------------------- | ------------------------ | ---------------------------- |
| `LOG_LEVEL`                   | `INFO`                   | Logging level                |
| `ENABLE_TRACING`              | `false`                  | Enable OpenTelemetry tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | -                        | OTLP endpoint for traces     |
| `SERVICE_NAME`                | `micro-consent-pipeline` | Service name for tracing     |

### File Locations

- Prometheus config: `ops/prometheus.yml`
- Grafana provisioning: `ops/grafana/provisioning/`
- Dashboard definition: `ops/grafana/provisioning/dashboards/micro-consent-pipeline.json`
- Metrics code: `micro_consent_pipeline/utils/metrics.py`
- Logging code: `micro_consent_pipeline/utils/logger.py`

## Development and Testing

### Running Tests

```bash
# Run observability tests
pytest micro_consent_pipeline/tests/test_observability.py -v

# Run with integration tests
pytest micro_consent_pipeline/tests/test_observability.py -m integration -v
```

### Local Development

For local development without Docker:

1. Install dependencies: `pip install prometheus-client python-json-logger`
2. Start Prometheus manually: `prometheus --config.file=ops/prometheus.yml`
3. Start Grafana manually: `grafana-server --config=ops/grafana.ini`

### Custom Metrics

To add new metrics:

1. Define in `micro_consent_pipeline/utils/metrics.py`
2. Use in application code via `MetricsCollector`
3. Add to Grafana dashboard
4. Update documentation

Example:

```python
# In metrics.py
custom_metric = Counter('custom_operations_total', 'Custom operations', registry=REGISTRY)

# In application code
from micro_consent_pipeline.utils.metrics import metrics_collector
metrics_collector.record_custom_operation()
```

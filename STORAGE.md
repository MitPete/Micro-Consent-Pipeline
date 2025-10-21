# Storage & Async Processing Documentation

This document covers database persistence, async job processing, and scaling recommendations for the Micro-Consent-Pipeline project.

## Overview

Module 9 adds enterprise-grade persistence and asynchronous processing capabilities:

- **Database Persistence**: Store analysis results in PostgreSQL or SQLite
- **Async Job Queue**: Background processing using Redis and RQ
- **History Dashboard**: View and analyze past results
- **Scalable Architecture**: Horizontal worker scaling

## Database Configuration

### Database Options

#### SQLite (Development)

```bash
DATABASE_URL=sqlite:///data/micro_consent.db
```

- Best for: Development, testing, small deployments
- Pros: No setup required, single file database
- Cons: Not suitable for high concurrency

#### PostgreSQL (Production)

```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

- Best for: Production deployments, high concurrency
- Pros: ACID compliance, excellent performance, concurrent access
- Cons: Requires separate database server

### Database Initialization

#### Manual Initialization

```bash
# Initialize database tables
python -c "from db.session import init_db; init_db()"
```

#### Using Docker Compose

```bash
# Start with PostgreSQL and Redis
docker-compose up -d db redis

# Run migrations (if using Alembic)
docker-compose exec micro-consent-pipeline alembic upgrade head
```

#### Using Initialization Script

```bash
# Run the initialization script
./scripts/init_db.sh
```

### Database Schema

#### ConsentRecord Table

- **id**: Primary key (UUID)
- **source_url**: URL or content identifier
- **language**: Detected language
- **created_at**: Timestamp
- **total_items**: Number of consent elements found
- **data**: JSON metadata (categories, etc.)
- **status**: Processing status (completed, failed, processing)

#### ClauseRecord Table

- **id**: Primary key (UUID)
- **consent_id**: Foreign key to ConsentRecord
- **text**: Clause text content
- **category**: Classification category
- **confidence**: ML confidence score
- **element_type**: HTML element type
- **is_interactive**: Whether element is interactive

#### JobRecord Table

- **id**: Job ID (matches RQ job ID)
- **consent_record_id**: Link to analysis results
- **source_url**: URL being processed
- **status**: Job status (queued, started, finished, failed)
- **created_at**: Job creation time
- **result_data**: JSON result data

## Async Job Processing

### Redis Configuration

#### Basic Setup

```bash
REDIS_URL=redis://localhost:6379/0
```

#### With Authentication

```bash
REDIS_URL=redis://password@host:6379/0
```

#### Redis Cluster (Production)

```bash
REDIS_URL=redis://user:pass@redis-cluster:6379/0
```

### Job Queue Architecture

The system uses **RQ (Redis Queue)** for background job processing:

#### Queue Priorities

- **High Priority**: `high` - Critical analysis jobs
- **Default Priority**: `default` - Regular analysis jobs
- **Low Priority**: `low` - Bulk processing, maintenance

#### Job Lifecycle

1. **Queued**: Job submitted to Redis queue
2. **Started**: Worker picks up job
3. **Finished**: Job completed successfully
4. **Failed**: Job encountered error

### Starting Workers

#### Single Worker

```bash
# Start worker for all queues
python -m scripts.start_worker

# Start worker for specific queues
python -m scripts.start_worker --queues high,default
```

#### Multiple Workers

```bash
# Start 3 workers for high-priority jobs
for i in {1..3}; do
  python -m scripts.start_worker --queues high --name "worker-high-$i" &
done

# Start 5 workers for default jobs
for i in {1..5}; do
  python -m scripts.start_worker --queues default --name "worker-default-$i" &
done
```

#### Using Docker

```bash
# Scale workers with docker-compose
docker-compose up --scale worker=5
```

#### Production Deployment with Supervisor

```ini
[program:consent-worker]
command=/app/.venv/bin/python -m scripts.start_worker
directory=/app
user=app
autostart=true
autorestart=true
numprocs=3
process_name=%(program_name)s_%(process_num)02d
stdout_logfile=/var/log/consent-worker.log
stderr_logfile=/var/log/consent-worker-error.log
```

### API Usage

#### Async Analysis

```bash
# Submit async job
curl -X POST "http://localhost:8000/analyze_async" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "https://example.com/privacy",
    "output_format": "json"
  }'

# Response: {"job_id": "abc-123", "status": "queued", ...}
```

#### Check Job Status

```bash
# Get job status and results
curl -X GET "http://localhost:8000/job/abc-123" \
  -H "X-API-Key: your-api-key"
```

#### Response Statuses

- `queued`: Job waiting for worker
- `started`: Job being processed
- `finished`: Job completed with results
- `failed`: Job failed with error message

## Migration Guide

### From Sync to Async Processing

#### 1. Update Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
# Copy and configure environment
cp .env.example .env
# Edit DATABASE_URL and REDIS_URL
```

#### 3. Initialize Database

```bash
./scripts/init_db.sh
```

#### 4. Start Services

```bash
# Start Redis
redis-server

# Start workers
python -m scripts.start_worker

# Start API
python -m api.app
```

### Database Migrations (Alembic)

#### Initialize Migrations

```bash
# Initialize Alembic
alembic init alembic

# Generate initial migration
alembic revision --autogenerate -m "Initial tables"

# Apply migration
alembic upgrade head
```

#### Schema Changes

```bash
# Generate migration for schema changes
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Scaling Recommendations

### Horizontal Scaling

#### Worker Scaling

- **Small Load**: 2-3 workers per queue
- **Medium Load**: 5-10 workers per queue
- **High Load**: 10+ workers with load balancing

#### Database Scaling

- **Read Replicas**: For analytics and reporting
- **Connection Pooling**: Use PgBouncer for PostgreSQL
- **Partitioning**: Partition by date for large datasets

#### Redis Scaling

- **Redis Cluster**: For high availability
- **Redis Sentinel**: For automatic failover
- **Separate Queues**: Different Redis instances per priority

### Vertical Scaling

#### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_consent_records_created_at ON consent_records(created_at);
CREATE INDEX idx_consent_records_status ON consent_records(status);
CREATE INDEX idx_clause_records_consent_id ON clause_records(consent_id);
CREATE INDEX idx_clause_records_category ON clause_records(category);
```

#### Memory Optimization

```bash
# Redis memory optimization
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 2gb
```

### Performance Monitoring

#### Key Metrics

- **Queue Length**: Monitor Redis queue sizes
- **Job Processing Time**: Track average job duration
- **Database Connections**: Monitor active connections
- **Error Rates**: Track failed job percentage

#### Monitoring Setup

```python
# Prometheus metrics example
from prometheus_client import Counter, Histogram, Gauge

job_counter = Counter('jobs_total', 'Total jobs processed', ['status'])
job_duration = Histogram('job_duration_seconds', 'Job processing time')
queue_size = Gauge('queue_size', 'Current queue size', ['queue'])
```

## Troubleshooting

### Common Issues

#### Database Connection Issues

```bash
# Test database connection
python -c "from db.session import get_db_sync; db = get_db_sync(); print('Connected successfully'); db.close()"
```

#### Redis Connection Issues

```bash
# Test Redis connection
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

#### Worker Not Processing Jobs

```bash
# Check Redis queues
redis-cli LLEN rq:queue:default
redis-cli LLEN rq:queue:high

# Check for failed jobs
redis-cli LLEN rq:queue:failed
```

### Maintenance

#### Clean Up Old Jobs

```python
from worker.queue import cleanup_old_jobs

# Clean up jobs older than 7 days
cleaned = cleanup_old_jobs(days=7)
print(f"Cleaned up {cleaned} old job records")
```

#### Database Maintenance

```sql
-- PostgreSQL maintenance
VACUUM ANALYZE consent_records;
VACUUM ANALYZE clause_records;
VACUUM ANALYZE job_records;

-- Check database size
SELECT pg_size_pretty(pg_database_size('micro_consent'));
```

#### Redis Maintenance

```bash
# Check Redis memory usage
redis-cli INFO memory

# Clear failed jobs
redis-cli DEL rq:queue:failed

# Monitor active workers
redis-cli SMEMBERS rq:workers
```

## Security Considerations

### Database Security

- Use strong passwords for database connections
- Enable SSL/TLS for database connections in production
- Regularly update database software
- Implement proper backup strategies

### Redis Security

- Use Redis AUTH for authentication
- Disable dangerous commands in production
- Use SSL/TLS for Redis connections
- Restrict network access to Redis

### Application Security

- Validate all job inputs
- Sanitize data before database storage
- Implement proper error handling
- Use secure random job IDs

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -h localhost -U postgres micro_consent > backup.sql

# SQLite backup
cp data/micro_consent.db backup/micro_consent_$(date +%Y%m%d).db
```

### Redis Backup

```bash
# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb backup/redis_$(date +%Y%m%d).rdb
```

### Recovery Procedures

```bash
# Restore PostgreSQL
psql -h localhost -U postgres micro_consent < backup.sql

# Restore SQLite
cp backup/micro_consent_20231201.db data/micro_consent.db

# Restore Redis
redis-cli FLUSHALL
redis-cli --pipe < backup/redis_20231201.rdb
```

## Performance Benchmarks

### Expected Performance

- **Sync Analysis**: 1-5 seconds per page
- **Async Job Throughput**: 10-100 jobs/minute per worker
- **Database Queries**: <100ms for typical operations
- **Memory Usage**: 50-200MB per worker process

### Load Testing

```bash
# Test async endpoint
ab -n 100 -c 10 -H "X-API-Key: test-key" \
  -p test_data.json -T application/json \
  http://localhost:8000/analyze_async
```

This documentation provides comprehensive guidance for implementing, deploying, and scaling the storage and async processing capabilities of the Micro-Consent-Pipeline project.

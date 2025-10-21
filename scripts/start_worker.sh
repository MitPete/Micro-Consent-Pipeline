#!/bin/bash
# scripts/start_worker.sh
# Purpose: Start RQ worker for background job processing

set -e

# Default values
QUEUES="high,default,low"
WORKER_NAME=""
VERBOSITY=""
LOG_LEVEL="INFO"

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Start RQ worker for background job processing"
    echo ""
    echo "OPTIONS:"
    echo "  -q, --queues QUEUES     Comma-separated list of queues (default: high,default,low)"
    echo "  -n, --name NAME         Worker name (default: auto-generated)"
    echo "  -v, --verbose           Enable verbose logging"
    echo "  -l, --log-level LEVEL   Log level (DEBUG, INFO, WARNING, ERROR) (default: INFO)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Start worker for all queues"
    echo "  $0 -q high,default                   # Start worker for high and default queues"
    echo "  $0 -n worker-1 -v                    # Start named worker with verbose logging"
    echo "  $0 -q high -l DEBUG                  # Start worker for high queue with debug logging"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -q|--queues)
            QUEUES="$2"
            shift 2
            ;;
        -n|--name)
            WORKER_NAME="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSITY="-v"
            shift
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Load environment variables if .env file exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
if [ -z "$REDIS_URL" ]; then
    echo "Warning: REDIS_URL not set, using default: redis://localhost:6379/0"
    export REDIS_URL="redis://localhost:6379/0"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "Warning: DATABASE_URL not set, using default SQLite database"
    export DATABASE_URL="sqlite:///data/micro_consent.db"
fi

# Set log level
export LOG_LEVEL="$LOG_LEVEL"

# Ensure data directory exists for SQLite
if [[ "$DATABASE_URL" == sqlite* ]]; then
    mkdir -p data
fi

echo "========================================="
echo "Starting Micro-Consent Pipeline Worker"
echo "========================================="
echo "Queues: $QUEUES"
echo "Redis URL: $REDIS_URL"
echo "Database URL: ${DATABASE_URL/password*/password:***}"
echo "Log Level: $LOG_LEVEL"
if [ -n "$WORKER_NAME" ]; then
    echo "Worker Name: $WORKER_NAME"
fi
echo "========================================="

# Build RQ command
RQ_CMD="python -m rq.cli worker"

# Add queue names
IFS=',' read -ra QUEUE_ARRAY <<< "$QUEUES"
for queue in "${QUEUE_ARRAY[@]}"; do
    RQ_CMD="$RQ_CMD $queue"
done

# Add worker name if specified
if [ -n "$WORKER_NAME" ]; then
    RQ_CMD="$RQ_CMD --name $WORKER_NAME"
fi

# Add verbosity if specified
if [ -n "$VERBOSITY" ]; then
    RQ_CMD="$RQ_CMD $VERBOSITY"
fi

# Add Redis URL
RQ_CMD="$RQ_CMD --url $REDIS_URL"

echo "Starting worker with command: $RQ_CMD"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down worker gracefully..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check Redis connectivity
echo "Testing Redis connection..."
python -c "
import redis
import sys
try:
    r = redis.from_url('$REDIS_URL')
    r.ping()
    print('✓ Redis connection successful')
except Exception as e:
    print(f'✗ Redis connection failed: {e}')
    sys.exit(1)
"

# Check database connectivity
echo "Testing database connection..."
python -c "
from db.session import get_db_sync
import sys
try:
    db = get_db_sync()
    db.close()
    print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    sys.exit(1)
"

echo "All connectivity tests passed. Starting worker..."
echo ""

# Start the worker
exec $RQ_CMD
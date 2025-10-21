#!/bin/bash
# scripts/init_db.sh
# Purpose: Initialize database tables and perform setup

set -e

# Default values
FORCE=false
MIGRATE=false
SEED=false

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Initialize database tables and perform setup"
    echo ""
    echo "OPTIONS:"
    echo "  -f, --force             Force drop and recreate all tables (DESTRUCTIVE)"
    echo "  -m, --migrate           Run database migrations (if using Alembic)"
    echo "  -s, --seed              Seed database with sample data"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                      # Initialize database with default settings"
    echo "  $0 -f                   # Force recreate all tables (destroys existing data)"
    echo "  $0 -m                   # Run migrations instead of direct table creation"
    echo "  $0 -s                   # Initialize and seed with sample data"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -m|--migrate)
            MIGRATE=true
            shift
            ;;
        -s|--seed)
            SEED=true
            shift
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
if [ -z "$DATABASE_URL" ]; then
    echo "Warning: DATABASE_URL not set, using default SQLite database"
    export DATABASE_URL="sqlite:///data/micro_consent.db"
fi

echo "========================================="
echo "Micro-Consent Pipeline Database Setup"
echo "========================================="
echo "Database URL: ${DATABASE_URL/password*/password:***}"
echo "Force recreate: $FORCE"
echo "Use migrations: $MIGRATE"
echo "Seed data: $SEED"
echo "========================================="

# Ensure data directory exists for SQLite
if [[ "$DATABASE_URL" == sqlite* ]]; then
    mkdir -p data
    echo "Created data directory for SQLite database"
fi

# Test database connectivity
echo "Testing database connection..."
python -c "
import sys
sys.path.append('.')
from db.session import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    sys.exit(1)
"

if [ "$FORCE" = true ]; then
    echo ""
    echo "⚠️  WARNING: Force mode will DROP ALL EXISTING TABLES!"
    echo "This will permanently delete all data in the database."
    echo ""
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "Operation cancelled."
        exit 1
    fi

    echo "Dropping all existing tables..."
    python -c "
import sys
sys.path.append('.')
from db.session import drop_db
try:
    drop_db()
    print('✓ All tables dropped successfully')
except Exception as e:
    print(f'✗ Failed to drop tables: {e}')
    sys.exit(1)
"
fi

if [ "$MIGRATE" = true ]; then
    echo ""
    echo "Running database migrations..."

    # Check if Alembic is configured
    if [ ! -f "alembic.ini" ]; then
        echo "⚠️  Alembic not configured. Initializing..."
        python -m alembic init alembic
        echo "✓ Alembic initialized"
        echo "Please configure alembic.ini and generate initial migration:"
        echo "  alembic revision --autogenerate -m 'Initial tables'"
        echo "  alembic upgrade head"
        exit 1
    fi

    # Run migrations
    python -m alembic upgrade head
    echo "✓ Database migrations completed"
else
    echo ""
    echo "Creating database tables..."
    python -c "
import sys
sys.path.append('.')
from db.session import init_db
try:
    init_db()
    print('✓ Database tables created successfully')
except Exception as e:
    print(f'✗ Failed to create tables: {e}')
    sys.exit(1)
"
fi

# Verify table creation
echo ""
echo "Verifying table creation..."
python -c "
import sys
sys.path.append('.')
from db.session import get_db_sync
from db.models import ConsentRecord, ClauseRecord, JobRecord

try:
    db = get_db_sync()

    # Test table existence by querying
    consent_count = db.query(ConsentRecord).count()
    clause_count = db.query(ClauseRecord).count()
    job_count = db.query(JobRecord).count()

    print(f'✓ ConsentRecord table: {consent_count} records')
    print(f'✓ ClauseRecord table: {clause_count} records')
    print(f'✓ JobRecord table: {job_count} records')

    db.close()
except Exception as e:
    print(f'✗ Table verification failed: {e}')
    sys.exit(1)
"

if [ "$SEED" = true ]; then
    echo ""
    echo "Seeding database with sample data..."
    python -c "
import sys
sys.path.append('.')
from db.session import get_db_sync
from db.models import ConsentRecord, ClauseRecord, JobRecord
from datetime import datetime
import uuid

try:
    db = get_db_sync()

    # Create sample consent record
    sample_record = ConsentRecord(
        source_url='https://example.com/privacy-policy',
        language='en',
        total_items=3,
        data={
            'categories': {
                'necessary': 1,
                'analytics': 1,
                'marketing': 1
            },
            'source_type': 'url'
        },
        status='completed'
    )

    db.add(sample_record)
    db.flush()  # Get the ID

    # Create sample clauses
    sample_clauses = [
        ClauseRecord(
            consent_id=sample_record.id,
            text='We use essential cookies for website functionality',
            category='necessary',
            confidence=0.95,
            element_type='text',
            is_interactive='false'
        ),
        ClauseRecord(
            consent_id=sample_record.id,
            text='Analytics cookies help us improve our service',
            category='analytics',
            confidence=0.87,
            element_type='text',
            is_interactive='false'
        ),
        ClauseRecord(
            consent_id=sample_record.id,
            text='Accept marketing cookies',
            category='marketing',
            confidence=0.92,
            element_type='button',
            is_interactive='true'
        )
    ]

    for clause in sample_clauses:
        db.add(clause)

    # Create sample job record
    sample_job = JobRecord(
        id=str(uuid.uuid4()),
        consent_record_id=sample_record.id,
        source_url='https://example.com/privacy-policy',
        status='finished',
        output_format='json',
        result_data={'success': True, 'items': 3}
    )

    db.add(sample_job)
    db.commit()

    print('✓ Sample data seeded successfully')
    print(f'  - Created 1 consent record with ID: {sample_record.id}')
    print(f'  - Created 3 clause records')
    print(f'  - Created 1 job record')

    db.close()
except Exception as e:
    print(f'✗ Failed to seed sample data: {e}')
    db.rollback()
    db.close()
    sys.exit(1)
"
fi

echo ""
echo "========================================="
echo "✓ Database initialization completed successfully!"
echo "========================================="

# Display connection info
echo ""
echo "Database Information:"
echo "  URL: ${DATABASE_URL/password*/password:***}"

if [[ "$DATABASE_URL" == sqlite* ]]; then
    echo "  Type: SQLite"
    echo "  File: ${DATABASE_URL#sqlite:///}"
else
    echo "  Type: PostgreSQL/Other"
fi

echo ""
echo "Next steps:"
echo "  1. Start Redis server: redis-server"
echo "  2. Start worker: ./scripts/start_worker.sh"
echo "  3. Start API: python -m api.app"
echo "  4. Start dashboard: streamlit run dashboard/app.py"
echo ""
echo "Useful commands:"
echo "  - Check database: python -c 'from db.session import get_db_sync; db = get_db_sync(); print(f\"Connected: {db}\"); db.close()'"
echo "  - View tables: python -c 'from db.models import *; print(\"Tables: ConsentRecord, ClauseRecord, JobRecord\")'"
echo "  - Clean up old data: python -c 'from worker.queue import cleanup_old_jobs; cleanup_old_jobs(7)'"
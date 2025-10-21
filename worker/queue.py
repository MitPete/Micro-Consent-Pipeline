# worker/queue.py
# Purpose: Async job queue management using RQ and Redis

"""
Async job queue system for background processing of consent analysis tasks.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable
import uuid

import redis
from rq import Queue, Worker
from rq.job import Job
from rq.exceptions import NoSuchJobError

from micro_consent_pipeline.config.settings import Settings
from db.session import get_db_sync
from db.models import JobRecord

# Initialize settings and Redis connection
settings = Settings()
redis_conn = redis.from_url(settings.redis_url)
logger = logging.getLogger(__name__)

# Create RQ queues
default_queue = Queue('default', connection=redis_conn)
high_priority_queue = Queue('high', connection=redis_conn)
low_priority_queue = Queue('low', connection=redis_conn)


def enqueue_task(func: Callable, *args, priority: str = 'default',
                job_timeout: Optional[int] = None,
                result_ttl: Optional[int] = None,
                job_id: Optional[str] = None,
                **kwargs) -> str:
    """
    Enqueue a task for background processing.

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        priority: Queue priority ('high', 'default', 'low')
        job_timeout: Job timeout in seconds (default from settings)
        result_ttl: Result time-to-live in seconds (default from settings)
        job_id: Custom job ID (default: generate UUID)
        **kwargs: Keyword arguments for the function

    Returns:
        str: Job ID
    """
    if job_id is None:
        job_id = str(uuid.uuid4())

    if job_timeout is None:
        job_timeout = settings.job_timeout

    if result_ttl is None:
        result_ttl = settings.result_ttl

    # Select queue based on priority
    if priority == 'high':
        queue = high_priority_queue
    elif priority == 'low':
        queue = low_priority_queue
    else:
        queue = default_queue

    # Enqueue the job
    job = queue.enqueue(
        func,
        *args,
        job_id=job_id,
        job_timeout=job_timeout,
        result_ttl=result_ttl,
        **kwargs
    )

    logger.info(f"Enqueued job {job_id} with priority {priority}")
    return job_id


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status and result of a job.

    Args:
        job_id: Job ID to check

    Returns:
        Dict containing job status information
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)

        status_info = {
            'job_id': job_id,
            'status': job.get_status(),
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'ended_at': job.ended_at.isoformat() if job.ended_at else None,
            'result': None,
            'error': None,
            'progress': None
        }

        if job.is_finished:
            status_info['result'] = job.result
        elif job.is_failed:
            status_info['error'] = str(job.exc_info) if job.exc_info else 'Unknown error'

        # Get progress if available
        if hasattr(job, 'meta') and job.meta:
            status_info['progress'] = job.meta.get('progress')

        return status_info

    except NoSuchJobError:
        return {
            'job_id': job_id,
            'status': 'not_found',
            'error': 'Job not found'
        }
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        return {
            'job_id': job_id,
            'status': 'error',
            'error': str(e)
        }


def cancel_job(job_id: str) -> bool:
    """
    Cancel a queued or running job.

    Args:
        job_id: Job ID to cancel

    Returns:
        bool: True if job was cancelled successfully
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.cancel()
        logger.info(f"Cancelled job {job_id}")
        return True
    except NoSuchJobError:
        logger.warning(f"Job {job_id} not found for cancellation")
        return False
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return False


def get_queue_info() -> Dict[str, Any]:
    """
    Get information about all queues.

    Returns:
        Dict containing queue statistics
    """
    return {
        'high_priority': {
            'name': 'high',
            'length': len(high_priority_queue),
            'failed_count': high_priority_queue.failed_job_registry.count,
            'started_count': high_priority_queue.started_job_registry.count,
            'finished_count': high_priority_queue.finished_job_registry.count,
        },
        'default': {
            'name': 'default',
            'length': len(default_queue),
            'failed_count': default_queue.failed_job_registry.count,
            'started_count': default_queue.started_job_registry.count,
            'finished_count': default_queue.finished_job_registry.count,
        },
        'low_priority': {
            'name': 'low',
            'length': len(low_priority_queue),
            'failed_count': low_priority_queue.failed_job_registry.count,
            'started_count': low_priority_queue.started_job_registry.count,
            'finished_count': low_priority_queue.finished_job_registry.count,
        }
    }


def create_job_record(job_id: str, source_url: str, output_format: str = 'json',
                     priority: int = 0, user_agent: Optional[str] = None,
                     ip_address: Optional[str] = None) -> None:
    """
    Create a database record for tracking job execution.

    Args:
        job_id: RQ job ID
        source_url: URL being analyzed
        output_format: Requested output format
        priority: Job priority level
        user_agent: User agent string
        ip_address: Client IP address
    """
    db = get_db_sync()
    try:
        job_record = JobRecord(
            id=job_id,
            source_url=source_url,
            status='queued',
            output_format=output_format,
            priority=priority,
            user_agent=user_agent,
            ip_address=ip_address
        )
        db.add(job_record)
        db.commit()
        logger.info(f"Created job record for {job_id}")
    except Exception as e:
        logger.error(f"Error creating job record for {job_id}: {e}")
        db.rollback()
    finally:
        db.close()


def update_job_record(job_id: str, status: Optional[str] = None,
                     consent_record_id: Optional[str] = None,
                     result_data: Optional[Dict] = None,
                     error_message: Optional[str] = None) -> None:
    """
    Update job record with execution results.

    Args:
        job_id: RQ job ID
        status: New job status
        consent_record_id: Associated consent record ID
        result_data: Job result data
        error_message: Error message if job failed
    """
    db = get_db_sync()
    try:
        job_record = db.query(JobRecord).filter(JobRecord.id == job_id).first()
        if job_record:
            if status:
                job_record.status = status
                if status == 'started':
                    job_record.started_at = datetime.utcnow()
                elif status in ['finished', 'failed']:
                    job_record.finished_at = datetime.utcnow()

            if consent_record_id:
                job_record.consent_record_id = consent_record_id
            if result_data:
                job_record.result_data = result_data
            if error_message:
                job_record.error_message = error_message

            db.commit()
            logger.info(f"Updated job record for {job_id}")
        else:
            logger.warning(f"Job record not found for {job_id}")
    except Exception as e:
        logger.error(f"Error updating job record for {job_id}: {e}")
        db.rollback()
    finally:
        db.close()


def cleanup_old_jobs(days: int = 7) -> int:
    """
    Clean up old job records and Redis job data.

    Args:
        days: Number of days to keep job records

    Returns:
        int: Number of records cleaned up
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    db = get_db_sync()

    try:
        # Clean up database records
        deleted_count = db.query(JobRecord).filter(
            JobRecord.created_at < cutoff_date
        ).delete()

        db.commit()
        logger.info(f"Cleaned up {deleted_count} old job records")
        return deleted_count

    except Exception as e:
        logger.error(f"Error cleaning up old jobs: {e}")
        db.rollback()
        return 0
    finally:
        db.close()


def start_worker(queues: Optional[list] = None, name: Optional[str] = None) -> Worker:
    """
    Start an RQ worker process.

    Args:
        queues: List of queue names to process (default: all queues)
        name: Worker name (default: auto-generated)

    Returns:
        Worker: RQ Worker instance
    """
    if queues is None:
        queues = [high_priority_queue, default_queue, low_priority_queue]
    else:
        # Convert queue names to queue objects
        queue_map = {
            'high': high_priority_queue,
            'default': default_queue,
            'low': low_priority_queue
        }
        queues = [queue_map.get(q, default_queue) for q in queues]

    worker = Worker(queues, connection=redis_conn, name=name)
    logger.info(f"Starting worker {worker.name} with queues: {[q.name for q in queues]}")

    return worker
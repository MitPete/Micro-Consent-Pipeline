#!/usr/bin/env python3
"""
scripts/worker_manager.py
Purpose: Python-based worker management for Docker integration

This module provides a Python interface for managing RQ workers,
designed to work seamlessly with Docker containers and the existing
bash scripts.
"""

import argparse
import os
import sys
import time
import signal
import logging
from typing import List, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import redis
    from rq import Worker, Queue
    from rq.job import Job
    from worker.queue import redis_conn, start_worker, get_queue_info
    from db.session import init_db, engine
    from sqlalchemy import text
except ImportError as e:
    print(f"Error: Missing required dependencies: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)


class WorkerManager:
    """Manages RQ workers with proper lifecycle and monitoring."""

    def __init__(self,
                 queues: List[str] = None,
                 worker_name: str = None,
                 log_level: str = "INFO"):
        """
        Initialize worker manager.

        Args:
            queues: List of queue names to process
            worker_name: Custom worker name
            log_level: Logging level
        """
        self.queues = queues or ['default']
        self.worker_name = worker_name
        self.log_level = log_level
        self.worker = None
        self.should_stop = False

        # Setup logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.should_stop = True
        if self.worker:
            self.worker.request_stop()

    def test_connections(self) -> bool:
        """Test Redis and database connectivity."""
        self.logger.info("Testing connections...")

        # Test Redis connection
        try:
            redis_conn.ping()
            self.logger.info("✓ Redis connection successful")
        except Exception as e:
            self.logger.error(f"✗ Redis connection failed: {e}")
            return False

        # Test database connection
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            self.logger.info("✓ Database connection successful")
        except Exception as e:
            self.logger.error(f"✗ Database connection failed: {e}")
            return False

        # Test queue accessibility
        try:
            queue_objs = [Queue(name, connection=redis_conn) for name in self.queues]
            queue_names = [q.name for q in queue_objs]
            self.logger.info(f"✓ Queues accessible: {queue_names}")
        except Exception as e:
            self.logger.error(f"✗ Queue access failed: {e}")
            return False

        return True

    def start_worker(self) -> int:
        """
        Start the RQ worker.

        Returns:
            Exit code (0 for success, 1 for error)
        """
        if not self.test_connections():
            return 1

        try:
            # Get queue objects
            queue_objs = [Queue(name, connection=redis_conn) for name in self.queues]

            # Create worker
            self.worker = Worker(
                queues=queue_objs,
                connection=redis_conn,
                name=self.worker_name
            )

            self.logger.info(f"Starting worker '{self.worker.name}' for queues: {self.queues}")
            self.logger.info(f"Worker PID: {os.getpid()}")

            # Start worker
            self.worker.work(with_scheduler=True)

            self.logger.info("Worker finished normally")
            return 0

        except Exception as e:
            self.logger.error(f"Worker error: {e}")
            return 1

    def get_worker_info(self) -> dict:
        """Get information about running workers."""
        try:
            workers = Worker.all(connection=redis_conn)
            worker_info = []

            for worker in workers:
                info = {
                    'name': worker.name,
                    'state': worker.get_state(),
                    'current_job': None,
                    'queues': [q.name for q in worker.queues]
                }

                current_job = worker.get_current_job()
                if current_job:
                    info['current_job'] = {
                        'id': current_job.id,
                        'func_name': current_job.func_name,
                        'created_at': current_job.created_at.isoformat() if current_job.created_at else None
                    }

                worker_info.append(info)

            return {
                'workers': worker_info,
                'total_workers': len(workers)
            }

        except Exception as e:
            self.logger.error(f"Error getting worker info: {e}")
            return {'error': str(e)}

    def cleanup_failed_jobs(self, max_age_days: int = 7) -> int:
        """
        Clean up old failed jobs.

        Args:
            max_age_days: Maximum age of jobs to keep

        Returns:
            Number of jobs cleaned up
        """
        try:
            from worker.queue import cleanup_old_jobs
            count = cleanup_old_jobs(max_age_days)
            self.logger.info(f"Cleaned up {count} old jobs")
            return count
        except Exception as e:
            self.logger.error(f"Error cleaning up jobs: {e}")
            return 0


def main():
    """Main entry point for worker management."""
    parser = argparse.ArgumentParser(
        description="Micro-Consent Pipeline Worker Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/worker_manager.py                     # Start worker for default queue
  python scripts/worker_manager.py -q high default     # Process high and default queues
  python scripts/worker_manager.py -n consent-worker-1 # Use custom worker name
  python scripts/worker_manager.py --info              # Show worker information
  python scripts/worker_manager.py --cleanup 3        # Clean up jobs older than 3 days
        """
    )

    parser.add_argument(
        '-q', '--queues',
        nargs='+',
        default=['default'],
        help='Queue names to process (default: %(default)s)'
    )

    parser.add_argument(
        '-n', '--name',
        help='Custom worker name (default: auto-generated)'
    )

    parser.add_argument(
        '-l', '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log level (default: %(default)s)'
    )

    parser.add_argument(
        '--info',
        action='store_true',
        help='Show information about running workers'
    )

    parser.add_argument(
        '--cleanup',
        type=int,
        metavar='DAYS',
        help='Clean up failed jobs older than DAYS'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test connections without starting worker'
    )

    args = parser.parse_args()

    # Load environment variables
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("Loaded environment variables from .env")

    # Create worker manager
    manager = WorkerManager(
        queues=args.queues,
        worker_name=args.name,
        log_level=args.log_level
    )

    # Handle different modes
    if args.info:
        info = manager.get_worker_info()
        if 'error' in info:
            print(f"Error: {info['error']}")
            return 1

        print(f"Total workers: {info['total_workers']}")
        for worker in info['workers']:
            print(f"\nWorker: {worker['name']}")
            print(f"  State: {worker['state']}")
            print(f"  Queues: {', '.join(worker['queues'])}")
            if worker['current_job']:
                job = worker['current_job']
                print(f"  Current job: {job['id']} ({job['func_name']})")
        return 0

    if args.cleanup is not None:
        count = manager.cleanup_failed_jobs(args.cleanup)
        print(f"Cleaned up {count} old jobs")
        return 0

    if args.test:
        success = manager.test_connections()
        return 0 if success else 1

    # Start worker
    return manager.start_worker()


if __name__ == '__main__':
    sys.exit(main())
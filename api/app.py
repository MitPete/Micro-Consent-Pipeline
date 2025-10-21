# api/app.py
# Purpose: Provide secure RESTful endpoints for the Micro-Consent-Pipeline

"""
Module: app.py
Purpose: Provide secure RESTful endpoints for the Micro-Consent-Pipeline with authentication,
rate limiting, input validation, and security headers.
"""

import re
import uuid
import time
from typing import List, Dict, Optional
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import bleach
from sqlalchemy.orm import Session

from micro_consent_pipeline.pipeline_runner import PipelineRunner
from micro_consent_pipeline.config.settings import Settings
from micro_consent_pipeline.utils.logger import get_logger, setup_json_logger, generate_request_id
from micro_consent_pipeline.utils.metrics import REGISTRY
from micro_consent_pipeline import __version__
from db.session import get_db, init_db
from db.models import ConsentRecord, ClauseRecord, JobRecord
from worker.queue import enqueue_task, get_job_status, create_job_record, update_job_record

# Initialize settings
settings = Settings()

# Setup JSON logging
setup_json_logger("uvicorn.access", settings.log_level)
setup_json_logger("uvicorn", settings.log_level)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Micro-Consent Pipeline API", version=__version__)

# Initialize database
try:
    init_db()
    logger = get_logger(__name__)
    logger.info("Database initialized successfully", extra={"version": __version__})
except Exception as e:
    logger = get_logger(__name__)
    logger.error(f"Failed to initialize database: {e}", extra={"version": __version__})

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize Prometheus instrumentator
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics", tags=["monitoring"])

# Security bearer for API key
security = HTTPBearer(auto_error=False)

# Optional OpenTelemetry tracing
if settings.enable_tracing:
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource

        # Configure tracing
        resource = Resource.create({"service.name": settings.service_name})
        trace.set_tracer_provider(TracerProvider(resource=resource))

        otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)

        logger = get_logger(__name__)
        logger.info("OpenTelemetry tracing enabled", extra={"service_name": settings.service_name})

    except ImportError as e:
        logger = get_logger(__name__)
        logger.warning("OpenTelemetry dependencies not available", extra={"error": str(e)})

logger = get_logger(__name__)


# Security middleware for headers
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response


# Payload size middleware
@app.middleware("http")
async def payload_size_middleware(request: Request, call_next):
    """Limit request payload size."""
    content_length = request.headers.get("content-length")

    if content_length:
        content_length = int(content_length)
        if content_length > settings.max_payload_bytes:
            logger.warning(
                "Request payload too large",
                extra={
                    "client_ip": get_remote_address(request),
                    "content_length": content_length,
                    "max_allowed": settings.max_payload_bytes,
                    "user_agent": request.headers.get("user-agent"),
                    "request_id": str(uuid.uuid4())[:8]
                }
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=413,
                content={
                    "detail": f"Payload too large. Maximum allowed: {settings.max_payload_bytes} bytes"
                }
            )

    return await call_next(request)


# Audit logging middleware
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log request details for security auditing."""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Add request ID to request state
    request.state.request_id = request_id

    # Log incoming request
    logger.info(
        "Incoming request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": get_remote_address(request),
            "user_agent": request.headers.get("user-agent"),
            "content_length": request.headers.get("content-length"),
        }
    )

    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    log_level = "warning" if response.status_code >= 400 else "info"
    log_extra = {
        "request_id": request_id,
        "status_code": response.status_code,
        "duration_ms": duration * 1000,
        "client_ip": get_remote_address(request),
    }

    if response.status_code >= 400:
        getattr(logger, log_level)(f"Request failed with status {response.status_code}", extra=log_extra)
    else:
        logger.info("Request completed", extra=log_extra)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# CORS middleware with strict origin control
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)


def verify_api_key(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Verify API key for protected endpoints.

    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials

    Returns:
        bool: True if authenticated

    Raises:
        HTTPException: 401 if authentication fails
    """
    # Check for API key in X-API-Key header
    api_key_header = request.headers.get("X-API-Key")

    # Also check Authorization header (Bearer token)
    api_key_auth = None
    if credentials:
        api_key_auth = credentials.credentials

    provided_key = api_key_header or api_key_auth

    request_id = getattr(request.state, 'request_id', generate_request_id())
    client_ip = get_remote_address(request)

    if not provided_key:
        logger.warning(
            "Missing API key",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent"),
                "auth_status": "missing_key"
            }
        )
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide key in X-API-Key header or Authorization: Bearer <key>"
        )

    if not settings.api_key or provided_key != settings.api_key:
        logger.warning(
            "Invalid API key",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent"),
                "auth_status": "invalid_key"
            }
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    logger.info(
        "API key authenticated",
        extra={
            "request_id": request_id,
            "client_ip": client_ip,
            "auth_status": "success"
        }
    )

    return True


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint with enhanced validation."""
    source: str = Field(..., description="URL (HTTP/HTTPS only) or raw HTML content", max_length=1048576)  # 1MB max
    output_format: str = Field(default="json", description="Output format (json or csv)")

    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        """Validate source input for security."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Source cannot be empty")

        # If it looks like a URL, validate it strictly
        if v.startswith(('http://', 'https://', 'file://', 'ftp://', 'javascript:', 'data:')):
            # Only allow http and https
            if not v.startswith(('http://', 'https://')):
                raise ValueError("Only HTTP and HTTPS URLs are allowed")

            # More permissive URL validation for localhost and valid domains
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:'
                r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?'  # domain with TLD
                r'|'
                r'localhost'  # localhost
                r'|'
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # IP address
                r')'
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)?$', re.IGNORECASE)  # optional path

            if not url_pattern.match(v):
                raise ValueError("Invalid URL format")
        else:
            # For HTML content, sanitize it
            v = bleach.clean(v, tags=bleach.ALLOWED_TAGS, attributes=bleach.ALLOWED_ATTRIBUTES)

        return v

    @field_validator('output_format')
    @classmethod
    def validate_output_format(cls, v):
        """Validate output format."""
        if v not in ['json', 'csv']:
            raise ValueError("Output format must be 'json' or 'csv'")
        return v


class ConsentItem(BaseModel):
    """Model for a single consent item."""
    text: str
    category: str
    confidence: float
    type: str
    element: str


class AnalyzeResponse(BaseModel):
    """Response model for analyze endpoint."""
    success: bool
    items: List[ConsentItem]
    total_items: int
    categories: Dict[str, int]
    request_id: str


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    timestamp: str
    version: str


class AsyncAnalyzeResponse(BaseModel):
    """Response model for async analyze endpoint."""
    job_id: str
    status: str
    message: str
    request_id: str


class JobStatusResponse(BaseModel):
    """Response model for job status endpoint."""
    job_id: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    result: Optional[AnalyzeResponse] = None
    error: Optional[str] = None
    progress: Optional[Dict] = None


@app.get("/health", response_model=HealthResponse)
@limiter.limit("60/minute")
async def health_check(request: Request):
    """
    Health check endpoint - open access for monitoring.

    Args:
        request: FastAPI request object

    Returns:
        HealthResponse: Status information
    """
    from datetime import datetime, timezone

    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=__version__
    )


@app.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_consent(
    request: Request,
    analyze_request: AnalyzeRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Analyze consent content using the pipeline - requires API key authentication.

    Args:
        request: FastAPI request object
        analyze_request: AnalyzeRequest with source and output format
        authenticated: Authentication dependency

    Returns:
        AnalyzeResponse: Analysis results with request ID
    """
    request_id = getattr(request.state, 'request_id', generate_request_id())
    client_ip = get_remote_address(request)

    try:
        extra = {
            "request_id": request_id,
            "client_ip": client_ip,
            "source_length": len(analyze_request.source),
            "output_format": analyze_request.output_format,
            "auth_status": "authenticated"
        }
        logger.info("Starting consent analysis", extra=extra)

        # Initialize and run pipeline with timeout
        runner = PipelineRunner()

        # Apply request timeout
        import asyncio
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(runner.run, analyze_request.source, output_format=None),
                timeout=settings.request_timeout
            )
        except asyncio.TimeoutError:
            logger.error(
                "Pipeline execution timed out",
                extra={
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "timeout_seconds": settings.request_timeout
                }
            )
            raise HTTPException(
                status_code=408,
                detail=f"Request timeout after {settings.request_timeout} seconds"
            )

        # Count categories
        categories = {}
        for result in results:
            category = result['category']
            categories[category] = categories.get(category, 0) + 1

        # Convert to Pydantic models
        items = [ConsentItem(**result) for result in results]

        success_extra = {
            "request_id": request_id,
            "client_ip": client_ip,
            "items": len(items),
            "categories": categories,
            "auth_status": "authenticated"
        }
        logger.info("Analysis completed successfully", extra=success_extra)

        return AnalyzeResponse(
            success=True,
            items=items,
            total_items=len(items),
            categories=categories,
            request_id=request_id
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like timeout)
        raise
    except Exception as e:
        error_extra = {
            "request_id": request_id,
            "client_ip": client_ip,
            "error": str(e),
            "error_type": type(e).__name__,
            "auth_status": "authenticated"
        }
        logger.error("Analysis failed", extra=error_extra)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Analysis failed",
                "message": str(e),
                "request_id": request_id
            }
        )


@app.post("/analyze_async", response_model=AsyncAnalyzeResponse)
@limiter.limit("5/minute")  # Lower limit for async jobs
async def analyze_consent_async(
    request: Request,
    analyze_request: AnalyzeRequest,
    authenticated: bool = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Queue consent analysis for background processing - requires API key authentication.

    Args:
        request: FastAPI request object
        analyze_request: AnalyzeRequest with source and output format
        authenticated: Authentication dependency
        db: Database session

    Returns:
        AsyncAnalyzeResponse: Job ID and status
    """
    request_id = getattr(request.state, 'request_id', generate_request_id())
    client_ip = get_remote_address(request)

    try:
        # Generate job ID
        job_id = str(uuid.uuid4())

        # Create job record in database
        create_job_record(
            job_id=job_id,
            source_url=analyze_request.source,
            output_format=analyze_request.output_format,
            user_agent=request.headers.get("user-agent"),
            ip_address=client_ip
        )

        # Enqueue the analysis job
        enqueue_task(
            run_analysis_with_storage,
            analyze_request.source,
            analyze_request.output_format,
            job_id,
            job_id=job_id,
            priority='default'
        )

        logger.info(
            "Async analysis job queued",
            extra={
                "request_id": request_id,
                "job_id": job_id,
                "client_ip": client_ip,
                "source_length": len(analyze_request.source),
                "output_format": analyze_request.output_format
            }
        )

        return AsyncAnalyzeResponse(
            job_id=job_id,
            status="queued",
            message="Analysis job has been queued for processing",
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to queue async analysis",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to queue analysis job",
                "message": str(e),
                "request_id": request_id
            }
        )


@app.get("/job/{job_id}", response_model=JobStatusResponse)
@limiter.limit("30/minute")
async def get_job_status_endpoint(
    job_id: str,
    request: Request,
    authenticated: bool = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get the status and result of an async job - requires API key authentication.

    Args:
        job_id: Job ID to check
        request: FastAPI request object
        authenticated: Authentication dependency
        db: Database session

    Returns:
        JobStatusResponse: Job status and result
    """
    request_id = getattr(request.state, 'request_id', generate_request_id())
    client_ip = get_remote_address(request)

    try:
        # Get job status from RQ
        job_status = get_job_status(job_id)

        # Also check database record for additional metadata
        job_record = db.query(JobRecord).filter(JobRecord.id == job_id).first()

        if not job_record and job_status['status'] == 'not_found':
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "job_id": job_id,
                    "request_id": request_id
                }
            )

        # Combine RQ status with database record
        response_data = {
            "job_id": job_id,
            "status": job_status.get('status', 'unknown'),
            "created_at": job_status.get('created_at'),
            "started_at": job_status.get('started_at'),
            "ended_at": job_status.get('ended_at'),
            "error": job_status.get('error'),
            "progress": job_status.get('progress')
        }

        # If job is finished, include the result
        if job_status.get('status') == 'finished' and job_status.get('result'):
            result_data = job_status['result']
            if isinstance(result_data, dict) and 'items' in result_data:
                # Convert to AnalyzeResponse format
                items = [ConsentItem(**item) for item in result_data['items']]
                response_data['result'] = AnalyzeResponse(
                    success=result_data.get('success', True),
                    items=items,
                    total_items=len(items),
                    categories=result_data.get('categories', {}),
                    request_id=result_data.get('request_id', request_id)
                )

        logger.info(
            "Job status retrieved",
            extra={
                "request_id": request_id,
                "job_id": job_id,
                "client_ip": client_ip,
                "job_status": response_data['status']
            }
        )

        return JobStatusResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get job status",
            extra={
                "request_id": request_id,
                "job_id": job_id,
                "client_ip": client_ip,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get job status",
                "message": str(e),
                "request_id": request_id
            }
        )


# Custom rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors with proper logging."""
    request_id = getattr(request.state, 'request_id', generate_request_id())
    client_ip = get_remote_address(request)

    logger.warning(
        "Rate limit exceeded",
        extra={
            "request_id": request_id,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "rate_limit_status": "exceeded",
            "endpoint": str(request.url.path)
        }
    )

    response_data = {
        "error": "Rate limit exceeded",
        "message": f"Too many requests. Please try again later.",
        "request_id": request_id,
        "retry_after": 60
    }

    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=429, content=response_data)


def run_analysis_with_storage(source: str, output_format: str, job_id: str) -> Dict:
    """
    Run consent analysis and store results in database.

    This function is designed to be executed as a background job.

    Args:
        source: URL or HTML content to analyze
        output_format: Output format (json or csv)
        job_id: Job ID for tracking

    Returns:
        Dict: Analysis results
    """
    from db.session import get_db_sync
    import traceback

    db = None
    try:
        # Update job status to started
        update_job_record(job_id, status='started')

        logger.info(f"Starting analysis job {job_id}")

        # Run the analysis
        runner = PipelineRunner()
        results = runner.run(source, output_format=None)

        # Store results in database
        consent_record_id = save_run_results(source, results, job_id)

        # Count categories
        categories = {}
        for result in results:
            category = result['category']
            categories[category] = categories.get(category, 0) + 1

        # Prepare response data
        response_data = {
            'success': True,
            'items': results,
            'total_items': len(results),
            'categories': categories,
            'request_id': job_id,
            'consent_record_id': str(consent_record_id)
        }

        # Update job record with success
        update_job_record(
            job_id,
            status='finished',
            consent_record_id=str(consent_record_id),
            result_data=response_data
        )

        logger.info(f"Analysis job {job_id} completed successfully")
        return response_data

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()

        logger.error(f"Analysis job {job_id} failed: {error_msg}")
        logger.debug(f"Job {job_id} traceback: {error_trace}")

        # Update job record with failure
        update_job_record(
            job_id,
            status='failed',
            error_message=error_msg
        )

        raise e


def save_run_results(source: str, results: List[Dict], job_id: Optional[str] = None) -> str:
    """
    Save analysis results to database.

    Args:
        source: Source URL or content that was analyzed
        results: List of analysis results
        job_id: Optional job ID for linking

    Returns:
        str: Created ConsentRecord ID
    """
    from db.session import get_db_sync
    from db.models import ConsentRecord, ClauseRecord

    db = get_db_sync()
    try:
        # Determine if source is URL or HTML content
        source_url = source if source.startswith(('http://', 'https://')) else None

        # Create ConsentRecord
        consent_record = ConsentRecord(
            source_url=source_url or "HTML_CONTENT",
            total_items=len(results),
            data={
                'source_type': 'url' if source_url else 'html',
                'total_items': len(results),
                'categories': {},
                'job_id': job_id
            },
            status='completed'
        )

        # Calculate categories
        categories = {}
        for result in results:
            category = result.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1

        consent_record.data['categories'] = categories

        db.add(consent_record)
        db.flush()  # Get the ID

        # Create ClauseRecords
        for result in results:
            clause_record = ClauseRecord(
                consent_id=consent_record.id,
                text=result.get('text', ''),
                category=result.get('category', 'unknown'),
                confidence=result.get('confidence'),
                element_type=result.get('element', 'unknown'),
                is_interactive=str(result.get('type', '')).lower()
            )
            db.add(clause_record)

        db.commit()

        logger.info(f"Saved analysis results to database: {consent_record.id}")
        return str(consent_record.id)

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save analysis results: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    settings = Settings()

    # Validate required security settings
    if not settings.api_key:
        logger.error("API_KEY environment variable is required for secure operation")
        exit(1)

    logger.info(
        "Starting secure API server",
        extra={
            "port": settings.fastapi_port,
            "cors_origins": settings.cors_origins,
            "max_payload_mb": settings.max_payload_bytes / 1024 / 1024,
            "request_timeout": settings.request_timeout
        }
    )

    uvicorn.run("api.app:app", host="0.0.0.0", port=settings.fastapi_port, reload=True)
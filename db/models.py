# db/models.py
# Purpose: SQLAlchemy ORM models for database persistence

"""
Database models for storing consent analysis results.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.sql import func

Base = declarative_base()


class ConsentRecord(Base):
    """
    Main record for a consent analysis run.

    Stores metadata about the analysis and aggregated results.
    """
    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url = Column(String(2048), nullable=False, index=True)
    language = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    total_items = Column(Integer, default=0)
    status = Column(String(50), default="completed", index=True)  # completed, failed, processing
    error_message = Column(Text, nullable=True)

    # Store aggregated analysis data as JSON
    data = Column(JSON, nullable=True)

    # Analysis metadata
    processing_time_seconds = Column(Float, nullable=True)
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length

    # Relationships
    clauses = relationship("ClauseRecord", back_populates="consent_record", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ConsentRecord(id={self.id}, source_url={self.source_url}, created_at={self.created_at})>"


class ClauseRecord(Base):
    """
    Individual clause/element found during consent analysis.

    Stores detailed information about each consent element.
    """
    __tablename__ = "clause_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consent_id = Column(UUID(as_uuid=True), ForeignKey("consent_records.id"), nullable=False, index=True)

    # Clause content and metadata
    text = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=True)

    # Location and context information
    element_type = Column(String(50), nullable=True)  # button, link, text, etc.
    xpath = Column(Text, nullable=True)  # XPath to element if available
    css_selector = Column(String(1024), nullable=True)  # CSS selector if available

    # Additional metadata
    is_interactive = Column(String(10), default="false")  # "true", "false", "unknown"
    parent_context = Column(Text, nullable=True)  # Surrounding text context

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    consent_record = relationship("ConsentRecord", back_populates="clauses")

    def __repr__(self):
        return f"<ClauseRecord(id={self.id}, category={self.category}, confidence={self.confidence})>"


class JobRecord(Base):
    """
    Track async job execution status and results.
    """
    __tablename__ = "job_records"

    id = Column(String(36), primary_key=True)  # RQ job ID
    consent_record_id = Column(UUID(as_uuid=True), ForeignKey("consent_records.id"), nullable=True, index=True)

    # Job metadata
    source_url = Column(String(2048), nullable=False, index=True)
    status = Column(String(50), default="queued", index=True)  # queued, started, finished, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Job configuration
    output_format = Column(String(10), default="json")
    priority = Column(Integer, default=0)

    # Results and error handling
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # User context
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)

    def __repr__(self):
        return f"<JobRecord(id={self.id}, status={self.status}, source_url={self.source_url})>"
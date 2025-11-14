"""
SQLAlchemy ORM models for Claudia database

Maps to schema in database/init.sql
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    String, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from .database import Base


class SessionModel(Base):
    """
    Claude Code session tracking
    Maps to: claudia.claude_sessions
    """
    __tablename__ = 'claude_sessions'
    __table_args__ = {'schema': 'claudia'}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    project_path = Column(Text, nullable=True, index=True)
    project_name = Column(String(255), nullable=True)
    started_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    session_metadata = Column('metadata', JSONB, default={}, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tool_executions = relationship('ToolExecutionModel', back_populates='session', cascade='all, delete-orphan')
    settings_snapshots = relationship('SettingsSnapshotModel', back_populates='session', cascade='all, delete-orphan')

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'session_id': self.session_id,
            'project_path': self.project_path,
            'project_name': self.project_name,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'is_active': self.is_active,
            'metadata': self.session_metadata,
        }


class ToolExecutionModel(Base):
    """
    Tool execution tracking
    Maps to: claudia.tool_executions
    """
    __tablename__ = 'tool_executions'
    __table_args__ = {'schema': 'claudia'}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey('claudia.claude_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    parameters = Column(JSONB, nullable=True)
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_ms = Column(Integer, nullable=True)

    # Relationships
    session = relationship('SessionModel', back_populates='tool_executions')

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'tool_name': self.tool_name,
            'parameters': self.parameters,
            'result': self.result,
            'error': self.error,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'duration_ms': self.duration_ms,
        }


class SettingsSnapshotModel(Base):
    """
    Settings snapshots tracking
    Maps to: claudia.settings_snapshots
    """
    __tablename__ = 'settings_snapshots'
    __table_args__ = {'schema': 'claudia'}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey('claudia.claude_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    settings_json = Column(JSONB, nullable=False)
    hierarchy_level = Column(String(50), nullable=True, index=True)  # 'user', 'project', 'local', 'managed'
    file_path = Column(Text, nullable=True)
    captured_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Relationships
    session = relationship('SessionModel', back_populates='settings_snapshots')

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'settings_json': self.settings_json,
            'hierarchy_level': self.hierarchy_level,
            'file_path': self.file_path,
            'captured_at': self.captured_at.isoformat() if self.captured_at else None,
        }

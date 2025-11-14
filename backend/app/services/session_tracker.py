"""
Session tracking service for Claude Code
Tracks active and recent sessions with metadata
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from app.constants import SESSION_TIMEOUT_MINUTES

logger = logging.getLogger(__name__)


class Session:
    """Represents a Claude Code session"""

    def __init__(
        self,
        session_id: str,
        project_path: str,
        project_name: str,
        started_at: Optional[datetime] = None,
        runtime_config: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.project_path = project_path
        self.project_name = project_name
        self.started_at = started_at or datetime.now(timezone.utc)
        self.ended_at: Optional[datetime] = None
        self.is_active = True
        self.runtime_config = runtime_config or {}
        self.last_activity = self.started_at
        self.tool_count = 0
        self.transcript_path: Optional[str] = None

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)

    def end(self):
        """Mark session as ended"""
        self.is_active = False
        self.ended_at = datetime.now(timezone.utc)

    def is_timed_out(self, timeout_minutes: int = SESSION_TIMEOUT_MINUTES) -> bool:
        """Check if session has timed out due to inactivity"""
        if not self.is_active:
            return False

        timeout = timedelta(minutes=timeout_minutes)
        return (datetime.now(timezone.utc) - self.last_activity) > timeout

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'project_path': self.project_path,
            'project_name': self.project_name,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'is_active': self.is_active,
            'runtime_config': self.runtime_config,
            'last_activity': self.last_activity.isoformat(),
            'tool_count': self.tool_count,
            'transcript_path': self.transcript_path,
            'duration_seconds': self.get_duration_seconds()
        }

    def get_duration_seconds(self) -> float:
        """Get session duration in seconds"""
        end_time = self.ended_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()


class SessionTracker:
    """
    Track Claude Code sessions
    Maintains in-memory state of active and recent sessions
    """

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.max_recent_sessions = 100  # Keep last 100 sessions in memory

    def start_session(
        self,
        session_id: str,
        project_path: str,
        project_name: str,
        transcript_path: Optional[str] = None,
        runtime_config: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Start tracking a new session"""
        session = Session(
            session_id=session_id,
            project_path=project_path,
            project_name=project_name,
            runtime_config=runtime_config
        )

        if transcript_path:
            session.transcript_path = transcript_path

        self.sessions[session_id] = session
        logger.info(f"Started tracking session: {session_id} ({project_name})")

        # Cleanup old sessions
        self._cleanup_old_sessions()

        return session

    def end_session(self, session_id: str):
        """Mark a session as ended"""
        if session_id in self.sessions:
            self.sessions[session_id].end()
            logger.info(f"Ended session: {session_id}")
        else:
            logger.warning(f"Attempted to end unknown session: {session_id}")

    def update_session_activity(self, session_id: str):
        """Update session activity timestamp"""
        if session_id in self.sessions:
            self.sessions[session_id].update_activity()

    def record_tool_execution(self, session_id: str):
        """Record a tool execution for a session"""
        if session_id in self.sessions:
            self.sessions[session_id].tool_count += 1
            self.sessions[session_id].update_activity()

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session"""
        return self.sessions.get(session_id)

    def get_active_sessions(self) -> List[Session]:
        """Get all currently active sessions"""
        # Check for timeouts
        self._check_timeouts()

        return [
            session for session in self.sessions.values()
            if session.is_active
        ]

    def get_recent_sessions(self, hours: int = 24) -> List[Session]:
        """Get sessions from the last N hours"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent = [
            session for session in self.sessions.values()
            if session.started_at >= cutoff
        ]

        # Sort by start time, most recent first
        return sorted(recent, key=lambda s: s.started_at, reverse=True)

    def get_sessions_by_project(self, project_path: str) -> List[Session]:
        """Get all sessions for a specific project"""
        return [
            session for session in self.sessions.values()
            if session.project_path == project_path
        ]

    def get_session_count(self, active_only: bool = False) -> int:
        """Get count of sessions"""
        if active_only:
            return len(self.get_active_sessions())
        return len(self.sessions)

    def _check_timeouts(self):
        """Check for and mark timed-out sessions"""
        for session in self.sessions.values():
            if session.is_timed_out():
                logger.info(f"Session timed out: {session.session_id}")
                session.end()

    def _cleanup_old_sessions(self):
        """Remove old inactive sessions to prevent unbounded memory growth"""
        if len(self.sessions) <= self.max_recent_sessions:
            return

        # Get all inactive sessions sorted by end time
        inactive = [
            (sid, session) for sid, session in self.sessions.items()
            if not session.is_active and session.ended_at
        ]

        if not inactive:
            return

        # Sort by end time, oldest first
        inactive.sort(key=lambda x: x[1].ended_at)

        # Remove oldest sessions until we're under the limit
        to_remove = len(self.sessions) - self.max_recent_sessions
        for i in range(min(to_remove, len(inactive))):
            session_id = inactive[i][0]
            del self.sessions[session_id]
            logger.debug(f"Cleaned up old session: {session_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        active = self.get_active_sessions()
        recent = self.get_recent_sessions(hours=24)

        total_tools = sum(s.tool_count for s in self.sessions.values())
        avg_duration = sum(s.get_duration_seconds() for s in self.sessions.values()) / len(self.sessions) if self.sessions else 0

        return {
            'total_sessions': len(self.sessions),
            'active_sessions': len(active),
            'sessions_last_24h': len(recent),
            'total_tools_executed': total_tools,
            'average_session_duration_seconds': avg_duration,
            'unique_projects': len(set(s.project_path for s in self.sessions.values()))
        }

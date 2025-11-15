"""
Session tracking service for Claude Code
Tracks active and recent sessions with database persistence
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any, Dict
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from loguru import logger

from app.db.models import SessionModel, ToolExecutionModel, UserPromptModel, AssistantMessageModel
from app.constants import SESSION_TIMEOUT_MINUTES
from app.exceptions import SessionNotFoundException
from app.services.embedding_service import get_embedding_service


class SessionTracker:
    """
    Track Claude Code sessions using database as single source of truth
    All methods are async and require a database session
    """

    def __init__(self):
        """Initialize session tracker with embedding service"""
        self.embedding_service = get_embedding_service()

    async def start_session(
        self,
        db: AsyncSession,
        session_id: str,
        project_path: str,
        project_name: str,
        transcript_path: Optional[str] = None,
        runtime_config: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None
    ) -> SessionModel:
        """Start tracking a new session by inserting into database

        If session exists (e.g., --continue), updates it with new data from Claude Code hook.
        This ensures session state reflects current Claude Code state.
        """

        # Check if session already exists
        stmt = select(SessionModel).where(
            SessionModel.session_id == session_id
        ).options(selectinload(SessionModel.tool_executions))
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"Session {session_id} resuming (source={source})")

            # CRITICAL: Replace with new data from Claude Code hook
            # This fixes the "0 active sessions" bug when using --continue
            existing.project_path = project_path
            existing.project_name = project_name
            existing.started_at = datetime.now(timezone.utc)
            existing.is_active = True
            existing.ended_at = None  # Clear previous end time
            existing.source = source

            # Store raw hook data in session_metadata
            session_metadata = runtime_config or {}
            if transcript_path:
                session_metadata['transcript_path'] = transcript_path
            existing.session_metadata = session_metadata

            # Our augmentations in claudia_metadata
            if not existing.claudia_metadata:
                existing.claudia_metadata = {}
            if 'first_seen_at' not in existing.claudia_metadata:
                existing.claudia_metadata['first_seen_at'] = str(existing.started_at)

            await db.flush()
            await db.refresh(existing, ['tool_executions'])
            logger.info(f"Reactivated session: {session_id}")
            return existing

        # Create new session
        session_metadata = runtime_config or {}
        if transcript_path:
            session_metadata['transcript_path'] = transcript_path

        claudia_metadata = {
            'first_seen_at': str(datetime.now(timezone.utc))
        }

        session = SessionModel(
            session_id=session_id,
            project_path=project_path,
            project_name=project_name,
            session_metadata=session_metadata,
            claudia_metadata=claudia_metadata,
            source=source,
            started_at=datetime.now(timezone.utc),
            is_active=True
        )

        db.add(session)
        await db.flush()  # Flush to get the ID without committing

        # Refresh with eager loading to prevent MissingGreenlet in to_dict()
        await db.refresh(session, ['tool_executions'])

        logger.info(f"Started tracking session: {session_id} ({project_name}, source={source})")
        return session

    async def end_session(
        self,
        db: AsyncSession,
        session_id: str,
        reason: Optional[str] = None,
        project_path: Optional[str] = None,
        project_name: Optional[str] = None,
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> SessionModel:
        """Mark a session as ended by updating database

        Updates all fields with data from Claude Code hook.
        """
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            logger.error(f"Cannot end unknown session: {session_id}")
            raise SessionNotFoundException(session_id)

        # Replace with data from Claude Code hook
        session.is_active = False
        session.ended_at = datetime.now(timezone.utc)
        session.reason = reason

        # Update other fields if provided by hook
        if project_path is not None:
            session.project_path = project_path
        if project_name is not None:
            session.project_name = project_name
        if session_metadata is not None:
            session.session_metadata = session_metadata

        await db.flush()
        logger.info(f"Ended session: {session_id} (reason={reason})")
        return session

    async def record_tool_execution(
        self,
        db: AsyncSession,
        session_id: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> ToolExecutionModel:
        """Record a tool execution for a session"""

        # Find session
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        result_row = await db.execute(stmt)
        session = result_row.scalar_one_or_none()

        if not session:
            logger.error(f"Cannot record tool execution for unknown session: {session_id}")
            raise SessionNotFoundException(session_id)

        # Create tool execution record
        tool_execution = ToolExecutionModel(
            session_id=session.id,
            tool_name=tool_name or "unknown",
            parameters=parameters,
            result=result,
            error=error,
            executed_at=datetime.now(timezone.utc),
            duration_ms=duration_ms
        )

        db.add(tool_execution)
        await db.flush()

        return tool_execution

    async def capture_user_prompt(
        self,
        db: AsyncSession,
        session_id: str,
        prompt_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserPromptModel:
        """Capture a user prompt for later vectorization"""

        # Find session
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            logger.error(f"Cannot capture prompt for unknown session: {session_id}")
            raise SessionNotFoundException(session_id)

        # Generate embedding for prompt
        embedding = await self.embedding_service.generate_embedding(prompt_text)

        # Create user prompt record
        user_prompt = UserPromptModel(
            session_id=session.id,
            prompt_text=prompt_text,
            prompt_metadata=metadata or {},
            embedding=embedding,
            created_at=datetime.now(timezone.utc)
        )

        db.add(user_prompt)
        await db.flush()

        logger.info(f"Captured user prompt for session {session_id} ({len(prompt_text)} chars, embedding: {embedding is not None})")
        return user_prompt

    async def capture_assistant_message(
        self,
        db: AsyncSession,
        session_id: str,
        message_text: str,
        conversation_turn: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AssistantMessageModel:
        """Capture an assistant message for later vectorization"""

        # Find session
        stmt = select(SessionModel).where(SessionModel.session_id == session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            logger.error(f"Cannot capture message for unknown session: {session_id}")
            raise SessionNotFoundException(session_id)

        # Generate embedding for message
        embedding = await self.embedding_service.generate_embedding(message_text)

        # Create assistant message record
        assistant_message = AssistantMessageModel(
            session_id=session.id,
            message_text=message_text,
            conversation_turn=conversation_turn,
            message_metadata=metadata or {},
            embedding=embedding,
            created_at=datetime.now(timezone.utc)
        )

        db.add(assistant_message)
        await db.flush()

        logger.info(f"Captured assistant message for session {session_id} (turn {conversation_turn}, {len(message_text)} chars, embedding: {embedding is not None})")
        return assistant_message

    async def get_session(self, db: AsyncSession, session_id: str) -> Optional[SessionModel]:
        """Get a specific session by session_id"""
        stmt = select(SessionModel).where(
            SessionModel.session_id == session_id
        ).options(selectinload(SessionModel.tool_executions))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_sessions(self, db: AsyncSession) -> List[SessionModel]:
        """Get all currently active sessions"""
        # Auto-timeout old sessions
        await self._check_timeouts(db)

        stmt = select(SessionModel).where(
            SessionModel.is_active == True
        ).options(selectinload(SessionModel.tool_executions)).order_by(SessionModel.started_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_sessions(
        self,
        db: AsyncSession,
        hours: int = 24
    ) -> List[SessionModel]:
        """Get sessions from the last N hours"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = select(SessionModel).where(
            SessionModel.started_at >= cutoff
        ).options(selectinload(SessionModel.tool_executions)).order_by(SessionModel.started_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_sessions_by_project(
        self,
        db: AsyncSession,
        project_path: str
    ) -> List[SessionModel]:
        """Get all sessions for a specific project"""
        stmt = select(SessionModel).where(
            SessionModel.project_path == project_path
        ).options(selectinload(SessionModel.tool_executions)).order_by(SessionModel.started_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_session_count(
        self,
        db: AsyncSession,
        active_only: bool = False
    ) -> int:
        """Get count of sessions"""
        if active_only:
            stmt = select(func.count()).select_from(SessionModel).where(
                SessionModel.is_active == True
            )
        else:
            stmt = select(func.count()).select_from(SessionModel)

        result = await db.execute(stmt)
        return result.scalar() or 0

    async def get_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get overall statistics from database"""

        # Total sessions
        total_stmt = select(func.count()).select_from(SessionModel)
        total_result = await db.execute(total_stmt)
        total_sessions = total_result.scalar() or 0

        # Active sessions
        active_stmt = select(func.count()).select_from(SessionModel).where(
            SessionModel.is_active == True
        )
        active_result = await db.execute(active_stmt)
        active_sessions = active_result.scalar() or 0

        # Sessions in last 24h
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_stmt = select(func.count()).select_from(SessionModel).where(
            SessionModel.started_at >= cutoff_24h
        )
        recent_result = await db.execute(recent_stmt)
        sessions_24h = recent_result.scalar() or 0

        # Total tool executions
        tools_stmt = select(func.count()).select_from(ToolExecutionModel)
        tools_result = await db.execute(tools_stmt)
        total_tools = tools_result.scalar() or 0

        # Average session duration (for ended sessions)
        # Using raw SQL for EXTRACT(EPOCH FROM ...) calculation
        duration_stmt = select(
            func.avg(
                func.extract('epoch', SessionModel.ended_at) -
                func.extract('epoch', SessionModel.started_at)
            )
        ).where(SessionModel.ended_at.isnot(None))

        duration_result = await db.execute(duration_stmt)
        avg_duration = duration_result.scalar() or 0

        # Unique projects
        projects_stmt = select(func.count(func.distinct(SessionModel.project_path)))
        projects_result = await db.execute(projects_stmt)
        unique_projects = projects_result.scalar() or 0

        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'sessions_last_24h': sessions_24h,
            'total_tools_executed': total_tools,
            'average_session_duration_seconds': float(avg_duration),
            'unique_projects': unique_projects
        }

    async def _check_timeouts(
        self,
        db: AsyncSession,
        timeout_minutes: int = SESSION_TIMEOUT_MINUTES
    ):
        """Check for and mark timed-out sessions"""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        # Find active sessions with last tool execution before cutoff
        # This is a simplified approach - we check if the session started before cutoff
        # A more sophisticated approach would track last_activity separately

        stmt = update(SessionModel).where(
            SessionModel.is_active == True,
            SessionModel.started_at < cutoff,
            SessionModel.ended_at.is_(None)
        ).values(
            is_active=False,
            ended_at=datetime.now(timezone.utc)
        )

        result = await db.execute(stmt)

        if result.rowcount > 0:
            logger.info(f"Timed out {result.rowcount} inactive session(s)")

"""
Claudia Backend - Claude Code Companion API
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import time
import uuid
import os
import pty
import signal

from app.config import settings, ensure_directories
from app.logging_config import setup_logging
from app.services import FileMonitor, SettingsAggregator, SessionTracker, get_search_service
from app.db.database import get_db, init_db, close_db, AsyncSessionLocal
from app.constants import (
    EVENT_SESSION_START,
    EVENT_SESSION_END,
    EVENT_TOOL_EXECUTION,
    EVENT_USER_PROMPT,
    EVENT_ASSISTANT_MESSAGE,
    EVENT_SETTINGS_UPDATE
)
from app.exceptions import (
    SessionNotFoundException,
    DirectoryNotFoundException,
    session_not_found_error
)
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logger = setup_logging()

# Global service instances
file_monitor: Optional[FileMonitor] = None
settings_aggregator: Optional[SettingsAggregator] = None
session_tracker: Optional[SessionTracker] = None
active_connections: List[WebSocket] = []


# Pydantic models for request/response
class SessionStartRequest(BaseModel):
    session_id: str
    project_path: str
    project_name: str
    transcript_path: Optional[str] = None
    permission_mode: Optional[str] = None
    runtime_config: Optional[Dict[str, Any]] = None
    source: Optional[str] = None  # startup|resume|clear|compact
    event_type: Optional[str] = None
    timestamp: Optional[str] = None


class SessionEndRequest(BaseModel):
    session_id: str
    reason: Optional[str] = None  # exit|logout|clear|prompt_input_exit|other
    project_path: Optional[str] = None
    project_name: Optional[str] = None
    session_metadata: Optional[Dict[str, Any]] = None
    event_type: Optional[str] = None


class ToolUseRequest(BaseModel):
    session_id: str
    event_type: Optional[str] = None
    tool_name: str
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    working_directory: Optional[str] = None
    timestamp: Optional[str] = None


class PromptCaptureRequest(BaseModel):
    session_id: str
    prompt_text: str
    timestamp: Optional[str] = None


class MessageCaptureRequest(BaseModel):
    session_id: str
    message_text: str
    conversation_turn: int = 0
    timestamp: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    similarity_threshold: float = 0.5
    session_id: Optional[str] = None


async def broadcast_event(event_type: str, data: Any):
    """Broadcast event to all connected WebSocket clients"""
    message = {
        "type": event_type,
        "data": data,
        "timestamp": None  # Could add server timestamp if needed
    }

    dead_connections = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            dead_connections.append(connection)

    # Clean up dead connections
    for conn in dead_connections:
        if conn in active_connections:
            active_connections.remove(conn)


def handle_file_event(event: Dict[str, Any]):
    """Handle events from file monitor"""
    event_type = event.get('type')

    if event_type == 'session_start':
        # File monitor detected new session directory
        session_id = event.get('session_id')
        project_path = event.get('project_path')

        if session_id and project_path:
            async def start_session_task():
                assert session_tracker is not None, "Service not initialized"
                async with AsyncSessionLocal() as db:
                    try:
                        await session_tracker.start_session(
                            db=db,
                            session_id=session_id,
                            project_path=project_path,
                            project_name=Path(project_path).name
                        )
                        await db.commit()
                    except Exception as e:
                        logger.error(f"Error starting session: {e}")
                        await db.rollback()

            asyncio.create_task(start_session_task())
            # Broadcast to clients
            asyncio.create_task(broadcast_event(EVENT_SESSION_START, event))

    elif event_type == 'tool_execution':
        # Update session activity
        session_id = event.get('session_id')
        if session_id:
            async def record_tool_task():
                assert session_tracker is not None, "Service not initialized"
                async with AsyncSessionLocal() as db:
                    try:
                        await session_tracker.record_tool_execution(
                            db=db,
                            session_id=session_id
                        )
                        await db.commit()
                    except Exception as e:
                        logger.error(f"Error recording tool execution: {e}")
                        await db.rollback()

            asyncio.create_task(record_tool_task())

        # Broadcast to clients
        asyncio.create_task(broadcast_event(EVENT_TOOL_EXECUTION, event))

    elif event_type == 'settings_update':
        # Broadcast settings update
        asyncio.create_task(broadcast_event(EVENT_SETTINGS_UPDATE, event))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    global file_monitor, settings_aggregator, session_tracker

    # Startup
    logger.info("Starting Claudia backend services...")

    # Check required directories exist
    try:
        ensure_directories()
        logger.info("✓ Required directories validated")
    except DirectoryNotFoundException as e:
        logger.error(
            f"Cannot start: {e.directory_path} does not exist. "
            "Please ensure Claude Code is installed and configured. "
            "Continuing startup for development, but monitoring will not work."
        )

    # Initialize database connection pool
    await init_db()
    logger.info("✓ Database initialized")

    # Initialize services
    settings_aggregator = SettingsAggregator(settings.claude_settings_path)
    session_tracker = SessionTracker()

    # Start file monitor
    file_monitor = FileMonitor(
        projects_path=settings.claude_projects_path,
        callback=handle_file_event
    )
    file_monitor.start()

    logger.info("✓ All services started")

    yield

    # Shutdown
    logger.info("Stopping Claudia backend services...")
    if file_monitor:
        file_monitor.stop()
    await close_db()
    logger.info("✓ All services stopped")


# Create FastAPI app with Swagger documentation
app = FastAPI(
    title="Claudia API",
    description="Real-time monitoring and enhancement API for Claude Code",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests and responses with timing and request IDs"""
    request_id = str(uuid.uuid4())[:8]  # Short request ID

    # Log request
    logger.info(
        f"→ {request.method} {request.url.path}",
        extra={"request_id": request_id, "client": request.client.host if request.client else "unknown"}
    )

    # Process request and measure duration
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    logger.info(
        f"← {request.method} {request.url.path} [{response.status_code}] {duration_ms:.2f}ms",
        extra={"request_id": request_id}
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Claudia API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    active_sessions = 0
    if session_tracker:
        active_sessions = await session_tracker.get_session_count(db, active_only=True)

    status = {
        "status": "healthy",
        "file_monitor": file_monitor.is_running() if file_monitor else False,
        "active_connections": len(active_connections),
        "active_sessions": active_sessions
    }
    return status


# Session endpoints
@app.get("/api/sessions/active")
async def get_active_sessions(db: AsyncSession = Depends(get_db)):
    """Get all currently active Claude Code sessions"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    sessions = await session_tracker.get_active_sessions(db)
    return {
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions)
    }


@app.get("/api/sessions/recent")
async def get_recent_sessions(hours: int = 24, db: AsyncSession = Depends(get_db)):
    """Get sessions from the last N hours"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    sessions = await session_tracker.get_recent_sessions(db, hours=hours)
    return {
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions),
        "hours": hours
    }


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get details of a specific session"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    session = await session_tracker.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    return session.to_dict()


@app.get("/api/sessions/{session_id}/prompts")
async def get_session_prompts(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get all user prompts for a specific session"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    try:
        prompts = await session_tracker.get_session_prompts(db, session_id)
        return {
            "prompts": [p.to_dict() for p in prompts],
            "count": len(prompts)
        }
    except SessionNotFoundException:
        raise session_not_found_error(session_id)


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get all assistant messages for a specific session"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    try:
        messages = await session_tracker.get_session_messages(db, session_id)
        return {
            "messages": [m.to_dict() for m in messages],
            "count": len(messages)
        }
    except SessionNotFoundException:
        raise session_not_found_error(session_id)


@app.get("/api/sessions/{session_id}/tools")
async def get_session_tools(
    session_id: str,
    tool_name: Optional[str] = None,
    has_error: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all tool executions for a specific session with optional filtering"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    try:
        tools = await session_tracker.get_session_tools(db, session_id, tool_name, has_error)
        return {
            "tools": [t.to_dict() for t in tools],
            "count": len(tools)
        }
    except SessionNotFoundException:
        raise session_not_found_error(session_id)


@app.get("/api/sessions/{session_id}/conversation")
async def get_session_conversation(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get chronological conversation (prompts + messages) for a specific session"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    try:
        conversation = await session_tracker.get_session_conversation(db, session_id)
        return {
            "conversation": conversation,
            "count": len(conversation)
        }
    except SessionNotFoundException:
        raise session_not_found_error(session_id)


@app.post("/api/sessions/start")
async def session_start(req: SessionStartRequest, db: AsyncSession = Depends(get_db)):
    """Handle session start event from hooks"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    # Start tracking session
    session = await session_tracker.start_session(
        db=db,
        session_id=req.session_id,
        project_path=req.project_path,
        project_name=req.project_name,
        transcript_path=req.transcript_path,
        runtime_config=req.runtime_config,
        source=req.source
    )

    # Broadcast to WebSocket clients
    await broadcast_event(EVENT_SESSION_START, session.to_dict())

    return {"status": "started", "session": session.to_dict()}


@app.post("/api/sessions/end")
async def session_end(req: SessionEndRequest, db: AsyncSession = Depends(get_db)):
    """Handle session end event from hooks"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    try:
        await session_tracker.end_session(
            db=db,
            session_id=req.session_id,
            reason=req.reason,
            project_path=req.project_path,
            project_name=req.project_name,
            session_metadata=req.session_metadata
        )

        session = await session_tracker.get_session(db, req.session_id)
        session_data = session.to_dict() if session else {"session_id": req.session_id}

        # Broadcast to WebSocket clients
        await broadcast_event(EVENT_SESSION_END, session_data)

        return {"status": "ended", "session_id": req.session_id}
    except SessionNotFoundException:
        raise session_not_found_error(req.session_id)


# Settings endpoints
@app.get("/api/settings/current")
async def get_current_settings(project_path: Optional[str] = None):
    """Get current computed settings"""
    if not settings_aggregator:
        raise HTTPException(status_code=503, detail="Settings aggregator not initialized")

    project = Path(project_path) if project_path else None
    summary = settings_aggregator.get_settings_summary(project_path=project)

    return summary


@app.get("/api/settings/hierarchy")
async def get_settings_hierarchy(project_path: Optional[str] = None):
    """Get settings hierarchy from all sources"""
    if not settings_aggregator:
        raise HTTPException(status_code=503, detail="Settings aggregator not initialized")

    project = Path(project_path) if project_path else None
    hierarchy = settings_aggregator.get_settings_hierarchy(project_path=project)

    return {
        "hierarchy": hierarchy,
        "sources": list(hierarchy.keys())
    }


# Monitoring endpoints
@app.post("/api/monitoring/tool-use")
async def tool_use(req: ToolUseRequest, db: AsyncSession = Depends(get_db)):
    """Handle tool execution event from hooks"""
    if not session_tracker:
        return {"status": "ok", "note": "Session tracker not initialized"}

    try:
        # Record tool execution in database
        await session_tracker.record_tool_execution(
            db=db,
            session_id=req.session_id,
            tool_name=req.tool_name,
            parameters=req.parameters,
            result=req.result
        )

        # Broadcast to WebSocket clients
        event_data = {
            "session_id": req.session_id,
            "tool_name": req.tool_name,
            "parameters": req.parameters,
            "timestamp": req.timestamp
        }
        await broadcast_event(EVENT_TOOL_EXECUTION, event_data)

        return {"status": "recorded"}
    except SessionNotFoundException:
        raise session_not_found_error(req.session_id)


@app.post("/api/prompts/capture")
async def capture_prompt(req: PromptCaptureRequest, db: AsyncSession = Depends(get_db)):
    """Capture user prompt from UserPromptSubmit hook"""
    if not session_tracker:
        return {"status": "ok", "note": "Session tracker not initialized"}

    try:
        await session_tracker.capture_user_prompt(
            db=db,
            session_id=req.session_id,
            prompt_text=req.prompt_text
        )

        # Broadcast real-time update
        prompt_data = {
            'session_id': req.session_id,
            'prompt_text': req.prompt_text,
            'timestamp': req.timestamp
        }
        await broadcast_event(EVENT_USER_PROMPT, prompt_data)

        return {"status": "captured", "session_id": req.session_id}
    except SessionNotFoundException:
        raise session_not_found_error(req.session_id)


@app.post("/api/messages/capture")
async def capture_message(req: MessageCaptureRequest, db: AsyncSession = Depends(get_db)):
    """Capture assistant message from Stop hook"""
    if not session_tracker:
        return {"status": "ok", "note": "Session tracker not initialized"}

    try:
        await session_tracker.capture_assistant_message(
            db=db,
            session_id=req.session_id,
            message_text=req.message_text,
            conversation_turn=req.conversation_turn
        )

        # Broadcast real-time update
        message_data = {
            'session_id': req.session_id,
            'message_text': req.message_text,
            'conversation_turn': req.conversation_turn,
            'timestamp': req.timestamp
        }
        await broadcast_event(EVENT_ASSISTANT_MESSAGE, message_data)

        return {"status": "captured", "session_id": req.session_id, "turn": req.conversation_turn}
    except SessionNotFoundException:
        raise session_not_found_error(req.session_id)


@app.post("/api/monitoring/settings-snapshot")
async def settings_snapshot(data: Dict[str, Any]):
    """Handle settings snapshot from hooks"""
    # Broadcast to WebSocket clients
    await broadcast_event(EVENT_SETTINGS_UPDATE, data)

    return {"status": "recorded"}


@app.get("/api/monitoring/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get overall monitoring statistics"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    return await session_tracker.get_stats(db)


# Semantic search endpoints
@app.post("/api/search/prompts")
async def search_prompts(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Search user prompts using semantic similarity

    Returns prompts similar to the query, ordered by similarity score
    """
    search_service = get_search_service()

    results = await search_service.search_prompts(
        db=db,
        query=req.query,
        limit=req.limit,
        similarity_threshold=req.similarity_threshold,
        session_id=req.session_id
    )

    return {
        "query": req.query,
        "results": results,
        "count": len(results)
    }


@app.post("/api/search/messages")
async def search_messages(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Search assistant messages using semantic similarity

    Returns messages similar to the query, ordered by similarity score
    """
    search_service = get_search_service()

    results = await search_service.search_messages(
        db=db,
        query=req.query,
        limit=req.limit,
        similarity_threshold=req.similarity_threshold,
        session_id=req.session_id
    )

    return {
        "query": req.query,
        "results": results,
        "count": len(results)
    }


@app.post("/api/search/conversations")
async def search_conversations(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Search both prompts and messages using semantic similarity

    Returns unified results from both prompts and messages, ordered by similarity
    """
    search_service = get_search_service()

    results = await search_service.search_conversations(
        db=db,
        query=req.query,
        limit=req.limit,
        similarity_threshold=req.similarity_threshold
    )

    return {
        "query": req.query,
        "results": results,
        "count": len(results)
    }


# WebSocket endpoint
@app.websocket("/api/monitoring/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")

    try:
        while True:
            # Keep connection alive (required by FastAPI/Starlette)
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Remaining: {len(active_connections)}")


@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    """Interactive terminal via PTY - spawns isolated shell session"""
    await websocket.accept()

    # Generate unique session ID for logging
    session_id = str(uuid.uuid4())[:8]
    logger.info(f"Terminal session {session_id} connected")

    shell = os.environ.get("SHELL", "/bin/zsh")
    pid, fd = pty.fork()

    if pid == 0:  # Child process
        # Execute login shell (PTY already provides isolation)
        os.execvp(shell, [shell, "-l"])

    # Parent process - track this session
    logger.info(f"Terminal session {session_id}: spawned shell PID {pid}")

    loop = asyncio.get_event_loop()

    async def pty_to_websocket():
        """Read from PTY, send to WebSocket"""
        try:
            while True:
                data = await loop.run_in_executor(None, os.read, fd, 1024)
                if not data:
                    break
                await websocket.send_text(data.decode(errors="ignore"))
        except Exception as e:
            logger.debug(f"Terminal session {session_id}: PTY read ended ({e})")

    reader_task = asyncio.create_task(pty_to_websocket())

    try:
        while True:
            msg = await websocket.receive_text()
            os.write(fd, msg.encode())
    except WebSocketDisconnect:
        logger.info(f"Terminal session {session_id}: client disconnected")
    except Exception as e:
        logger.error(f"Terminal session {session_id}: error - {e}")
    finally:
        # Cleanup: aggressive process termination
        reader_task.cancel()
        try:
            await reader_task
        except asyncio.CancelledError:
            pass

        # Try graceful shutdown first
        try:
            # Kill process group (negative PID)
            os.kill(-pid, signal.SIGTERM)
            logger.debug(f"Terminal session {session_id}: sent SIGTERM to process group {pid}")
        except ProcessLookupError:
            logger.debug(f"Terminal session {session_id}: process {pid} already dead")
        except Exception as e:
            logger.warning(f"Terminal session {session_id}: SIGTERM failed - {e}")

        # Wait briefly for graceful shutdown
        await asyncio.sleep(0.1)

        # Force kill if still alive
        try:
            os.kill(-pid, signal.SIGKILL)
            logger.debug(f"Terminal session {session_id}: sent SIGKILL to process group {pid}")
        except ProcessLookupError:
            pass  # Already dead, good
        except Exception as e:
            logger.warning(f"Terminal session {session_id}: SIGKILL failed - {e}")

        # Close PTY
        try:
            os.close(fd)
        except OSError:
            pass

        # Wait for zombie cleanup
        try:
            os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            pass

        logger.info(f"Terminal session {session_id}: cleanup complete")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

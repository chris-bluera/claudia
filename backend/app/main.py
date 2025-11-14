"""
Claudia Backend - Claude Code Companion API
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import json
import logging

from app.config import settings
from app.services import FileMonitor, SettingsAggregator, SessionTracker
from app.db.database import get_db, init_db, close_db, AsyncSessionLocal
from app.db.models import SessionModel
from app.constants import (
    EVENT_SESSION_START,
    EVENT_SESSION_END,
    EVENT_TOOL_EXECUTION,
    EVENT_SETTINGS_UPDATE
)
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logging.basicConfig(level=settings.backend_log_level)
logger = logging.getLogger(__name__)

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
    event_type: Optional[str] = None
    timestamp: Optional[str] = None


class SessionEndRequest(BaseModel):
    session_id: str
    event_type: Optional[str] = None


class ToolUseRequest(BaseModel):
    session_id: str
    event_type: Optional[str] = None
    tool_name: str
    parameters: Optional[Dict[str, Any]] = None
    working_directory: Optional[str] = None
    timestamp: Optional[str] = None


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
        runtime_config=req.runtime_config
    )

    # Broadcast to WebSocket clients
    await broadcast_event(EVENT_SESSION_START, session.to_dict())

    return {"status": "started", "session": session.to_dict()}


@app.post("/api/sessions/end")
async def session_end(req: SessionEndRequest, db: AsyncSession = Depends(get_db)):
    """Handle session end event from hooks"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    await session_tracker.end_session(db, req.session_id)

    session = await session_tracker.get_session(db, req.session_id)
    session_data = session.to_dict() if session else {"session_id": req.session_id}

    # Broadcast to WebSocket clients
    await broadcast_event(EVENT_SESSION_END, session_data)

    return {"status": "ended", "session_id": req.session_id}


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

    # Record tool execution in database
    await session_tracker.record_tool_execution(
        db=db,
        session_id=req.session_id,
        tool_name=req.tool_name,
        parameters=req.parameters
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


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

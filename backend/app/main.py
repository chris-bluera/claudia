"""
Claudia Backend - Claude Code Companion API
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Dict, Any
import asyncio
import json

# Create FastAPI app with Swagger documentation
app = FastAPI(
    title="Claudia API",
    description="Real-time monitoring and enhancement API for Claude Code",
    version="0.1.0",
    docs_url="/api/docs",      # Swagger UI endpoint
    redoc_url="/api/redoc",    # ReDoc alternative
    openapi_url="/api/openapi.json"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: List[WebSocket] = []

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
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/sessions")
async def get_sessions():
    """Get all active Claude Code sessions"""
    # TODO: Implement session tracking
    return {
        "sessions": [],
        "count": 0
    }

@app.get("/api/settings")
async def get_settings():
    """Get current Claude Code settings hierarchy"""
    # TODO: Implement settings aggregation
    return {
        "user": {},
        "project": {},
        "local": {},
        "computed": {}
    }

@app.get("/api/hooks")
async def get_hooks():
    """Get configured hooks"""
    # TODO: Implement hook management
    return {
        "hooks": [],
        "count": 0
    }

@app.post("/api/hooks")
async def create_hook(hook_config: Dict[str, Any]):
    """Create a new hook configuration"""
    # TODO: Implement hook creation
    return {"message": "Hook created", "hook": hook_config}

@app.websocket("/api/monitoring/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)

            # Echo message to all connected clients (for now)
            for connection in active_connections:
                await connection.send_json({
                    "type": "message",
                    "data": message
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)

async def broadcast_update(update_type: str, data: Any):
    """Broadcast updates to all connected WebSocket clients"""
    message = {
        "type": update_type,
        "data": data
    }

    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            # Remove dead connections
            active_connections.remove(connection)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
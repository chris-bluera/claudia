# System Architecture Overview

## Overview

Claudia is a companion GUI for Claude Code that provides real-time visibility into Claude Code's state and activities. The system consists of three main components:

1. **Backend (Python/FastAPI)** - Monitors Claude Code files and provides REST/WebSocket APIs
2. **Frontend (Vue.js)** - Web interface for visualization and control
3. **Database (PostgreSQL + pgvector)** - Stores session data, configurations, and embeddings

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Claude Code    │────▶│  File System    │◀────│   Claudia       │
│   Sessions      │     │  (.claude/*)    │     │   Backend       │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                           │
                              │                           ▼
                        ┌─────▼────────┐         ┌─────────────────┐
                        │              │         │                 │
                        │    Hooks     │◀────────│   PostgreSQL    │
                        │              │         │   + pgvector    │
                        └──────────────┘         │                 │
                                                  └─────────────────┘
                                                           ▲
                                                           │
                                                  ┌─────────────────┐
                                                  │                 │
                                                  │   Vue.js        │
                                                  │   Frontend      │
                                                  │                 │
                                                  └─────────────────┘
```

## Key Design Decisions

### 1. File System Monitoring
- Uses Python's `watchdog` library to monitor Claude Code directories
- Watches: `~/.claude/projects/`, `~/.claude/settings.json`, `.claude/` in projects
- Non-intrusive read-only monitoring by default

### 2. Real-time Updates
- WebSocket connection between frontend and backend
- Events broadcast to all connected clients
- Supports multiple simultaneous Claude Code sessions

### 3. Hook Integration
- Generates hook scripts that communicate with Claudia backend
- Stores hook configurations in database
- Dynamically creates/updates `.claude/settings.json` entries

### 4. Data Persistence
- PostgreSQL for structured data (sessions, settings, tool executions)
- pgvector extension for semantic search capabilities (future)
- JSONB columns for flexible metadata storage

## Data Flow

1. **Claude Code → Claudia**
   - File watchers detect changes in Claude Code files
   - Transcript parser extracts conversation events
   - Settings aggregator computes active configuration

2. **Claudia → Claude Code**
   - Hook scripts execute during Claude Code events
   - Scripts send data to Claudia backend via HTTP
   - Backend can modify hook configurations

3. **Backend → Frontend**
   - WebSocket broadcasts real-time updates
   - REST API provides on-demand data queries
   - Frontend maintains synchronized state

## Security Considerations

- Local-only deployment (no cloud exposure)
- Read-only file system access by default
- Hook scripts require explicit user approval
- Database credentials in environment variables

## Scalability

- Designed for single-user/small team usage
- Can monitor multiple Claude Code sessions
- Database indexes optimized for common queries
- WebSocket connection pooling for multiple clients

## Future Enhancements

1. **Semantic Search** - Use pgvector for finding similar conversations
2. **Pattern Recognition** - Identify recurring workflows
3. **Context Injection** - Augment Claude Code prompts with relevant history
4. **Team Sharing** - Export/import configurations and patterns
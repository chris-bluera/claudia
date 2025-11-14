# Claudia - Claude Code Companion

Real-time monitoring and enhancement GUI for Claude Code. Provides visibility into Claude Code's state, settings, and activities with future capabilities for intelligent augmentation via pgvector.

## Quick Start

```bash
# Clone repository
git clone git@github.com:chris-bluera/claudia.git
cd claudia

# Install backend dependencies
cd backend && uv sync

# Install frontend dependencies
cd ../frontend && npm install

# Start PostgreSQL (requires Docker)
docker-compose up -d

# Run backend (separate terminal)
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Run frontend (separate terminal)
cd frontend && npm run dev

# Install Claudia monitoring hooks (one-time setup)
cd hooks && python3 install_hooks.py
```

Access:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/api/docs
- WebSocket: ws://localhost:8000/api/monitoring/ws

## Hook Installation

Claudia monitors Claude Code through hooks installed at the **user level** (`~/.claude/settings.json`). This architecture enables:

✅ **Universal Monitoring**: All Claude Code sessions across all projects are monitored
✅ **Multiple Sessions**: Concurrent sessions in different projects tracked independently
✅ **Dogfooding**: Claudia monitors itself when working on the Claudia codebase
✅ **No Duplicates**: Each session has a unique `session_id`, preventing double events

### Why Global Installation?

Claude Code's hook system is **additive** - hooks from multiple sources (managed, user, project, local) all execute in parallel. Installing hooks at the user level ensures:

- **Single Source**: Hooks defined once, apply everywhere
- **Session Isolation**: Each session tracked by unique ID
- **Multi-Project Support**: Work on multiple repos simultaneously without conflicts

### Important: Avoid Duplicate Installations

⚠️ **DO NOT** install hooks at multiple levels for the same project. This would cause duplicate events:

```
❌ BAD - Causes duplicates:
~/.claude/settings.json           ← Claudia hooks
yourproject/.claude/settings.json ← Same hooks again = 2x events!

✅ GOOD - Current setup:
~/.claude/settings.json           ← Claudia hooks (user level only)
yourproject/.claude/settings.json ← Your project-specific hooks (if any)
```

Claudia's hooks are specifically designed for user-level installation and will peacefully coexist with any project-specific hooks you may have.

## Architecture

- **Backend**: FastAPI with real-time file monitoring of Claude Code state
- **Frontend**: Vue 3 SPA with WebSocket updates
- **Database**: PostgreSQL + pgvector for conversation history and embeddings
- **Integration**: Hooks system for bidirectional Claude Code interaction

## Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- uv (Python package manager)
- Claude Code installation

### Project Structure

```
claudia/
├── backend/              # FastAPI backend
├── frontend/             # Vue.js frontend
├── database/             # SQL schemas and migrations
├── hooks/                # Claudia monitoring hooks
├── generated-hooks/      # User-created hooks (gitignored)
├── docker/               # Docker configurations
└── docs/                 # Technical documentation
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

Key variables:
- `CLAUDE_PROJECTS_PATH`: Path to Claude Code projects (~/.claude/projects)
- `DATABASE_URL`: PostgreSQL connection string
- `VITE_API_URL`: Backend API URL for frontend

## Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [Development Setup](docs/development/setup.md)
- [API Reference](docs/api/endpoints.md)
- [Hook System](docs/hooks/monitoring-hooks.md)

## Features

### Current
- Real-time Claude Code session monitoring
- Settings hierarchy visualization
- Tool execution tracking
- Conversation transcript parsing

### Planned
- Hook management UI
- Context augmentation via pgvector
- Workflow automation
- Pattern recognition

## Testing

```bash
# Backend tests
cd backend && uv run pytest

# Frontend tests
cd frontend && npm run test
```

## Contributing

See [docs/development/contributing.md](docs/development/contributing.md) for guidelines.

## License

MIT
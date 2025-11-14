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
```

Access:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/api/docs
- WebSocket: ws://localhost:8000/api/monitoring/ws

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
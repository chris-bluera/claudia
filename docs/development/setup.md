# Development Setup

## Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend build tools
- **Docker & Docker Compose** - PostgreSQL container
- **uv** - Python package manager ([install guide](https://github.com/astral-sh/uv))
- **Claude Code** - The tool we're monitoring

## Initial Setup

### 1. Clone Repository

```bash
git clone git@github.com:chris-bluera/claudia.git
cd claudia
```

### 2. VSCode Setup (Optional but Recommended)

```bash
# Copy VSCode settings template
cp .vscode/settings.json.example .vscode/settings.json

# This provides proper Python interpreter configuration
# You can add your personal preferences to settings.json
# (it's gitignored)
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
# Key variables to configure:
# - CLAUDE_PROJECTS_PATH (usually ~/.claude/projects)
# - DATABASE_URL (if changing from default)
```

### 3. Start PostgreSQL

```bash
# Start database container
docker-compose up -d

# Verify it's running
docker ps | grep claudia-postgres

# Check database logs if needed
docker-compose logs postgres
```

### 4. Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies (uv will create venv automatically)
uv sync

# Run database migrations (first time only)
uv run alembic upgrade head

# Start backend server
uv run uvicorn app.main:app --reload --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/api/docs
- WebSocket: ws://localhost:8000/api/monitoring/ws

### 5. Frontend Setup

In a new terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at:
- http://localhost:5173

## Verification

1. **Check Backend Health**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

2. **Check Database Connection**
   ```bash
   docker exec -it claudia-postgres psql -U claudia -d claudia -c "SELECT version();"
   ```

3. **Check Frontend**
   - Open http://localhost:5173
   - Should see Claudia dashboard

## Installing Monitoring Hooks

To enable Claude Code monitoring:

```bash
# Install Claudia's monitoring hooks
cd hooks
./install-hooks.sh

# This will:
# 1. Copy hook scripts to ~/.claude/hooks/
# 2. Update ~/.claude/settings.json with hook configurations
```

## Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm run test

# E2E tests (future)
npm run test:e2e
```

### Code Formatting

```bash
# Backend (using ruff)
cd backend
uv run ruff format .

# Frontend (using prettier)
cd frontend
npm run format
```

### Database Management

```bash
# Create new migration
cd backend
uv run alembic revision -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

### Database Connection Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Check PostgreSQL logs
docker-compose logs postgres
```

### Permission Errors

```bash
# Ensure Claude Code directories exist
mkdir -p ~/.claude/projects
mkdir -p ~/.claude/settings
```

### WebSocket Connection Failed

- Check CORS settings in backend
- Ensure frontend .env has correct `VITE_WS_URL`
- Check browser console for errors

## VSCode Setup (Optional)

Recommended extensions:
- Python (ms-python.python)
- Vue Language Features (Vue.volar)
- Prettier (esbenp.prettier-vscode)
- Docker (ms-azuretools.vscode-docker)

Settings (.vscode/settings.json):
```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```
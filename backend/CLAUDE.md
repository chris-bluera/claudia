# Claudia Backend - Development Context

Backend-specific conventions and patterns for the Claudia FastAPI application.

## Core Philosophy

**This app is expected to work.** If things aren't working as expected, that's an error condition.

**No fallbacks unless explicitly stated.** Don't create automatic fallback logic, polling fallbacks, or degraded modes. If something fails, it's an error—handle it as such.

## Error Handling Standards

### Principle: Errors are the default

**ERRORS (throw exceptions) - If things aren't working as expected:**
- Missing sessions, users, or required resources
- Data loss or corruption
- Validation failures
- External service failures
- Configuration errors
- Unexpected behavior of any kind
- **If functionality is impacted in ANY way, it's an ERROR**

**WARNINGS (log only) - Almost never used:**
- Only for things that don't impact functionality at all
- Examples: "Optional telemetry disabled", "Performance monitoring unavailable"
- If you're considering a warning, ask: "Does this impact functionality?" If yes → ERROR

**INFO/DEBUG - Normal logging:**
- INFO: Standard operation ("Session started", "Request processed")
- DEBUG: Detailed troubleshooting info

### Custom Exceptions

Defined in `app/exceptions.py`:

- `SessionNotFoundException` → HTTP 422 (session doesn't exist)
- `DirectoryNotFoundException` → Startup error (Claude Code not installed)
- `ServiceNotInitializedException` → HTTP 503 (service unavailable)

All return structured error responses with error codes and debugging context.

### Implementation Pattern

```python
# ✅ CORRECT - Error throws exception (DEFAULT)
if not session:
    logger.error(f"Session not found: {session_id}")
    raise SessionNotFoundException(session_id)

# ✅ CORRECT - Info for normal operation
logger.info(f"Session started: {session_id}")

# ❌ WRONG - Never return None for errors
if not session:
    logger.warning(f"Session not found: {session_id}")
    return None  # Silent data loss!

# ❌ WRONG - Using warning for functionality issue
try:
    data = json.loads(line)
except json.JSONDecodeError:
    logger.warning("Malformed JSON")  # This impacts functionality → ERROR
    continue
```

### HTTP Status Codes

- `200 OK` - Success
- `422 Unprocessable Entity` - Validation error (missing session, invalid input)
- `503 Service Unavailable` - Service not initialized
- `500 Internal Server Error` - Unexpected errors (should be rare with proper exception handling)

## Logging Standards

### Technology: Loguru

- **Never use `print()`** - all output goes through logger
- Logs written to `backend/logs/app.log` (10MB rotation, 30-day retention, zip compression)
- Error-only log: `backend/logs/errors.log` (50MB rotation, 60-day retention)
- All handlers use `enqueue=True` for async-safety in FastAPI

### Log Levels

- **DEBUG**: Detailed debugging info (file only)
- **INFO**: Normal operations, request/response logging
- **WARNING**: Almost never - only for non-impactful informational notices
- **ERROR**: Anything not working as expected (logged before throwing exception)

### Usage

```python
from loguru import logger

logger.debug("Detailed state: {state}")
logger.info("Session started: {session_id}")
logger.error("Session not found: {session_id}")  # Then throw exception
```

## Database Patterns

### Technology: PostgreSQL + async SQLAlchemy

### Key Patterns

**1. Always use async sessions:**
```python
async def get_session(self, db: AsyncSession, session_id: str) -> SessionModel:
    stmt = select(SessionModel).where(SessionModel.session_id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

**2. Use eager loading for relationships:**
```python
stmt = select(SessionModel).where(...).options(
    selectinload(SessionModel.tool_executions)
)
```

**3. Refresh after flush to prevent MissingGreenlet errors:**
```python
db.add(session)
await db.flush()
# Critical: Load relationships before to_dict() or any serialization
await db.refresh(session, ['tool_executions'])
```

**4. Never access lazy-loaded relationships in non-async context:**
- `to_dict()` methods must have all relationships eager-loaded
- Use `selectinload()` in queries or `refresh()` after creation
- Failing to do this causes `MissingGreenlet` errors

## API Endpoint Conventions

- RESTful design with proper HTTP status codes
- Use FastAPI dependency injection for database sessions
- Structured error responses with error codes
- Request logging middleware with request IDs and timing
- OpenAPI/Swagger documentation at `/api/docs`

**Example endpoint with error handling:**
```python
@app.post("/api/sessions/end")
async def session_end(req: SessionEndRequest, db: AsyncSession = Depends(get_db)):
    """Handle session end event from hooks"""
    if not session_tracker:
        raise HTTPException(status_code=503, detail="Session tracker not initialized")

    try:
        await session_tracker.end_session(db, req.session_id)
        return {"status": "ended", "session_id": req.session_id}
    except SessionNotFoundException:
        raise session_not_found_error(req.session_id)  # HTTP 422
```

## Technology Stack

### Core Technologies

- **FastAPI** - Async web framework with automatic OpenAPI docs
- **PostgreSQL** - Primary database with pgvector extension
- **SQLAlchemy 2.0** - Async ORM with declarative models
- **Loguru** - Structured logging with rotation and compression
- **Pydantic** - Data validation and settings management
- **Watchdog** - File system monitoring for Claude Code directories
- **asyncpg** - Async PostgreSQL driver

### Future Technologies

- **pgvector** - Vector similarity search for semantic search
- **OpenRouter** - Embeddings API (model: `openai/text-embedding-3-small`)
  - Base URL: `https://openrouter.ai/api/v1`
  - Allows flexibility to switch embedding providers

**For setup, running, and testing instructions, see:** @../README.md

**Logs location:** `backend/logs/app.log` and `backend/logs/errors.log`

## Common Issues & Solutions

### MissingGreenlet Error

**Symptom:** `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called`

**Cause:** Accessing lazy-loaded relationships in non-async context (usually in `to_dict()`)

**Fix:**
```python
# After creating/flushing:
await db.refresh(model, ['relationship_name'])

# Or in queries:
stmt = select(Model).options(selectinload(Model.relationship))
```

**Location:** Common in `session_tracker.py:start_session()` line 62

### HTTP 422: Session Not Found

**Symptom:** Tool execution hooks return 422 errors

**Cause:** Session creation failed, so session doesn't exist in database

**Debugging:**
1. Check `logs/app.log` for session start errors
2. Verify hooks are installed: `cat ~/.claude/settings.json`
3. Check database: `curl http://localhost:8000/api/sessions/active`

### Directory Not Found at Startup

**Symptom:** `ERROR: Required directory does not exist: /Users/.../.claude/projects`

**Cause:** Claude Code not installed or not initialized

**Fix:** Run `claude` CLI at least once to initialize directories

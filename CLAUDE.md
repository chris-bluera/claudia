# Claudia Development Context

This file provides context for Claude Code when working on the Claudia project.

## Project Overview

Claudia is a companion GUI for Claude Code that provides:
- Real-time monitoring of Claude Code sessions
- Settings hierarchy visualization
- Tool execution tracking
- Future: pgvector-powered semantic search and context augmentation

## Key Development Considerations

### Naming Conventions

To avoid confusion with Claude Code's own configuration files when building this Claude Code companion app:
- **Our config**: `claudia-*` prefix (e.g., `claudia-config.json`)
- **Our hooks**: Located in `hooks/` directory, prefixed with descriptive names
- **Generated hooks**: Stored in `generated-hooks/` (gitignored)
- **Our docs**: In `docs/` directory
- **Claude Code reference docs**: In `reference/claude-code/`

### Directory Structure

```
claudia/                    # Our project root
├── .claude/               # Claude Code's config (gitignored, when developing)
├── backend/               # FastAPI backend
├── frontend/              # Vue.js frontend
├── hooks/                 # Our monitoring hooks
├── generated-hooks/       # User-created hooks (gitignored)
└── reference/            # Claude Code reference docs
```

### Current Implementation Status

✅ **Completed - MVP Ready:**
- ✅ Backend services (FileMonitor, SettingsAggregator, SessionTracker)
- ✅ FastAPI with WebSocket broadcasting
- ✅ Vue.js frontend with design tokens (no hardcoded styles)
- ✅ PostgreSQL + pgvector schema
- ✅ Monitoring hooks (Python, cross-platform)
- ✅ TypeScript types with `unknown` instead of `any`
- ✅ Dashboard with SessionsPanel, ActivityFeed, SettingsPanel
- ✅ Pinia store with WebSocket integration
- ✅ Hooks installed at user level (`~/.claude/settings.json`)

🚀 **Ready for Dogfooding:**
- Backend monitoring `~/.claude/projects` for all sessions
- Frontend dashboard showing real-time updates
- Hooks capturing session events, tool usage, settings changes

### Hook Installation Architecture

**IMPORTANT:** Hooks are installed **globally at user level** (`~/.claude/settings.json`), NOT at project level.

**Why Global?**
- Claude Code's hook system is **additive** - hooks from all levels (managed/user/project/local) execute in parallel
- Installing at user level monitors ALL Claude Code sessions across ALL projects
- Each session has unique `session_id` → no duplicate events
- Supports multiple concurrent sessions in different projects
- Works when Claudia monitors itself (dogfooding)

**Avoid Duplicates:**
- ✅ User level only: `~/.claude/settings.json` (current approach)
- ❌ Never install at project level: `.claude/settings.json` (would cause duplicates)
- ❌ Never install at both levels (2x events for every action!)

The `.claude/settings.local.json` in this repo contains only permissions, NOT hooks.

### Running the Stack

```bash
# Terminal 1: Database
docker-compose up -d

# Terminal 2: Backend
cd backend && uv run uvicorn app.main:app --reload

# Terminal 3: Frontend
cd frontend && npm run dev

# One-time: Install hooks (if not already done)
cd hooks && python3 install_hooks.py
```

### Testing Integration

Start a Claude Code session in this project:
```bash
claude "Help me enhance Claudia"
```

Monitor the backend logs to see hook events coming through.

### Future Enhancements

1. **Semantic Search**: Index conversations with pgvector (using OpenRouter for embeddings)
2. **Pattern Recognition**: Identify recurring development workflows
3. **Context Injection**: Augment prompts with relevant history
4. **Team Sharing**: Export/import successful patterns

### Technology Choices

- **Embeddings**: Using OpenRouter API for embeddings (supports multiple providers)
  - Model: `openai/text-embedding-3-small` (via OpenRouter)
  - Base URL: `https://openrouter.ai/api/v1`
  - Allows flexibility to switch providers without code changes

- **Settings Monitoring**: Two-tier approach for accuracy
  - File-based settings from Claude Code's configuration hierarchy
  - Runtime configuration captured via hooks (includes CLI overrides)
  - Merged to show actual effective configuration per session
  - Handles cases where CLI args override file settings (e.g., `claude --model opus`)

### Development Tips

- Keep backend endpoints RESTful and well-documented (Swagger)
- Use WebSocket for real-time updates only (not for commands)
- Maintain clear separation between monitoring (read) and control (write)
- Test hooks independently before integration
- Use CSS variables consistently for theming
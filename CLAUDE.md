# Claudia Development Context

> **About CLAUDE.md files:** See @CLAUDE_ABOUT.md for explanation of what these files are and how they're maintained.

---

## Project Overview

Claudia is a companion GUI for Claude Code that provides:
- Real-time monitoring of Claude Code sessions
- Settings hierarchy visualization
- Tool execution tracking
- Future: pgvector-powered semantic search and context augmentation

**For setup and running instructions, see:** @README.md

## Core Development Principles

These principles apply to **the entire codebase** (frontend and backend):

### 1. This App Is Expected to Work

**Errors are the default response to unexpected conditions:**
- If things aren't working as expected → that's an ERROR condition
- Warnings are almost never used (only for things that don't impact functionality)
- Backend: Throw exceptions for errors
- Frontend: Show error states clearly (more lenient for UX, but still errors)

### 2. No Fallbacks Unless Explicitly Stated

**Critical: Claude models tend to add fallback code automatically. Resist this.**

- ❌ Don't create automatic fallback logic
- ❌ Don't add polling fallbacks for WebSocket failures
- ❌ Don't add degraded modes automatically
- ✅ If something fails, show error state clearly
- ✅ Let user decide whether to retry

**Examples of what NOT to do:**
- Auto-switching to polling when WebSocket fails
- Silent fallback to alternative implementations
- Degraded modes that hide failures from user

### 3. No Hardcoded Styles

- Frontend: All styles use design tokens from `frontend/src/assets/tokens.css`
- Never hardcode colors, spacing, fonts, shadows, etc.

### 4. TypeScript Type Safety

- Use `unknown` instead of `any` for better type safety
- Properly type all interfaces and API responses

## Key Development Considerations

> **Note to Claude Code:** When adding implementation details, put backend-specific items in `backend/CLAUDE.md` and frontend-specific items in `frontend/CLAUDE.md`. Keep project-level status and cross-cutting concerns here.

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
- `session_id` is stable per conversation (persists across `--continue`) → hooks fire once per event
- Supports multiple concurrent sessions/conversations in different projects
- Works when Claudia monitors itself (dogfooding)

**Avoid Duplicates:**
- ✅ User level only: `~/.claude/settings.json` (current approach)
- ❌ Never install at project level: `.claude/settings.json` (would cause duplicates)
- ❌ Never install at both levels (2x events for every action!)

The `.claude/settings.local.json` in this repo contains only permissions, NOT hooks.

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
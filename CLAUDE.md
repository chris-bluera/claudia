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

✅ **Completed:**
- Project structure and basic setup
- FastAPI backend with WebSocket support
- Vue.js frontend with design tokens
- PostgreSQL + pgvector schema
- Monitoring hooks (Python, cross-platform)
- Developer documentation

🚧 **Next Steps:**
1. Implement file watchers in backend
2. Create frontend dashboard components
3. Wire up WebSocket real-time updates
4. Test hook integration with actual Claude Code

### Running the Stack

```bash
# Terminal 1: Database
docker-compose up -d

# Terminal 2: Backend
cd backend && uv run uvicorn app.main:app --reload

# Terminal 3: Frontend
cd frontend && npm run dev

# Terminal 4: Install hooks
cd hooks && python install_hooks.py
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

### Development Tips

- Keep backend endpoints RESTful and well-documented (Swagger)
- Use WebSocket for real-time updates only (not for commands)
- Maintain clear separation between monitoring (read) and control (write)
- Test hooks independently before integration
- Use CSS variables consistently for theming
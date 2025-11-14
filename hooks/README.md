# Claudia Monitoring Hooks

These Python scripts integrate with Claude Code's hook system to monitor activities and state.

## Hook Scripts

- **`monitor_tool_use.py`** - Tracks tool executions (PreToolUse/PostToolUse events)
- **`capture_session.py`** - Monitors session lifecycle (SessionStart/SessionEnd events)
- **`settings_watcher.py`** - Captures settings snapshots on various events

## Installation

Run the installation script to set up hooks:

```bash
python3 install_hooks.py
```

This will:
1. Check if Claudia backend is running
2. Install hooks at **user level** (`~/.claude/settings.json`)
3. Make hook scripts executable (Unix systems)
4. Preserve any existing hooks in your settings

### Installation Architecture

Hooks are installed **globally at the user level** for these reasons:

**✅ Correct Approach (Current):**
- Hooks in `~/.claude/settings.json` → monitors ALL Claude Code sessions
- Unique `session_id` for each session → no duplicate events
- Supports multiple concurrent sessions across different projects
- Works seamlessly when Claudia monitors itself (dogfooding)

**❌ Incorrect Approach (Avoided):**
- Installing hooks at project level would require per-project setup
- Multiple installations at different levels cause duplicate events
- No benefit to project-specific hook installation for monitoring

### Multiple Concurrent Sessions

Claudia is designed to handle multiple Claude Code sessions simultaneously:

```
Session A (project-foo) → Unique session_id=abc123
Session B (project-bar) → Unique session_id=def456
Session C (claudia)     → Unique session_id=ghi789
```

All sessions are tracked independently in the dashboard:
- **Sessions Panel**: Shows all active sessions with their own durations and tool counts
- **Activity Feed**: Streams events from all sessions with session identification
- **Settings Panel**: Can display settings for any active session

Claude Code's hook system is **additive** - hooks from user, project, and local levels all execute in parallel. By keeping Claudia hooks at user level only, we ensure consistent monitoring without duplication.

## Configuration

Hooks respect these environment variables:

- `CLAUDIA_API_URL` - Backend API URL (default: http://localhost:8000)
- `CLAUDIA_MONITORING` - Enable/disable monitoring (default: true)

## Testing

Test individual hooks:

```bash
# Test with sample input
echo '{"session_id": "test", "event": {"type": "SessionStart"}}' | python3 capture_session.py
```

## Troubleshooting

### Hooks not firing
- Check Claude Code settings: `cat ~/.claude/settings.json`
- Verify hook permissions: `ls -la *.py`
- Check Claudia backend is running: `curl http://localhost:8000/health`

### Errors in hook execution
- Check Claude Code session logs
- Run hook manually with test data
- Ensure Python 3 is available in PATH

## Cross-Platform Compatibility

All hooks are written in Python for Windows/macOS/Linux compatibility.
No shell scripts or OS-specific commands are used.
# Claudia Monitoring Hooks

These Python scripts integrate with Claude Code's hook system to monitor activities and state.

## Hook Scripts

- **`monitor_tool_use.py`** - Tracks tool executions (PreToolUse/PostToolUse events)
- **`capture_session.py`** - Monitors session lifecycle (SessionStart/SessionEnd events)
- **`settings_watcher.py`** - Captures settings snapshots on various events

## Installation

Run the installation script to set up hooks:

```bash
python install_hooks.py
```

This will:
1. Make hook scripts executable
2. Update your Claude Code settings to register the hooks
3. Verify the Claudia backend is accessible

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
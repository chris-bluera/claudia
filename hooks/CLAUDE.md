# Claudia Monitoring Hooks - Development Context

> **About CLAUDE.md files:** See @CLAUDE_ABOUT.md for explanation of what these files are and how they're maintained.

Development context for Claude Code when working with Claudia's monitoring hook system.

## Overview

These Python scripts integrate with Claude Code's hook system to monitor activities and state:

- **`monitor_tool_use.py`** - Tracks tool executions (PreToolUse/PostToolUse events)
- **`capture_session.py`** - Monitors session lifecycle (SessionStart/SessionEnd events)
- **`capture_prompts.py`** - Captures user prompts (UserPromptSubmit event)
- **`capture_assistant_messages.py`** - Captures assistant responses (Stop event)
- **`settings_watcher.py`** - Captures settings snapshots on various events

## CRITICAL: Installing and Maintaining Hooks

### When Hooks Need Reinstalling

**⚠️ ALWAYS run installer after:**
- Modifying `install_hooks.py` (changes to hook registration)
- Adding new hook scripts to be registered
- Changing which events hooks respond to

**✅ NO reinstall needed after:**
- Editing existing hook script logic (e.g., fixing bug in `capture_prompts.py`)
- Changes to hook implementation that don't affect registration

### Claude Code Restart Requirement

**🔴 CRITICAL:** Claude Code loads hooks **at startup only**.

After running `install_hooks.py`, you **MUST** restart Claude Code:

```bash
# If resuming existing work (PREFERRED):
claude --continue

# If starting fresh:
claude
```

**Why?** Claude Code captures a snapshot of hooks at startup for security (prevents malicious hook injection into running sessions). Changes to `~/.claude/settings.json` don't take effect until a new session starts.

### Installation Workflow

When you modify `install_hooks.py` or add new hooks:

1. **Run the installer:**
   ```bash
   cd hooks
   python3 install_hooks.py
   ```

2. **Inform the user:**
   - Claude Code must be restarted for hooks to take effect
   - Use `claude --continue` to resume current work
   - Wait for confirmation that restart is complete

3. **Verify installation:**
   ```bash
   # Check hooks are registered
   cat ~/.claude/settings.json | grep -A5 "UserPromptSubmit"

   # After restart, check database for captured data
   curl http://localhost:8000/api/monitoring/stats
   ```

### Real Example: Phase 1 Installation Mistake

**What happened:**
- Implemented Phase 1 conversation capture (prompts + messages)
- Created `capture_prompts.py` and `capture_assistant_messages.py`
- Updated `install_hooks.py` to register new hooks
- ❌ **Forgot to run the installer**
- Result: Database showed 0 prompts, 0 messages despite code being correct

**Discovery:**
```bash
$ cat ~/.claude/settings.json | grep -A5 "UserPromptSubmit"
# Found: Only settings_watcher.py registered
# Missing: capture_prompts.py

$ cat ~/.claude/settings.json | grep "Stop"
# Missing: Entire "Stop" event registration for capture_assistant_messages.py
```

**Fix:**
```bash
cd hooks
python3 install_hooks.py
# Then: claude --continue
# Verify: Database started capturing prompts and messages
```

**Lesson:** After creating hooks and updating `install_hooks.py`, **ALWAYS** run the installer and restart Claude Code.

## Installation Architecture

### User-Level Installation (Current Design)

Hooks are installed **globally at the user level** (`~/.claude/settings.json`) for these reasons:

**✅ Correct Approach:**
- Hooks monitor ALL Claude Code sessions across all projects
- Unique `session_id` for each session prevents duplicate events
- Supports multiple concurrent sessions in different projects
- Works seamlessly when Claudia monitors itself (dogfooding)

**❌ Incorrect Approach (Avoided):**
- Installing hooks at project level requires per-project setup
- Multiple installations at different levels cause duplicate events
- No benefit to project-specific hook installation for monitoring

### Multiple Concurrent Sessions

Claudia handles multiple Claude Code sessions simultaneously:

```
Session A (project-foo) → session_id=abc123
Session B (project-bar) → session_id=def456
Session C (claudia)     → session_id=ghi789
```

All sessions tracked independently:
- **Sessions Panel**: Shows all active sessions with durations and tool counts
- **Activity Feed**: Streams events from all sessions with session identification
- **Settings Panel**: Can display settings for any active session

Claude Code's hook system is **additive** - hooks from user, project, and local levels all execute in parallel. By keeping Claudia hooks at user level only, we ensure consistent monitoring without duplication.

## Configuration

Hooks respect these environment variables:

- `CLAUDIA_API_URL` - Backend API URL (default: http://localhost:8000)
- `CLAUDIA_MONITORING` - Enable/disable monitoring (default: true)

## Testing Hook Scripts

Test individual hooks manually:

```bash
# Test session capture
echo '{"session_id": "test", "event": {"type": "SessionStart"}}' | python3 capture_session.py

# Test prompt capture
echo '{"session_id": "test", "prompt_text": "Hello Claude"}' | python3 capture_prompts.py
```

## Troubleshooting

### Hooks not firing

1. Check hooks are registered:
   ```bash
   cat ~/.claude/settings.json | grep -A5 "SessionStart"
   ```

2. Verify hook scripts are executable:
   ```bash
   ls -la hooks/*.py
   ```

3. Check Claudia backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

4. **Did you restart Claude Code?** Hooks load at startup only.

### Errors in hook execution

- Check Claude Code session logs for hook errors
- Run hook manually with test data (see Testing section above)
- Ensure Python 3 is available in PATH
- Check backend logs: `backend/logs/app.log`

### Data not appearing in database

1. Verify hooks are installed: `cat ~/.claude/settings.json`
2. Verify Claude Code was restarted after installation
3. Check database directly:
   ```bash
   curl http://localhost:8000/api/monitoring/stats
   curl http://localhost:8000/api/sessions/active
   ```
4. Check backend logs for errors: `tail -f backend/logs/app.log`

## Cross-Platform Compatibility

All hooks are written in Python for Windows/macOS/Linux compatibility.
No shell scripts or OS-specific commands are used.

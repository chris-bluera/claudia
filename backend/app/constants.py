"""
Constants for Claudia backend
"""
import sys
from pathlib import Path

# =====================================
# Claude Code Paths
# =====================================

def get_managed_settings_path() -> Path:
    """Get platform-specific managed settings path"""
    if sys.platform == 'darwin':  # macOS
        return Path('/Library/Application Support/ClaudeCode/managed-settings.json')
    elif sys.platform == 'win32':  # Windows
        return Path('C:/ProgramData/ClaudeCode/managed-settings.json')
    else:  # Linux/WSL
        return Path('/etc/claude-code/managed-settings.json')


# Claude Code directory structure
CLAUDE_SETTINGS_FILENAME = 'settings.json'
CLAUDE_LOCAL_SETTINGS_FILENAME = 'settings.local.json'
CLAUDE_DIR_NAME = '.claude'
CLAUDE_PROJECTS_DIR_NAME = 'projects'

# =====================================
# File Patterns
# =====================================

TRANSCRIPT_FILE_EXTENSION = '.jsonl'
SETTINGS_FILE_PATTERN = '*settings.json'

# =====================================
# Event Types
# =====================================

# WebSocket event types
EVENT_SESSION_START = 'session_start'
EVENT_SESSION_END = 'session_end'
EVENT_TOOL_EXECUTION = 'tool_execution'
EVENT_USER_PROMPT = 'user_prompt'
EVENT_SETTINGS_UPDATE = 'settings_update'

# Claude Code transcript event types
TRANSCRIPT_EVENT_TOOL_USE = 'tool_use'
TRANSCRIPT_EVENT_USER_MESSAGE = 'user_message'
TRANSCRIPT_EVENT_ASSISTANT_MESSAGE = 'assistant_message'

# =====================================
# Settings Hierarchy Levels
# =====================================

SETTINGS_LEVEL_MANAGED = 'managed'
SETTINGS_LEVEL_USER = 'user'
SETTINGS_LEVEL_PROJECT = 'project'
SETTINGS_LEVEL_LOCAL = 'local'

# Settings precedence (lowest to highest)
SETTINGS_PRECEDENCE = [
    SETTINGS_LEVEL_MANAGED,
    SETTINGS_LEVEL_USER,
    SETTINGS_LEVEL_PROJECT,
    SETTINGS_LEVEL_LOCAL
]

# =====================================
# Database
# =====================================

# Activity feed ring buffer size
MAX_ACTIVITY_EVENTS = 100

# =====================================
# WebSocket
# =====================================

WEBSOCKET_RECONNECT_DELAY_MS = 3000
WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 10

# =====================================
# Monitoring
# =====================================

# File watch interval (seconds)
FILE_WATCH_POLL_INTERVAL = 1

# Session timeout (minutes)
SESSION_TIMEOUT_MINUTES = 60

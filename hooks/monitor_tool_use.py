#!/usr/bin/env python3
"""
Claudia monitoring hook for tracking Claude Code tool usage.
Sends tool execution data to Claudia backend.

Based on official Claude Code hook input structure from:
- reference/claude-code/claude-code-official-repo/examples/hooks/bash_command_validator_example.py
- reference/claude-code/claude-code-docs/06-reference/05-hooks-reference.md
"""
import json
import sys
import os
from datetime import datetime, timezone
import urllib.request
import urllib.error

# Configuration (can be overridden by environment variables)
CLAUDIA_API_URL = os.getenv('CLAUDIA_API_URL', 'http://localhost:8000')
CLAUDIA_ENABLED = os.getenv('CLAUDIA_MONITORING', 'true').lower() == 'true'

def send_to_claudia(endpoint: str, data: dict[str, object]) -> bool:
    """Send data to Claudia backend API"""
    if not CLAUDIA_ENABLED:
        return True

    try:
        url = f"{CLAUDIA_API_URL}/api/{endpoint}"
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        # Log error but don't block Claude Code
        sys.stderr.write(f"Claudia monitoring error: {e}\n")
        return False

def main():
    """Process PreToolUse/PostToolUse hook events"""
    try:
        # Read input from Claude Code
        # Structure: { session_id, hook_event_name, tool_name, tool_input, cwd, ... }
        raw_input = sys.stdin.read()
        input_data: dict[str, object] = json.loads(raw_input)

        # Extract hook input fields (per official Claude Code hook specification)
        hook_event_name = input_data.get('hook_event_name', '')  # 'PreToolUse' or 'PostToolUse'
        tool_name = input_data.get('tool_name', '')              # e.g., 'Bash', 'Write', 'Read'
        tool_input = input_data.get('tool_input', {})            # Tool-specific parameters dict
        session_id = input_data.get('session_id', '')
        cwd = input_data.get('cwd', '')

        # Ensure we have required fields
        if not isinstance(hook_event_name, str) or not isinstance(session_id, str):
            sys.exit(0)

        # Prepare monitoring data
        monitoring_data: dict[str, object] = {
            'session_id': session_id,
            'event_type': hook_event_name,
            'tool_name': tool_name,
            'parameters': tool_input,
            'working_directory': cwd,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        # Send to Claudia backend
        send_to_claudia('monitoring/tool-use', monitoring_data)

        # Always exit successfully to avoid blocking Claude Code
        sys.exit(0)

    except Exception as e:
        # Log error but don't block
        sys.stderr.write(f"Hook error: {e}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()

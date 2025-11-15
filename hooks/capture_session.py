#!/usr/bin/env python3
"""
Claudia monitoring hook for tracking Claude Code session lifecycle.
Captures session start/end events.

Based on official Claude Code hook input structure from:
- reference/claude-code/claude-code-docs/06-reference/05-hooks-reference.md
"""
import json
import sys
import os
from datetime import datetime, timezone
import urllib.request

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
        sys.stderr.write(f"Claudia monitoring error: {e}\n")
        return False

def main():
    """Process SessionStart/SessionEnd events"""
    try:
        # Read input from Claude Code
        # Structure: { session_id, hook_event_name, transcript_path, cwd, permission_mode, ... }
        raw_input = sys.stdin.read()
        input_data: dict[str, object] = json.loads(raw_input)

        # Extract session information (per official Claude Code hook specification)
        hook_event_name = input_data.get('hook_event_name', '')  # 'SessionStart' or 'SessionEnd'
        session_id = input_data.get('session_id', '')
        cwd = input_data.get('cwd', '')
        transcript_path = input_data.get('transcript_path', '')
        permission_mode = input_data.get('permission_mode', '')

        # Extract event-specific fields
        source = input_data.get('source', '')  # SessionStart: startup|resume|clear|compact
        reason = input_data.get('reason', '')  # SessionEnd: exit|logout|clear|prompt_input_exit|other

        # Ensure we have required fields with proper types
        if not isinstance(hook_event_name, str) or not isinstance(session_id, str):
            sys.exit(0)
        if not isinstance(cwd, str) or not isinstance(transcript_path, str):
            sys.exit(0)
        if not isinstance(permission_mode, str):
            sys.exit(0)

        # Determine project info from path
        project_path = cwd
        project_name = os.path.basename(project_path)

        # Capture runtime configuration
        # This includes settings we can detect from the runtime environment
        env_vars: dict[str, str] = {}
        if claude_remote := os.getenv('CLAUDE_CODE_REMOTE'):
            env_vars['CLAUDE_CODE_REMOTE'] = claude_remote
        if claude_project := os.getenv('CLAUDE_PROJECT_DIR'):
            env_vars['CLAUDE_PROJECT_DIR'] = claude_project

        runtime_config: dict[str, object] = {
            'permission_mode': permission_mode,
            'env': env_vars
        }

        # Prepare base session data
        session_data: dict[str, object] = {
            'session_id': session_id,
            'event_type': hook_event_name,
            'project_path': project_path,
            'project_name': project_name,
            'transcript_path': transcript_path,
            'permission_mode': permission_mode,
            'runtime_config': runtime_config,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        # Send appropriate event with event-specific fields
        if hook_event_name == 'SessionStart':
            # Add source field for SessionStart
            if source:
                session_data['source'] = source
            send_to_claudia('sessions/start', session_data)
        elif hook_event_name == 'SessionEnd':
            # Add reason field and updated session data for SessionEnd
            if reason:
                session_data['reason'] = reason
            # Include session_metadata (raw hook data for full capture)
            session_data['session_metadata'] = runtime_config
            send_to_claudia('sessions/end', session_data)

        # Always exit successfully
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Hook error: {e}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Claudia monitoring hook for tracking Claude Code session lifecycle.
Captures session start/end events.
"""
import json
import sys
import os
from datetime import datetime, timezone
import urllib.request

CLAUDIA_API_URL = os.getenv('CLAUDIA_API_URL', 'http://localhost:8000')
CLAUDIA_ENABLED = os.getenv('CLAUDIA_MONITORING', 'true').lower() == 'true'

def send_to_claudia(endpoint: str, data: dict) -> bool:
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
        input_data = json.loads(sys.stdin.read())

        # Extract session information
        event_type = input_data.get('event', {}).get('type', '')
        session_id = input_data.get('session_id', '')
        cwd = input_data.get('cwd', '')
        transcript_path = input_data.get('transcript_path', '')
        permission_mode = input_data.get('permission_mode', '')

        # Determine project info from path
        project_path = cwd
        project_name = os.path.basename(project_path)

        # Capture runtime configuration
        # This includes settings we can detect from the runtime environment
        runtime_config = {
            'permission_mode': permission_mode,
            # Check for Claude Code environment variables
            'env': {
                'CLAUDE_CODE_REMOTE': os.getenv('CLAUDE_CODE_REMOTE'),
                'CLAUDE_PROJECT_DIR': os.getenv('CLAUDE_PROJECT_DIR'),
                # Add other known Claude Code env vars
            }
        }

        # Remove None values
        runtime_config['env'] = {k: v for k, v in runtime_config['env'].items() if v is not None}

        # Prepare session data
        session_data = {
            'session_id': session_id,
            'event_type': event_type,
            'project_path': project_path,
            'project_name': project_name,
            'transcript_path': transcript_path,
            'permission_mode': permission_mode,
            'runtime_config': runtime_config,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        # Send appropriate event
        if event_type == 'SessionStart':
            send_to_claudia('sessions/start', session_data)
        elif event_type == 'SessionEnd':
            send_to_claudia('sessions/end', session_data)

        # Always exit successfully
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Hook error: {e}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Claudia monitoring hook for tracking Claude Code tool usage.
Sends tool execution data to Claudia backend.
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
        # Log error but don't block Claude Code
        sys.stderr.write(f"Claudia monitoring error: {e}\n")
        return False

def main():
    """Process PreToolUse/PostToolUse hook events"""
    try:
        # Read input from Claude Code
        input_data = json.loads(sys.stdin.read())

        # Extract relevant information
        event_type = input_data.get('event', {}).get('type', '')
        tool_name = input_data.get('event', {}).get('toolName', '')
        parameters = input_data.get('event', {}).get('parameters', {})
        session_id = input_data.get('session_id', '')
        cwd = input_data.get('cwd', '')

        # Prepare monitoring data
        monitoring_data = {
            'session_id': session_id,
            'event_type': event_type,
            'tool_name': tool_name,
            'parameters': parameters,
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
#!/usr/bin/env python3
"""
Claudia monitoring hook for capturing user prompts.
Fires on UserPromptSubmit event (when user submits a prompt).

Captures the full prompt text and sends it to Claudia backend
for storage and future embedding/vectorization.
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
    """Process UserPromptSubmit event"""
    try:
        # Read input from Claude Code
        raw_input = sys.stdin.read()
        input_data: dict[str, object] = json.loads(raw_input)

        # Extract UserPromptSubmit event fields
        session_id = input_data.get('session_id', '')
        prompt = input_data.get('prompt', '')

        # Type validation
        if not isinstance(session_id, str) or not isinstance(prompt, str):
            sys.exit(0)

        # Skip empty prompts
        if not prompt.strip():
            sys.exit(0)

        # Send to Claudia backend
        prompt_data: dict[str, object] = {
            'session_id': session_id,
            'prompt_text': prompt,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        send_to_claudia('prompts/capture', prompt_data)

        # Always exit successfully to avoid blocking Claude Code
        # Note: Returning 0 allows the prompt to proceed normally
        # Exit code 2 would block the prompt
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Hook error: {e}\n")
        sys.exit(0)


if __name__ == '__main__':
    main()

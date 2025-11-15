#!/usr/bin/env python3
"""
Claudia monitoring hook for capturing Claude Code assistant messages.
Fires on Stop event (when Claude finishes responding).

Extracts the last assistant message from the transcript and sends it
to Claudia backend for storage and future embedding/vectorization.
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


def extract_last_assistant_message(transcript_path: str) -> tuple[str, int]:
    """
    Extract the most recent assistant message from transcript JSONL.

    Returns:
        tuple: (message_content, conversation_turn)
    """
    try:
        with open(transcript_path, 'r') as f:
            lines = f.readlines()

        # Count conversation turns (user prompts)
        conversation_turn = 0
        for line in lines:
            try:
                entry = json.loads(line)
                if entry.get('type') == 'user_message':
                    conversation_turn += 1
            except json.JSONDecodeError:
                continue

        # Find last assistant message (iterate backwards)
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get('type') == 'assistant_message':
                    content = entry.get('content', '')
                    if isinstance(content, list):
                        # Content may be array of content blocks
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                text_parts.append(block.get('text', ''))
                        return '\n'.join(text_parts), conversation_turn
                    elif isinstance(content, str):
                        return content, conversation_turn
            except json.JSONDecodeError:
                continue

        return '', conversation_turn

    except FileNotFoundError:
        sys.stderr.write(f"Transcript not found: {transcript_path}\n")
        return '', 0
    except Exception as e:
        sys.stderr.write(f"Error reading transcript: {e}\n")
        return '', 0


def main():
    """Process Stop event"""
    try:
        # Read input from Claude Code
        raw_input = sys.stdin.read()
        input_data: dict[str, object] = json.loads(raw_input)

        # Extract Stop event fields
        session_id = input_data.get('session_id', '')
        transcript_path = input_data.get('transcript_path', '')
        stop_hook_active = input_data.get('stop_hook_active', False)

        # Type validation
        if not isinstance(session_id, str) or not isinstance(transcript_path, str):
            sys.exit(0)
        if not isinstance(stop_hook_active, bool):
            sys.exit(0)

        # Skip if stop hook already running (prevents infinite loops)
        if stop_hook_active:
            sys.exit(0)

        # Extract assistant's message from transcript
        message_text, conversation_turn = extract_last_assistant_message(transcript_path)

        if not message_text:
            # No message found, exit successfully
            sys.exit(0)

        # Send to Claudia backend
        message_data: dict[str, object] = {
            'session_id': session_id,
            'message_text': message_text,
            'conversation_turn': conversation_turn,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        send_to_claudia('messages/capture', message_data)

        # Always exit successfully to avoid blocking Claude Code
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Hook error: {e}\n")
        sys.exit(0)


if __name__ == '__main__':
    main()

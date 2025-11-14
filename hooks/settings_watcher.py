#!/usr/bin/env python3
"""
Claudia monitoring hook for capturing Claude Code settings snapshots.
Works cross-platform (Windows, macOS, Linux).
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path
import urllib.request

CLAUDIA_API_URL = os.getenv('CLAUDIA_API_URL', 'http://localhost:8000')
CLAUDIA_ENABLED = os.getenv('CLAUDIA_MONITORING', 'true').lower() == 'true'

def read_json_file(filepath: Path) -> dict:
    """Safely read and parse a JSON file"""
    try:
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error reading {filepath}: {e}\n")
    return {}

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
    """Capture and send Claude Code settings snapshot"""
    try:
        # Read input from Claude Code
        input_data = json.loads(sys.stdin.read())

        session_id = input_data.get('session_id', '')
        cwd = Path(input_data.get('cwd', os.getcwd()))

        # Paths to check for settings
        home = Path.home()
        user_settings_path = home / '.claude' / 'settings.json'
        project_settings_path = cwd / '.claude' / 'settings.json'
        local_settings_path = cwd / '.claude' / 'settings.local.json'

        # Also check for managed settings (enterprise)
        if sys.platform == 'darwin':  # macOS
            managed_path = Path('/Library/Application Support/ClaudeCode/managed-settings.json')
        elif sys.platform == 'win32':  # Windows
            managed_path = Path('C:/ProgramData/ClaudeCode/managed-settings.json')
        else:  # Linux/WSL
            managed_path = Path('/etc/claude-code/managed-settings.json')

        # Collect all settings
        settings_snapshot = {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'settings': {
                'user': read_json_file(user_settings_path),
                'project': read_json_file(project_settings_path),
                'local': read_json_file(local_settings_path),
                'managed': read_json_file(managed_path) if managed_path.exists() else {}
            },
            'paths': {
                'user': str(user_settings_path) if user_settings_path.exists() else None,
                'project': str(project_settings_path) if project_settings_path.exists() else None,
                'local': str(local_settings_path) if local_settings_path.exists() else None,
                'managed': str(managed_path) if managed_path.exists() else None
            }
        }

        # Send to Claudia
        send_to_claudia('monitoring/settings-snapshot', settings_snapshot)

        # Always exit successfully
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Hook error: {e}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
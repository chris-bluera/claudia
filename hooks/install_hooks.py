#!/usr/bin/env python3
"""
Install Claudia monitoring hooks into Claude Code settings.
Handles both new installations and updates to existing settings.
"""
import json
import sys
import os
from pathlib import Path
import urllib.request
import urllib.error

def check_backend_health():
    """Check if Claudia backend is running"""
    api_url = os.getenv('CLAUDIA_API_URL', 'http://localhost:8000')
    try:
        with urllib.request.urlopen(f"{api_url}/health", timeout=5) as response:
            return response.status == 200
    except:
        return False

def get_hook_config():
    """Generate hook configuration for Claude Code settings"""
    hooks_dir = Path(__file__).parent.absolute()

    return {
        "PreToolUse": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python3 {hooks_dir}/monitor_tool_use.py",
                        "timeout": 5
                    }
                ]
            }
        ],
        "PostToolUse": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python3 {hooks_dir}/monitor_tool_use.py",
                        "timeout": 5
                    }
                ]
            }
        ],
        "SessionStart": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python3 {hooks_dir}/capture_session.py",
                        "timeout": 5
                    },
                    {
                        "type": "command",
                        "command": f"python3 {hooks_dir}/settings_watcher.py",
                        "timeout": 5
                    }
                ]
            }
        ],
        "SessionEnd": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python3 {hooks_dir}/capture_session.py",
                        "timeout": 5
                    }
                ]
            }
        ],
        "UserPromptSubmit": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python3 {hooks_dir}/settings_watcher.py",
                        "timeout": 5
                    }
                ]
            }
        ]
    }

def install_hooks():
    """Install or update Claude Code hooks configuration"""
    # Determine settings file path
    settings_path = Path.home() / '.claude' / 'settings.json'

    # Create directory if it doesn't exist
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing settings or start fresh
    if settings_path.exists():
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            print(f"✓ Found existing Claude Code settings at {settings_path}")
        except json.JSONDecodeError:
            print(f"⚠ Warning: Could not parse existing settings, starting fresh")
            settings = {}
    else:
        settings = {}
        print(f"✓ Creating new Claude Code settings at {settings_path}")

    # Merge hook configuration
    hook_config = get_hook_config()

    if 'hooks' not in settings:
        settings['hooks'] = {}

    # Add Claudia hooks
    for event_type, event_config in hook_config.items():
        if event_type not in settings['hooks']:
            settings['hooks'][event_type] = []

        # Check if our hooks are already installed
        claudia_commands = set()
        for matcher_group in event_config:
            for hook in matcher_group['hooks']:
                claudia_commands.add(hook['command'])

        # Remove old Claudia hooks (if any) and add new ones
        existing_hooks = settings['hooks'][event_type]
        filtered_hooks = []

        for matcher_group in existing_hooks:
            non_claudia_hooks = []
            for hook in matcher_group.get('hooks', []):
                if 'claudia/hooks' not in hook.get('command', ''):
                    non_claudia_hooks.append(hook)

            if non_claudia_hooks:
                matcher_group['hooks'] = non_claudia_hooks
                filtered_hooks.append(matcher_group)

        # Add our hooks
        settings['hooks'][event_type] = filtered_hooks + event_config

    # Write updated settings
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)

    print(f"✓ Updated Claude Code settings with Claudia hooks")

    # Make hook scripts executable (Unix-like systems)
    if sys.platform != 'win32':
        hooks_dir = Path(__file__).parent
        for script in hooks_dir.glob('*.py'):
            script.chmod(0o755)
        print(f"✓ Made hook scripts executable")

    return True

def main():
    """Main installation process"""
    print("Claudia Hook Installer")
    print("=" * 50)

    # Check backend
    print("\n1. Checking Claudia backend...")
    if check_backend_health():
        print("   ✓ Backend is running")
    else:
        print("   ⚠ Backend not accessible (hooks will queue events)")
        print("   Start backend with: cd backend && uv run uvicorn app.main:app")

    # Install hooks
    print("\n2. Installing hooks...")
    if install_hooks():
        print("\n✓ Installation complete!")
        print("\nClaudia monitoring hooks are now active.")
        print("Start a new Claude Code session to begin monitoring.")
    else:
        print("\n✗ Installation failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
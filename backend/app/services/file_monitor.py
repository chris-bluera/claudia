"""
File monitoring service for Claude Code directories
Watches for session changes, transcript updates, and configuration modifications
"""
import json
import asyncio
from pathlib import Path
from typing import Callable, Dict, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from loguru import logger

class ClaudeCodeEventHandler(FileSystemEventHandler):
    """Handle file system events in Claude Code directories"""

    def __init__(self, callback: Callable[[Dict[str, Any]], None]):
        self.callback = callback
        self.monitored_transcripts = set()

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if event.is_directory:
            # New session directory
            path = Path(event.src_path)
            if path.parent.name == "projects":
                self._handle_session_start(path)
        elif event.src_path.endswith('.jsonl'):
            # New transcript file
            self._handle_transcript_created(Path(event.src_path))

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if not event.is_directory and event.src_path.endswith('.jsonl'):
            # Transcript updated
            self._handle_transcript_update(Path(event.src_path))
        elif not event.is_directory and event.src_path.endswith('settings.json'):
            # Settings changed
            self._handle_settings_change(Path(event.src_path))

    def _handle_session_start(self, session_dir: Path):
        """Handle new Claude Code session"""
        try:
            session_id = session_dir.name
            self.callback({
                'type': 'session_start',
                'session_id': session_id,
                'project_path': str(session_dir.parent.parent),
                'timestamp': None  # Will be set by receiver
            })
        except Exception as e:
            logger.error(f"Error handling session start: {e}")

    def _handle_transcript_created(self, transcript_path: Path):
        """Handle new transcript file"""
        try:
            session_id = transcript_path.parent.name
            self.monitored_transcripts.add(str(transcript_path))
            logger.info(f"Now monitoring transcript: {transcript_path}")
        except Exception as e:
            logger.error(f"Error handling transcript creation: {e}")

    def _handle_transcript_update(self, transcript_path: Path):
        """Handle transcript file updates - parse new events"""
        try:
            # Read last line (most recent event)
            with open(transcript_path, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return

                last_line = lines[-1].strip()
                if not last_line:
                    return

                event_data = json.loads(last_line)

                # Extract relevant information
                if 'type' in event_data:
                    event_type = event_data['type']

                    # Tool execution event
                    if event_type == 'tool_use':
                        self.callback({
                            'type': 'tool_execution',
                            'session_id': transcript_path.parent.name,
                            'tool_name': event_data.get('name', ''),
                            'parameters': event_data.get('input', {}),
                            'timestamp': event_data.get('timestamp')
                        })

                    # User prompt
                    elif event_type == 'user_message':
                        self.callback({
                            'type': 'user_prompt',
                            'session_id': transcript_path.parent.name,
                            'content': event_data.get('content', ''),
                            'timestamp': event_data.get('timestamp')
                        })

        except json.JSONDecodeError as e:
            # Malformed JSON in transcript (can happen during writes)
            logger.warning(f"Malformed JSON in transcript {transcript_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing transcript update: {e}")

    def _handle_settings_change(self, settings_path: Path):
        """Handle settings file changes"""
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)

            # Determine settings level
            if '.claude' in str(settings_path):
                level = 'project' if settings_path.parent.name == '.claude' else 'local'
            else:
                level = 'user'

            self.callback({
                'type': 'settings_update',
                'level': level,
                'settings': settings,
                'path': str(settings_path)
            })
        except Exception as e:
            logger.error(f"Error handling settings change: {e}")


class FileMonitor:
    """
    Monitor Claude Code directories for changes
    Watches projects directory and settings files
    """

    def __init__(self, projects_path: Path, callback: Callable[[Dict[str, Any]], None]):
        self.projects_path = projects_path
        self.callback = callback
        self.observer: Optional[Observer] = None
        self.event_handler = ClaudeCodeEventHandler(callback)

    def start(self):
        """Start monitoring Claude Code directories"""
        if self.observer is not None:
            logger.warning("File monitor already running")
            return

        if not self.projects_path.exists():
            logger.error(f"Projects path does not exist: {self.projects_path}")
            return

        self.observer = Observer()

        # Monitor projects directory recursively
        self.observer.schedule(
            self.event_handler,
            str(self.projects_path),
            recursive=True
        )

        # Monitor user settings
        user_settings = self.projects_path.parent / 'settings.json'
        if user_settings.exists():
            self.observer.schedule(
                self.event_handler,
                str(user_settings.parent),
                recursive=False
            )

        self.observer.start()
        logger.info(f"File monitor started for: {self.projects_path}")

    def stop(self):
        """Stop monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("File monitor stopped")

    def is_running(self) -> bool:
        """Check if monitor is running"""
        return self.observer is not None and self.observer.is_alive()

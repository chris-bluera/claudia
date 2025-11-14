"""
Settings aggregation service for Claude Code
Reads and merges settings from the configuration hierarchy
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from app.constants import (
    get_managed_settings_path,
    CLAUDE_SETTINGS_FILENAME,
    CLAUDE_LOCAL_SETTINGS_FILENAME,
    CLAUDE_DIR_NAME,
    SETTINGS_PRECEDENCE
)

logger = logging.getLogger(__name__)

class SettingsAggregator:
    """
    Aggregate Claude Code settings from all sources

    Settings Hierarchy (highest to lowest precedence):
    1. Command-line arguments (captured via hooks)
    2. Enterprise managed settings (cannot be overridden)
    3. Local project settings (.claude/settings.local.json)
    4. Shared project settings (.claude/settings.json)
    5. User settings (~/.claude/settings.json)

    This service computes file-based settings. Runtime configuration
    (including CLI overrides) is captured via session hooks and merged separately.
    """

    def __init__(self, claude_settings_path: Path):
        self.claude_settings_path = claude_settings_path
        self.user_settings_path = claude_settings_path / CLAUDE_SETTINGS_FILENAME

    def read_settings_file(self, path: Path) -> Dict[str, Any]:
        """Safely read a settings JSON file"""
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {path}")
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
        return {}

    def get_settings_hierarchy(self, project_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get settings from all sources
        Returns dict with keys: managed, user, project, local
        """
        hierarchy = {
            'managed': {},
            'user': {},
            'project': {},
            'local': {}
        }

        # Managed settings (enterprise)
        managed_path = get_managed_settings_path()
        if managed_path:
            hierarchy['managed'] = self.read_settings_file(managed_path)

        # User settings
        hierarchy['user'] = self.read_settings_file(self.user_settings_path)

        # Project settings (if project path provided)
        if project_path:
            project_settings_path = project_path / CLAUDE_DIR_NAME / CLAUDE_SETTINGS_FILENAME
            hierarchy['project'] = self.read_settings_file(project_settings_path)

            local_settings_path = project_path / CLAUDE_DIR_NAME / CLAUDE_LOCAL_SETTINGS_FILENAME
            hierarchy['local'] = self.read_settings_file(local_settings_path)

        return hierarchy

    def compute_effective_settings(self, project_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Compute effective settings from files only
        This is the baseline configuration before CLI overrides
        """
        hierarchy = self.get_settings_hierarchy(project_path)

        # Start with empty base
        effective = {}

        # Merge in order of precedence (lowest to highest)
        for level in SETTINGS_PRECEDENCE:
            self._deep_merge(effective, hierarchy[level])

        return effective

    def merge_runtime_overrides(
        self,
        file_based: Dict[str, Any],
        runtime: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge runtime configuration (from hooks) with file-based settings
        Runtime overrides take highest precedence
        """
        result = file_based.copy()
        self._deep_merge(result, runtime)
        return result

    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]):
        """
        Deep merge overlay into base
        Mutates base dict
        """
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                self._deep_merge(base[key], value)
            else:
                # Override or add new key
                base[key] = value

    def get_settings_summary(
        self,
        project_path: Optional[Path] = None,
        runtime_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of settings including hierarchy and computed values

        Args:
            project_path: Optional project directory path
            runtime_config: Optional runtime configuration captured from hooks
        """
        hierarchy = self.get_settings_hierarchy(project_path)
        file_based = self.compute_effective_settings(project_path)

        # If we have runtime config, merge it in
        effective = file_based
        if runtime_config:
            effective = self.merge_runtime_overrides(file_based, runtime_config)

        # Count how many sources have settings
        active_sources = [
            level for level, settings in hierarchy.items()
            if settings
        ]

        if runtime_config:
            active_sources.append('runtime')

        return {
            'hierarchy': hierarchy,
            'file_based': file_based,
            'runtime': runtime_config or {},
            'effective': effective,
            'active_sources': active_sources,
            'total_keys': len(effective.keys()),
            'has_runtime_overrides': bool(runtime_config)
        }

-- Migration 03: Add source, reason, and claudia_metadata to claude_sessions
-- Date: 2025-11-14
-- Purpose:
--   - Capture SessionStart source (startup|resume|clear|compact) from Claude Code
--   - Capture SessionEnd reason (exit|logout|clear|prompt_input_exit|other) from Claude Code
--   - Add claudia_metadata for internal tracking (separate from Claude Code API data)
--
-- Related to: Session model investigation and "0 active sessions" bug fix
-- See: HOOKS_ANALYSIS_REPORT.md "Session Model Investigation & Fixes"

-- Add source column (SessionStart matcher type)
ALTER TABLE claudia.claude_sessions
  ADD COLUMN IF NOT EXISTS source VARCHAR(50);

-- Add reason column (SessionEnd reason)
ALTER TABLE claudia.claude_sessions
  ADD COLUMN IF NOT EXISTS reason VARCHAR(50);

-- Add claudia_metadata column (internal tracking data)
ALTER TABLE claudia.claude_sessions
  ADD COLUMN IF NOT EXISTS claudia_metadata JSONB DEFAULT '{}' NOT NULL;

-- Add column comments
COMMENT ON COLUMN claudia.claude_sessions.source IS
  'SessionStart source: startup|resume|clear|compact (from Claude Code hook)';

COMMENT ON COLUMN claudia.claude_sessions.reason IS
  'SessionEnd reason: exit|logout|clear|prompt_input_exit|other (from Claude Code hook)';

COMMENT ON COLUMN claudia.claude_sessions.claudia_metadata IS
  'Claudia internal tracking data, NOT from Claude Code API. Contains: first_seen_at, derived fields, internal state.';

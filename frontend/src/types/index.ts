/**
 * Type definitions for Claudia frontend
 */

// Claude Code runtime configuration
export interface RuntimeConfig {
  permission_mode?: string
  model?: string
  [key: string]: unknown
}

// Claude Code settings structure
export interface ClaudeSettings {
  model?: string
  alwaysThinkingEnabled?: boolean
  statusLine?: {
    type: 'command' | 'text'
    command?: string
    text?: string
  }
  hooks?: {
    [hookType: string]: string
  }
  mcpServers?: {
    [serverName: string]: {
      command: string
      args?: string[]
      env?: Record<string, string>
    }
  }
  [key: string]: unknown
}

export interface Session {
  session_id: string
  project_path: string
  project_name: string
  started_at: string
  ended_at: string | null
  is_active: boolean
  runtime_config: RuntimeConfig
  last_activity: string
  tool_count: number
  transcript_path: string | null
  duration_seconds: number
}

export interface ToolExecution {
  session_id: string
  tool_name: string
  parameters: Record<string, unknown>
  timestamp: string
}

export interface SettingsHierarchy {
  managed: ClaudeSettings
  user: ClaudeSettings
  project: ClaudeSettings
  local: ClaudeSettings
}

export interface SettingsSummary {
  hierarchy: SettingsHierarchy
  file_based: ClaudeSettings
  runtime: RuntimeConfig
  effective: ClaudeSettings
  active_sources: string[]
}

export interface MonitoringStats {
  total_sessions: number
  active_sessions: number
  sessions_last_24h: number
  total_tools_executed: number
  average_session_duration_seconds: number
  unique_projects: number
}

export interface HealthStatus {
  status: string
  file_monitor: boolean
  active_connections: number
  active_sessions: number
}

export interface WebSocketEvent {
  type: 'session_start' | 'session_end' | 'tool_execution' | 'settings_update'
  data: unknown
  timestamp: string | null
}

export interface ActivityEvent {
  id: string
  type: 'session_start' | 'session_end' | 'tool_execution' | 'settings_update'
  session_id?: string
  tool_name?: string
  project_name?: string
  timestamp: string
  data: unknown
}

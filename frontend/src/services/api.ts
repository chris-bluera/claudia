/**
 * API client for Claudia backend
 */
import type {
  Session,
  SettingsSummary,
  MonitoringStats,
  HealthStatus
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Health
  async getHealth(): Promise<HealthStatus> {
    return this.fetch<HealthStatus>('/health')
  }

  // Sessions
  async getActiveSessions(): Promise<{ sessions: Session[]; count: number }> {
    return this.fetch('/api/sessions/active')
  }

  async getRecentSessions(hours: number = 24): Promise<{ sessions: Session[]; count: number; hours: number }> {
    return this.fetch(`/api/sessions/recent?hours=${hours}`)
  }

  async getSession(sessionId: string): Promise<Session> {
    return this.fetch(`/api/sessions/${sessionId}`)
  }

  // Settings
  async getCurrentSettings(projectPath?: string): Promise<SettingsSummary> {
    const query = projectPath ? `?project_path=${encodeURIComponent(projectPath)}` : ''
    return this.fetch(`/api/settings/current${query}`)
  }

  async getSettingsHierarchy(projectPath?: string): Promise<{
    hierarchy: SettingsSummary['hierarchy']
    sources: string[]
  }> {
    const query = projectPath ? `?project_path=${encodeURIComponent(projectPath)}` : ''
    return this.fetch(`/api/settings/hierarchy${query}`)
  }

  // Monitoring
  async getStats(): Promise<MonitoringStats> {
    return this.fetch('/api/monitoring/stats')
  }
}

export const apiClient = new ApiClient()

/**
 * Pinia store for monitoring Claude Code state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/services/api'
import { wsClient } from '@/services/websocket'
import type {
  Session,
  SettingsSummary,
  MonitoringStats,
  HealthStatus,
  ActivityEvent,
  WebSocketEvent
} from '@/types'

export const useMonitoringStore = defineStore('monitoring', () => {
  // State
  const sessions = ref<Session[]>([])
  const settings = ref<SettingsSummary | null>(null)
  const stats = ref<MonitoringStats | null>(null)
  const health = ref<HealthStatus | null>(null)
  const activityFeed = ref<ActivityEvent[]>([])
  const isConnected = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const activeSessions = computed(() =>
    sessions.value.filter(s => s.is_active)
  )

  const recentActivity = computed(() =>
    activityFeed.value.slice(0, 50) // Keep last 50 events
  )

  // Actions
  async function fetchHealth() {
    try {
      health.value = await apiClient.getHealth()
    } catch (err) {
      console.error('Error fetching health:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
    }
  }

  async function fetchSessions() {
    try {
      isLoading.value = true
      const response = await apiClient.getActiveSessions()
      sessions.value = response.sessions
    } catch (err) {
      console.error('Error fetching sessions:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
    } finally {
      isLoading.value = false
    }
  }

  async function fetchSettings(projectPath?: string) {
    try {
      settings.value = await apiClient.getCurrentSettings(projectPath)
    } catch (err) {
      console.error('Error fetching settings:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
    }
  }

  async function fetchStats() {
    try {
      stats.value = await apiClient.getStats()
    } catch (err) {
      console.error('Error fetching stats:', err)
      error.value = err instanceof Error ? err.message : 'Unknown error'
    }
  }

  async function refreshAll() {
    await Promise.all([
      fetchHealth(),
      fetchSessions(),
      fetchSettings(),
      fetchStats()
    ])
  }

  function handleWebSocketEvent(event: WebSocketEvent) {
    console.log('WebSocket event:', event)

    // Add to activity feed
    const activityEvent: ActivityEvent = {
      id: `${event.type}-${Date.now()}-${Math.random()}`,
      type: event.type,
      timestamp: event.timestamp || new Date().toISOString(),
      data: event.data
    }

    // Extract session_id and other fields based on event type
    if (typeof event.data === 'object' && event.data !== null) {
      const data = event.data as Record<string, unknown>

      if ('session_id' in data && typeof data.session_id === 'string') {
        activityEvent.session_id = data.session_id
      }

      if ('tool_name' in data && typeof data.tool_name === 'string') {
        activityEvent.tool_name = data.tool_name
      }

      if ('project_name' in data && typeof data.project_name === 'string') {
        activityEvent.project_name = data.project_name
      }
    }

    activityFeed.value.unshift(activityEvent)

    // Keep only last 100 events
    if (activityFeed.value.length > 100) {
      activityFeed.value = activityFeed.value.slice(0, 100)
    }

    // Handle specific events
    switch (event.type) {
      case 'session_start':
        // Refresh sessions
        fetchSessions()
        break

      case 'session_end':
        // Refresh sessions
        fetchSessions()
        break

      case 'tool_execution':
        // Update tool count for session
        if (typeof event.data === 'object' && event.data !== null) {
          const data = event.data as Record<string, unknown>
          if ('session_id' in data && typeof data.session_id === 'string') {
            const session = sessions.value.find(s => s.session_id === data.session_id)
            if (session) {
              session.tool_count++
              session.last_activity = event.timestamp || new Date().toISOString()
            }
          }
        }
        break

      case 'settings_update':
        // Refresh settings
        fetchSettings()
        break
    }
  }

  function connectWebSocket() {
    wsClient.on(handleWebSocketEvent)
    wsClient.connect()
    isConnected.value = true
  }

  function disconnectWebSocket() {
    wsClient.disconnect()
    isConnected.value = false
  }

  // Initialize
  async function initialize() {
    await refreshAll()
    connectWebSocket()
  }

  function cleanup() {
    disconnectWebSocket()
  }

  return {
    // State
    sessions,
    settings,
    stats,
    health,
    activityFeed,
    isConnected,
    isLoading,
    error,
    // Computed
    activeSessions,
    recentActivity,
    // Actions
    fetchHealth,
    fetchSessions,
    fetchSettings,
    fetchStats,
    refreshAll,
    connectWebSocket,
    disconnectWebSocket,
    initialize,
    cleanup
  }
})

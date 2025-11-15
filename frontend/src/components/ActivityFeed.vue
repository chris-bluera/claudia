<template>
  <div class="panel">
    <div class="panel-header">
      <h2>Activity Feed</h2>
      <span v-if="selectedSessionId" class="filter-indicator">
        Filtered by session
      </span>
    </div>

    <div v-if="filteredEvents.length === 0" class="empty-state">
      <p v-if="selectedSessionId">No activity for this session</p>
      <p v-else>No recent activity</p>
      <p class="hint">Real-time events will appear here</p>
    </div>

    <div v-else class="activity-list">
      <div
        v-for="event in filteredEvents"
        :key="event.id"
        :class="['activity-item', `type-${event.type.replace('_', '-')}`]"
      >
        <div class="activity-icon">{{ getEventIcon(event.type) }}</div>
        <div class="activity-content">
          <div class="activity-title">{{ getEventTitle(event) }}</div>
          <div class="activity-meta">{{ formatTimestamp(event.timestamp) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useMonitoringStore } from '@/stores/monitoring'
import type { ActivityEvent } from '@/types'

const props = defineProps<{
  events: ActivityEvent[]
}>()

const store = useMonitoringStore()
const { selectedSessionId } = storeToRefs(store)

const filteredEvents = computed(() => {
  if (!selectedSessionId.value) {
    return props.events
  }
  return props.events.filter(event => event.session_id === selectedSessionId.value)
})

function getEventIcon(type: string): string {
  switch (type) {
    case 'session_start': return '▶️'
    case 'session_end': return '⏹️'
    case 'tool_execution': return '🔧'
    case 'settings_update': return '⚙️'
    default: return '📌'
  }
}

function getEventTitle(event: ActivityEvent): string {
  switch (event.type) {
    case 'session_start':
      return `Session started${event.project_name ? `: ${event.project_name}` : ''}`
    case 'session_end':
      return `Session ended${event.project_name ? `: ${event.project_name}` : ''}`
    case 'tool_execution':
      return `Tool executed: ${event.tool_name || 'Unknown'}`
    case 'settings_update':
      return 'Settings updated'
    default:
      return 'Activity event'
  }
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 1000) return 'just now'
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`

  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.panel {
  background: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  max-height: 400px;
}

.panel-header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}

.panel-header h2 {
  font-size: var(--font-size-xl);
}

.filter-indicator {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-normal);
}

.empty-state {
  padding: var(--space-2xl);
  text-align: center;
  color: var(--color-text-secondary);
}

.empty-state .hint {
  margin-top: var(--space-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.activity-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md);
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  transition: background-color var(--duration-fast) var(--easing-default);
}

.activity-item:hover {
  background-color: var(--color-bg-secondary);
}

.activity-item:last-child {
  margin-bottom: 0;
}

.activity-icon {
  flex-shrink: 0;
  font-size: var(--font-size-lg);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  margin-bottom: var(--space-xxs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-meta {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Type-specific styling */
.type-session-start {
  border-left: 3px solid var(--color-success);
}

.type-session-end {
  border-left: 3px solid var(--color-text-tertiary);
}

.type-tool-execution {
  border-left: 3px solid var(--color-accent);
}

.type-settings-update {
  border-left: 3px solid var(--color-warning);
}
</style>

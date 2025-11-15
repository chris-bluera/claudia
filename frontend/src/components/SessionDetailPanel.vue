<template>
  <div class="panel">
    <div class="panel-header" @click="toggleCollapsed">
      <h2>Session Details</h2>
      <button class="collapse-toggle" :aria-label="isCollapsed ? 'Expand' : 'Collapse'">
        {{ isCollapsed ? '▼' : '▲' }}
      </button>
    </div>

    <div v-if="!session && !isCollapsed" class="empty-state">
      <p>No session selected</p>
    </div>

    <div v-else-if="session && !isCollapsed" class="details-grid">
      <div class="detail-item">
        <span class="detail-label">Status</span>
        <span :class="['detail-value', 'status', session.is_active ? 'active' : 'inactive']">
          {{ session.is_active ? 'Active' : 'Ended' }}
        </span>
      </div>

      <div v-if="session.source" class="detail-item">
        <span class="detail-label">Source</span>
        <span class="detail-value">
          <span :class="['source-badge', `source-${session.source}`]">
            {{ session.source }}
          </span>
        </span>
      </div>

      <div v-if="!session.is_active && session.reason" class="detail-item">
        <span class="detail-label">End Reason</span>
        <span class="detail-value">{{ session.reason }}</span>
      </div>

      <div class="detail-item">
        <span class="detail-label">Duration</span>
        <span class="detail-value">{{ formatDuration(session.duration_seconds) }}</span>
      </div>

      <div class="detail-item">
        <span class="detail-label">Started</span>
        <span class="detail-value">{{ formatTimestamp(session.started_at) }}</span>
      </div>

      <div v-if="session.ended_at" class="detail-item">
        <span class="detail-label">Ended</span>
        <span class="detail-value">{{ formatTimestamp(session.ended_at) }}</span>
      </div>

      <div v-if="session.transcript_path" class="detail-item full-width">
        <span class="detail-label">Transcript</span>
        <code class="detail-value monospace">{{ session.transcript_path }}</code>
      </div>

      <div v-if="session.claudia_metadata?.first_seen_at" class="detail-item">
        <span class="detail-label">First Seen</span>
        <span class="detail-value">{{ formatTimestamp(session.claudia_metadata.first_seen_at) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Session } from '@/types'

defineProps<{
  session: Session | null
}>()

const isCollapsed = ref(true)

function toggleCollapsed() {
  isCollapsed.value = !isCollapsed.value
}

function formatDuration(seconds: number): string {
  if (seconds === undefined || seconds === null || isNaN(seconds)) return '—'
  if (seconds < 60) return `${Math.floor(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}h ${minutes}m`
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return 'just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return date.toLocaleString()
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
}

.panel-header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
  transition: background-color var(--duration-fast) var(--easing-standard);
}

.panel-header:hover {
  background: var(--color-bg-secondary);
}

.panel-header h2 {
  font-size: var(--font-size-xl);
  margin: 0;
}

.collapse-toggle {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--font-size-lg);
  cursor: pointer;
  padding: var(--space-xs);
  line-height: 1;
  transition: color var(--duration-fast) var(--easing-standard);
}

.collapse-toggle:hover {
  color: var(--color-text-primary);
}

.empty-state {
  padding: var(--space-2xl);
  text-align: center;
  color: var(--color-text-secondary);
}

.details-grid {
  padding: var(--space-lg);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-medium);
}

.detail-value {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
}

.detail-value.monospace {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  overflow-wrap: break-word;
}

.detail-value.status {
  font-weight: var(--font-weight-semibold);
}

.detail-value.status.active {
  color: var(--color-success);
}

.detail-value.status.inactive {
  color: var(--color-text-tertiary);
}

.source-badge {
  display: inline-block;
  padding: var(--space-xxs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  text-transform: uppercase;
  font-weight: var(--font-weight-semibold);
}

.source-startup {
  background: var(--color-success-light);
  color: var(--color-success);
}

.source-resume {
  background: var(--color-accent-light);
  color: var(--color-accent);
}

.source-clear,
.source-compact {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

@media (max-width: 968px) {
  .details-grid {
    grid-template-columns: 1fr;
  }
}
</style>

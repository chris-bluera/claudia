<template>
  <div class="panel">
    <div class="panel-header">
      <h2>Active Sessions</h2>
      <span class="count-badge">{{ sessions.length }}</span>
    </div>

    <div v-if="loading" class="loading">Loading sessions...</div>

    <div v-else-if="sessions.length === 0" class="empty-state">
      <p>No active Claude Code sessions</p>
      <p class="hint">Sessions will appear here when Claude Code is running</p>
    </div>

    <div v-else class="sessions-list">
      <div v-for="session in sessions" :key="session.session_id" class="session-card">
        <div class="session-header">
          <div class="project-name">{{ session.project_name }}</div>
          <div class="session-time">{{ formatDuration(session.duration_seconds) }}</div>
        </div>
        <div class="session-meta">
          <div class="meta-item">
            <span class="meta-label">Tools:</span>
            <span class="meta-value">{{ session.tool_count }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Started:</span>
            <span class="meta-value">{{ formatTimestamp(session.started_at) }}</span>
          </div>
        </div>
        <div class="session-path">{{ session.project_path }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Session } from '@/types'

defineProps<{
  sessions: Session[]
  loading?: boolean
}>()

function formatDuration(seconds: number): string {
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
  return date.toLocaleDateString()
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
  height: 100%;
}

.panel-header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-header h2 {
  font-size: var(--font-size-xl);
}

.count-badge {
  background: var(--color-accent-light);
  color: var(--color-accent);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.loading,
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

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md);
}

.session-card {
  background: var(--color-bg-secondary);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  border: 1px solid var(--color-border);
  transition: border-color var(--duration-fast) var(--easing-default);
}

.session-card:hover {
  border-color: var(--color-accent);
}

.session-card:last-child {
  margin-bottom: 0;
}

.session-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-sm);
}

.project-name {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
}

.session-time {
  font-size: var(--font-size-sm);
  color: var(--color-accent);
  font-weight: var(--font-weight-medium);
}

.session-meta {
  display: flex;
  gap: var(--space-lg);
  margin-bottom: var(--space-sm);
}

.meta-item {
  display: flex;
  gap: var(--space-xs);
  font-size: var(--font-size-sm);
}

.meta-label {
  color: var(--color-text-tertiary);
}

.meta-value {
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.session-path {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  font-family: var(--font-family-mono);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

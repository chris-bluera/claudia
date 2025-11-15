<template>
  <div class="session-tabs">
    <button
      v-for="session in activeSessions"
      :key="session.session_id"
      class="tab"
      :class="{ active: isSelected(session.session_id) }"
      @click="selectSession(session.session_id)"
    >
      <span class="tab-name">{{ session.project_name }}</span>
      <span v-if="session.source" class="tab-badge" :class="`badge-${session.source}`">
        {{ session.source }}
      </span>
      <span class="tab-duration">{{ formatDuration(session.duration_seconds) }}</span>
    </button>
    <button
      v-if="selectedSessionId"
      class="tab tab-clear"
      @click="clearSelection"
      title="Show all sessions"
    >
      All
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useMonitoringStore } from '@/stores/monitoring'

const store = useMonitoringStore()
const { activeSessions, selectedSessionId } = storeToRefs(store)

function isSelected(sessionId: string): boolean {
  return selectedSessionId.value === sessionId
}

function selectSession(sessionId: string) {
  store.selectSession(sessionId)
}

function clearSelection() {
  store.clearSelection()
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${hours}h ${mins}m`
}
</script>

<style scoped>
.session-tabs {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-md) 0;
  border-bottom: 1px solid var(--color-border);
  overflow-x: auto;
}

.tab {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  font-size: var(--font-size-sm);
}

.tab:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-accent);
}

.tab.active {
  background: var(--color-accent);
  color: var(--color-text-inverse);
  border-color: var(--color-accent);
}

.tab-clear {
  background: transparent;
  border: 1px dashed var(--color-border);
}

.tab-clear:hover {
  background: var(--color-bg-tertiary);
  border-style: solid;
}

.tab-name {
  font-weight: var(--font-weight-medium);
}

.tab-badge {
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  text-transform: uppercase;
  font-weight: var(--font-weight-semibold);
}

.badge-startup {
  background: var(--color-success-light);
  color: var(--color-success);
}

.badge-resume {
  background: var(--color-accent-light);
  color: var(--color-accent);
}

.badge-clear,
.badge-compact {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.tab-duration {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.tab.active .tab-duration {
  color: var(--color-text-inverse);
  opacity: 0.8;
}
</style>

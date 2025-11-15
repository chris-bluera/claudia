<template>
  <div class="dashboard">
    <header class="header">
      <h1>Claudia</h1>
      <p class="subtitle">Claude Code Companion</p>
      <div class="status">
        <span :class="['status-indicator', health?.file_monitor ? 'active' : 'inactive']"></span>
        <span class="status-text">
          {{ health?.file_monitor ? 'Monitoring Active' : 'Monitoring Inactive' }}
        </span>
      </div>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Active Sessions</div>
        <div class="stat-value">{{ stats?.active_sessions ?? 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Sessions (24h)</div>
        <div class="stat-value">{{ stats?.sessions_last_24h ?? 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Tools Executed</div>
        <div class="stat-value">{{ stats?.total_tools_executed ?? 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Unique Projects</div>
        <div class="stat-value">{{ stats?.unique_projects ?? 0 }}</div>
      </div>
    </div>

    <SessionTabs v-if="activeSessions.length > 0" />

    <!-- Main content area - conditional based on selection -->
    <div v-if="!selectedSessionId" class="global-view">
      <!-- Global overview (existing panels grid) -->
      <div class="panels-grid">
        <SessionsPanel :sessions="activeSessions" :loading="isLoading" />
        <ActivityFeed :events="recentActivity" />
        <SettingsPanel :settings="settings" />
      </div>
    </div>

    <div v-else class="session-view">
      <!-- Session-specific details -->
      <div class="session-layout">
        <div class="session-main">
          <SessionDetailPanel :session="selectedSession" />
          <ConversationView :conversation="sessionConversation" />
        </div>
        <div class="session-sidebar">
          <ToolExecutionList :tools="sessionTools" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useMonitoringStore } from '@/stores/monitoring'
import SessionTabs from '@/components/SessionTabs.vue'
import SessionsPanel from '@/components/SessionsPanel.vue'
import ActivityFeed from '@/components/ActivityFeed.vue'
import SettingsPanel from '@/components/SettingsPanel.vue'
import SessionDetailPanel from '@/components/SessionDetailPanel.vue'
import ToolExecutionList from '@/components/ToolExecutionList.vue'
import ConversationView from '@/components/ConversationView.vue'

const store = useMonitoringStore()
const { settings, stats, health, isLoading, activeSessions, recentActivity, selectedSession, selectedSessionId, sessionTools, sessionConversation } = storeToRefs(store)

let statsInterval: number

onMounted(async () => {
  await store.initialize()

  // Refresh stats every 30 seconds
  statsInterval = window.setInterval(() => {
    store.fetchStats()
    store.fetchHealth()
  }, 30000)
})

onUnmounted(() => {
  if (statsInterval) {
    clearInterval(statsInterval)
  }
  store.cleanup()
})
</script>

<style scoped>
.dashboard {
  padding: var(--space-xl);
}

.header {
  margin-bottom: var(--space-xl);
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

.header h1 {
  margin: 0;
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
}

.status {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-left: auto;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-full);
}

.status-indicator.active {
  background-color: var(--color-success);
  box-shadow: 0 0 8px rgba(0, 170, 0, 0.6);
}

.status-indicator.inactive {
  background-color: var(--color-text-tertiary);
}

.status-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.stat-card {
  background: var(--color-bg-primary);
  padding: var(--space-lg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-sm);
}

.stat-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.panels-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: var(--space-lg);
}

.panels-grid > :nth-child(1) {
  grid-column: 1 / 2;
  grid-row: 1 / 3;
}

.panels-grid > :nth-child(2) {
  grid-column: 2 / 3;
  grid-row: 1 / 2;
}

.panels-grid > :nth-child(3) {
  grid-column: 2 / 3;
  grid-row: 2 / 3;
}

.session-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--space-lg);
}

.session-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.session-sidebar {
  display: flex;
  flex-direction: column;
}

@media (max-width: 968px) {
  .panels-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }

  .panels-grid > :nth-child(1),
  .panels-grid > :nth-child(2),
  .panels-grid > :nth-child(3) {
    grid-column: 1 / 2;
    grid-row: auto;
  }

  .session-layout {
    grid-template-columns: 1fr;
  }
}
</style>

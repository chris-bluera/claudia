<script setup lang="ts">
import CollapsibleCard from './CollapsibleCard.vue'

interface McpServer {
  command: string
  args?: string[]
  env?: Record<string, string>
  type?: string
  url?: string
}

interface McpServersSetting {
  [serverName: string]: McpServer
}

interface Props {
  value: McpServersSetting
}

defineProps<Props>()
</script>

<template>
  <div class="mcp-servers-display">
    <CollapsibleCard
      v-for="(server, serverName) in value"
      :key="serverName"
      :title="serverName"
      :icon="'🔌'"
      :default-expanded="false"
    >
      <div class="server-details">
        <div v-if="server.type" class="detail-row">
          <span class="label">Type:</span>
          <span class="badge">{{ server.type }}</span>
        </div>

        <div v-if="server.url" class="detail-row">
          <span class="label">URL:</span>
          <code class="value-code">{{ server.url }}</code>
        </div>

        <div v-if="server.command" class="detail-row">
          <span class="label">Command:</span>
          <code class="value-code">{{ server.command }}</code>
        </div>

        <div v-if="server.args && server.args.length > 0" class="detail-row">
          <span class="label">Arguments:</span>
          <div class="args-list">
            <code
              v-for="(arg, idx) in server.args"
              :key="idx"
              class="arg-item"
            >
              {{ arg }}
            </code>
          </div>
        </div>

        <div v-if="server.env && Object.keys(server.env).length > 0" class="detail-row">
          <span class="label">Environment:</span>
          <div class="env-list">
            <div
              v-for="(value, key) in server.env"
              :key="key"
              class="env-item"
            >
              <code class="env-key">{{ key }}</code>
              <span class="env-separator">=</span>
              <code class="env-value">{{ value }}</code>
            </div>
          </div>
        </div>
      </div>
    </CollapsibleCard>
  </div>
</template>

<style scoped>
.mcp-servers-display {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.server-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2xs);
}

.label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.badge {
  display: inline-block;
  padding: var(--spacing-2xs) var(--spacing-xs);
  background: var(--accent-color);
  color: var(--bg-primary);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  width: fit-content;
}

.value-code {
  background: var(--bg-tertiary);
  padding: var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  border: 1px solid var(--border-color);
  display: block;
}

.args-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2xs);
}

.arg-item {
  background: var(--bg-tertiary);
  padding: var(--spacing-2xs) var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  width: fit-content;
}

.env-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2xs);
}

.env-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2xs);
  padding: var(--spacing-2xs) var(--spacing-xs);
  background: var(--bg-tertiary);
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--border-color);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
}

.env-key {
  color: var(--accent-color);
  font-weight: var(--font-weight-medium);
}

.env-separator {
  color: var(--text-secondary);
}

.env-value {
  color: var(--text-primary);
}
</style>

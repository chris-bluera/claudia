<template>
  <div class="panel">
    <div class="panel-header">
      <h2>Tool Executions</h2>
      <span class="count-badge">{{ props.tools.length }}</span>
    </div>

    <div v-if="props.tools.length === 0" class="empty-state">
      <p>No tool executions for this session</p>
      <p class="hint">Tool calls will appear here as they are executed</p>
    </div>

    <div v-else class="tools-list">
      <div
        v-for="tool in props.tools"
        :key="tool.id"
        :class="['tool-item', { 'has-error': tool.error }]"
      >
        <div class="tool-header" @click="toggleExpanded(tool.id)">
          <div class="tool-info">
            <span class="tool-name">{{ tool.tool_name }}</span>
            <span v-if="tool.executed_at" class="tool-timestamp">
              {{ formatTimestamp(tool.executed_at) }}
            </span>
          </div>
          <div class="tool-badges">
            <span v-if="tool.error" class="error-badge">Error</span>
            <span v-if="tool.duration_ms !== null" class="duration-badge">
              {{ formatDuration(tool.duration_ms) }}
            </span>
            <span class="expand-icon">{{ isExpanded(tool.id) ? '▼' : '▶' }}</span>
          </div>
        </div>

        <div v-if="isExpanded(tool.id)" class="tool-details">
          <div v-if="tool.parameters" class="detail-section">
            <h4>Parameters</h4>
            <vue-json-pretty
              :data="tool.parameters"
              :show-line="true"
              :show-icon="true"
              :show-length="true"
              :deep="2"
              theme="light"
            />
          </div>
          <div v-if="tool.result" class="detail-section">
            <h4>Result</h4>
            <vue-json-pretty
              :data="tool.result"
              :show-line="true"
              :show-icon="true"
              :show-length="true"
              :deep="2"
              theme="light"
            />
          </div>
          <div v-if="tool.error" class="detail-section error-section">
            <h4>Error</h4>
            <pre class="error-content">{{ tool.error }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import VueJsonPretty from 'vue-json-pretty'
import 'vue-json-pretty/lib/styles.css'
import type { ToolExecution } from '@/types'

interface Props {
  tools?: ToolExecution[]
}

const props = withDefaults(defineProps<Props>(), {
  tools: () => []
})

const expandedToolIds = ref<Set<string>>(new Set())

function toggleExpanded(toolId: string) {
  if (expandedToolIds.value.has(toolId)) {
    expandedToolIds.value.delete(toolId)
  } else {
    expandedToolIds.value.add(toolId)
  }
}

function isExpanded(toolId: string): boolean {
  return expandedToolIds.value.has(toolId)
}

function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`
  }
  return `${(ms / 1000).toFixed(2)}s`
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
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.tools-list {
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex: 1;
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
  margin: 0;
}

.count-badge {
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  padding: var(--space-xxs) var(--space-sm);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.empty-state {
  padding: var(--space-2xl);
  text-align: center;
  color: var(--color-text-secondary);
}

.empty-state .hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin-top: var(--space-sm);
}


.tool-item {
  border-bottom: 1px solid var(--color-border);
  transition: background-color var(--duration-fast) var(--easing-standard);
}

.tool-item:last-child {
  border-bottom: none;
}

.tool-item.has-error {
  background: var(--color-error-light);
  border-left: 3px solid var(--color-error);
}

.tool-header {
  padding: var(--space-md) var(--space-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.tool-header:hover {
  background: var(--color-bg-secondary);
}

.tool-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  flex: 1;
}

.tool-name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-family: var(--font-family-mono);
}

.tool-timestamp {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.tool-badges {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.error-badge {
  background: var(--color-error);
  color: var(--color-bg-primary);
  padding: var(--space-xxs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
}

.duration-badge {
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  padding: var(--space-xxs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-family: var(--font-family-mono);
}

.expand-icon {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  width: 16px;
  text-align: center;
}

.tool-details {
  padding: 0 var(--space-lg) var(--space-lg) var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.detail-section {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  border: 1px solid var(--color-border);
}

.detail-section h4 {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-sm) 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-section.error-section {
  background: var(--color-error-light);
  border-color: var(--color-error);
}

/* vue-json-pretty design token overrides */
.detail-section :deep(.vjs-tree) {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.detail-section :deep(.vjs-key) {
  color: var(--color-text-primary);
}

.detail-section :deep(.vjs-value__string) {
  color: var(--color-success);
}

.detail-section :deep(.vjs-value__number) {
  color: var(--color-info);
}

.detail-section :deep(.vjs-value__boolean) {
  color: var(--color-info);
}

.detail-section :deep(.vjs-value__null),
.detail-section :deep(.vjs-value__undefined) {
  color: var(--color-text-tertiary);
}

.detail-section :deep(.vjs-tree-node:hover) {
  background-color: var(--color-bg-secondary);
}

.detail-section :deep(.vjs-tree__brackets) {
  color: var(--color-text-secondary);
}

.error-content {
  margin: 0;
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  line-height: 1.5;
  color: var(--color-error);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Scrollbar styling for panel */
.panel::-webkit-scrollbar {
  width: 8px;
}

.panel::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
}

.panel::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-sm);
}

.panel::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

@media (max-width: 968px) {
  .tool-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }

  .tool-badges {
    width: 100%;
    justify-content: space-between;
  }
}
</style>

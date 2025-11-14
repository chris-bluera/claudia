<script setup lang="ts">
interface StatusLineSetting {
  type: 'command' | 'text'
  command?: string
  text?: string
  padding?: number
}

interface Props {
  value: StatusLineSetting
}

defineProps<Props>()
</script>

<template>
  <div class="status-line-display">
    <div class="setting-row">
      <span class="label">Type:</span>
      <span class="badge">{{ value.type }}</span>
    </div>

    <div v-if="value.type === 'command' && value.command" class="setting-row">
      <span class="label">Command:</span>
      <code class="code-block">{{ value.command }}</code>
    </div>

    <div v-if="value.type === 'text' && value.text" class="setting-row">
      <span class="label">Text:</span>
      <span class="value">{{ value.text }}</span>
    </div>

    <div v-if="value.padding !== undefined" class="setting-row">
      <span class="label">Padding:</span>
      <span class="value">{{ value.padding }}</span>
    </div>
  </div>
</template>

<style scoped>
.status-line-display {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.setting-row {
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

.code-block {
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
}

.value {
  color: var(--text-primary);
}
</style>

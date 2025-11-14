<template>
  <div class="panel">
    <div class="panel-header">
      <h2>Settings</h2>
    </div>

    <div v-if="!settings" class="empty-state">
      <p>No settings loaded</p>
    </div>

    <div v-else class="settings-content">
      <div class="sources-section">
        <div class="section-label">Active Sources</div>
        <div class="sources-list">
          <span
            v-for="source in settings.active_sources"
            :key="source"
            class="source-badge"
          >
            {{ source }}
          </span>
        </div>
      </div>

      <div class="settings-section">
        <div class="section-label">Effective Settings</div>
        <div class="settings-list">
          <div
            v-for="(value, key) in settings.effective"
            :key="key"
            class="setting-item"
          >
            <span class="setting-key">{{ key }}</span>
            <component
              :is="getSettingComponent(key, value)"
              v-if="isComplexSetting(key, value)"
              :value="value"
              class="setting-complex"
            />
            <span v-else class="setting-value">{{ formatSimpleValue(value) }}</span>
          </div>
        </div>
      </div>

      <div v-if="Object.keys(settings.runtime).length > 0" class="settings-section">
        <div class="section-label">Runtime Overrides</div>
        <div class="settings-list">
          <div
            v-for="(value, key) in settings.runtime"
            :key="key"
            class="setting-item runtime"
          >
            <span class="setting-key">{{ key }}</span>
            <component
              :is="getSettingComponent(key, value)"
              v-if="isComplexSetting(key, value)"
              :value="value"
              class="setting-complex"
            />
            <span v-else class="setting-value">{{ formatSimpleValue(value) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SettingsSummary } from '@/types'
import type { Component } from 'vue'
import StatusLineDisplay from './settings/StatusLineDisplay.vue'
import HooksDisplay from './settings/HooksDisplay.vue'
import McpServerDisplay from './settings/McpServerDisplay.vue'

defineProps<{
  settings: SettingsSummary | null
}>()

function isComplexSetting(key: string, value: unknown): boolean {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  // Check for known complex setting types
  return key === 'statusLine' || key === 'hooks' || key === 'mcpServers'
}

function getSettingComponent(key: string, value: unknown): Component | null {
  if (key === 'statusLine') {
    return StatusLineDisplay
  }
  if (key === 'hooks') {
    return HooksDisplay
  }
  if (key === 'mcpServers') {
    return McpServerDisplay
  }
  return null
}

function formatSimpleValue(value: unknown): string {
  if (value === null || value === undefined) {
    return ''
  }
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false'
  }
  return String(value)
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

.empty-state {
  padding: var(--space-2xl);
  text-align: center;
  color: var(--color-text-secondary);
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md);
}

.sources-section,
.settings-section {
  margin-bottom: var(--space-lg);
}

.sources-section:last-child,
.settings-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-sm);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sources-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.source-badge {
  background: var(--color-accent-light);
  color: var(--color-accent);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-base);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-transform: capitalize;
}

.settings-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-xxs);
  padding: var(--space-sm);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-base);
  border: 1px solid transparent;
}

.setting-item.runtime {
  border-color: var(--color-warning);
  background: var(--color-warning-light);
}

.setting-key {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  font-family: var(--font-family-mono);
}

.setting-value {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-family: var(--font-family-mono);
  word-break: break-all;
  white-space: pre-wrap;
}

.setting-complex {
  width: 100%;
  margin-top: var(--space-xs);
}
</style>

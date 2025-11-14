<script setup lang="ts">
import CollapsibleCard from './CollapsibleCard.vue'

interface Hook {
  type: 'command' | 'prompt'
  command?: string
  prompt?: string
  timeout?: number
}

interface HookMatcher {
  matcher?: string
  hooks: Hook[]
}

interface HooksSetting {
  [hookType: string]: HookMatcher[]
}

interface Props {
  value: HooksSetting
}

defineProps<Props>()

function getHookIcon(hookType: string): string {
  const icons: Record<string, string> = {
    'PreToolUse': '⚡',
    'PostToolUse': '✓',
    'SessionStart': '🚀',
    'SessionEnd': '🏁',
    'UserPromptSubmit': '💬',
    'Notification': '🔔',
    'Stop': '🛑',
    'SubagentStop': '⏸️',
    'PreCompact': '📦'
  }
  return icons[hookType] || '🔗'
}

function getHookTypeColor(hookType: string): string {
  const colors: Record<string, string> = {
    'PreToolUse': '#3b82f6',
    'PostToolUse': '#10b981',
    'SessionStart': '#8b5cf6',
    'SessionEnd': '#ef4444',
    'UserPromptSubmit': '#f59e0b',
    'Notification': '#06b6d4',
    'Stop': '#dc2626',
    'SubagentStop': '#f97316',
    'PreCompact': '#6366f1'
  }
  return colors[hookType] || 'var(--accent-color)'
}
</script>

<template>
  <div class="hooks-display">
    <CollapsibleCard
      v-for="(matchers, hookType) in value"
      :key="hookType"
      :title="hookType"
      :icon="getHookIcon(hookType)"
      :default-expanded="false"
    >
      <div class="hook-type-content">
        <div
          v-for="(matcher, matcherIdx) in matchers"
          :key="matcherIdx"
          class="matcher-group"
        >
          <div v-if="matcher.matcher" class="matcher-info">
            <span class="matcher-label">Matcher:</span>
            <code class="matcher-pattern">{{ matcher.matcher }}</code>
          </div>

          <div class="hooks-list">
            <div
              v-for="(hook, hookIdx) in matcher.hooks"
              :key="hookIdx"
              class="hook-item"
            >
              <div class="hook-header">
                <span class="hook-type-badge" :style="{ background: getHookTypeColor(hookType) }">
                  {{ hook.type }}
                </span>
                <span v-if="hook.timeout" class="hook-timeout">
                  ⏱️ {{ hook.timeout }}s
                </span>
              </div>

              <code v-if="hook.command" class="hook-command">{{ hook.command }}</code>
              <div v-if="hook.prompt" class="hook-prompt">{{ hook.prompt }}</div>
            </div>
          </div>
        </div>
      </div>
    </CollapsibleCard>
  </div>
</template>

<style scoped>
.hooks-display {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.hook-type-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.matcher-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.matcher-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-2xs);
}

.matcher-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
}

.matcher-pattern {
  background: var(--bg-tertiary);
  padding: var(--spacing-2xs) var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  border: 1px solid var(--border-color);
}

.hooks-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding-left: var(--spacing-sm);
  border-left: 2px solid var(--border-color);
}

.hook-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2xs);
  padding: var(--spacing-xs);
  background: var(--bg-tertiary);
  border-radius: var(--border-radius-sm);
  border: 1px solid var(--border-color);
}

.hook-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.hook-type-badge {
  display: inline-block;
  padding: var(--spacing-2xs) var(--spacing-xs);
  color: white;
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-transform: lowercase;
}

.hook-timeout {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.hook-command {
  background: var(--bg-primary);
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

.hook-prompt {
  background: var(--bg-primary);
  padding: var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  font-style: italic;
}
</style>

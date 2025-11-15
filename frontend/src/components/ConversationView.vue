<template>
  <div class="panel">
    <div class="panel-header">
      <h2>Conversation</h2>
      <span class="count-badge">{{ props.conversation.length }} entries</span>
    </div>

    <div v-if="props.conversation.length === 0" class="empty-state">
      <p>No conversation data for this session</p>
      <p class="hint">Prompts and responses will appear here</p>
    </div>

    <div v-else class="conversation-timeline">
      <div
        v-for="entry in props.conversation"
        :key="entry.id"
        :class="['entry', `entry-${entry.type}`]"
      >
        <div class="entry-icon">{{ getIcon(entry.type) }}</div>
        <div class="entry-content">
          <div class="entry-header">
            <span class="entry-label">{{ getLabel(entry) }}</span>
            <span v-if="entry.turn !== undefined" class="turn-badge">
              Turn {{ entry.turn }}
            </span>
            <span v-if="entry.has_embedding" class="embedding-badge">
              Embedded
            </span>
          </div>
          <div class="entry-text">{{ entry.text }}</div>
          <div class="entry-meta">{{ formatTimestamp(entry.timestamp) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConversationEntry } from '@/types'

interface Props {
  conversation?: ConversationEntry[]
}

const props = withDefaults(defineProps<Props>(), {
  conversation: () => []
})

function getIcon(type: 'prompt' | 'message'): string {
  return type === 'prompt' ? '👤' : '🤖'
}

function getLabel(entry: ConversationEntry): string {
  if (entry.type === 'prompt') {
    return 'User Prompt'
  }
  return 'Assistant Response'
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

.conversation-timeline {
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  max-height: 600px;
  overflow-y: auto;
}

.entry {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  transition: background-color var(--duration-fast) var(--easing-standard);
}

.entry:hover {
  background: var(--color-bg-secondary);
}

.entry-prompt {
  border-left: 3px solid var(--color-accent);
}

.entry-message {
  border-left: 3px solid var(--color-success);
}

.entry-icon {
  font-size: var(--font-size-2xl);
  line-height: 1;
  flex-shrink: 0;
}

.entry-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.entry-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.entry-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.turn-badge {
  background: var(--color-bg-secondary);
  color: var(--color-text-tertiary);
  padding: var(--space-xxs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.embedding-badge {
  background: var(--color-success-light);
  color: var(--color-success);
  padding: var(--space-xxs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
}

.entry-text {
  font-size: var(--font-size-base);
  line-height: 1.6;
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.entry-meta {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

/* Scrollbar styling */
.conversation-timeline::-webkit-scrollbar {
  width: 8px;
}

.conversation-timeline::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
}

.conversation-timeline::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-sm);
}

.conversation-timeline::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

@media (max-width: 968px) {
  .entry {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .entry-icon {
    font-size: var(--font-size-xl);
  }

  .conversation-timeline {
    max-height: 400px;
  }
}
</style>

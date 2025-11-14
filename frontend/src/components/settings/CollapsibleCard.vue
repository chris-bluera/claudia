<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  title: string
  defaultExpanded?: boolean
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultExpanded: false,
  icon: ''
})

const isExpanded = ref(props.defaultExpanded)

function toggle() {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div class="collapsible-card">
    <div class="card-header" @click="toggle">
      <span class="expand-icon">{{ isExpanded ? '▼' : '▶' }}</span>
      <span v-if="icon" class="header-icon">{{ icon }}</span>
      <span class="header-title">{{ title }}</span>
    </div>
    <div v-if="isExpanded" class="card-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.collapsible-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-sm);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease;
}

.card-header:hover {
  background: var(--bg-hover);
}

.expand-icon {
  color: var(--text-secondary);
  font-size: 0.75rem;
  width: 1rem;
  display: inline-block;
}

.header-icon {
  font-size: 1rem;
}

.header-title {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.card-content {
  padding: var(--spacing-sm);
  padding-top: 0;
  border-top: 1px solid var(--border-color);
  margin-top: var(--spacing-xs);
}
</style>

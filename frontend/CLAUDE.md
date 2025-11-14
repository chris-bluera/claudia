# Claudia Frontend - Development Context

Frontend-specific conventions and patterns for the Claudia Vue.js application.

## Core Philosophy

**This app is expected to work.** Unexpected conditions are errors—handle them clearly, don't hide them.

**No fallbacks unless explicitly stated.** Don't create automatic fallback code, polling fallbacks, or degraded modes. If WebSocket fails, show error state—don't silently switch to polling. Claude models tend to add fallbacks automatically; resist this.

**Frontend is more lenient for UX:** Show error states clearly instead of crashing, but don't pretend things work when they don't.

## Error Handling Standards

### Principle: Show errors clearly, don't hide them with fallbacks

**Error handling in frontend:**
- If something fails, show error state clearly
- Allow user to retry or reload
- Don't silently switch to fallback behavior
- User should know when things aren't working as expected

**Examples:**

```typescript
// ✅ CORRECT - Show error clearly
try {
  const sessions = await api.getActiveSessions()
  this.sessions = sessions
} catch (error) {
  console.error('Failed to load sessions:', error)
  this.error = 'Unable to load sessions. Please refresh.'
  // Shows error UI, user can retry
}

// ✅ CORRECT - Clear when feature unavailable
if (!websocket.connected) {
  // Show "Real-time updates unavailable - Reconnect" button
  // Don't automatically fall back to polling
}

// ❌ WRONG - Silent fallback
if (!websocket.connected) {
  // Silently start polling instead
  startPolling()  // User doesn't know WebSocket failed!
}

// ❌ WRONG - Silent failure
try {
  await api.saveSettings(settings)
} catch (error) {
  // Do nothing - user thinks it saved!
}
```

### Error UI Patterns

- **Toast notifications** for transient errors
- **Error states** in components with retry buttons
- **Clear messages** when features unavailable
- **Loading states** to prevent perceived errors
- **NO automatic fallbacks** to alternative implementations

## TypeScript Conventions

### Type Safety

- **Use `unknown` instead of `any`** for better type safety
- Properly type all API responses
- Use strict TypeScript configuration

```typescript
// ✅ CORRECT
function handleData(data: unknown) {
  if (isValidSession(data)) {
    processSession(data)
  }
}

// ❌ WRONG
function handleData(data: any) {
  processSession(data)  // No type checking
}
```

## Vue.js & Pinia Conventions

### Component Structure

- Use `<script setup>` for composition API
- Co-locate types with components
- Use design tokens for all styling (no hardcoded values)

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Session } from '@/types'

interface Props {
  session: Session
}

const props = defineProps<Props>()
const isActive = computed(() => props.session.is_active)
</script>

<template>
  <div class="session-card">
    <h3>{{ session.project_name }}</h3>
    <span v-if="isActive" class="status-active">Active</span>
  </div>
</template>

<style scoped>
.session-card {
  background: var(--card-background);
  padding: var(--spacing-md);
  border-radius: var(--border-radius-md);
}

.status-active {
  color: var(--color-success);
}
</style>
```

### Pinia Store Patterns

```typescript
// stores/sessions.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Session } from '@/types'

export const useSessionsStore = defineStore('sessions', () => {
  // State
  const sessions = ref<Session[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const activeSessions = computed(() =>
    sessions.value.filter(s => s.is_active)
  )

  // Actions
  async function fetchSessions() {
    loading.value = true
    error.value = null
    try {
      const response = await api.getActiveSessions()
      sessions.value = response.sessions
    } catch (err) {
      error.value = 'Failed to load sessions'
      console.error('Error fetching sessions:', err)
      // Error shown in UI, user can retry
    } finally {
      loading.value = false
    }
  }

  return {
    sessions,
    loading,
    error,
    activeSessions,
    fetchSessions
  }
})
```

## Design Token System

### Never Hardcode Styles

All visual properties use CSS design tokens defined in `src/assets/tokens.css`.

**Categories:**
- Colors: `--color-*`
- Spacing: `--spacing-*`
- Typography: `--font-*`, `--text-*`
- Borders: `--border-*`
- Shadows: `--shadow-*`

```vue
<!-- ✅ CORRECT - Use design tokens -->
<style scoped>
.card {
  background: var(--card-background);
  padding: var(--spacing-md);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-sm);
}
</style>

<!-- ❌ WRONG - Hardcoded values -->
<style scoped>
.card {
  background: #ffffff;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
```

## WebSocket Integration

### Real-time Updates

```typescript
// stores/websocket.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWebSocketStore = defineStore('websocket', () => {
  const connected = ref(false)
  const error = ref<string | null>(null)
  const ws = ref<WebSocket | null>(null)

  function connect() {
    ws.value = new WebSocket('ws://localhost:8000/api/monitoring/ws')

    ws.value.onopen = () => {
      connected.value = true
      error.value = null
      console.log('WebSocket connected')
    }

    ws.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleMessage(message)
    }

    ws.value.onerror = (err) => {
      console.error('WebSocket error:', err)
      error.value = 'WebSocket connection failed'
      // Show error in UI, user can retry
      // Do NOT automatically fall back to polling
    }

    ws.value.onclose = () => {
      connected.value = false
      console.log('WebSocket disconnected')
      // Show disconnected state in UI
      // Do NOT automatically reconnect or fall back
    }
  }

  function handleMessage(message: WebSocketMessage) {
    const sessionsStore = useSessionsStore()

    switch (message.type) {
      case 'session_start':
        sessionsStore.addSession(message.data)
        break
      case 'tool_execution':
        sessionsStore.updateToolExecution(message.data)
        break
    }
  }

  return { connected, error, connect }
})
```

## Technology Stack

### Core Technologies

- **Vue 3** - Composition API with `<script setup>`
- **TypeScript** - Strict type checking
- **Pinia** - State management
- **Vue Router** - Client-side routing
- **Vite** - Build tool and dev server

### UI Libraries

- Custom components using design tokens
- No UI framework dependencies (building custom for lightweight and control)

## Project Structure

```
frontend/
├── src/
│   ├── main.ts              # App entry point
│   ├── App.vue              # Root component
│   ├── assets/
│   │   └── tokens.css       # Design tokens
│   ├── components/
│   │   ├── SessionsPanel.vue
│   │   ├── ActivityFeed.vue
│   │   └── SettingsPanel.vue
│   ├── stores/
│   │   ├── sessions.ts      # Session state management
│   │   └── websocket.ts     # WebSocket connection
│   ├── types/
│   │   └── index.ts         # TypeScript type definitions
│   └── router/
│       └── index.ts         # Vue Router configuration
├── public/                  # Static assets
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript configuration
└── CLAUDE.md               # This file
```

## Development Workflow

### Starting the Frontend

```bash
cd frontend
npm run dev
```

### Building for Production

```bash
npm run build
npm run preview  # Preview production build
```

### Type Checking

```bash
npm run type-check
```

## Common Patterns

### Loading States

```vue
<template>
  <div v-if="loading" class="loading">
    Loading sessions...
  </div>
  <div v-else-if="error" class="error">
    {{ error }}
    <button @click="retry">Retry</button>
  </div>
  <div v-else>
    <!-- Content -->
  </div>
</template>
```

### Error States

```vue
<template>
  <div v-if="!websocket.connected" class="warning">
    Real-time updates unavailable
    <button @click="websocket.connect">Reconnect</button>
  </div>
</template>
```

### NO Automatic Fallbacks

```typescript
// ❌ WRONG - Don't do this
if (!websocket.connected) {
  // Automatically start polling
  setInterval(fetchSessions, 5000)
}

// ✅ CORRECT - Show error state
if (!websocket.connected) {
  showError('Real-time updates unavailable')
  // User decides whether to reconnect
}
```

## Common Issues & Solutions

### TypeScript Errors with Unknown Types

**Symptom:** `Type 'unknown' is not assignable to type 'X'`

**Solution:** Use type guards

```typescript
function isSession(data: unknown): data is Session {
  return (
    typeof data === 'object' &&
    data !== null &&
    'session_id' in data &&
    typeof data.session_id === 'string'
  )
}
```

### Design Token Not Working

**Symptom:** CSS variable shows as literal string

**Solution:** Ensure `tokens.css` is imported in `main.ts`

```typescript
import './assets/tokens.css'
```

<template>
  <div class="terminal-page">
    <div class="terminal-header">
      <h1>Terminal Test</h1>
      <div class="status">
        <span :class="['status-indicator', wsConnected ? 'connected' : 'disconnected']"></span>
        <span>{{ wsConnected ? 'Connected' : 'Disconnected' }}</span>
      </div>
    </div>
    <div ref="terminalContainer" class="terminal-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const terminalContainer = ref<HTMLElement | null>(null)
const wsConnected = ref(false)

let terminal: Terminal | null = null
let ws: WebSocket | null = null
let fitAddon: FitAddon | null = null

onMounted(() => {
  if (!terminalContainer.value) return

  // Create terminal instance
  terminal = new Terminal({
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    fontSize: 14,
    cursorBlink: true,
    cursorStyle: 'block',
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#d4d4d4',
      selection: '#264f78'
    }
  })

  // Add fit addon for auto-sizing
  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)

  // Attach to DOM
  terminal.open(terminalContainer.value)
  fitAddon.fit()

  // Connect to WebSocket
  const wsUrl = `ws://localhost:8000/ws/terminal`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    wsConnected.value = true
    terminal?.write('\r\n\x1b[32m[Connected to shell]\x1b[0m\r\n\r\n')
  }

  ws.onmessage = (event) => {
    terminal?.write(event.data)
  }

  ws.onclose = () => {
    wsConnected.value = false
    terminal?.write('\r\n\r\n\x1b[31m[Connection closed]\x1b[0m\r\n')
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    terminal?.write('\r\n\x1b[31m[Connection error]\x1b[0m\r\n')
  }

  // Send user input to WebSocket
  terminal.onData((data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(data)
    }
  })

  // Handle window resize
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close()
  }

  if (terminal) {
    terminal.dispose()
  }
})

function handleResize() {
  if (fitAddon) {
    fitAddon.fit()
  }
}
</script>

<style scoped>
.terminal-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg-primary);
}

.terminal-header {
  padding: var(--space-md) var(--space-lg);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.terminal-header h1 {
  font-size: var(--font-size-xl);
  margin: 0;
}

.status {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--font-size-sm);
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.connected {
  background: var(--color-success);
  box-shadow: 0 0 8px rgba(0, 170, 0, 0.6);
}

.status-indicator.disconnected {
  background: var(--color-text-tertiary);
}

.terminal-container {
  flex: 1;
  padding: var(--space-md);
  overflow: hidden;
}

/* Override xterm.js default background */
.terminal-container :deep(.xterm) {
  height: 100%;
}

.terminal-container :deep(.xterm-viewport) {
  background-color: #1e1e1e !important;
}
</style>

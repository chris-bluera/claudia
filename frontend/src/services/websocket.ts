/**
 * WebSocket client for real-time updates from Claudia backend
 */
import type { WebSocketEvent } from '@/types'

type EventCallback = (event: WebSocketEvent) => void

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/monitoring/ws'
const RECONNECT_DELAY = 3000

export class WebSocketClient {
  private ws: WebSocket | null = null
  private callbacks: Set<EventCallback> = new Set()
  private reconnectTimer: number | null = null
  private url: string
  private shouldReconnect = true

  constructor(url: string = WS_URL) {
    this.url = url
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          // Broadcast to all callbacks
          this.callbacks.forEach(callback => {
            try {
              callback(data as WebSocketEvent)
            } catch (error) {
              console.error('Error in WebSocket callback:', error)
            }
          })
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')

        if (this.shouldReconnect) {
          this.scheduleReconnect()
        }
      }
    } catch (error) {
      console.error('Error creating WebSocket:', error)
      if (this.shouldReconnect) {
        this.scheduleReconnect()
      }
    }
  }

  disconnect(): void {
    this.shouldReconnect = false

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  on(callback: EventCallback): () => void {
    this.callbacks.add(callback)

    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback)
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return
    }

    console.log(`Reconnecting in ${RECONNECT_DELAY}ms...`)
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, RECONNECT_DELAY)
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

export const wsClient = new WebSocketClient()

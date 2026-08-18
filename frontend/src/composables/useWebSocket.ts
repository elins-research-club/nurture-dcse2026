import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

export interface WebSocketMessage {
  type: string
  data?: any
  message?: string
}

export function useWebSocket(url: string) {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const lastMessage = ref<any>(null)
  const error = ref<string | null>(null)
  const authStore = useAuthStore()

  let reconnectTimer: any = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 5
  const baseDelay = 1000

  const connect = () => {
    if (!authStore.token) return

    try {
      const wsUrl = new URL(url)
      wsUrl.searchParams.append('token', authStore.token)

      ws.value = new WebSocket(wsUrl.toString())

      ws.value.onopen = () => {
        isConnected.value = true
        error.value = null
        reconnectAttempts = 0
        console.log('WebSocket connected')
      }

      ws.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          lastMessage.value = data
        } catch (e) {
          console.error('Failed to parse WebSocket message', e)
        }
      }

      ws.value.onclose = () => {
        isConnected.value = false
        ws.value = null
        handleReconnect()
      }

      ws.value.onerror = (err) => {
        error.value = 'WebSocket connection error'
        console.error('WebSocket error:', err)
      }
    } catch (err) {
      error.value = 'Failed to create WebSocket connection'
      console.error('Failed to create WebSocket:', err)
    }
  }

  const handleReconnect = () => {
    if (reconnectAttempts < maxReconnectAttempts && authStore.token) {
      const delay = baseDelay * Math.pow(2, reconnectAttempts)
      reconnectAttempts++
      console.log(`Reconnecting in ${delay}ms... (Attempt ${reconnectAttempts})`)
      reconnectTimer = setTimeout(connect, delay)
    } else if (reconnectAttempts >= maxReconnectAttempts) {
      error.value = 'Max reconnection attempts reached'
    }
  }

  const disconnect = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    isConnected.value = false
  }

  const sendMessage = (msg: any) => {
    if (ws.value && isConnected.value) {
      ws.value.send(JSON.stringify(msg))
    } else {
      console.warn('Cannot send message: WebSocket is not connected')
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    disconnect,
    connect
  }
}

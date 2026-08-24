import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

const API_BASE_URL = 'http://localhost:8000/api/v1'
const WS_URL = 'ws://localhost:8000/ws/dashboard'

export const useTelemetryStore = defineStore('telemetry', () => {
  const authStore = useAuthStore()

  // State: NodeId -> 50 latest telemetry feeds (index 0 is newest)
  const telemetryHistory = ref<Record<string, any[]>>({})
  const sensorsCache = ref<Record<string, any[]>>({})
  const isConnected = ref(false)

  let ws: WebSocket | null = null
  let reconnectTimer: any = null

  const connectWebSocket = () => {
    if (ws || !authStore.token) return

    try {
      const url = new URL(WS_URL)
      url.searchParams.append('token', authStore.token)

      ws = new WebSocket(url.toString())

      ws.onopen = () => {
        isConnected.value = true
        console.log('[TelemetryStore] WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg?.event === 'sensor_update' && msg.node_id) {
            const nodeId = msg.node_id
            const current = telemetryHistory.value[nodeId] ? [...telemetryHistory.value[nodeId]] : []
            const previousFeed = current[0] || {}
            
            // Merge multi-channel fields so fields from channel 1 and channel 2 never erase each other
            const newFeed = {
              ...previousFeed,
              ...msg.data,
              created_at: msg.created_at || new Date().toISOString()
            }
            
            current.unshift(newFeed)
            telemetryHistory.value[nodeId] = current.slice(0, 50)
          }
        } catch (e) {
          console.error('[TelemetryStore] Failed to parse message', e)
        }
      }

      ws.onclose = () => {
        isConnected.value = false
        ws = null
        if (authStore.isAuthenticated()) {
          reconnectTimer = setTimeout(connectWebSocket, 3000)
        }
      }

      ws.onerror = (err) => {
        console.error('[TelemetryStore] WebSocket error', err)
      }
    } catch (err) {
      console.error('[TelemetryStore] Failed to init WebSocket', err)
    }
  }

  const disconnectWebSocket = () => {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (ws) {
      ws.close()
      ws = null
    }
    isConnected.value = false
  }

  const fetchSensors = async (nodeId: string) => {
    if (sensorsCache.value[nodeId]) return sensorsCache.value[nodeId]
    try {
      const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/sensors/`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      if (res.ok) {
        const data = await res.json()
        sensorsCache.value[nodeId] = data
        return data
      }
    } catch (e) {
      console.error('[TelemetryStore] Failed to fetch sensors', e)
    }
    return []
  }

  const fetchHistory = async (nodeId: string, force = false) => {
    // If already in store and not forced, return cached instantly
    if (!force && telemetryHistory.value[nodeId]?.length > 0) {
      return telemetryHistory.value[nodeId]
    }

    try {
      const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/telemetry/history?results=50`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      if (res.ok) {
        const data = await res.json()
        if (data.feeds && Array.isArray(data.feeds)) {
          telemetryHistory.value[nodeId] = data.feeds.reverse()
          return telemetryHistory.value[nodeId]
        }
      }
    } catch (e) {
      console.error('[TelemetryStore] Failed to fetch history', e)
    }
    return telemetryHistory.value[nodeId] || []
  }

  const getLatest = (nodeId: string) => {
    return telemetryHistory.value[nodeId]?.[0] ?? null
  }

  const getChartData = (nodeId: string) => {
    return [...(telemetryHistory.value[nodeId] || [])].reverse()
  }

  return {
    telemetryHistory,
    sensorsCache,
    isConnected,
    connectWebSocket,
    disconnectWebSocket,
    fetchSensors,
    fetchHistory,
    getLatest,
    getChartData
  }
})

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

const API_BASE_URL = 'http://localhost:8000/api/v1'
const WS_URL = 'ws://localhost:8000/ws/dashboard'

export interface HistoryOptions {
  range?: '1h' | '1d' | '1w' | '1M'
  start?: string
  end?: string
  results?: number
  average?: number
  force?: boolean
}

export const useTelemetryStore = defineStore('telemetry', () => {
  const authStore = useAuthStore()

  // State: NodeId -> Live telemetry feeds (index 0 is newest, updated by WS)
  const telemetryHistory = ref<Record<string, any[]>>({})
  // State: NodeId -> Static Archive telemetry feeds (oldest first, for historical ranges 1w, 1M, custom)
  const archiveHistory = ref<Record<string, any[]>>({})
  const isArchiveLoading = ref<Record<string, boolean>>({})
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
            // Retain live window stream (up to 500 recent points)
            telemetryHistory.value[nodeId] = current.slice(0, 500)
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
    try {
      const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/sensors/`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      if (res.ok) {
        return await res.json()
      }
    } catch (e) {
      console.error('[TelemetryStore] Failed to fetch sensors from PostgreSQL', e)
    }
    return []
  }

  const fetchHistory = async (nodeId: string, options?: HistoryOptions) => {
    const isLiveWindow = !options?.range || options.range === '1d' || options.range === '1h'
    const isCustom = !!(options?.start || options?.end)
    const force = options?.force ?? false

    // If live window and not forced and already in store, return cached live data
    if (isLiveWindow && !isCustom && !force && telemetryHistory.value[nodeId]?.length > 0) {
      return telemetryHistory.value[nodeId]
    }

    const params = new URLSearchParams()
    if (options?.range) params.append('range', options.range)
    else if (!isCustom) params.append('range', '1d')

    if (options?.start) params.append('start', options.start)
    if (options?.end) params.append('end', options.end)
    if (options?.results) params.append('results', String(options.results))
    if (options?.average) params.append('average', String(options.average))

    if (!isLiveWindow || isCustom) {
      isArchiveLoading.value[nodeId] = true
    }

    try {
      const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/telemetry/history?${params.toString()}`, {
        headers: { Authorization: `Bearer ${authStore.token}` }
      })
      if (res.ok) {
        const data = await res.json()
        if (data.feeds && Array.isArray(data.feeds)) {
          if (isLiveWindow && !isCustom) {
            telemetryHistory.value[nodeId] = [...data.feeds].reverse()
            return telemetryHistory.value[nodeId]
          } else {
            archiveHistory.value[nodeId] = data.feeds
            return archiveHistory.value[nodeId]
          }
        }
      }
    } catch (e) {
      console.error('[TelemetryStore] Failed to fetch history', e)
    } finally {
      if (!isLiveWindow || isCustom) {
        isArchiveLoading.value[nodeId] = false
      }
    }

    return (isLiveWindow && !isCustom) ? (telemetryHistory.value[nodeId] || []) : (archiveHistory.value[nodeId] || [])
  }

  const getLatest = (nodeId: string) => {
    return telemetryHistory.value[nodeId]?.[0] ?? null
  }

  const getChartData = (nodeId: string, isArchive = false) => {
    if (isArchive) {
      return archiveHistory.value[nodeId] || []
    }
    return [...(telemetryHistory.value[nodeId] || [])].reverse()
  }

  return {
    telemetryHistory,
    archiveHistory,
    isArchiveLoading,
    isConnected,
    connectWebSocket,
    disconnectWebSocket,
    fetchSensors,
    fetchHistory,
    getLatest,
    getChartData
  }
})

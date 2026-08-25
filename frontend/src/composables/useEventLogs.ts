import { useQuery } from '@tanstack/vue-query'
import { useAuthStore } from '@/stores/auth'

const API_BASE_URL = '/api/v1'

export interface EventLog {
  id: string
  node_id: string | null
  level: string
  message: string
  created_at: string
}

export function useEventLogs() {
  const authStore = useAuthStore()

  const fetchLogs = async (): Promise<EventLog[]> => {
    const response = await fetch(`${API_BASE_URL}/event-logs/`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (!response.ok) {
      if (response.status === 401) {
        authStore.logout()
      }
      throw new Error('Failed to fetch event logs')
    }

    return response.json()
  }

  const logsQuery = useQuery({
    queryKey: ['eventLogs'],
    queryFn: fetchLogs,
    refetchInterval: 15000 // refetch every 15s
  })

  return {
    logsQuery
  }
}

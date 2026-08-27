import { ref, computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useAuthStore } from '@/stores/auth'

const API_BASE_URL = '/api/v1'

export interface EventLog {
  id: string
  node_id: string | null
  node_name?: string | null
  node_code?: string | null
  level: string
  message: string
  created_at: string
}

export function useEventLogs(options?: {
  page?: Ref<number>
  pageSize?: Ref<number>
  level?: Ref<string | undefined>
}) {
  const authStore = useAuthStore()
  const page = options?.page || ref(1)
  const pageSize = options?.pageSize || ref(25)
  const level = options?.level || ref(undefined)
  const totalCount = ref(0)

  const fetchLogs = async (): Promise<EventLog[]> => {
    const skip = (page.value - 1) * pageSize.value
    const limit = pageSize.value
    const params = new URLSearchParams()
    params.set('skip', String(skip))
    params.set('limit', String(limit))
    if (level.value) {
      params.set('level', level.value)
    }

    const response = await fetch(`${API_BASE_URL}/event-logs/?${params.toString()}`, {
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

    const totalHeader = response.headers.get('X-Total-Count')
    if (totalHeader != null) {
      totalCount.value = parseInt(totalHeader, 10) || 0
    }

    const data: EventLog[] = await response.json()
    if (totalHeader == null) {
      totalCount.value = data.length
    }

    return data
  }

  const logsQuery = useQuery({
    queryKey: ['eventLogs', page, pageSize, level],
    queryFn: fetchLogs,
    refetchInterval: 15000
  })

  const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))

  return {
    logsQuery,
    totalCount,
    totalPages
  }
}

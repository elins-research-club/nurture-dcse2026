import { computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useAuthStore } from '@/stores/auth'
import type { NodeDevice, NodeDeviceWithData } from '@/types'

const API_BASE_URL = 'http://localhost:8000/api/v1'

export function useNodes() {
  const authStore = useAuthStore()
  const queryClient = useQueryClient()

  const fetchNodes = async (): Promise<NodeDeviceWithData[]> => {
    if (!authStore.token) throw new Error('Not authenticated')
    
    const response = await fetch(`${API_BASE_URL}/nodes/`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (!response.ok) {
      if (response.status === 401) {
        authStore.logout()
        throw new Error('Session expired')
      }
      throw new Error('Failed to fetch nodes')
    }
    
    return response.json()
  }

  const nodesQuery = useQuery({
    queryKey: ['nodes'],
    queryFn: fetchNodes,
    enabled: computed(() => !!authStore.token),
    refetchInterval: 30000 // Refetch every 30s as fallback to WS
  })

  const addNodeMutation = useMutation({
    mutationFn: async (newNode: Partial<NodeDevice>) => {
      if (!authStore.token) throw new Error('Not authenticated')
      
      const response = await fetch(`${API_BASE_URL}/nodes/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify(newNode)
      })
      
      if (!response.ok) {
        if (response.status === 401) {
          authStore.logout()
          throw new Error('Session expired')
        }
        throw new Error('Failed to add node')
      }
      
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
    }
  })

  const updateNodeMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<NodeDevice> }) => {
      if (!authStore.token) throw new Error('Not authenticated')
      
      const response = await fetch(`${API_BASE_URL}/nodes/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify(data)
      })
      
      if (!response.ok) {
        if (response.status === 401) authStore.logout()
        throw new Error('Failed to update node')
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
    }
  })

  const deleteNodeMutation = useMutation({
    mutationFn: async (id: string) => {
      if (!authStore.token) throw new Error('Not authenticated')
      
      const response = await fetch(`${API_BASE_URL}/nodes/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        if (response.status === 401) authStore.logout()
        throw new Error('Failed to delete node')
      }
      return true
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] })
    }
  })

  return {
    nodesQuery,
    addNodeMutation,
    updateNodeMutation,
    deleteNodeMutation,
    queryClient
  }
}

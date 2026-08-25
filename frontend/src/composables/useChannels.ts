import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useAuthStore } from '@/stores/auth'
import type { ThingspeakChannel } from '@/types'
import { unref, type MaybeRef } from 'vue'

const API_BASE_URL = '/api/v1'

export function useChannels(nodeIdRef: MaybeRef<string>) {
  const authStore = useAuthStore()
  const queryClient = useQueryClient()

  const fetchChannels = async (): Promise<ThingspeakChannel[]> => {
    const nodeId = unref(nodeIdRef)
    if (!authStore.token) throw new Error('Not authenticated')
    if (!nodeId) return []
    
    const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/channels/`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (!response.ok) {
      if (response.status === 401) authStore.logout()
      throw new Error('Failed to fetch channels')
    }
    
    return response.json()
  }

  const channelsQuery = useQuery({
    queryKey: ['channels', () => unref(nodeIdRef)],
    queryFn: fetchChannels,
    enabled: () => !!unref(nodeIdRef) && !!authStore.token
  })

  const addChannelMutation = useMutation({
    mutationFn: async (channelData: { channel_id: string; read_api_key: string; write_api_key: string; label?: string }) => {
      const nodeId = unref(nodeIdRef)
      if (!authStore.token) throw new Error('Not authenticated')
      
      const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/channels/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify(channelData)
      })
      
      if (!response.ok) {
        if (response.status === 401) authStore.logout()
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to add channel')
      }
      
      return response.json()
    },
    onSuccess: () => {
      const nodeId = unref(nodeIdRef)
      queryClient.invalidateQueries({ queryKey: ['channels', nodeId] })
    }
  })

  const deleteChannelMutation = useMutation({
    mutationFn: async (channelUuid: string) => {
      const nodeId = unref(nodeIdRef)
      if (!authStore.token) throw new Error('Not authenticated')
      
      const response = await fetch(`${API_BASE_URL}/nodes/${nodeId}/channels/${channelUuid}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        if (response.status === 401) authStore.logout()
        throw new Error('Failed to delete channel')
      }
      
      return true
    },
    onSuccess: () => {
      const nodeId = unref(nodeIdRef)
      queryClient.invalidateQueries({ queryKey: ['channels', nodeId] })
    }
  })

  return {
    channelsQuery,
    addChannelMutation,
    deleteChannelMutation
  }
}

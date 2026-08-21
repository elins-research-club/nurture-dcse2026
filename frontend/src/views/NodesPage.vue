<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import AddNodeDialog from '@/components/dashboard/AddNodeDialog.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useNodes } from '@/composables/useNodes'
import { useWebSocket } from '@/composables/useWebSocket'
import type { NodeDeviceWithData } from '@/types'

const router = useRouter()
const { nodesQuery } = useNodes()

const wsUrl = 'ws://localhost:8000/ws/dashboard'
const { lastMessage } = useWebSocket(wsUrl)

const nodesList = ref<NodeDeviceWithData[]>([])

watch(() => nodesQuery.data.value, (newData) => {
  if (newData) {
    nodesList.value = [...newData]
  }
}, { immediate: true })

// Handle real-time WebSocket updates
watch(lastMessage, (msg) => {
  if (!msg || msg.event !== 'sensor_update') return
  
  const nodeIndex = nodesList.value.findIndex(n => n.node_id === msg.node_id)
  if (nodeIndex !== -1) {
    const node = nodesList.value[nodeIndex]
    node.last_seen = msg.created_at || new Date().toISOString()
    nodesList.value[nodeIndex] = { ...node }
  }
})

const isNodeActive = (lastSeen: string | undefined) => {
  if (!lastSeen) return false
  const diffMinutes = (new Date().getTime() - new Date(lastSeen).getTime()) / (1000 * 60)
  return diffMinutes < 15
}

const goToNodeDetail = (id: number) => {
  router.push(`/nodes/${id}`)
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-3xl font-bold tracking-tight">Nodes</h2>
        </div>
        
        <AddNodeDialog>
          <template #trigger>
            <Button>Add New Node</Button>
          </template>
        </AddNodeDialog>
      </div>

      <!-- Loading State -->
      <div v-if="nodesQuery.isLoading.value" class="py-12 text-center text-muted-foreground">
        Loading nodes...
      </div>
      
      <!-- Error State -->
      <div v-else-if="nodesQuery.isError.value" class="py-12 text-center text-destructive">
        Failed to load data. Please check connection.
      </div>

      <!-- Empty State -->
      <div v-else-if="nodesList.length === 0" class="py-16 text-center border border-dashed rounded-xl bg-card/30">
        <div class="mx-auto flex max-w-[420px] flex-col items-center justify-center text-center">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" class="h-10 w-10 text-muted-foreground mb-4" viewBox="0 0 24 24">
            <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
            <path d="M3 9h18M9 21V9"/>
          </svg>
          <h3 class="mt-4 text-lg font-semibold">No nodes added</h3>
          <p class="mb-4 mt-2 text-sm text-muted-foreground">
            You have not added any nodes. Add one below to start monitoring your field data.
          </p>
          <AddNodeDialog>
            <template #trigger>
              <Button>Add New Node</Button>
            </template>
          </AddNodeDialog>
        </div>
      </div>
      
      <!-- Grid View -->
      <div v-else class="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        <Card v-for="node in nodesList" :key="node.id" class="cursor-pointer hover:border-primary/50 transition-colors" @click="goToNodeDetail(node.id)">
          <CardHeader class="pb-2">
            <div class="flex justify-between items-start">
              <div>
                <CardTitle class="text-lg">{{ node.name }}</CardTitle>
                <CardDescription class="mt-1 font-mono text-xs">{{ node.node_id }}</CardDescription>
              </div>
              <StatusBadge :is-active="isNodeActive(node.last_seen)" :last-seen="node.last_seen" />
            </div>
          </CardHeader>
          <CardContent>
            <div class="text-sm text-muted-foreground mt-4">
              <p><strong>Location:</strong> {{ node.location || 'Not specified' }}</p>
              <p><strong>Last Seen:</strong> {{ node.last_seen ? new Date(node.last_seen).toLocaleString() : 'Never' }}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </DashboardLayout>
</template>

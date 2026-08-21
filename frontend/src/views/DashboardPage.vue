<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import NodeDashboard from '@/components/dashboard/NodeDashboard.vue'
import { useNodes } from '@/composables/useNodes'
import { useWebSocket } from '@/composables/useWebSocket'
import type { NodeDeviceWithData } from '@/types'

const { nodesQuery } = useNodes()
const wsUrl = 'ws://localhost:8000/ws/dashboard'
const { lastMessage } = useWebSocket(wsUrl)

const nodes = ref<NodeDeviceWithData[]>([])
const selectedNodeId = ref<number | null>(null)

// When API data loads, update local state
watch(() => nodesQuery.data.value, (newData) => {
  if (newData) {
    nodes.value = [...newData]
    if (!selectedNodeId.value && nodes.value.length > 0) {
      selectedNodeId.value = nodes.value[0].id
    }
  }
}, { immediate: true })

// Handle real-time WebSocket updates to update last_seen dots
watch(lastMessage, (msg) => {
  if (!msg || msg.event !== 'sensor_update') return
  
  const nodeIndex = nodes.value.findIndex(n => n.node_id === msg.node_id)
  if (nodeIndex !== -1) {
    const node = nodes.value[nodeIndex]
    node.last_seen = msg.created_at || new Date().toISOString()
    nodes.value[nodeIndex] = { ...node }
  }
})

const isNodeActive = (lastSeen: string | undefined) => {
  if (!lastSeen) return false
  const diffMinutes = (new Date().getTime() - new Date(lastSeen).getTime()) / (1000 * 60)
  return diffMinutes < 15
}

const getActiveNodeData = () => {
  return nodes.value.find(n => n.id === selectedNodeId.value)
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold tracking-tight">Dashboard</h2>
        </div>
      </div>
      
      <!-- Loading State -->
      <div v-if="nodesQuery.isLoading.value" class="py-12 text-center text-muted-foreground">
        Loading nodes data...
      </div>
      
      <!-- Error State -->
      <div v-else-if="nodesQuery.isError.value" class="py-12 text-center text-destructive">
        Failed to load data. Please check connection.
      </div>
      
      <!-- No Data State -->
      <div v-else-if="!nodes.length" class="py-12 text-center text-muted-foreground border border-dashed rounded-xl">
        No nodes found. Add a node to get started.
      </div>
      
      <template v-else>
        <!-- Node Selector & Summary -->
        <div class="flex gap-2 pb-1 overflow-x-auto">
          <button
            v-for="node in nodes"
            :key="node.id"
            @click="selectedNodeId = node.id"
            :class="[
              'px-4 py-2 rounded-lg border text-sm font-semibold transition-all duration-300 whitespace-nowrap flex items-center gap-2',
              selectedNodeId === node.id 
                ? 'bg-primary text-primary-foreground border-primary shadow-md scale-105' 
                : 'bg-card/50 backdrop-blur-sm text-card-foreground hover:bg-card/80 hover:border-border/80'
            ]"
          >
            {{ node.name }}
            <div 
              :class="['w-1.5 h-1.5 rounded-full', isNodeActive(node.last_seen) ? 'bg-green-500' : 'bg-red-500']" 
            />
          </button>
        </div>
        
        <div v-if="getActiveNodeData()" class="mt-2">
          <NodeDashboard :node-id="getActiveNodeData()!.node_id" :node-name="getActiveNodeData()!.name" />
        </div>
      </template>
    </div>
  </DashboardLayout>
</template>

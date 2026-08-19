<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import SensorCard from '@/components/dashboard/SensorCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import SensorLineChart from '@/components/charts/SensorLineChart.vue'
import { useNodes } from '@/composables/useNodes'
import { useWebSocket } from '@/composables/useWebSocket'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import type { NodeDeviceWithData } from '@/types'

const { nodesQuery } = useNodes()
const wsUrl = 'ws://localhost:8000/ws/dashboard'
const { lastMessage, isConnected } = useWebSocket(wsUrl)

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

// Handle real-time WebSocket updates
watch(lastMessage, (msg) => {
  if (!msg || msg.type !== 'telemetry') return
  
  const nodeIndex = nodes.value.findIndex(n => n.node_id === msg.node_id)
  if (nodeIndex !== -1) {
    const node = nodes.value[nodeIndex]
    
    // Check if telemetry list exists
    if (!node.telemetry) {
      node.telemetry = []
    }
    
    // Add new telemetry to the start (descending order)
    node.telemetry.unshift(msg.data)
    
    // Limit to 50 recent points
    if (node.telemetry.length > 50) {
      node.telemetry = node.telemetry.slice(0, 50)
    }
    
    // Trigger reactivity
    nodes.value[nodeIndex] = { ...node }
  }
})

const activeNode = computed(() => {
  return nodes.value.find(n => n.id === selectedNodeId.value)
})

const latestTelemetry = computed(() => {
  if (!activeNode.value || !activeNode.value.telemetry || activeNode.value.telemetry.length === 0) {
    return null
  }
  return activeNode.value.telemetry[0]
})

// Reverse the array to feed it to the chart (chronological order)
const chartData = computed(() => {
  if (!activeNode.value || !activeNode.value.telemetry) return []
  return [...activeNode.value.telemetry].reverse()
})

const isNodeActive = (lastSeen: string | undefined) => {
  if (!lastSeen) return false
  const diffMinutes = (new Date().getTime() - new Date(lastSeen).getTime()) / (1000 * 60)
  return diffMinutes < 15
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold tracking-tight">Dashboard</h2>
        </div>
        
        <!-- Live Connection Status -->
        <div class="flex items-center gap-2 text-sm font-medium">
          <div :class="['w-2.5 h-2.5 rounded-full', isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500']"></div>
          {{ isConnected ? 'Live Connection Active' : 'Disconnected' }}
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
        
        <div v-if="activeNode" class="space-y-4">
          <div class="flex items-center gap-3">
            <h3 class="text-lg font-semibold">{{ activeNode.name }}</h3>
            <StatusBadge 
              :is-active="isNodeActive(activeNode.last_seen)" 
              :last-seen="activeNode.last_seen" 
            />
          </div>

          <!-- Sensors Grid -->
          <div class="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <SensorCard
              title="Temperature"
              :value="latestTelemetry?.temperature"
              unit="°C"
              type="temperature"
            />
            <SensorCard
              title="Humidity"
              :value="latestTelemetry?.humidity"
              unit="%"
              type="humidity"
            />
            <SensorCard
              title="Soil Moisture"
              :value="latestTelemetry?.soil_moisture"
              unit="%"
              type="soil"
            />
            <SensorCard
              title="Battery"
              :value="latestTelemetry?.battery_level"
              unit="%"
              type="battery"
            />
          </div>
          
          <!-- Charts & Map -->
          <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7 animate-slide-up" style="animation-delay: 0.1s">
            <div class="col-span-4 border border-border/50 rounded-xl bg-card/90 backdrop-blur-xl p-4 min-h-[320px] shadow-sm relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50 pointer-events-none"></div>
              <SensorLineChart :data="chartData" :title="`Telemetry Trends - ${activeNode.name}`" class="relative z-10" />
            </div>
            <div class="col-span-3 border border-border/50 rounded-xl bg-card/90 backdrop-blur-xl p-4 min-h-[320px] shadow-sm relative overflow-hidden">
              <div class="flex flex-col h-full relative z-10">
                <h4 class="text-sm font-medium text-muted-foreground mb-3 text-center">Node Location</h4>
                <div class="flex-1 bg-muted/30 rounded-lg flex items-center justify-center border border-dashed">
                  <p class="text-muted-foreground text-sm">Map Component Pending</p>
                </div>
                <div class="mt-3 text-sm text-center text-muted-foreground" v-if="activeNode.latitude && activeNode.longitude">
                  Lat: {{ activeNode.latitude.toFixed(4) }}, Lng: {{ activeNode.longitude.toFixed(4) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </DashboardLayout>
</template>

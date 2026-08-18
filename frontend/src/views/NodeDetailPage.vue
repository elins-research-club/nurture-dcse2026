<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import SensorCard from '@/components/dashboard/SensorCard.vue'
import SensorLineChart from '@/components/charts/SensorLineChart.vue'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Trash2, Edit } from 'lucide-vue-next'
import { useNodes } from '@/composables/useNodes'
import { useWebSocket } from '@/composables/useWebSocket'
import type { NodeDeviceWithData } from '@/types'

const route = useRoute()
const router = useRouter()
const nodeId = Number(route.params.id)

const { nodesQuery } = useNodes()
const wsUrl = 'ws://localhost:8000/ws/dashboard'
const { lastMessage } = useWebSocket(wsUrl)

const nodes = ref<NodeDeviceWithData[]>([])

watch(() => nodesQuery.data.value, (newData) => {
  if (newData) {
    nodes.value = [...newData]
  }
}, { immediate: true })

watch(lastMessage, (msg) => {
  if (!msg || msg.type !== 'telemetry') return
  
  const index = nodes.value.findIndex(n => n.node_id === msg.node_id)
  if (index !== -1) {
    const node = nodes.value[index]
    if (!node.telemetry) node.telemetry = []
    node.telemetry.unshift(msg.data)
    if (node.telemetry.length > 100) node.telemetry = node.telemetry.slice(0, 100)
    nodes.value[index] = { ...node }
  }
})

const activeNode = computed(() => {
  return nodes.value.find(n => n.id === nodeId)
})

const latestTelemetry = computed(() => {
  if (!activeNode.value || !activeNode.value.telemetry || activeNode.value.telemetry.length === 0) {
    return null
  }
  return activeNode.value.telemetry[0]
})

const chartData = computed(() => {
  if (!activeNode.value || !activeNode.value.telemetry) return []
  return [...activeNode.value.telemetry].reverse()
})

const isNodeActive = (lastSeen: string | undefined) => {
  if (!lastSeen) return false
  const diffMinutes = (new Date().getTime() - new Date(lastSeen).getTime()) / (1000 * 60)
  return diffMinutes < 15
}

const goBack = () => {
  router.push('/nodes')
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6">
      <div class="flex items-center gap-4">
        <Button variant="outline" size="icon" @click="goBack">
          <ArrowLeft class="w-4 h-4" />
        </Button>
        <div class="flex-1">
          <h2 class="text-3xl font-bold tracking-tight flex items-center gap-4">
            {{ activeNode?.name || 'Loading Node...' }}
            <StatusBadge 
              v-if="activeNode"
              :is-active="isNodeActive(activeNode.last_seen)" 
              :last-seen="activeNode.last_seen" 
            />
          </h2>
          <p class="text-muted-foreground font-mono text-sm mt-1">ID: {{ activeNode?.node_id }}</p>
        </div>
        
        <div class="flex gap-2">
          <Button variant="outline"><Edit class="w-4 h-4 mr-2" /> Edit</Button>
          <Button variant="destructive"><Trash2 class="w-4 h-4 mr-2" /> Delete</Button>
        </div>
      </div>
      
      <div v-if="!activeNode && !nodesQuery.isLoading.value" class="py-12 text-center text-destructive">
        Node not found.
      </div>
      
      <template v-if="activeNode">
        <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <SensorCard title="Temperature" :value="latestTelemetry?.temperature" unit="°C" type="temperature" />
          <SensorCard title="Humidity" :value="latestTelemetry?.humidity" unit="%" type="humidity" />
          <SensorCard title="Soil Moisture" :value="latestTelemetry?.soil_moisture" unit="%" type="soil" />
          <SensorCard title="Battery" :value="latestTelemetry?.battery_level" unit="%" type="battery" />
        </div>
        
        <div class="border rounded-xl bg-card p-6 min-h-[500px]">
          <SensorLineChart :data="chartData" :title="`Historical Telemetry - ${activeNode.name}`" />
        </div>
      </template>
    </div>
  </DashboardLayout>
</template>

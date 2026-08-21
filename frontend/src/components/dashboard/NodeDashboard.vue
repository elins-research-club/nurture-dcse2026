<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useWebSocket } from '@/composables/useWebSocket'
import SensorCard from '@/components/dashboard/SensorCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import SensorLineChart from '@/components/charts/SensorLineChart.vue'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const props = defineProps<{
  nodeId: string
  nodeName?: string
}>()

const authStore = useAuthStore()
const wsUrl = 'ws://localhost:8000/ws/dashboard'
const { lastMessage, isConnected } = useWebSocket(wsUrl)

const sensors = ref<any[]>([])
const telemetry = ref<any[]>([])
const isLoading = ref(true)

const fetchNodeData = async () => {
  if (!props.nodeId) return
  isLoading.value = true
  
  // Fetch sensors instantly
  fetch(`http://localhost:8000/api/v1/nodes/${props.nodeId}/sensors/`, {
    headers: { 'Authorization': `Bearer ${authStore.token}` }
  }).then(async res => {
    if (res.ok) {
      sensors.value = await res.json()
    }
  }).catch(console.error)
  
  // Fetch history in background
  fetch(`http://localhost:8000/api/v1/nodes/${props.nodeId}/telemetry/history?results=50`, {
    headers: { 'Authorization': `Bearer ${authStore.token}` }
  }).then(async res => {
    if (res.ok) {
      const historyData = await res.json()
      if (historyData.feeds && Array.isArray(historyData.feeds)) {
        telemetry.value = historyData.feeds.reverse()
      }
    }
    isLoading.value = false
  }).catch((e) => {
    console.error(e)
    isLoading.value = false
  })
}

onMounted(() => {
  fetchNodeData()
})

watch(() => props.nodeId, () => {
  sensors.value = []
  telemetry.value = []
  fetchNodeData()
})

watch(lastMessage, (msg) => {
  if (!msg || msg.event !== 'sensor_update') return
  if (msg.node_id !== props.nodeId) return
  
  const currentTelemetry = [...telemetry.value]
  currentTelemetry.unshift(msg.data)
  if (currentTelemetry.length > 50) {
    telemetry.value = currentTelemetry.slice(0, 50)
  } else {
    telemetry.value = currentTelemetry
  }
})

const latestTelemetry = computed(() => {
  if (telemetry.value.length === 0) return null
  return telemetry.value[0]
})

const chartData = computed(() => {
  return [...telemetry.value].reverse()
})

const lastSeen = computed(() => {
  if (telemetry.value.length === 0) return undefined
  return telemetry.value[0].created_at
})

const isNodeActive = computed(() => {
  if (!lastSeen.value) return false
  const diffMinutes = (new Date().getTime() - new Date(lastSeen.value).getTime()) / (1000 * 60)
  return diffMinutes < 15
})
</script>

<template>
  <div class="space-y-4 w-full">
    <div class="flex items-center gap-3">
      <h3 v-if="nodeName" class="text-lg font-semibold">{{ nodeName }}</h3>
      <StatusBadge 
        v-if="!nodeName"
        :is-active="isNodeActive" 
        :last-seen="lastSeen" 
      />
      <!-- Live Connection Status -->
      <div class="ml-auto flex items-center gap-2 text-sm font-medium">
        <div :class="['w-2.5 h-2.5 rounded-full', isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500']"></div>
        <span class="hidden sm:inline">{{ isConnected ? 'Live Connection Active' : 'Disconnected' }}</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading && sensors.length === 0" class="py-12 text-center text-muted-foreground">
      Loading sensors...
    </div>

    <!-- Sensors Grid -->
    <div v-else-if="sensors.length > 0" class="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
      <!-- Normal Sensors -->
      <template v-for="sensor in sensors.filter(s => s.name !== 'Status aktuator')" :key="sensor.id">
        <SensorCard
          :title="sensor.name"
          :value="latestTelemetry ? latestTelemetry[`${sensor.channel_id}_${sensor.thingspeak_field}`] : null"
          :unit="sensor.unit"
          type="default"
        />
      </template>
      
      <!-- Actuator Status Bitmask Parser -->
      <template v-for="sensor in sensors.filter(s => s.name === 'Status aktuator')" :key="sensor.id">
        <div class="col-span-full mt-4">
          <h3 class="text-sm font-semibold mb-3">Actuators Status</h3>
          <div class="grid gap-3 md:grid-cols-3">
            <Card v-for="i in 3" :key="i">
              <CardContent class="p-4 flex items-center justify-between">
                <span class="font-medium">Actuator {{ i }}</span>
                <Badge 
                  :variant="(latestTelemetry && latestTelemetry[`${sensor.channel_id}_${sensor.thingspeak_field}`] != null && (latestTelemetry[`${sensor.channel_id}_${sensor.thingspeak_field}`] & Math.pow(2, i-1))) ? 'success' : 'destructive'"
                >
                  {{ (latestTelemetry && latestTelemetry[`${sensor.channel_id}_${sensor.thingspeak_field}`] != null && (latestTelemetry[`${sensor.channel_id}_${sensor.thingspeak_field}`] & Math.pow(2, i-1))) ? 'Online' : 'Offline' }}
                </Badge>
              </CardContent>
            </Card>
          </div>
        </div>
      </template>
    </div>
    <div v-else class="py-12 text-center text-muted-foreground border border-dashed rounded-xl">
      No sensors configured. Add sensors in Settings.
    </div>
    
    <!-- Charts & Map -->
    <div v-if="sensors.length > 0" class="grid gap-4 md:grid-cols-2 lg:grid-cols-7 animate-slide-up" style="animation-delay: 0.1s">
      <div class="col-span-4 border border-border/50 rounded-xl bg-card/90 backdrop-blur-xl p-4 min-h-[320px] shadow-sm relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50 pointer-events-none"></div>
        <SensorLineChart :data="chartData" :title="`Telemetry Trends - ${nodeName || nodeId}`" :sensors="sensors" class="relative z-10" />
      </div>
      <div class="col-span-3 border border-border/50 rounded-xl bg-card/90 backdrop-blur-xl p-4 min-h-[320px] shadow-sm relative overflow-hidden">
        <div class="flex flex-col h-full relative z-10">
          <h4 class="text-sm font-medium text-muted-foreground mb-3 text-center">Node Map Component Pending</h4>
          <div class="flex-1 bg-muted/30 rounded-lg flex items-center justify-center border border-dashed">
            <p class="text-muted-foreground text-sm">Map rendering here</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

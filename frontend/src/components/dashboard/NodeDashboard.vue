<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTelemetryStore } from '@/stores/telemetry'
import SensorCard from '@/components/dashboard/SensorCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import SensorLineChart from '@/components/charts/SensorLineChart.vue'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import L from 'leaflet'

const props = defineProps<{
  nodeId: string
  nodeName?: string
}>()

const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()

const isLoading = ref(false)

const sensors = computed(() => telemetryStore.sensorsCache[props.nodeId] || [])
const telemetry = computed(() => telemetryStore.telemetryHistory[props.nodeId] || [])

const loadNodeData = async () => {
  if (!props.nodeId) return
  if (!telemetry.value.length) isLoading.value = true
  await Promise.all([
    telemetryStore.fetchSensors(props.nodeId),
    telemetryStore.fetchHistory(props.nodeId)
  ])
  isLoading.value = false
}

onMounted(() => {
  loadNodeData()
})

watch(() => props.nodeId, () => {
  loadNodeData()
  if (miniMap) {
    miniMap.remove()
    miniMap = null
    miniMapReady.value = false
  }
})

const latestTelemetry = computed(() => {
  return telemetryStore.getLatest(props.nodeId)
})

const chartData = computed(() => {
  return telemetryStore.getChartData(props.nodeId)
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

// Mini-map
const miniMapContainer = ref<HTMLElement | null>(null)
const miniMapReady = ref(false)
let miniMap: L.Map | null = null

const initMiniMap = (lat: number, lng: number) => {
  if (!miniMapContainer.value || miniMap) return
  miniMap = L.map(miniMapContainer.value, { zoomControl: false, dragging: false, scrollWheelZoom: false, attributionControl: false })
    .setView([lat, lng], 18)
  L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', { 
    maxZoom: 21,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
  }).addTo(miniMap)
  const icon = L.divIcon({
    html: `<div style="width:16px;height:22px"><svg width="16" height="22" viewBox="0 0 24 32" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 20 12 20s12-11 12-20C24 5.373 18.627 0 12 0z" fill="#2563eb"/><circle cx="12" cy="12" r="5" fill="white"/></svg></div>`,
    className: '', iconSize: [16, 22], iconAnchor: [8, 22],
  })
  L.marker([lat, lng], { icon }).addTo(miniMap)
  miniMapReady.value = true
}

// Fetch node coords and init mini-map
const API_BASE_URL = 'http://localhost:8000/api/v1'
const fetchNodeCoords = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/nodes/${props.nodeId}`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!res.ok) return
    const node = await res.json()
    if (node.latitude != null && node.longitude != null) {
      // Wait for DOM
      setTimeout(() => initMiniMap(node.latitude, node.longitude), 100)
    }
  } catch { /* no coords, skip */ }
}

onMounted(() => fetchNodeCoords())
onUnmounted(() => { miniMap?.remove(); miniMap = null })
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
      <div class="col-span-3 border border-border/50 rounded-xl bg-card/90 backdrop-blur-xl shadow-sm relative overflow-hidden" style="min-height:320px">
        <div ref="miniMapContainer" class="w-full h-full" style="min-height:320px" />
        <div v-if="!miniMapReady" class="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-30"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
          <p class="text-xs opacity-50">No location set for this node</p>
          <a href="/map" class="text-xs text-primary hover:underline opacity-70">Set in Maps page →</a>
        </div>
      </div>
    </div>
  </div>
</template>

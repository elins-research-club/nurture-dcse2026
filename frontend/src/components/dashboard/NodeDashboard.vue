<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTelemetryStore } from '@/stores/telemetry'
import SensorCard from '@/components/dashboard/SensorCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import SensorLineChart from '@/components/charts/SensorLineChart.vue'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Calendar, Clock, Check, Layers, Sprout, CloudSun, Leaf, Zap, MapPin, 
  Cpu, Thermometer, Droplet
} from 'lucide-vue-next'
import L from 'leaflet'

const props = defineProps<{
  nodeId: string
  nodeName?: string
}>()

const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()

const isLoading = ref(false)
const selectedCategory = ref<'all' | 'npk' | 'soil' | 'environment'>('npk')
const selectedRange = ref<'1d' | '1w' | '1M' | 'custom'>('1d')
const customStartDate = ref('')
const customEndDate = ref('')

const sensors = ref<any[]>([])
const telemetry = computed(() => telemetryStore.telemetryHistory[props.nodeId] || [])

const loadNodeData = async () => {
  if (!props.nodeId) return
  if (!telemetry.value.length) isLoading.value = true
  const [sensorsData] = await Promise.all([
    telemetryStore.fetchSensors(props.nodeId),
    telemetryStore.fetchHistory(props.nodeId, { range: '1d' })
  ])
  sensors.value = sensorsData
  isLoading.value = false
}

onMounted(() => {
  loadNodeData()
})

watch(() => props.nodeId, () => {
  selectedRange.value = '1d'
  loadNodeData()
  if (miniMap) {
    miniMap.remove()
    miniMap = null
    miniMapReady.value = false
  }
  nodeCoords.value = null
  fetchNodeCoords()
})

// Categorize sensors intelligently
const getSensorCategory = (sensor: any): 'npk' | 'soil' | 'environment' | 'other' => {
  const name = (sensor.name || '').toLowerCase()
  const type = (sensor.type || '').toLowerCase()
  
  if (name.includes('nitrogen') || name.includes('phosphorus') || name.includes('potassium') || 
      name.includes('kalium') || name.includes('fosfor') || type.includes('npk')) {
    return 'npk'
  }
  if (name.includes('soil') || name.includes('tanah') || name.includes('ph') || 
      name.includes('ec') || name.includes('analog') || name.includes('probe') || type.includes('soil')) {
    return 'soil'
  }
  if (name.includes('suhu') || name.includes('temp') || name.includes('kelembaban') || 
      name.includes('humidity') || name.includes('enclosure') || name.includes('udara') || 
      name.includes('cahaya') || name.includes('light') || type.includes('env') || type.includes('temp')) {
    return 'environment'
  }
  return 'other'
}

const activeCategorySensors = computed(() => {
  const nonActuators = sensors.value.filter(s => s.name !== 'Status aktuator')
  if (selectedCategory.value === 'all') {
    return nonActuators
  }
  const filtered = nonActuators.filter(s => getSensorCategory(s) === selectedCategory.value)
  return filtered.length > 0 ? filtered : nonActuators
})

const changeRange = async (range: '1d' | '1w' | '1M' | 'custom') => {
  selectedRange.value = range
  if (range === '1d') {
    await telemetryStore.fetchHistory(props.nodeId, { range: '1d' })
  } else if (range === '1w') {
    await telemetryStore.fetchHistory(props.nodeId, { range: '1w', average: 15 })
  } else if (range === '1M') {
    await telemetryStore.fetchHistory(props.nodeId, { range: '1M', average: 60 })
  }
}

const applyCustomDate = async () => {
  if (!customStartDate.value) return
  selectedRange.value = 'custom'
  const startIso = `${customStartDate.value}T00:00:00`
  const endIso = customEndDate.value ? `${customEndDate.value}T23:59:59` : undefined

  let avg: number | undefined = undefined
  if (customEndDate.value) {
    const diffDays = (new Date(customEndDate.value).getTime() - new Date(customStartDate.value).getTime()) / (1000 * 3600 * 24)
    if (diffDays > 14) avg = 60
    else if (diffDays > 3) avg = 15
  }

  await telemetryStore.fetchHistory(props.nodeId, { start: startIso, end: endIso, average: avg })
}

const latestTelemetry = computed(() => {
  return telemetryStore.getLatest(props.nodeId)
})

// field8 kanal pendukung: bitmask 3 bit (Kipas, Lampu, Valve)
const aktuator = computed(() => {
  const s = sensors.value.find(x => x.name === 'Status aktuator')
  if (!s || !latestTelemetry.value) return null

  const mentah = latestTelemetry.value[`${s.channel_id}_${s.thingspeak_field}`]
  if (mentah == null) return null

  const v = Number(mentah)
  if (!Number.isFinite(v) || v < 0 || v > 7) return null

  return {
    kipas: !!(v & 0b0001),
    lampu: !!(v & 0b0010),
    valve: !!(v & 0b0100),
  }
})

const isArchive = computed(() => selectedRange.value !== '1d')

const chartData = computed(() => {
  return telemetryStore.getChartData(props.nodeId, isArchive.value)
})

const isArchiveLoading = computed(() => {
  return telemetryStore.isArchiveLoading[props.nodeId] || false
})

const lastSeen = computed(() => {
  if (telemetry.value.length === 0) return undefined
  return telemetry.value[0].created_at
})

const isConnected = computed(() => telemetryStore.isConnected)

const isNodeActive = computed(() => {
  if (!lastSeen.value) return false
  const dateStr = String(lastSeen.value).endsWith('Z') ? String(lastSeen.value) : String(lastSeen.value) + 'Z'
  const diffMinutes = (new Date().getTime() - new Date(dateStr).getTime()) / (1000 * 60)
  return diffMinutes < 15
})

// Formatted last seen timestamp
const formattedLastSeen = computed(() => {
  if (!lastSeen.value) return '--'
  try {
    const dateStr = String(lastSeen.value).endsWith('Z') ? String(lastSeen.value) : String(lastSeen.value) + 'Z'
    const d = new Date(dateStr)
    return d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) + ' WIB'
  } catch {
    return '--'
  }
})

// Grouped sensors
const npkSensors = computed(() => sensors.value.filter(s => getSensorCategory(s) === 'npk'))

// Helper to get raw sensor value by exact sensor object
const getSensorValue = (sensor: any) => {
  if (!sensor || !latestTelemetry.value) return null
  return latestTelemetry.value[`${sensor.channel_id}_${sensor.thingspeak_field}`]
}

// Helper to find value by keyword matching
const getValueByKeywords = (keywords: string[]) => {
  const sensor = sensors.value.find(s => {
    const name = (s.name || '').toLowerCase()
    const type = (s.type || '').toLowerCase()
    return keywords.some(k => name.includes(k) || type.includes(k))
  })
  if (!sensor || !latestTelemetry.value) return null
  return latestTelemetry.value[`${sensor.channel_id}_${sensor.thingspeak_field}`]
}

// Specific Sensor Values for Soil Portlet
const phValue = computed(() => getValueByKeywords(['ph']))
const soilTempValue = computed(() => getValueByKeywords(['soil temp', 'suhu tanah', 'temp tanah']))
const soilEcValue = computed(() => getValueByKeywords(['ec', 'conductivity', 'daya hantar']))
const moistureAvgValue = computed(() => getValueByKeywords(['avg', 'rata-rata', 'soil moisture avg']))

const probe1Value = computed(() => getValueByKeywords(['probe 1', 'moisture 1', 'analog 1', 'analog probe 1']))
const probe2Value = computed(() => getValueByKeywords(['probe 2', 'moisture 2', 'analog 2', 'analog probe 2']))
const probe3Value = computed(() => getValueByKeywords(['probe 3', 'moisture 3', 'analog 3', 'analog probe 3']))

// Specific Sensor Values for IoT & Ambient Portlet
const enclosureTempValue = computed(() => getValueByKeywords(['enclosure', 'panel', 'dalam box', 'box temp', 'suhu panel', 'suhu box']))
const airTempValue = computed(() => getValueByKeywords(['air temp', 'suhu luar', 'suhu udara', 'ambient', 'temp luar']))
const airHumidityValue = computed(() => getValueByKeywords(['air humidity', 'kelembaban udara', 'humidity', 'kelembaban luar', 'kelembapan']))
const modbusCodeValue = computed(() => getValueByKeywords(['modbus', 'status modbus', 'modbus code']))

// Dynamic Soil pH Status badge
const phStatus = computed(() => {
  const v = phValue.value
  if (v == null) return { text: 'Netral', bg: 'bg-slate-100', border: 'border-slate-200', textClass: 'text-slate-600' }
  const num = Number(v)
  if (num < 6.0) return { text: 'Asam', bg: 'bg-rose-500/10', border: 'border-rose-500/30', textClass: 'text-rose-600' }
  if (num <= 7.5) return { text: 'Optimal', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', textClass: 'text-emerald-600' }
  return { text: 'Basa', bg: 'bg-amber-500/10', border: 'border-amber-500/30', textClass: 'text-amber-600' }
})

// Dynamic IoT Thermal Status badge
const thermalStatus = computed(() => {
  const v = enclosureTempValue.value
  if (v == null) return { text: 'Normal', badgeClass: 'border-slate-200 bg-slate-100 text-slate-600', dotClass: 'bg-slate-500' }
  const num = Number(v)
  if (num < 40) return { text: 'Normal', badgeClass: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600', dotClass: 'bg-emerald-500' }
  if (num <= 50) return { text: 'Hangat', badgeClass: 'border-amber-500/30 bg-amber-500/10 text-amber-600', dotClass: 'bg-amber-500' }
  return { text: 'Overheat', badgeClass: 'border-rose-500/30 bg-rose-500/10 text-rose-600', dotClass: 'bg-rose-500 animate-pulse' }
})

// Mini-map logic with reactive watch & 1:1 square ratio
const miniMapContainer = ref<HTMLElement | null>(null)
const miniMapReady = ref(false)
const nodeCoords = ref<{ lat: number; lng: number } | null>(null)
let miniMap: L.Map | null = null

const initMiniMap = (lat: number, lng: number) => {
  if (!miniMapContainer.value || miniMap) return
  try {
    miniMap = L.map(miniMapContainer.value, { 
      zoomControl: false, 
      dragging: false, 
      scrollWheelZoom: false, 
      attributionControl: false 
    }).setView([lat, lng], 18)

    L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', { 
      maxZoom: 21,
      subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
    }).addTo(miniMap)

    const icon = L.divIcon({
      html: `<div style="width:20px;height:26px"><svg width="20" height="26" viewBox="0 0 24 32" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 20 12 20s12-11 12-20C24 5.373 18.627 0 12 0z" fill="#2563eb"/><circle cx="12" cy="12" r="5" fill="white"/></svg></div>`,
      className: '', iconSize: [20, 26], iconAnchor: [10, 26],
    })
    L.marker([lat, lng], { icon }).addTo(miniMap)
    miniMapReady.value = true

    setTimeout(() => {
      miniMap?.invalidateSize()
    }, 150)
  } catch (err) {
    console.error('[NodeDashboard] Failed to initialize mini-map:', err)
  }
}

// Fetch node coords and set state
const API_BASE_URL = '/api/v1'
const fetchNodeCoords = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/nodes/${props.nodeId}`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!res.ok) return
    const node = await res.json()
    if (node.latitude != null && node.longitude != null) {
      nodeCoords.value = { lat: node.latitude, lng: node.longitude }
    }
  } catch { /* no coords, skip */ }
}

// Watch both container and coords so map initializes as soon as DOM container is mounted
watch(
  [miniMapContainer, nodeCoords],
  async ([container, coords]) => {
    if (container && coords && !miniMap) {
      await nextTick()
      initMiniMap(coords.lat, coords.lng)
    }
  },
  { flush: 'post', immediate: true }
)

onMounted(() => {
  fetchNodeCoords()
})

onUnmounted(() => {
  if (miniMap) {
    miniMap.remove()
    miniMap = null
  }
})
</script>

<template>
  <div class="w-full">
    <!-- Loading State -->
    <div v-if="isLoading && sensors.length === 0" class="py-16 text-center text-muted-foreground">
      <div class="flex items-center justify-center gap-2 animate-pulse">
        <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Memuat data sensor...
      </div>
    </div>

    <!-- No Sensors State -->
    <div v-else-if="sensors.length === 0" class="py-16 text-center text-muted-foreground border border-dashed rounded-2xl">
      No sensors configured. Add sensors in Settings.
    </div>

    <!-- ═══════════════ BENTO GRID: FLAT WHITE CARDS ON #F1F5F9 CANVAS ═══════════════ -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-start">
      
      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <!-- SISI KIRI (lg:col-span-3 / ~25%): HARDWARE, IDENTITY & CONTROL HUB (COMPACT) -->
      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <div class="lg:col-span-3 flex flex-col gap-3.5">
        
        <!-- CARD 1: Compact Node Identity & Status Card -->
        <Card class="relative overflow-hidden border border-border/80 bg-white shadow-none">
          <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-primary/5 pointer-events-none"></div>
          <CardContent class="p-3.5 sm:p-4 relative z-10 flex flex-col gap-2.5">
            <!-- Node Title & Status Badge -->
            <div class="flex items-start justify-between gap-2">
              <div class="space-y-0.5">
                <h2 class="text-base sm:text-lg font-bold tracking-tight">{{ nodeName || nodeId }}</h2>
                <p class="text-[11px] text-muted-foreground font-mono">ID: {{ nodeId }}</p>
              </div>

              <!-- Single Node Status Badge on top-right -->
              <StatusBadge :is-active="isNodeActive" :last-seen="lastSeen" class="shrink-0" />
            </div>

            <!-- Footer: Last seen & GPS Coordinates -->
            <div class="flex flex-col gap-1 pt-2 border-t border-border/40 text-[11px] text-muted-foreground">
              <div class="flex items-center gap-1.5">
                <Clock class="w-3 h-3 text-primary shrink-0" />
                <span>Update: <strong class="text-foreground">{{ formattedLastSeen }}</strong></span>
              </div>
              <div v-if="nodeCoords" class="flex items-center gap-1.5">
                <MapPin class="w-3 h-3 text-blue-500 shrink-0" />
                <span class="font-mono text-[10px]">{{ nodeCoords.lat.toFixed(5) }}, {{ nodeCoords.lng.toFixed(5) }}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- CARD 2: Mini Map (1:1 Ratio Square Card) -->
        <Card class="relative overflow-hidden w-full aspect-square border border-border/80 shadow-none flex flex-col group rounded-xl bg-white">
          <div ref="miniMapContainer" class="w-full h-full absolute inset-0 z-0" />
          
          <!-- Map Overlay Link to Full Map Page -->
          <div v-if="miniMapReady" class="absolute bottom-2.5 right-2.5 z-10">
            <a 
              href="/map" 
              class="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-white/90 backdrop-blur-md text-foreground border border-border/70 hover:bg-white flex items-center gap-1.5 transition-all hover:scale-105"
            >
              <MapPin class="w-3.5 h-3.5 text-primary" />
              <span>Buka Peta →</span>
            </a>
          </div>

          <div v-if="!miniMapReady" class="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground gap-1 bg-slate-50 p-3 text-center z-10">
            <MapPin class="w-6 h-6 opacity-40 text-primary" />
            <p class="text-xs font-semibold opacity-70">Lokasi belum diset</p>
            <a href="/map" class="text-xs text-primary hover:underline font-bold mt-0.5">Atur di Maps →</a>
          </div>
        </Card>

        <!-- CARD 3: Compact Actuator Control Status -->
        <Card v-if="aktuator" class="relative overflow-hidden border border-border/80 bg-white shadow-none hover:border-amber-500/30 transition-all">
          <div class="p-3 flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <div class="w-5 h-5 rounded bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600">
                  <Zap class="w-3 h-3" />
                </div>
                <h4 class="text-xs font-bold tracking-tight">Status Aktuator</h4>
              </div>
              <span class="text-[9px] text-muted-foreground">3 Relay</span>
            </div>

            <!-- 3 Inline State Chips -->
            <div class="grid grid-cols-3 gap-1">
              <div 
                v-for="a in [
                  { nama: 'Kipas', aktif: aktuator.kipas },
                  { nama: 'Lampu', aktif: aktuator.lampu },
                  { nama: 'Valve', aktif: aktuator.valve },
                ]" 
                :key="a.nama"
                :class="[
                  'p-1.5 rounded-md text-[10px] font-medium border flex flex-col items-center justify-center gap-0.5 transition-all text-center',
                  a.aktif 
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 font-semibold' 
                    : 'bg-slate-50 border-slate-200 text-slate-500'
                ]"
              >
                <div class="flex items-center gap-1">
                  <div :class="['w-1.5 h-1.5 rounded-full', a.aktif ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400']"></div>
                  <span class="font-bold">{{ a.nama }}</span>
                </div>
                <span class="text-[9px] font-bold">{{ a.aktif ? 'ON' : 'OFF' }}</span>
              </div>
            </div>
          </div>
        </Card>

      </div>

      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <!-- SISI KANAN (lg:col-span-9 / ~75%): NPK, CHART & DOMAIN PORTLETS -->
      <!-- ═══════════════════════════════════════════════════════════════════════════ -->
      <div class="lg:col-span-9 flex flex-col gap-3.5">
        
        <!-- ROW 1: 3 NPK Highlight Cards (Original Compact Rectangular Size!) -->
        <div v-if="npkSensors.length > 0" class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <SensorCard
            v-for="sensor in npkSensors"
            :key="sensor.id"
            :title="sensor.name"
            :value="getSensorValue(sensor)"
            :unit="sensor.unit"
            type="npk"
            size="default"
            :min-threshold="sensor.min_threshold"
            :max-threshold="sensor.max_threshold"
          />
        </div>

        <!-- ROW 2: Wide Sensor Trends Line Chart -->
        <Card class="relative overflow-hidden flex flex-col border border-border/80 bg-white dark:bg-card shadow-none">
          <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-30 pointer-events-none"></div>
          <CardContent class="p-4 relative z-10 flex flex-col gap-3 flex-1">
            
            <!-- Chart Header: Category Pills + Time Range -->
            <div class="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-border/40">
              
              <!-- Category Pills -->
              <div class="flex flex-wrap items-center gap-1">
                <button
                  @click="selectedCategory = 'npk'"
                  :class="['px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer', selectedCategory === 'npk' ? 'bg-emerald-500/15 text-emerald-600 border border-emerald-500/30' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-foreground border border-transparent']"
                >
                  <Leaf class="w-3.5 h-3.5 text-emerald-500" />
                  <span>NPK</span>
                </button>
                <button
                  @click="selectedCategory = 'soil'"
                  :class="['px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer', selectedCategory === 'soil' ? 'bg-amber-500/15 text-amber-600 border border-amber-500/30' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-foreground border border-transparent']"
                >
                  <Sprout class="w-3.5 h-3.5 text-amber-500" />
                  <span>Tanah</span>
                </button>
                <button
                  @click="selectedCategory = 'environment'"
                  :class="['px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer', selectedCategory === 'environment' ? 'bg-blue-500/15 text-blue-600 border border-blue-500/30' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-foreground border border-transparent']"
                >
                  <CloudSun class="w-3.5 h-3.5 text-blue-500" />
                  <span>IoT & Iklim</span>
                </button>
                <button
                  @click="selectedCategory = 'all'"
                  :class="['px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer', selectedCategory === 'all' ? 'bg-primary/15 text-primary border border-primary/30' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-foreground border border-transparent']"
                >
                  <Layers class="w-3.5 h-3.5 text-primary" />
                  <span>Semua</span>
                </button>
              </div>

              <!-- Time Range Selector -->
              <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200/80 dark:border-slate-700/80 text-xs">
                <button
                  @click="changeRange('1d')"
                  :class="[
                    'px-2 py-1 rounded-md font-semibold transition-all cursor-pointer flex items-center gap-1 text-xs',
                    selectedRange === '1d' 
                      ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-none' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  24J
                </button>
                <button
                  @click="changeRange('1w')"
                  :class="[
                    'px-2 py-1 rounded-md font-semibold transition-all cursor-pointer text-xs',
                    selectedRange === '1w' 
                      ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-none' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  7H
                </button>
                <button
                  @click="changeRange('1M')"
                  :class="[
                    'px-2 py-1 rounded-md font-semibold transition-all cursor-pointer text-xs',
                    selectedRange === '1M' 
                      ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-none' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                >
                  30H
                </button>
                <button
                  @click="selectedRange = 'custom'"
                  :class="[
                    'px-1.5 py-1 rounded-md font-semibold transition-all cursor-pointer text-xs',
                    selectedRange === 'custom' 
                      ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-none' 
                      : 'text-muted-foreground hover:text-foreground'
                  ]"
                  title="Rentang Kustom"
                >
                  <Calendar class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <!-- Custom Date Picker -->
            <div v-if="selectedRange === 'custom'" class="flex flex-wrap items-center gap-2 p-2 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-lg text-xs animate-slide-up">
              <div class="flex items-center gap-1.5">
                <span class="text-slate-500 dark:text-slate-400">Dari:</span>
                <Input type="date" v-model="customStartDate" class="h-7 text-xs w-32 px-2 py-0 bg-white dark:bg-slate-800" />
              </div>
              <div class="flex items-center gap-1.5">
                <span class="text-slate-500 dark:text-slate-400">Sampai:</span>
                <Input type="date" v-model="customEndDate" class="h-7 text-xs w-32 px-2 py-0 bg-white dark:bg-slate-800" />
              </div>
              <Button size="sm" variant="default" class="h-7 text-xs px-2.5 shadow-none" @click="applyCustomDate" :disabled="!customStartDate">
                <Check class="w-3 h-3 mr-1" />
                Terapkan
              </Button>
            </div>

            <!-- Chart Visual Canvas -->
            <div class="h-[350px] w-full">
              <SensorLineChart 
                :data="chartData" 
                :title="`Tren ${selectedCategory === 'npk' ? 'Unsur Hara NPK' : (selectedCategory === 'soil' ? 'Kondisi Tanah' : (selectedCategory === 'environment' ? 'Kondisi IoT' : 'Sensor'))}`" 
                :sensors="activeCategorySensors" 
                :is-loading="isArchiveLoading"
              />
            </div>
          </CardContent>
        </Card>

        <!-- ROW 3: Dua Portlet Berdampingan (Kondisi Tanah & Kondisi IoT) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          
          <!-- PORTLET 1: KONDISI TANAH -->
          <Card class="relative overflow-hidden border border-border/80 bg-white dark:bg-card shadow-none hover:border-amber-500/30 transition-all flex flex-col">
            <div class="p-4 flex flex-col gap-3 flex-1 justify-between">
              <!-- Portlet Header -->
              <div class="flex items-center justify-between pb-2 border-b border-border/40">
                <div class="flex items-center gap-2">
                  <div class="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600">
                    <Sprout class="w-4 h-4" />
                  </div>
                  <h3 class="text-sm font-bold tracking-tight text-foreground">Kondisi Tanah</h3>
                </div>
              </div>

              <!-- Multi-Probe Moisture Comparison Widget -->
              <div class="bg-slate-50 dark:bg-slate-900/50 rounded-xl p-3 border border-slate-200/80 dark:border-slate-800 space-y-2">
                <div class="flex items-center justify-between text-xs">
                  <span class="font-semibold text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                    <Droplet class="w-3.5 h-3.5 text-blue-500" />
                    Kelembaban Multi-Titik
                  </span>
                  <span v-if="moistureAvgValue != null" class="font-bold text-xs text-slate-900 dark:text-slate-100">
                    Avg: <span class="text-blue-500 font-extrabold">{{ moistureAvgValue }}%</span>
                  </span>
                </div>

                <!-- Probe Bars -->
                <div class="space-y-1.5 pt-0.5">
                  <div class="space-y-0.5">
                    <div class="flex justify-between text-[11px]">
                      <span class="text-slate-500 dark:text-slate-400 font-medium">Probe 1 (Titik A)</span>
                      <span class="font-bold text-foreground">{{ probe1Value ?? '--' }}%</span>
                    </div>
                    <div class="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        class="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-500" 
                        :style="{ width: `${Math.min(Math.max(Number(probe1Value || 0), 0), 100)}%` }"
                      />
                    </div>
                  </div>

                  <div class="space-y-0.5">
                    <div class="flex justify-between text-[11px]">
                      <span class="text-slate-500 dark:text-slate-400 font-medium">Probe 2 (Titik B)</span>
                      <span class="font-bold text-foreground">{{ probe2Value ?? '--' }}%</span>
                    </div>
                    <div class="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        class="h-full bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full transition-all duration-500" 
                        :style="{ width: `${Math.min(Math.max(Number(probe2Value || 0), 0), 100)}%` }"
                      />
                    </div>
                  </div>

                  <div class="space-y-0.5">
                    <div class="flex justify-between text-[11px]">
                      <span class="text-slate-500 dark:text-slate-400 font-medium">Probe 3 (Titik C)</span>
                      <span class="font-bold text-foreground">{{ probe3Value ?? '--' }}%</span>
                    </div>
                    <div class="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        class="h-full bg-gradient-to-r from-teal-400 to-cyan-500 rounded-full transition-all duration-500" 
                        :style="{ width: `${Math.min(Math.max(Number(probe3Value || 0), 0), 100)}%` }"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Compact Mini Metrics: pH, Suhu Tanah, EC -->
              <div class="grid grid-cols-3 gap-2">
                <!-- pH Tanah Card -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[58px]">
                  <div class="flex items-center justify-between gap-1">
                    <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">pH</span>
                    <span :class="['text-[9px] font-bold px-1.5 py-0.2 rounded-full border whitespace-nowrap', phStatus.border, phStatus.bg, phStatus.textClass]">
                      {{ phStatus.text }}
                    </span>
                  </div>
                  <div class="mt-1">
                    <span class="text-base sm:text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ phValue ?? '--' }}</span>
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 ml-1">pH</span>
                  </div>
                </div>

                <!-- Suhu Tanah Card -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[58px]">
                  <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">Suhu Tanah</span>
                  <div class="mt-1">
                    <span class="text-base sm:text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ soilTempValue ?? '--' }}</span>
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 ml-1">°C</span>
                  </div>
                </div>

                <!-- EC (Electrical Conductivity) Card -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[58px]">
                  <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">EC Tanah</span>
                  <div class="mt-1">
                    <span class="text-base sm:text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ soilEcValue ?? '--' }}</span>
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 ml-1 font-sans">µS/cm</span>
                  </div>
                </div>
              </div>

            </div>
          </Card>

          <!-- PORTLET 2: KONDISI IOT -->
          <Card class="relative overflow-hidden border border-border/80 bg-white dark:bg-card shadow-none hover:border-blue-500/30 transition-all flex flex-col">
            <div class="p-4 flex flex-col gap-3 flex-1 justify-between">
              <!-- Portlet Header -->
              <div class="flex items-center justify-between pb-2 border-b border-border/40">
                <div class="flex items-center gap-2">
                  <div class="w-7 h-7 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-600">
                    <Cpu class="w-4 h-4" />
                  </div>
                  <h3 class="text-sm font-bold tracking-tight text-foreground">Kondisi IoT</h3>
                </div>
              </div>

              <!-- Highlight Suhu Dalam Panel (Enclosure) & Thermal Status -->
              <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                  <div class="w-9 h-9 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-orange-500 shadow-none">
                    <Thermometer class="w-5 h-5" />
                  </div>
                  <div>
                    <p class="text-xs font-medium text-slate-500 dark:text-slate-400">Suhu Dalam Panel (Box)</p>
                    <div class="flex items-baseline gap-1">
                      <span class="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ enclosureTempValue ?? '--' }}</span>
                      <span class="text-xs text-slate-500 dark:text-slate-400 font-medium">°C</span>
                    </div>
                  </div>
                </div>
                <!-- Thermal status badge -->
                <div class="text-right">
                  <span :class="['text-[11px] font-semibold px-2.5 py-1 rounded-full border flex items-center gap-1.5 shadow-none', thermalStatus.badgeClass]">
                    <span :class="['w-1.5 h-1.5 rounded-full', thermalStatus.dotClass]"></span>
                    {{ thermalStatus.text }}
                  </span>
                  <p class="text-[10px] text-muted-foreground mt-0.5">Status Termal</p>
                </div>
              </div>

              <!-- Mini Grid: Suhu Luar (Ambient), Kelembaban Udara, Status Modbus -->
              <div class="grid grid-cols-3 gap-2">
                <!-- Suhu Luar / Ambient -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[58px]">
                  <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">Suhu Luar</span>
                  <div class="mt-1">
                    <span class="text-base sm:text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ airTempValue ?? '--' }}</span>
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 ml-1">°C</span>
                  </div>
                </div>

                <!-- Kelembaban Udara -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[58px]">
                  <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">Kelembaban</span>
                  <div class="mt-1">
                    <span class="text-base sm:text-lg font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ airHumidityValue ?? '--' }}</span>
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 ml-1">%</span>
                  </div>
                </div>

                <!-- Modbus Status -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[58px]">
                  <span class="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">Modbus Code</span>
                  <div class="mt-1 flex items-center">
                    <span class="text-xs font-bold font-mono bg-slate-200 dark:bg-slate-800 px-1.5 py-0.5 rounded border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200">
                      {{ modbusCodeValue != null ? `Code ${modbusCodeValue}` : 'OK (0)' }}
                    </span>
                  </div>
                </div>
              </div>

            </div>
          </Card>

        </div>

      </div>

    </div>
  </div>
</template>

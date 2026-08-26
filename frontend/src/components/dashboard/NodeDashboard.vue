<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTelemetryStore } from '@/stores/telemetry'
import SensorCard from '@/components/dashboard/SensorCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import SensorLineChart from '@/components/charts/SensorLineChart.vue'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Calendar, Clock, Check, Layers, Sprout, CloudSun, Leaf, Zap, MapPin } from 'lucide-vue-next'
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
  // Fallback to all if category has no sensors
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

// Grouped sensors by category for bento layout
const npkSensors = computed(() => sensors.value.filter(s => getSensorCategory(s) === 'npk'))
const soilSensors = computed(() => sensors.value.filter(s => getSensorCategory(s) === 'soil'))
const envSensors = computed(() => sensors.value.filter(s => getSensorCategory(s) === 'environment'))

// Helper to get sensor value
const getSensorValue = (sensor: any) => {
  if (!latestTelemetry.value) return null
  return latestTelemetry.value[`${sensor.channel_id}_${sensor.thingspeak_field}`]
}

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
const API_BASE_URL = '/api/v1'
const fetchNodeCoords = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/nodes/${props.nodeId}`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!res.ok) return
    const node = await res.json()
    if (node.latitude != null && node.longitude != null) {
      setTimeout(() => initMiniMap(node.latitude, node.longitude), 100)
    }
  } catch { /* no coords, skip */ }
}

onMounted(() => fetchNodeCoords())
onUnmounted(() => { miniMap?.remove(); miniMap = null })
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

    <!-- ═══════════════ BENTO GRID ═══════════════ -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 auto-rows-auto">
      
      <!-- ═══ ROW 1: Hero Status + Mini Map ═══ -->
      
      <!-- Hero Status Card -->
      <Card class="lg:col-span-3 relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/8 via-transparent to-primary/5 pointer-events-none"></div>
        <CardContent class="p-5 relative z-10">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div class="flex flex-col gap-1.5">
              <div class="flex items-center gap-3">
                <h2 class="text-xl sm:text-2xl font-bold tracking-tight">{{ nodeName || nodeId }}</h2>
                <StatusBadge :is-active="isNodeActive" :last-seen="lastSeen" />
              </div>
              <div class="flex items-center gap-4 text-sm text-muted-foreground">
                <span class="flex items-center gap-1.5">
                  <Clock class="w-3.5 h-3.5" />
                  Terakhir diperbarui: {{ formattedLastSeen }}
                </span>
              </div>
            </div>
            <!-- Live Connection Indicator -->
            <div class="flex items-center gap-2 text-sm font-medium">
              <div :class="['w-2.5 h-2.5 rounded-full', isConnected ? 'bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-red-500']"></div>
              <span class="text-muted-foreground">{{ isConnected ? 'Live Connection' : 'Disconnected' }}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Mini Map Card (row-span-2) -->
      <Card class="lg:row-span-2 relative overflow-hidden" style="min-height: 200px">
        <div ref="miniMapContainer" class="w-full h-full absolute inset-0" style="min-height: 200px" />
        <div v-if="!miniMapReady" class="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground gap-2 bg-muted/30">
          <MapPin class="w-8 h-8 opacity-30" />
          <p class="text-xs opacity-50">Lokasi belum diatur</p>
          <a href="/map" class="text-xs text-primary hover:underline opacity-70">Atur di Halaman Maps →</a>
        </div>
      </Card>

      <!-- ═══ ROW 2: NPK Highlight Cards ═══ -->
      <template v-if="npkSensors.length > 0">
        <SensorCard
          v-for="sensor in npkSensors"
          :key="sensor.id"
          :title="sensor.name"
          :value="getSensorValue(sensor)"
          :unit="sensor.unit"
          type="npk"
          size="lg"
          accent-gradient="linear-gradient(135deg, rgba(16,185,129,0.08) 0%, transparent 60%)"
        />
      </template>
      <!-- Fill remaining cols if NPK < 3 -->
      <template v-if="npkSensors.length > 0 && npkSensors.length < 3">
        <div v-for="_ in (3 - npkSensors.length)" :key="'npk-fill-' + _" />
      </template>

      <!-- ═══ ROW 3: Chart + Soil Condition ═══ -->

      <!-- Chart Card (col-span-2, row-span-2) -->
      <Card class="md:col-span-2 lg:col-span-2 lg:row-span-2 relative overflow-hidden flex flex-col">
        <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-50 pointer-events-none"></div>
        <CardContent class="p-4 relative z-10 flex flex-col gap-3 flex-1">
          
          <!-- Header: Category Pills + Time Range -->
          <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-2.5 pb-2.5 border-b border-border/40">
            
            <!-- Category Pills -->
            <div class="flex items-center gap-1 overflow-x-auto pb-1 lg:pb-0 scrollbar-none">
              <button
                @click="selectedCategory = 'npk'"
                :class="['px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all', selectedCategory === 'npk' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 shadow-xs' : 'bg-muted/40 text-muted-foreground hover:text-foreground border border-transparent']"
              >
                <Leaf class="w-3.5 h-3.5 text-emerald-500" />
                <span>Unsur Hara (NPK)</span>
              </button>
              <button
                @click="selectedCategory = 'soil'"
                :class="['px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all', selectedCategory === 'soil' ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 shadow-xs' : 'bg-muted/40 text-muted-foreground hover:text-foreground border border-transparent']"
              >
                <Sprout class="w-3.5 h-3.5 text-amber-500" />
                <span>Kondisi Tanah</span>
              </button>
              <button
                @click="selectedCategory = 'environment'"
                :class="['px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all', selectedCategory === 'environment' ? 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30 shadow-xs' : 'bg-muted/40 text-muted-foreground hover:text-foreground border border-transparent']"
              >
                <CloudSun class="w-3.5 h-3.5 text-blue-500" />
                <span>Lingkungan</span>
              </button>
              <button
                @click="selectedCategory = 'all'"
                :class="['px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 transition-all', selectedCategory === 'all' ? 'bg-primary/15 text-primary border border-primary/30 shadow-xs' : 'bg-muted/40 text-muted-foreground hover:text-foreground border border-transparent']"
              >
                <Layers class="w-3.5 h-3.5" />
                <span>Semua</span>
              </button>
            </div>

            <!-- Time Range Selector -->
            <div class="flex items-center self-end lg:self-auto bg-muted/60 p-0.5 rounded-lg border border-border/40 text-xs">
              <button
                @click="changeRange('1d')"
                :class="['px-2 py-0.5 rounded-md font-medium transition-all flex items-center gap-1', selectedRange === '1d' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground']"
                title="Live stream 24 jam terakhir"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                24J
              </button>
              <button
                @click="changeRange('1w')"
                :class="['px-2 py-0.5 rounded-md font-medium transition-all', selectedRange === '1w' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground']"
                title="Arsip 7 hari terakhir"
              >
                7H
              </button>
              <button
                @click="changeRange('1M')"
                :class="['px-2 py-0.5 rounded-md font-medium transition-all', selectedRange === '1M' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground']"
                title="Arsip 30 hari terakhir (agregasi 1 jam)"
              >
                30H
              </button>
              <button
                @click="selectedRange = 'custom'"
                :class="['px-2 py-0.5 rounded-md font-medium transition-all flex items-center gap-1', selectedRange === 'custom' ? 'bg-background text-foreground shadow-xs' : 'text-muted-foreground hover:text-foreground']"
                title="Pilih tanggal khusus"
              >
                <Calendar class="w-3 h-3" />
              </button>
            </div>
          </div>

          <!-- Custom Date Picker -->
          <div v-if="selectedRange === 'custom'" class="flex flex-wrap items-center gap-2 p-2 bg-muted/30 border border-border/40 rounded-lg text-xs animate-slide-up">
            <div class="flex items-center gap-1.5">
              <span class="text-muted-foreground">Dari:</span>
              <Input type="date" v-model="customStartDate" class="h-7 text-xs w-32 px-2 py-0 bg-background" />
            </div>
            <div class="flex items-center gap-1.5">
              <span class="text-muted-foreground">Sampai:</span>
              <Input type="date" v-model="customEndDate" class="h-7 text-xs w-32 px-2 py-0 bg-background" />
            </div>
            <Button size="sm" variant="default" class="h-7 text-xs px-2.5" @click="applyCustomDate" :disabled="!customStartDate">
              <Check class="w-3 h-3 mr-1" />
              Terapkan
            </Button>
          </div>

          <!-- Chart -->
          <div class="flex-1 min-h-[300px]">
            <SensorLineChart 
              :data="chartData" 
              :title="`Tren ${selectedCategory === 'npk' ? 'Unsur Hara NPK' : (selectedCategory === 'soil' ? 'Kondisi Tanah' : (selectedCategory === 'environment' ? 'Lingkungan & Iklim' : 'Sensor'))}`" 
              :sensors="activeCategorySensors" 
              :is-loading="isArchiveLoading"
            />
          </div>
        </CardContent>
      </Card>

      <!-- Soil Condition Cards (col-span-2) -->
      <div v-if="soilSensors.length > 0" class="md:col-span-2 lg:col-span-2 grid grid-cols-2 gap-3">
        <SensorCard
          v-for="sensor in soilSensors"
          :key="sensor.id"
          :title="sensor.name"
          :value="getSensorValue(sensor)"
          :unit="sensor.unit"
          type="soil"
          accent-gradient="linear-gradient(135deg, rgba(245,158,11,0.06) 0%, transparent 60%)"
        />
      </div>

      <!-- Environment Cards (col-span-2) -->
      <div v-if="envSensors.length > 0" class="md:col-span-2 lg:col-span-2 grid grid-cols-2 gap-3">
        <SensorCard
          v-for="sensor in envSensors"
          :key="sensor.id"
          :title="sensor.name"
          :value="getSensorValue(sensor)"
          :unit="sensor.unit"
          type="temperature"
          accent-gradient="linear-gradient(135deg, rgba(59,130,246,0.06) 0%, transparent 60%)"
        />
      </div>

      <!-- ═══ ROW BOTTOM: Actuator Status ═══ -->
      <div v-if="aktuator" class="col-span-full">
        <Card>
          <CardContent class="p-4">
            <h3 class="text-sm font-semibold mb-3 flex items-center gap-2">
              <Zap class="w-4 h-4 text-amber-500" />
              Status Aktuator
            </h3>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div 
                v-for="a in [
                  { nama: 'Kipas', aktif: aktuator.kipas },
                  { nama: 'Lampu', aktif: aktuator.lampu },
                  { nama: 'Valve', aktif: aktuator.valve },
                ]" 
                :key="a.nama"
                class="flex items-center justify-between p-3 rounded-xl bg-muted/30 border border-border/40"
              >
                <span class="font-medium text-sm">{{ a.nama }}</span>
                <Badge :variant="a.aktif ? 'success' : 'destructive'">
                  {{ a.aktif ? 'ON' : 'OFF' }}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  </div>
</template>

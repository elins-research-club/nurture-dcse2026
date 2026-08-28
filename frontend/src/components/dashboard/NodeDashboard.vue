<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTelemetryStore } from '@/stores/telemetry'
import SensorCard from '@/components/dashboard/SensorCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import SensorLineChart from '@/components/charts/SensorLineChart.vue'
import DashboardPreloader from '@/components/ui/DashboardPreloader.vue'
import { DotPattern } from '@/components/ui/dot-pattern'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Calendar, Clock, Check, Layers, MapPin, 
  Thermometer, Droplet, Sparkles, TrendingUp, 
  TrendingDown, Minus, Info, Activity, AlertTriangle,
  ChevronDown
} from 'lucide-vue-next'
import L from 'leaflet'

const props = defineProps<{
  nodeId: string
  nodeName?: string
}>()

const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()

const isLoading = ref(true)
const isInitialLoaded = ref(false)
const selectedCategory = ref<'all' | 'npk' | 'soil' | 'environment'>('npk')
const isCategoryDropdownOpen = ref(false)
const categoryDropdownRef = ref<HTMLElement | null>(null)

const categoryOptions = [
  {
    id: 'npk' as const,
    label: 'NPK',
    fullLabel: 'Unsur Hara NPK',
    desc: 'Nitrogen (N), Fosfor (P), Kalium (K)',
    icon: '/npk-icon.svg',
    isLucide: false,
    activeColor: 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10'
  },
  {
    id: 'soil' as const,
    label: 'Tanah',
    fullLabel: 'Kondisi Tanah',
    desc: 'pH Tanah, Multi-Probe Kelembapan, EC, Suhu',
    icon: '/soil-icon.svg',
    isLucide: false,
    activeColor: 'text-amber-600 dark:text-amber-400 bg-amber-500/10'
  },
  {
    id: 'environment' as const,
    label: 'IoT & Iklim',
    fullLabel: 'IoT & Mikroklimat',
    desc: 'Suhu Casing/Box, Kelembaban & Suhu Udara',
    icon: '/iot-icon.svg',
    isLucide: false,
    activeColor: 'text-blue-600 dark:text-blue-400 bg-blue-500/10'
  },
  {
    id: 'all' as const,
    label: 'Semua',
    fullLabel: 'Semua Domain Sensor',
    desc: 'Agregasi seluruh telemetri multi-domain',
    icon: null,
    isLucide: true,
    activeColor: 'text-primary bg-primary/10'
  }
]

const currentCategoryMeta = computed(() => {
  return categoryOptions.find(c => c.id === selectedCategory.value) || categoryOptions[0]
})

const selectCategory = (catId: 'all' | 'npk' | 'soil' | 'environment') => {
  selectedCategory.value = catId
  isCategoryDropdownOpen.value = false
}

const handleClickOutsideCategory = (e: MouseEvent) => {
  if (categoryDropdownRef.value && !categoryDropdownRef.value.contains(e.target as Node)) {
    isCategoryDropdownOpen.value = false
  }
}
const selectedRange = ref<'1d' | '1w' | '1M' | 'custom'>('1d')
const customStartDate = ref('')
const customEndDate = ref('')

const sensors = ref<any[]>([])
const telemetry = computed(() => telemetryStore.telemetryHistory[props.nodeId] || [])
const dashboardSummary = computed(() => telemetryStore.dashboardSummaries[props.nodeId])

const loadNodeData = async () => {
  if (!props.nodeId) return
  isLoading.value = true
  try {
    const [sensorsData] = await Promise.all([
      telemetryStore.fetchSensors(props.nodeId),
      telemetryStore.fetchDashboardSummary(props.nodeId),
      telemetryStore.fetchHistory(props.nodeId, { range: '1d' })
    ])
    sensors.value = sensorsData || []
  } catch (err) {
    console.error('Failed to load node data:', err)
  } finally {
    isLoading.value = false
    isInitialLoaded.value = true
  }
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

// Categorize sensors for chart tabs
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

// Helper to get real-time dynamic value prioritizing live WS stream
const getLiveVal = (metric: any) => {
  if (!metric) return null
  if (latestTelemetry.value && metric.field_key && latestTelemetry.value[metric.field_key] !== undefined && latestTelemetry.value[metric.field_key] !== null) {
    const v = Number(latestTelemetry.value[metric.field_key])
    return isNaN(v) ? latestTelemetry.value[metric.field_key] : v
  }
  return metric.current_value ?? null
}

const findSensorByKeywords = (keywords: string[], excludeKeywords: string[] = []) => {
  return sensors.value.find(s => {
    const name = (s.name || '').toLowerCase()
    const type = (s.type || '').toLowerCase()
    if (excludeKeywords.some(ex => name.includes(ex) || type.includes(ex))) return false
    return keywords.some(k => name.includes(k) || type.includes(k))
  })
}

const wrapSensorAsMetric = (s: any) => {
  if (!s) return null
  return {
    id: s.id,
    name: s.name,
    type: s.type,
    unit: s.unit,
    thingspeak_field: s.thingspeak_field,
    channel_id: s.channel_id,
    field_key: `${s.channel_id}_${s.thingspeak_field}`,
    current_value: latestTelemetry.value ? latestTelemetry.value[`${s.channel_id}_${s.thingspeak_field}`] : null,
    min_threshold: s.min_threshold,
    max_threshold: s.max_threshold,
    min_recorded: null,
    max_recorded: null
  }
}

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

const isConnected = computed(() => telemetryStore.isConnected)

const isNodeActive = computed(() => {
  return dashboardSummary.value?.is_active ?? telemetryStore.isNodeOnline(props.nodeId, null)
})

// Formatted last seen timestamp from centralized store
const formattedLastSeen = computed(() => {
  return telemetryStore.getFormattedLastSeen(props.nodeId, dashboardSummary.value?.last_seen)
})

// Grouped Sensors directly from PostgreSQL API with graceful fallback
const npkSensors = computed(() => {
  if (dashboardSummary.value?.npk_sensors?.length) {
    return dashboardSummary.value.npk_sensors
  }
  return sensors.value
    .filter(s => getSensorCategory(s) === 'npk')
    .map(s => wrapSensorAsMetric(s))
    .filter(Boolean)
})

const soilProbes = computed(() => {
  if (dashboardSummary.value?.soil_probes?.length) {
    return dashboardSummary.value.soil_probes
  }
  return sensors.value
    .filter(s => {
      const n = (s.name || '').toLowerCase()
      return n.includes('probe') && (n.includes('soil') || n.includes('titik') || n.includes('1') || n.includes('2') || n.includes('3'))
    })
    .map(s => wrapSensorAsMetric(s))
    .filter(Boolean)
    .sort((a: any, b: any) => (a?.name || '').localeCompare(b?.name || ''))
})

// Specific Portlet Metrics from PostgreSQL API with fallback
const phMetric = computed(() => {
  return dashboardSummary.value?.soil_metrics?.ph || wrapSensorAsMetric(findSensorByKeywords(['ph']))
})
const soilTempMetric = computed(() => {
  return dashboardSummary.value?.soil_metrics?.soil_temp || wrapSensorAsMetric(findSensorByKeywords(['suhu tanah', 'soil temp']))
})
const ecMetric = computed(() => {
  return dashboardSummary.value?.soil_metrics?.ec || wrapSensorAsMetric(findSensorByKeywords(['ec', 'conductivity']))
})
const avgMoistureMetric = computed(() => {
  return dashboardSummary.value?.soil_metrics?.avg_moisture || wrapSensorAsMetric(findSensorByKeywords(['rata-rata kelembapan', 'kelembapan tanah']))
})

const enclosureTempMetric = computed(() => {
  return dashboardSummary.value?.iot_metrics?.enclosure_temp || wrapSensorAsMetric(findSensorByKeywords(['suhu dalam', 'dalam casing', 'dalam box', 'enclosure'], ['luar', 'ambient']))
})
const airTempMetric = computed(() => {
  return dashboardSummary.value?.iot_metrics?.air_temp || wrapSensorAsMetric(findSensorByKeywords(['suhu luar', 'luar casing', 'ambient']))
})
const humidityMetric = computed(() => {
  return dashboardSummary.value?.iot_metrics?.humidity || wrapSensorAsMetric(findSensorByKeywords(['lembab luar', 'kelembaban udara', 'humidity']))
})
const modbusMetric = computed(() => {
  return dashboardSummary.value?.iot_metrics?.modbus || wrapSensorAsMetric(findSensorByKeywords(['modbus', 'error']))
})

const enclosureMinVal = computed(() => {
  if (enclosureTempMetric.value?.min_recorded != null) return enclosureTempMetric.value.min_recorded
  const curr = getLiveVal(enclosureTempMetric.value)
  return curr != null ? curr : null
})

const enclosureMaxVal = computed(() => {
  if (enclosureTempMetric.value?.max_recorded != null) return enclosureTempMetric.value.max_recorded
  const curr = getLiveVal(enclosureTempMetric.value)
  return curr != null ? curr : null
})

// Dynamic Soil pH Status badge
const phStatus = computed(() => {
  const v = getLiveVal(phMetric.value)
  if (v == null) return { text: 'Netral', bg: 'bg-slate-100', border: 'border-slate-200', textClass: 'text-slate-600' }
  const num = Number(v)
  const min = phMetric.value?.min_threshold ?? 5.8
  const max = phMetric.value?.max_threshold ?? 7.5
  if (num < min) return { text: 'Asam', bg: 'bg-rose-500/10', border: 'border-rose-500/30', textClass: 'text-rose-600' }
  if (num <= max) return { text: 'Optimal', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', textClass: 'text-emerald-600' }
  return { text: 'Basa', bg: 'bg-amber-500/10', border: 'border-amber-500/30', textClass: 'text-amber-600' }
})

// Dynamic Safe Threshold from database sensor config or default hardware standard (45°C)
const enclosureSafeThreshold = computed(() => {
  return enclosureTempMetric.value?.max_threshold ?? 45
})

// Dynamic IoT Thermal Status & Saturated NPK-style Gradient Styling
const thermalStatus = computed(() => {
  const v = getLiveVal(enclosureTempMetric.value)
  const num = v != null ? Number(v) : null
  const currentNum = num ?? 0
  const safeLimit = enclosureSafeThreshold.value
  const percentage = safeLimit > 0 ? Math.min(Math.max((currentNum / safeLimit) * 100, 0), 100) : 0
  
  if (num == null) {
    return {
      gradient: 'linear-gradient(135deg, #94A3B8 0%, #64748B 100%)',
      shadowClass: 'shadow-md shadow-slate-500/20',
      barGradient: 'from-white/70 to-white',
      percentage: 0,
      safeLimit
    }
  }
  
  if (num < safeLimit - 5) {
    return {
      // Bright & Fresh Emerald Green gradient (Same as NPK Ideal)
      gradient: 'linear-gradient(135deg, #34D399 0%, #10B981 45%, #059669 100%)',
      shadowClass: 'shadow-md shadow-emerald-400/20 hover:shadow-lg hover:shadow-emerald-400/30',
      barGradient: 'from-white/70 to-white',
      percentage,
      safeLimit
    }
  }
  
  if (num <= safeLimit + 5) {
    return {
      // Bright Warm Amber gradient
      gradient: 'linear-gradient(135deg, #FBBF24 0%, #F59E0B 45%, #D97706 100%)',
      shadowClass: 'shadow-md shadow-amber-400/20 hover:shadow-lg hover:shadow-amber-400/30',
      barGradient: 'from-white/70 to-white',
      percentage,
      safeLimit
    }
  }
  
  return {
    // Bright Coral Rose gradient (Same as NPK High)
    gradient: 'linear-gradient(135deg, #FB7185 0%, #F43F5E 45%, #E11D48 100%)',
    shadowClass: 'shadow-md shadow-rose-400/20 hover:shadow-lg hover:shadow-rose-400/30',
    barGradient: 'from-white/70 to-white',
    percentage,
    safeLimit
  }
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
      attributionControl: false,
      zoomSnap: 1,
      zoomDelta: 1
    }).setView([lat, lng], 19)

    L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', { 
      maxZoom: 20,
      subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
      keepBuffer: 4
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

// Range Label for context
const rangeLabel = computed(() => {
  switch (selectedRange.value) {
    case '1d': return '24 Jam'
    case '1w': return '7 Hari'
    case '1M': return '30 Hari'
    case 'custom': return 'Rentang Kustom'
    default: return '24 Jam'
  }
})

// Dynamic Reactive Analytics Data based on selectedCategory & selectedRange
const analyticsData = computed(() => {
  const feeds = chartData.value || []
  const catSensors = (activeCategorySensors.value || []).filter((s: any) => s.name !== 'Status aktuator')
  
  if (!feeds.length || !catSensors.length) {
    return {
      hasData: false,
      dataPoints: 0,
      summaryTitle: 'Analisis Sensor',
      badgeText: 'Memuat...',
      badgeColor: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700',
      boxClass: 'bg-slate-500/10 dark:bg-slate-900/40 border-slate-500/20 text-slate-700 dark:text-slate-300',
      iconClass: 'text-slate-500 dark:text-slate-400',
      icon: Info,
      metrics: [],
      insightText: 'Menghubungkan data telemetri historis untuk periode ini...',
      npkRatio: null
    }
  }

  // Calculate statistics per active sensor in current category
  const sensorStats = catSensors.map((s: any) => {
    const key = `${s.channel_id}_${s.thingspeak_field}`
    const rawVals = feeds.map((f: any) => parseFloat(f[key])).filter((v: number) => Number.isFinite(v))
    
    if (!rawVals.length) {
      return {
        id: s.id,
        name: s.name,
        unit: s.unit || '',
        current: null,
        avg: null,
        min: null,
        max: null,
        delta: 0,
        trend: 'stable'
      }
    }

    const current = rawVals.length ? Number(rawVals[rawVals.length - 1].toFixed(1)) : null
    const min = rawVals.length ? Number(Math.min(...rawVals).toFixed(1)) : null
    const max = rawVals.length ? Number(Math.max(...rawVals).toFixed(1)) : null
    const sum = rawVals.reduce((a: number, b: number) => a + b, 0)
    const avg = rawVals.length ? Number((sum / rawVals.length).toFixed(1)) : null
    const first = rawVals[0]
    const delta = (current != null && first != null) ? Number((current - first).toFixed(1)) : 0
    const trend = delta > 0.3 ? 'up' : (delta < -0.3 ? 'down' : 'stable')

    return {
      id: s.id,
      name: s.name,
      unit: s.unit || '',
      current,
      avg,
      min,
      max,
      delta,
      trend
    }
  })

  // Universal Sensor Anomaly & Threshold Evaluator
  const anomalies: { sensor: any; severity: 'critical' | 'warning'; message: string }[] = []

  sensorStats.forEach((stat: any) => {
    const s = catSensors.find((cs: any) => cs.id === stat.id) || stat
    const sName = (stat.name || '').toLowerCase()
    const val = stat.current ?? stat.avg

    if (val == null) return

    // 1. Check Explicit Database Thresholds
    if (s.max_threshold != null && stat.max != null && stat.max > s.max_threshold) {
      const isExtreme = stat.max > s.max_threshold * 1.2
      anomalies.push({
        sensor: stat,
        severity: isExtreme ? 'critical' : 'warning',
        message: `${stat.name} menyentuh angka ${stat.max} ${stat.unit} (melebihi ambang batas maksimal ${s.max_threshold} ${stat.unit}).`
      })
      return
    }
    if (s.min_threshold != null && stat.min != null && stat.min < s.min_threshold) {
      const isExtreme = stat.min < s.min_threshold * 0.8
      anomalies.push({
        sensor: stat,
        severity: isExtreme ? 'critical' : 'warning',
        message: `${stat.name} turun hingga ${stat.min} ${stat.unit} (di bawah batas minimal ${s.min_threshold} ${stat.unit}).`
      })
      return
    }

    // 2. Intelligent Agronomic & Hardware Standard Fallbacks
    if (sName.includes('ph')) {
      if (stat.avg != null && (stat.avg < 5.0 || stat.avg > 8.5)) {
        anomalies.push({
          sensor: stat,
          severity: 'critical',
          message: `Nilai pH rata-rata (${stat.avg}) tergolong ekstrem. Segera lakukan penyesuaian media tanah.`
        })
      } else if (stat.avg != null && (stat.avg < 5.8 || stat.avg > 7.5)) {
        anomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Nilai pH rata-rata (${stat.avg}) berada di luar ambang netral ideal 6.0–7.0 pada periode ${rangeLabel.value}.`
        })
      }
    } else if (sName.includes('nitrogen') || sName.includes('nitrat')) {
      if (val < 20) {
        anomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Nitrogen rata-rata berada di bawah target (${val} mg/kg). Pertimbangkan pemupukan N pada siklus berikutnya.`
        })
      } else if (val > 70) {
        anomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Nitrogen rata-rata tinggi (${val} mg/kg). Hindari akumulasi pupuk berlebih.`
        })
      }
    } else if (sName.includes('phosphor') || sName.includes('fosfor')) {
      if (val < 15) {
        anomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Fosfor rata-rata (${val} mg/kg) di bawah target optimal untuk perkembangan akar.`
        })
      }
    } else if (sName.includes('potassium') || sName.includes('kalium')) {
      if (val < 20) {
        anomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Kalium rata-rata (${val} mg/kg) di bawah target untuk ketahanan tanaman.`
        })
      }
    } else if (sName.includes('suhu dalam') || sName.includes('enclosure') || sName.includes('box')) {
      if (stat.max != null && stat.max > 45) {
        anomalies.push({
          sensor: stat,
          severity: 'critical',
          message: `Suhu box panel IoT mencapai puncak ${stat.max}°C (di atas batas aman 45°C). Pastikan kipas & ventilasi box beroperasi optimal.`
        })
      } else if (stat.max != null && stat.max > 38) {
        anomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Suhu box panel IoT sempat menghangat hingga ${stat.max}°C pada rentang ${rangeLabel.value}.`
        })
      }
    } else if (sName.includes('suhu') || sName.includes('temp')) {
      if (stat.max != null && stat.max > 38) {
        anomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Suhu udara lingkungan sempat menyentuh ${stat.max}°C pada periode ${rangeLabel.value}.`
        })
      }
    } else if (sName.includes('lembab') || sName.includes('moisture') || sName.includes('humidity')) {
      if (sName.includes('tanah') || sName.includes('probe')) {
        if (stat.min != null && stat.min < 25) {
          anomalies.push({
            sensor: stat,
            severity: 'warning',
            message: `Kelembaban tanah sempat turun hingga ${stat.min}%. Rekomendasikan pengairan/irigasi.`
          })
        }
      } else {
        if (stat.min != null && stat.min < 35) {
          anomalies.push({
            sensor: stat,
            severity: 'warning',
            message: `Kelembaban udara lingkungan rendah (${stat.min}%). Kondisi cenderung kering.`
          })
        }
      }
    }
  })

  // Determine Semantic Wrapper Colors and Status
  const criticalAnomaly = anomalies.find(a => a.severity === 'critical')
  const warningAnomaly = anomalies.find(a => a.severity === 'warning')

  let defaultBadgeText = 'Status Optimal'
  let defaultBadgeColor = 'bg-emerald-500/15 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
  let defaultBoxClass = 'bg-emerald-500/10 dark:bg-emerald-950/30 border-emerald-500/20 text-emerald-900 dark:text-emerald-300'
  let defaultIconClass = 'text-emerald-600 dark:text-emerald-400'
  let defaultIcon = Check
  let defaultInsightText = `Seluruh telemetri dalam rentang ${rangeLabel.value} terpantau stabil dalam batas operasional normal.`

  // 1. Kategori NPK
  if (selectedCategory.value === 'npk') {
    const nStat = sensorStats.find((s: any) => s.name.toLowerCase().includes('nitrogen') || s.name.toLowerCase().includes('n'))
    const pStat = sensorStats.find((s: any) => s.name.toLowerCase().includes('phosphor') || s.name.toLowerCase().includes('p'))
    const kStat = sensorStats.find((s: any) => s.name.toLowerCase().includes('potassium') || s.name.toLowerCase().includes('kalium') || s.name.toLowerCase().includes('k'))
    
    const nVal = Number((nStat?.current ?? nStat?.avg ?? 0).toFixed(1))
    const pVal = Number((pStat?.current ?? pStat?.avg ?? 0).toFixed(1))
    const kVal = Number((kStat?.current ?? kStat?.avg ?? 0).toFixed(1))
    const total = (nVal + pVal + kVal) || 1

    const distributionWidget = {
      title: 'Rasio Keseimbangan NPK',
      subtitle: `${nVal} : ${pVal} : ${kVal}`,
      segments: [
        { label: `N: ${Math.round((nVal / total) * 100)}%`, percent: Math.round((nVal / total) * 100), color: 'bg-emerald-500', textClass: 'text-emerald-600 dark:text-emerald-400' },
        { label: `P: ${Math.round((pVal / total) * 100)}%`, percent: Math.round((pVal / total) * 100), color: 'bg-blue-500', textClass: 'text-blue-600 dark:text-blue-400' },
        { label: `K: ${Math.round((kVal / total) * 100)}%`, percent: Math.round((kVal / total) * 100), color: 'bg-purple-500', textClass: 'text-purple-600 dark:text-purple-400' }
      ]
    }

    defaultBadgeText = 'Nutrisi Seimbang'
    defaultInsightText = `Keseimbangan NPK dalam rentang ${rangeLabel.value} terpantau stabil. Rasio N:P:K (${nVal} : ${pVal} : ${kVal}) mendukung fase vegetatif tanaman.`

    return {
      hasData: true,
      dataPoints: feeds.length,
      summaryTitle: 'Analisis Nutrisi NPK',
      badgeText: criticalAnomaly ? 'Peringatan Kritis' : (warningAnomaly ? (warningAnomaly.sensor.name + ' Perhatian') : defaultBadgeText),
      badgeColor: criticalAnomaly ? 'bg-rose-500/15 border-rose-500/30 text-rose-700 dark:text-rose-400' : (warningAnomaly ? 'bg-amber-500/15 border-amber-500/30 text-amber-700 dark:text-amber-400' : defaultBadgeColor),
      boxClass: criticalAnomaly ? 'bg-rose-500/10 dark:bg-rose-950/30 border-rose-500/25 text-rose-900 dark:text-rose-300' : (warningAnomaly ? 'bg-amber-500/10 dark:bg-amber-950/30 border-amber-500/25 text-amber-900 dark:text-amber-300' : defaultBoxClass),
      iconClass: criticalAnomaly ? 'text-rose-600 dark:text-rose-400' : (warningAnomaly ? 'text-amber-600 dark:text-amber-400' : defaultIconClass),
      icon: criticalAnomaly ? AlertTriangle : (warningAnomaly ? AlertTriangle : defaultIcon),
      metrics: sensorStats,
      insightText: criticalAnomaly?.message || warningAnomaly?.message || defaultInsightText,
      distributionWidget
    }
  }

  // 2. Kategori Tanah
  if (selectedCategory.value === 'soil') {
    const moistProbes = sensorStats.filter((s: any) => s.name.toLowerCase().includes('probe') || s.name.toLowerCase().includes('kelembapan'))
    
    const avgMoist = moistProbes.length > 0 
      ? Number((moistProbes.reduce((sum: number, p: any) => sum + (p.avg ?? p.current ?? 0), 0) / moistProbes.length).toFixed(1))
      : null

    const p1 = Number((moistProbes[0]?.current ?? moistProbes[0]?.avg ?? 33).toFixed(1))
    const p2 = Number((moistProbes[1]?.current ?? moistProbes[1]?.avg ?? 33).toFixed(1))
    const p3 = Number((moistProbes[2]?.current ?? moistProbes[2]?.avg ?? 34).toFixed(1))
    const pTotal = (p1 + p2 + p3) || 1

    const distributionWidget = {
      title: 'Distribusi Multi-Probe Kelembaban',
      subtitle: `Rata-rata: ${avgMoist ?? '--'}%`,
      segments: [
        { label: `P1: ${Math.round((p1 / pTotal) * 100)}%`, percent: Math.round((p1 / pTotal) * 100), color: 'bg-sky-400', textClass: 'text-sky-600 dark:text-sky-400' },
        { label: `P2: ${Math.round((p2 / pTotal) * 100)}%`, percent: Math.round((p2 / pTotal) * 100), color: 'bg-blue-500', textClass: 'text-blue-600 dark:text-blue-400' },
        { label: `P3: ${Math.round((p3 / pTotal) * 100)}%`, percent: Math.round((p3 / pTotal) * 100), color: 'bg-indigo-600', textClass: 'text-indigo-600 dark:text-indigo-400' }
      ]
    }

    defaultBadgeText = 'Media Tanah Prima'
    defaultInsightText = `Kelembaban rata-rata perakaran (${avgMoist ?? '--'}%) terjaga stabil sepanjang ${rangeLabel.value}. Daya hantar listrik (EC) optimal tanpa akumulasi garam berlebih.`

    return {
      hasData: true,
      dataPoints: feeds.length,
      summaryTitle: 'Analisis Kondisi Tanah',
      badgeText: criticalAnomaly ? 'Peringatan Kritis' : (warningAnomaly ? (warningAnomaly.sensor.name + ' Perhatian') : defaultBadgeText),
      badgeColor: criticalAnomaly ? 'bg-rose-500/15 border-rose-500/30 text-rose-700 dark:text-rose-400' : (warningAnomaly ? 'bg-amber-500/15 border-amber-500/30 text-amber-700 dark:text-amber-400' : defaultBadgeColor),
      boxClass: criticalAnomaly ? 'bg-rose-500/10 dark:bg-rose-950/30 border-rose-500/25 text-rose-900 dark:text-rose-300' : (warningAnomaly ? 'bg-amber-500/10 dark:bg-amber-950/30 border-amber-500/25 text-amber-900 dark:text-amber-300' : defaultBoxClass),
      iconClass: criticalAnomaly ? 'text-rose-600 dark:text-rose-400' : (warningAnomaly ? 'text-amber-600 dark:text-amber-400' : defaultIconClass),
      icon: criticalAnomaly ? AlertTriangle : (warningAnomaly ? AlertTriangle : defaultIcon),
      metrics: sensorStats,
      insightText: criticalAnomaly?.message || warningAnomaly?.message || defaultInsightText,
      distributionWidget
    }
  }

  // 3. Kategori IoT & Iklim
  if (selectedCategory.value === 'environment') {
    const encStat = sensorStats.find((s: any) => s.name.toLowerCase().includes('suhu dalam') || s.name.toLowerCase().includes('enclosure') || s.name.toLowerCase().includes('box'))
    const airStat = sensorStats.find((s: any) => s.name.toLowerCase().includes('suhu luar') || s.name.toLowerCase().includes('air'))
    
    const encVal = Number((encStat?.current ?? encStat?.avg ?? 35).toFixed(1))
    const airVal = Number((airStat?.current ?? airStat?.avg ?? 28).toFixed(1))
    const tTotal = (encVal + airVal) || 1

    const distributionWidget = {
      title: 'Perbandingan Suhu Box vs Lingkungan',
      subtitle: `Δ ${(encVal - airVal).toFixed(1)}°C`,
      segments: [
        { label: `Box: ${Math.round((encVal / tTotal) * 100)}%`, percent: Math.round((encVal / tTotal) * 100), color: 'bg-rose-500', textClass: 'text-rose-600 dark:text-rose-400' },
        { label: `Luar: ${Math.round((airVal / tTotal) * 100)}%`, percent: Math.round((airVal / tTotal) * 100), color: 'bg-amber-500', textClass: 'text-amber-600 dark:text-amber-400' }
      ]
    }

    defaultBadgeText = 'Termal & Uptime Aman'
    defaultInsightText = `Suhu operasional box panel (${encStat?.avg ?? '--'}°C) berada di bawah batas aman. Manajemen termal perangkat stabil selama ${rangeLabel.value}.`

    return {
      hasData: true,
      dataPoints: feeds.length,
      summaryTitle: 'Analisis IoT & Mikroklimat',
      badgeText: criticalAnomaly ? 'Peringatan Termal' : (warningAnomaly ? (warningAnomaly.sensor.name + ' Perhatian') : defaultBadgeText),
      badgeColor: criticalAnomaly ? 'bg-rose-500/15 border-rose-500/30 text-rose-700 dark:text-rose-400' : (warningAnomaly ? 'bg-amber-500/15 border-amber-500/30 text-amber-700 dark:text-amber-400' : defaultBadgeColor),
      boxClass: criticalAnomaly ? 'bg-rose-500/10 dark:bg-rose-950/30 border-rose-500/25 text-rose-900 dark:text-rose-300' : (warningAnomaly ? 'bg-amber-500/10 dark:bg-amber-950/30 border-amber-500/25 text-amber-900 dark:text-amber-300' : defaultBoxClass),
      iconClass: criticalAnomaly ? 'text-rose-600 dark:text-rose-400' : (warningAnomaly ? 'text-amber-600 dark:text-amber-400' : defaultIconClass),
      icon: criticalAnomaly ? AlertTriangle : (warningAnomaly ? AlertTriangle : defaultIcon),
      metrics: sensorStats,
      insightText: criticalAnomaly?.message || warningAnomaly?.message || defaultInsightText,
      distributionWidget
    }
  }

  // 4. Kategori Semua Sensor
  const distributionWidget = {
    title: 'Sebaran Kanal Sensor Telemetri',
    subtitle: `${sensorStats.length} Kanal Aktif`,
    segments: [
      { label: 'NPK: 33%', percent: 33, color: 'bg-emerald-500', textClass: 'text-emerald-600 dark:text-emerald-400' },
      { label: 'Tanah: 45%', percent: 45, color: 'bg-amber-500', textClass: 'text-amber-600 dark:text-amber-400' },
      { label: 'IoT: 22%', percent: 22, color: 'bg-blue-500', textClass: 'text-blue-600 dark:text-blue-400' }
    ]
  }

  defaultBadgeText = `${sensorStats.length} Kanal Aktif`
  defaultInsightText = `Berhasil mengagregasi ${feeds.length} titik data telemetri untuk seluruh domain sensor pada rentang ${rangeLabel.value}.`

  return {
    hasData: true,
    dataPoints: feeds.length,
    summaryTitle: 'Ikhtisar Seluruh Telemetri',
    badgeText: criticalAnomaly ? 'Peringatan Kritis' : (warningAnomaly ? (warningAnomaly.sensor.name + ' Perhatian') : defaultBadgeText),
    badgeColor: criticalAnomaly ? 'bg-rose-500/15 border-rose-500/30 text-rose-700 dark:text-rose-400' : (warningAnomaly ? 'bg-amber-500/15 border-amber-500/30 text-amber-700 dark:text-amber-400' : 'bg-primary/15 border-primary/30 text-primary'),
    boxClass: criticalAnomaly ? 'bg-rose-500/10 dark:bg-rose-950/30 border-rose-500/25 text-rose-900 dark:text-rose-300' : (warningAnomaly ? 'bg-amber-500/10 dark:bg-amber-950/30 border-amber-500/25 text-amber-900 dark:text-amber-300' : 'bg-sky-500/10 dark:bg-sky-950/30 border-sky-500/20 text-sky-900 dark:text-sky-300'),
    iconClass: criticalAnomaly ? 'text-rose-600 dark:text-rose-400' : (warningAnomaly ? 'text-amber-600 dark:text-amber-400' : 'text-sky-600 dark:text-sky-400'),
    icon: criticalAnomaly ? AlertTriangle : (warningAnomaly ? AlertTriangle : Info),
    metrics: sensorStats.slice(0, 3),
    insightText: criticalAnomaly?.message || warningAnomaly?.message || defaultInsightText,
    distributionWidget
  }
})

onMounted(() => {
  fetchNodeCoords()
  window.addEventListener('click', handleClickOutsideCategory)
})

onUnmounted(() => {
  if (miniMap) {
    miniMap.remove()
    miniMap = null
  }
  window.removeEventListener('click', handleClickOutsideCategory)
})
</script>

<template>
  <div class="w-full">
    <!-- Loading Screen Preloader -->
    <DashboardPreloader v-if="!isInitialLoaded || (isLoading && sensors.length === 0)" />

    <!-- No Sensors State (Shown only after loading completes and there are genuinely no sensors) -->
    <div v-else-if="isInitialLoaded && sensors.length === 0" class="py-16 text-center text-muted-foreground border border-dashed rounded-2xl">
      Belum ada sensor yang terpasang pada node ini. Tambahkan sensor di menu Pengaturan.
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
                <h2 class="text-lg sm:text-xl font-bold tracking-tight">{{ nodeName || nodeId }}</h2>
                <p class="text-xs text-muted-foreground font-mono">ID: {{ nodeId }}</p>
              </div>

              <!-- Single Node Status Badge on top-right -->
              <StatusBadge 
                :is-active="isNodeActive" 
                :last-seen="telemetryStore.getNodeLastSeen(nodeId, dashboardSummary?.last_seen)" 
                class="shrink-0" 
              />
            </div>

            <!-- Footer: Last seen & GPS Coordinates (Horizontal Layout with Larger Text) -->
            <div class="flex flex-wrap items-center justify-between gap-2.5 pt-2.5 border-t border-border/40 text-xs sm:text-sm text-muted-foreground">
              <div class="flex items-center gap-1.5">
                <Clock class="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span class="text-xs sm:text-sm">Update: <strong class="text-foreground font-bold">{{ formattedLastSeen }}</strong></span>
              </div>
              <div v-if="nodeCoords" class="flex items-center gap-1.5">
                <MapPin class="w-4 h-4 text-blue-500 shrink-0" />
                <span class="text-xs sm:text-sm font-bold text-foreground/90">{{ nodeCoords.lat.toFixed(5) }}, {{ nodeCoords.lng.toFixed(5) }}</span>
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
              class="px-2.5 py-1 rounded-lg text-xs font-bold bg-white/90 backdrop-blur-md text-foreground border border-border/70 hover:bg-white flex items-center gap-1.5 transition-all hover:scale-105"
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

        <!-- CARD 3: Compact Actuator Control Status (Enlarged Height & Typography) -->
        <Card v-if="aktuator" class="relative overflow-hidden border border-border/80 bg-white dark:bg-card shadow-none hover:border-amber-500/30 transition-all">
          <div class="p-4 sm:p-4.5 flex flex-col gap-3.5">
            <!-- Header: Title, Icon -->
            <div class="flex items-center gap-2">
              <img src="/actuator-icon.svg" alt="Status Aktuator" class="w-5 h-5 object-contain dark:invert shrink-0" />
              <h4 class="text-base sm:text-lg font-bold tracking-tight text-foreground">Status Aktuator</h4>
            </div>

            <!-- 3 Expanded State Chips -->
            <div class="grid grid-cols-3 gap-2">
              <div 
                v-for="a in [
                  { nama: 'Kipas', aktif: aktuator.kipas },
                  { nama: 'Lampu', aktif: aktuator.lampu },
                  { nama: 'Valve', aktif: aktuator.valve },
                ]" 
                :key="a.nama"
                :class="[
                  'py-3 px-2 rounded-xl text-xs sm:text-sm font-medium border flex flex-col items-center justify-center gap-1.5 transition-all text-center min-h-[72px] sm:min-h-[78px]',
                  a.aktif 
                    ? 'bg-emerald-500/10 dark:bg-emerald-950/30 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 shadow-xs' 
                    : 'bg-slate-50 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800 text-slate-500 dark:text-slate-400'
                ]"
              >
                <!-- Actuator Name & Status Dot -->
                <div class="flex items-center gap-1.5">
                  <div :class="['w-2 h-2 rounded-full shrink-0', a.aktif ? 'bg-emerald-500 animate-pulse ring-2 ring-emerald-500/30' : 'bg-slate-400 dark:bg-slate-600']"></div>
                  <span class="text-xs sm:text-sm font-extrabold text-foreground tracking-tight">{{ a.nama }}</span>
                </div>
                
                <!-- ON / OFF Pill Badge -->
                <span 
                  :class="[
                    'text-[11px] sm:text-xs font-black tracking-wider px-2.5 py-0.5 rounded-md leading-tight uppercase',
                    a.aktif 
                      ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 font-black' 
                      : 'bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-bold'
                  ]"
                >
                  {{ a.aktif ? 'ON' : 'OFF' }}
                </span>
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
            :value="getLiveVal(sensor)"
            :unit="sensor.unit"
            type="npk"
            size="default"
            :min-threshold="sensor.min_threshold"
            :max-threshold="sensor.max_threshold"
          />
        </div>

        <!-- ROW 2: Split Row: Line Chart (~67%) + Quick Analytics & Health Insights (~33%) -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-stretch">
          
          <!-- LEFT COL (lg:col-span-8): Wide Sensor Trends Line Chart -->
          <Card class="lg:col-span-8 relative overflow-hidden flex flex-col border border-border/80 bg-white dark:bg-card shadow-none min-h-[460px]">
            <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-30 pointer-events-none"></div>
            <CardContent class="p-4 relative z-10 flex flex-col gap-2 flex-1">
              
              <!-- Chart Header: Category Pills + Time Range -->
              <div class="flex flex-wrap items-center justify-between gap-2.5 pb-2 border-b border-border/40">
                
                <!-- Category Dropdown Selector -->
                <div class="relative" ref="categoryDropdownRef">
                  <button
                    type="button"
                    @click.stop="isCategoryDropdownOpen = !isCategoryDropdownOpen"
                    class="h-8.5 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200/80 dark:hover:bg-slate-700/80 border border-slate-200/90 dark:border-slate-700/90 text-foreground text-xs sm:text-sm font-bold flex items-center gap-2 transition-all cursor-pointer shadow-2xs select-none"
                    :title="`Kategori: ${currentCategoryMeta.fullLabel}`"
                  >
                    <!-- Icon -->
                    <img 
                      v-if="!currentCategoryMeta.isLucide" 
                      :src="currentCategoryMeta.icon!" 
                      :alt="currentCategoryMeta.label" 
                      class="w-4 h-4 object-contain dark:invert shrink-0" 
                    />
                    <Layers v-else class="w-4 h-4 text-primary shrink-0" />

                    <!-- Selected Category Label -->
                    <span class="tracking-tight">{{ currentCategoryMeta.fullLabel }}</span>

                    <!-- Chevron -->
                    <ChevronDown 
                      class="w-3.5 h-3.5 text-muted-foreground transition-transform duration-200" 
                      :class="isCategoryDropdownOpen ? 'rotate-180 text-foreground' : ''" 
                    />
                  </button>

                  <!-- Dropdown Menu Popover -->
                  <div
                    v-if="isCategoryDropdownOpen"
                    class="absolute left-0 top-full mt-1.5 w-60 z-50 rounded-2xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200/90 dark:border-slate-800 shadow-2xl p-1.5 flex flex-col gap-1 animate-in fade-in zoom-in-95 duration-150 select-none"
                  >
                    <div class="px-2.5 py-1 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                      Pilih Domain Sensor
                    </div>

                    <button
                      v-for="cat in categoryOptions"
                      :key="cat.id"
                      type="button"
                      @click="selectCategory(cat.id)"
                      :class="[
                        'w-full px-2.5 py-2 rounded-xl text-left flex items-center justify-between gap-2.5 transition-all cursor-pointer text-xs sm:text-sm',
                        selectedCategory === cat.id 
                          ? `${cat.activeColor} font-black border border-border/40 shadow-xs` 
                          : 'text-foreground hover:bg-slate-100/80 dark:hover:bg-slate-800/80 border border-transparent font-medium'
                      ]"
                    >
                      <div class="flex items-center gap-2.5 min-w-0">
                        <div class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0 border border-slate-200/60 dark:border-slate-700/60">
                          <img 
                            v-if="!cat.isLucide" 
                            :src="cat.icon!" 
                            :alt="cat.label" 
                            class="w-4 h-4 object-contain dark:invert" 
                          />
                          <Layers v-else class="w-4 h-4 text-primary" />
                        </div>
                        <div class="truncate">
                          <div class="font-extrabold text-foreground leading-tight">{{ cat.fullLabel }}</div>
                          <div class="text-[10px] text-muted-foreground truncate">{{ cat.desc }}</div>
                        </div>
                      </div>

                      <Check v-if="selectedCategory === cat.id" class="w-4 h-4 shrink-0 stroke-[2.5]" />
                    </button>
                  </div>
                </div>

                <!-- Time Range Selector (Enlarged) -->
                <div class="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl border border-slate-200/80 dark:border-slate-700/80 text-xs sm:text-sm">
                  <button
                    @click="changeRange('1d')"
                    :class="[
                      'px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5 text-xs sm:text-sm',
                      selectedRange === '1d' 
                        ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    24J
                  </button>
                  <button
                    @click="changeRange('1w')"
                    :class="[
                      'px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer text-xs sm:text-sm',
                      selectedRange === '1w' 
                        ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    7H
                  </button>
                  <button
                    @click="changeRange('1M')"
                    :class="[
                      'px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer text-xs sm:text-sm',
                      selectedRange === '1M' 
                        ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    30H
                  </button>
                  <button
                    @click="selectedRange = 'custom'"
                    :class="[
                      'px-2 py-1 rounded-lg font-bold transition-all cursor-pointer text-xs sm:text-sm',
                      selectedRange === 'custom' 
                        ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                    title="Rentang Kustom"
                  >
                    <Calendar class="w-4 h-4" />
                  </button>
                </div>
              </div>

              <!-- Custom Date Picker -->
              <div v-if="selectedRange === 'custom'" class="flex flex-wrap items-center gap-2.5 p-2.5 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 rounded-xl text-xs sm:text-sm animate-slide-up">
                <div class="flex items-center gap-2">
                  <span class="text-slate-500 dark:text-slate-400 font-semibold">Dari:</span>
                  <Input type="date" v-model="customStartDate" class="h-8 text-xs sm:text-sm w-36 px-2.5 py-0 bg-white dark:bg-slate-800" />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-slate-500 dark:text-slate-400 font-semibold">Sampai:</span>
                  <Input type="date" v-model="customEndDate" class="h-8 text-xs sm:text-sm w-36 px-2.5 py-0 bg-white dark:bg-slate-800" />
                </div>
                <Button size="sm" variant="default" class="h-8 text-xs sm:text-sm px-3 shadow-none font-bold" @click="applyCustomDate" :disabled="!customStartDate">
                  <Check class="w-3.5 h-3.5 mr-1" />
                  Terapkan
                </Button>
              </div>

              <!-- Chart Visual Canvas (Fills 100% of Stretched Card Height) -->
              <div class="w-full flex-1 flex flex-col min-h-[350px] pt-1">
                <SensorLineChart 
                  :data="chartData" 
                  :title="`Tren ${selectedCategory === 'npk' ? 'Unsur Hara NPK' : (selectedCategory === 'soil' ? 'Kondisi Tanah' : (selectedCategory === 'environment' ? 'Kondisi IoT' : 'Sensor'))}`" 
                  :sensors="activeCategorySensors" 
                  :is-loading="isArchiveLoading || isLoading || (!isInitialLoaded && chartData.length === 0)"
                />
              </div>
            </CardContent>
          </Card>

          <!-- RIGHT COL (lg:col-span-4): Dynamic Category-Aware Analytics & Insights Card (Enlarged Typography) -->
          <Card class="lg:col-span-4 relative overflow-hidden flex flex-col border border-border/80 bg-white dark:bg-card shadow-none min-h-[460px]">
            <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-primary/5 pointer-events-none"></div>
            <CardContent class="p-4 sm:p-4.5 relative z-10 flex flex-col justify-between gap-3 flex-1 h-full">
              
              <!-- Header: Title (Badge removed, icon color neutral/black) -->
              <div class="pb-2.5 border-b border-border/40">
                <div class="space-y-0.5">
                  <div class="flex items-center gap-2">
                    <Sparkles class="w-5 h-5 text-foreground shrink-0" />
                    <h4 class="text-base sm:text-lg font-extrabold text-foreground tracking-tight">{{ analyticsData.summaryTitle }}</h4>
                  </div>
                  <p class="text-xs sm:text-sm text-muted-foreground font-medium">Periode {{ rangeLabel }} ({{ analyticsData.dataPoints }} data)</p>
                </div>
              </div>

              <!-- Unified Distribution Bar (Present in ALL categories: NPK, Tanah, IoT, Semua) -->
              <div v-if="analyticsData.distributionWidget" class="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 space-y-2">
                <div class="flex items-center justify-between text-xs sm:text-sm font-bold text-foreground">
                  <span>{{ analyticsData.distributionWidget.title }}</span>
                  <span class="text-xs sm:text-sm font-extrabold text-muted-foreground">
                    {{ analyticsData.distributionWidget.subtitle }}
                  </span>
                </div>
                <div class="h-2.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden flex">
                  <div 
                    v-for="(seg, i) in analyticsData.distributionWidget.segments" 
                    :key="i"
                    :class="[seg.color, 'h-full transition-all duration-500']" 
                    :style="{ width: `${seg.percent}%` }"
                    :title="seg.label"
                  />
                </div>
                <div class="flex justify-between text-xs sm:text-sm font-extrabold pt-0.5">
                  <span 
                    v-for="(seg, i) in analyticsData.distributionWidget.segments" 
                    :key="i"
                    :class="seg.textClass"
                  >
                    {{ seg.label }}
                  </span>
                </div>
              </div>

              <!-- Dynamic Key Period Sensor Metrics -->
              <div class="space-y-2.5 flex-1 flex flex-col justify-center">
                <div 
                  v-for="stat in analyticsData.metrics.slice(0, 3)" 
                  :key="stat.id"
                  class="p-2.5 sm:p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between gap-2.5"
                >
                  <div class="space-y-1">
                    <span class="text-sm sm:text-base font-extrabold text-foreground block truncate max-w-[130px] sm:max-w-[160px]">{{ stat.name }}</span>
                    <div class="flex items-center gap-1.5 text-xs sm:text-sm text-muted-foreground font-medium">
                      <span>Rata-rata: <strong class="text-sm sm:text-base font-extrabold text-foreground">{{ stat.avg ?? '--' }}{{ stat.unit }}</strong></span>
                    </div>
                  </div>

                  <!-- Min / Max & Trend Badge -->
                  <div class="flex items-center gap-2.5 text-right shrink-0">
                    <div class="text-xs sm:text-sm text-muted-foreground leading-tight font-semibold">
                      <div>Min: <span class="font-extrabold text-foreground">{{ stat.min != null ? (typeof stat.min === 'number' ? Number(stat.min.toFixed(1)) : stat.min) : '--' }}</span></div>
                      <div>Max: <span class="font-extrabold text-foreground">{{ stat.max != null ? (typeof stat.max === 'number' ? Number(stat.max.toFixed(1)) : stat.max) : '--' }}</span></div>
                    </div>
                    <div 
                      :class="[
                        'w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center border shrink-0',
                        stat.trend === 'up' 
                          ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-600' 
                          : (stat.trend === 'down' 
                            ? 'bg-rose-500/15 border-rose-500/30 text-rose-600' 
                            : 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500')
                      ]"
                      :title="`Delta tren: ${stat.delta > 0 ? '+' : ''}${stat.delta} ${stat.unit}`"
                    >
                      <TrendingUp v-if="stat.trend === 'up'" class="w-4 h-4" />
                      <TrendingDown v-else-if="stat.trend === 'down'" class="w-4 h-4" />
                      <Minus v-else class="w-4 h-4" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Contextual Agronomy Insight Box -->
              <div 
                :class="[
                  'p-3 rounded-xl border text-xs sm:text-sm flex items-start gap-2.5 leading-relaxed min-h-[64px] transition-colors duration-200',
                  analyticsData.boxClass || 'bg-emerald-500/10 dark:bg-emerald-950/30 border-emerald-500/20 text-emerald-900 dark:text-emerald-300'
                ]"
              >
                <component 
                  :is="analyticsData.icon || Info" 
                  :class="['w-5 h-5 shrink-0 mt-0.5', analyticsData.iconClass || 'text-emerald-600 dark:text-emerald-400']" 
                />
                <p class="text-xs sm:text-sm font-semibold">{{ analyticsData.insightText }}</p>
              </div>

            </CardContent>
          </Card>

        </div>

        <!-- ROW 3: Dua Portlet Berdampingan (Kondisi Tanah & Kondisi IoT) -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          
          <!-- PORTLET 1: KONDISI TANAH -->
          <Card class="relative overflow-hidden border border-border/80 bg-white dark:bg-card shadow-none hover:border-amber-500/30 transition-all flex flex-col">
            <div class="p-4 flex flex-col gap-3 flex-1 justify-between">
              <!-- Portlet Header -->
              <div class="flex items-center justify-between pb-2 border-b border-border/40">
                <div class="flex items-center gap-2">
                  <img src="/soil-icon.svg" alt="Kondisi Tanah" class="w-5 h-5 object-contain dark:invert shrink-0" />
                  <h4 class="text-base sm:text-lg font-bold tracking-tight text-foreground">Kondisi Tanah</h4>
                </div>
              </div>

              <!-- Multi-Probe Moisture Comparison Widget -->
              <div class="bg-slate-50 dark:bg-slate-900/50 rounded-xl p-3 border border-slate-200/80 dark:border-slate-800 space-y-2">
                <div class="flex items-center justify-between text-sm">
                  <span class="font-semibold text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                    <Droplet class="w-4 h-4 text-blue-500" />
                    {{ avgMoistureMetric?.name || 'Kelembaban Multi-Titik' }}
                  </span>
                  <span v-if="getLiveVal(avgMoistureMetric) != null" class="font-bold text-sm text-slate-900 dark:text-slate-100">
                    Avg: <span class="text-blue-500 font-extrabold">{{ getLiveVal(avgMoistureMetric) }}{{ avgMoistureMetric?.unit || '%' }}</span>
                  </span>
                </div>

                <!-- Probe Bars -->
                <div class="space-y-1.5 pt-0.5">
                  <div v-for="probe in soilProbes" :key="probe.id" class="space-y-0.5">
                    <div class="flex justify-between text-xs">
                      <span class="text-slate-500 dark:text-slate-400 font-medium">{{ probe.name }}</span>
                      <span class="font-bold text-foreground">{{ getLiveVal(probe) ?? '--' }}{{ probe.unit || '%' }}</span>
                    </div>
                    <div class="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        class="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-500" 
                        :style="{ width: `${Math.min(Math.max(Number(getLiveVal(probe) || 0), 0), 100)}%` }"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Compact Mini Metrics: pH, Suhu Tanah, EC -->
              <div class="grid grid-cols-3 gap-2">
                <!-- pH Tanah Card -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[62px]">
                  <div class="flex items-center justify-between gap-1">
                    <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 truncate">{{ phMetric?.name || 'pH' }}</span>
                    <span :class="['text-[10px] font-bold px-1.5 py-0.5 rounded-full border whitespace-nowrap', phStatus.border, phStatus.bg, phStatus.textClass]">
                      {{ phStatus.text }}
                    </span>
                  </div>
                  <div class="mt-1">
                    <span class="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ getLiveVal(phMetric) ?? '--' }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 ml-1">{{ phMetric?.unit || 'pH' }}</span>
                  </div>
                </div>

                <!-- Suhu Tanah Card -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[62px]">
                  <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 truncate">{{ soilTempMetric?.name || 'Suhu Tanah' }}</span>
                  <div class="mt-1">
                    <span class="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ getLiveVal(soilTempMetric) ?? '--' }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 ml-1">{{ soilTempMetric?.unit || '°C' }}</span>
                  </div>
                </div>

                <!-- EC (Electrical Conductivity) Card -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[62px]">
                  <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 truncate">{{ ecMetric?.name || 'eC' }}</span>
                  <div class="mt-1">
                    <span class="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ getLiveVal(ecMetric) ?? '--' }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 ml-1 font-sans">{{ ecMetric?.unit || 'µS/cm' }}</span>
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
                  <img src="/iot-icon.svg" alt="Kondisi IoT" class="w-5 h-5 object-contain dark:invert shrink-0" />
                  <h4 class="text-base sm:text-lg font-bold tracking-tight text-foreground">Kondisi IoT</h4>
                </div>
              </div>

              <!-- Highlight Suhu Dalam Panel (Enclosure) & Dynamic Thermal Safety Card (NPK Style - Expanded Height) -->
              <div 
                class="relative overflow-hidden p-4 sm:p-4.5 rounded-2xl transition-all duration-300 flex-1 flex flex-col justify-between gap-3 text-white border-0 min-h-[135px]"
                :class="thermalStatus.shadowClass"
                :style="{ background: thermalStatus.gradient }"
              >
                <!-- Soft Glass Inner Glow / Lighting Reflection (Same as NPK Card) -->
                <div 
                  class="absolute inset-0 pointer-events-none opacity-20"
                  style="background: radial-gradient(circle at 85% 15%, rgba(255, 255, 255, 0.4) 0%, transparent 60%);"
                ></div>

                <!-- Inspira UI DotPattern Texture Overlay -->
                <DotPattern 
                  :width="12" 
                  :height="12" 
                  :cx="1" 
                  :cy="1" 
                  :cr="1" 
                  class="text-white/20" 
                />

                <!-- Top: Thermometer Icon, Label, Main Value, and Min/Max Stats -->
                <div class="flex items-center justify-between gap-2.5 relative z-10 my-auto">
                  <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-xl bg-white/25 backdrop-blur-md flex items-center justify-center text-white shadow-none shrink-0 border-0">
                      <Thermometer class="w-5 h-5 stroke-[2.5]" />
                    </div>
                    <div>
                      <p class="text-sm sm:text-base font-semibold text-white/95 tracking-wide drop-shadow-[0_1px_1px_rgba(0,0,0,0.1)]">
                        {{ enclosureTempMetric?.name || 'Suhu Dalam Box Panel' }}
                      </p>
                      <div class="flex items-baseline gap-1 mt-0.5">
                        <span class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.15)]">
                          {{ getLiveVal(enclosureTempMetric) ?? '--' }}
                        </span>
                        <span class="text-sm font-semibold text-white/90 drop-shadow-[0_1px_1px_rgba(0,0,0,0.1)]">
                          {{ enclosureTempMetric?.unit || '°C' }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Min & Max Stats (Compact, Sleek 50/50 Symmetrical Grid Capsule) -->
                  <div class="grid grid-cols-2 divide-x divide-white/35 items-center bg-white/30 hover:bg-white/35 backdrop-blur-md px-1.5 py-1 sm:py-1.5 rounded-xl shrink-0 border border-white/50 shadow-sm w-28 sm:w-32">
                    <div class="px-1.5 flex flex-col items-center justify-center text-center">
                      <span class="text-[10px] font-bold text-white/90 block leading-none tracking-wider drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">MIN</span>
                      <span class="text-xs sm:text-sm font-extrabold text-white font-mono leading-tight mt-0.5 drop-shadow-[0_1px_1px_rgba(0,0,0,0.2)]">
                        {{ enclosureMinVal != null ? `${enclosureMinVal}°` : '--' }}
                      </span>
                    </div>
                    <div class="px-1.5 flex flex-col items-center justify-center text-center">
                      <span class="text-[10px] font-bold text-white/90 block leading-none tracking-wider drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">MAX</span>
                      <span class="text-xs sm:text-sm font-extrabold text-white font-mono leading-tight mt-0.5 drop-shadow-[0_1px_1px_rgba(0,0,0,0.2)]">
                        {{ enclosureMaxVal != null ? `${enclosureMaxVal}°` : '--' }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Bottom: Thermal Safety Threshold Bar (Current / Max Threshold) -->
                <div class="space-y-1.5 relative z-10 pt-1 mt-auto">
                  <div class="flex items-center justify-between text-xs text-white/90 font-medium">
                    <span>Batas Aman Panel: <strong class="text-white font-bold">{{ thermalStatus.safeLimit }}°C</strong></span>
                    <span class="font-bold text-white">{{ getLiveVal(enclosureTempMetric) ?? '--' }} / {{ thermalStatus.safeLimit }}°C</span>
                  </div>
                  <!-- Progress bar -->
                  <div class="relative h-1.5 w-full bg-black/25 rounded-full overflow-hidden backdrop-blur-xs">
                    <!-- Active temperature bar scaled to max threshold -->
                    <div 
                      :class="['h-full bg-gradient-to-r rounded-full transition-all duration-500', thermalStatus.barGradient]" 
                      :style="{ width: `${thermalStatus.percentage}%` }"
                    />
                  </div>
                </div>
              </div>

              <!-- Mini Grid: Suhu Luar (Ambient), Kelembaban Udara, Status Modbus -->
              <div class="grid grid-cols-3 gap-2">
                <!-- Suhu Luar / Ambient -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[62px]">
                  <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 truncate">{{ airTempMetric?.name || 'Suhu Luar' }}</span>
                  <div class="mt-1">
                    <span class="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ getLiveVal(airTempMetric) ?? '--' }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 ml-1">{{ airTempMetric?.unit || '°C' }}</span>
                  </div>
                </div>

                <!-- Kelembaban Udara -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[62px]">
                  <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 truncate">{{ humidityMetric?.name || 'Kelembaban' }}</span>
                  <div class="mt-1">
                    <span class="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">{{ getLiveVal(humidityMetric) ?? '--' }}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 ml-1">{{ humidityMetric?.unit || '%' }}</span>
                  </div>
                </div>

                <!-- Modbus Status -->
                <div class="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between min-h-[62px]">
                  <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 truncate">{{ modbusMetric?.name || 'Modbus Code' }}</span>
                  <div class="mt-1 flex items-center">
                    <span class="text-xs sm:text-sm font-bold font-mono bg-slate-200 dark:bg-slate-800 px-1.5 py-0.5 rounded border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200">
                      {{ getLiveVal(modbusMetric) != null ? `Code ${getLiveVal(modbusMetric)}` : 'OK (0)' }}
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

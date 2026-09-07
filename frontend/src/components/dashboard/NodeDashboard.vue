<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTelemetryStore } from '@/stores/telemetry'
import SensorCard from '@/components/dashboard/SensorCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import PowerStateBadge from '@/components/dashboard/PowerStateBadge.vue'
import SensorLineChart from '@/components/charts/SensorLineChart.vue'
import DashboardPreloader from '@/components/ui/DashboardPreloader.vue'
import { DotPattern } from '@/components/ui/dot-pattern'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import ExportTelemetryModal from '@/components/dashboard/ExportTelemetryModal.vue'
import ReportPreviewModal from '@/components/dashboard/ReportPreviewModal.vue'
import { getSensorCategory, filterSensorsByCategory } from '@/lib/sensorTaxonomy'
import ExcelIcon from '@/components/icons/ExcelIcon.vue'
import PdfIcon from '@/components/icons/PdfIcon.vue'
import { 
  Calendar, Clock, Check, Layers, MapPin, 
  Thermometer, Droplet, Sparkles, TrendingUp, 
  TrendingDown, Minus, Info, Activity, AlertTriangle,
  ChevronDown, Fan, Lightbulb, Droplets, Download,
  Sun, ShieldCheck, Beaker, Zap,
  Battery, BatteryCharging, ArrowDownRight
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
const isExportModalOpen = ref(false)
const isReportModalOpen = ref(false)
const selectedCategory = ref<'all' | 'npk' | 'soil' | 'environment' | 'power'>('npk')
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
    lucideIcon: null,
    iconColorClass: 'bg-foreground',
    iconTextColorClass: 'text-foreground',
    wrapperClass: 'bg-transparent border-transparent shadow-none'
  },
  {
    id: 'soil' as const,
    label: 'Tanah',
    fullLabel: 'Kondisi Tanah',
    desc: 'pH Tanah, Multi-Probe Kelembapan, EC, Suhu',
    icon: '/soil-icon.svg',
    isLucide: false,
    lucideIcon: null,
    iconColorClass: 'bg-foreground',
    iconTextColorClass: 'text-foreground',
    wrapperClass: 'bg-transparent border-transparent shadow-none'
  },
  {
    id: 'environment' as const,
    label: 'IoT & Lingkungan',
    fullLabel: 'IoT & Lingkungan',
    desc: 'Suhu Casing/Box, Kelembaban & Suhu Udara',
    icon: '/iot-icon.svg',
    isLucide: false,
    lucideIcon: null,
    iconColorClass: 'bg-foreground',
    iconTextColorClass: 'text-foreground',
    wrapperClass: 'bg-transparent border-transparent shadow-none'
  },
  {
    id: 'power' as const,
    label: 'Manajemen Daya',
    fullLabel: 'Sistem Manajemen Daya',
    desc: 'Tegangan, Arus, & Daya Baterai/Beban',
    icon: null,
    isLucide: true,
    lucideIcon: Zap,
    iconColorClass: 'bg-foreground',
    iconTextColorClass: 'text-foreground',
    wrapperClass: 'bg-transparent border-transparent shadow-none'
  },
  {
    id: 'all' as const,
    label: 'Semua',
    fullLabel: 'Semua Parameter',
    desc: 'Agregasi seluruh telemetri',
    icon: null,
    isLucide: true,
    lucideIcon: Layers,
    iconColorClass: 'bg-foreground',
    iconTextColorClass: 'text-foreground',
    wrapperClass: 'bg-transparent border-transparent shadow-none'
  }
]

const currentCategoryMeta = computed(() => {
  return categoryOptions.find(c => c.id === selectedCategory.value) || categoryOptions[0]
})

const selectCategory = (catId: 'all' | 'npk' | 'soil' | 'environment' | 'power') => {
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
// Categorisation lives in @/lib/sensorTaxonomy so every view agrees.

const activeCategorySensors = computed(() =>
  filterSensorsByCategory(sensors.value || [], selectedCategory.value)
)

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

// Status aktuator diambil apa adanya dari backend (services/aktuator.py).
//
// Dulu di sini bitmask didekode ulang dan gagal karena tiga hal sekaligus:
// sensornya dicari lewat nama persis 'Status aktuator', batasnya 0-7 sehingga
// bit3 (valve_timeout) membuang seluruh pembacaan, dan Node 2 tetap ditampilkan
// punya valve padahal tidak. Backend sudah menangani ketiganya.
const aktuator = computed(() =>
  // WebSocket lebih baru, tapi saat halaman baru dibuka belum ada pesan masuk;
  // ringkasan dashboard membawa hasil decode yang sama supaya kartu tidak
  // kosong sampai node mengirim paket berikutnya.
  telemetryStore.aktuatorByNode[props.nodeId] ?? dashboardSummary.value?.aktuator ?? null
)

// bit3: firmware menutup valve paksa karena kelamaan terbuka. Nilai ini dulu
// mustahil sampai ke sini.
const valveTimeout = computed(() => aktuator.value?.valve_timeout === true)

// Dynamic Animated Actuator List for Actuator Status Card
const actuatorList = computed(() => {
  const a = aktuator.value
  if (!a) return []
  const daftar: any[] = [
    {
      id: 'kipas',
      nama: 'Kipas',
      aktif: aktuator.value.kipas,
      icon: Fan,
      iconActiveClass: 'text-emerald-500 animate-spin [animation-duration:0.8s]',
      iconInactiveClass: 'text-slate-400 dark:text-slate-500',
      activeBg: 'bg-emerald-500/10 dark:bg-emerald-950/30 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 shadow-xs',
      badgeActiveClass: 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 font-black',
    },
    {
      id: 'lampu',
      nama: 'Lampu',
      aktif: aktuator.value.lampu,
      icon: Lightbulb,
      iconActiveClass: 'text-amber-500 fill-amber-400/50 drop-shadow-[0_0_8px_rgba(245,158,11,0.7)] animate-pulse',
      iconInactiveClass: 'text-slate-400 dark:text-slate-500',
      activeBg: 'bg-amber-500/10 dark:bg-amber-950/30 border-amber-500/30 text-amber-600 dark:text-amber-400 shadow-xs',
      badgeActiveClass: 'bg-amber-500/20 text-amber-700 dark:text-amber-300 font-black',
    },
  ]

  // Valve cuma ada di Node 1. Kalau backend tidak mengirim kuncinya, node ini
  // memang tidak punya valve -- itu beda dari valve yang sedang mati.
  if ('valve' in a) {
    daftar.push({
      id: 'valve',
      nama: valveTimeout.value ? 'Valve (timeout)' : 'Valve',
      aktif: a.valve,
      icon: Droplets,
      iconActiveClass: 'text-sky-500 drop-shadow-[0_0_6px_rgba(14,165,233,0.6)] animate-bounce [animation-duration:1.2s]',
      iconInactiveClass: 'text-slate-400 dark:text-slate-500',
      activeBg: 'bg-sky-500/10 dark:bg-sky-950/30 border-sky-500/30 text-sky-600 dark:text-sky-400 shadow-xs',
      badgeActiveClass: 'bg-sky-500/20 text-sky-700 dark:text-sky-300 font-black',
    })
  }
  return daftar
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
  let list: any[] = []
  if (dashboardSummary.value?.npk_sensors?.length) {
    list = dashboardSummary.value.npk_sensors
  } else {
    list = sensors.value
      .filter(s => getSensorCategory(s) === 'npk')
      .map(s => wrapSensorAsMetric(s))
      .filter(Boolean)
  }

  // Canonical NPK sorting: Nitrogen (1) -> Phosphorus (2) -> Potassium (3)
  return [...list].sort((a, b) => {
    const nameA = (a.name || '').toLowerCase()
    const nameB = (b.name || '').toLowerCase()
    const getOrder = (n: string) => {
      if (n.includes('nitrogen') || n === 'n') return 1
      if (n.includes('phosphor') || n.includes('phospor') || n.includes('fosfor') || n === 'p') return 2
      if (n.includes('potassium') || n.includes('kalium') || n === 'k') return 3
      return 99
    }
    return getOrder(nameA) - getOrder(nameB)
  })
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
// Rata-rata kelembapan tanah: didukung langsung dari field ThingSpeak (Node 1 Ch1 field6 atau Node 2 Ch2 field2)
const avgMoistureMetric = computed(() => {
  return dashboardSummary.value?.soil_metrics?.avg_moisture ||
         wrapSensorAsMetric(findSensorByKeywords(['rata-rata kelembapan', 'kelembapan probe npk', 'kelembapan tanah', 'kelembaban tanah']))
})

// Real-time Average Moisture: membaca nilai live dari sensor kelembapan tanah atau rata-rata probe
const realTimeAvgMoisture = computed(() => {
  const val = getLiveVal(avgMoistureMetric.value)
  if (val != null && !isNaN(Number(val))) {
    return Number(val).toFixed(1)
  }
  if (soilProbes.value?.length) {
    const validVals = soilProbes.value
      .map((p: any) => getLiveVal(p))
      .filter((v: any) => v != null && !isNaN(Number(v)))
      .map((v: any) => Number(v))
    if (validVals.length > 0) {
      const sum = validVals.reduce((acc, curr) => acc + curr, 0)
      return (sum / validVals.length).toFixed(1)
    }
  }
  return null
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

// --- Sistem Solar Panel (INA226 dari Backend FastAPI) ---
const power = computed<any>(() => {
  return dashboardSummary.value?.power_metrics || {}
})

const batteryLevelPercent = computed<number | null>(() => {
  return power.value?.battery_level_percent ?? null
})

const batteryStatusInfo = computed(() => {
  const percent = batteryLevelPercent.value
  const volt = power.value?.tegangan_in != null ? Number(power.value.tegangan_in) : null

  // Evaluasi semantik kapasitas baterai (State of Charge):
  // > 60% (>12.5V): Sehat & Penuh (Hijau)
  // 25% - 60% (11.8V - 12.5V): Sedang (Kuning/Amber)
  // < 25% (<11.8V): Kritis / Perlu Pengisian (Merah/Rose)
  if (percent != null ? percent > 60 : (volt != null && volt >= 12.5)) {
    return {
      status: 'good',
      label: 'Optimal',
      barColor: 'from-emerald-400 to-emerald-500',
      textColor: 'text-emerald-600 dark:text-emerald-400'
    }
  }
  if (percent != null ? percent >= 25 : (volt != null && volt >= 11.8)) {
    return {
      status: 'warning',
      label: 'Sedang',
      barColor: 'from-amber-400 to-amber-500',
      textColor: 'text-amber-600 dark:text-amber-400'
    }
  }
  if (percent != null || volt != null) {
    return {
      status: 'critical',
      label: 'Kritis',
      barColor: 'from-rose-500 to-red-600',
      textColor: 'text-rose-600 dark:text-rose-400'
    }
  }
  return {
    status: 'unknown',
    label: 'Offline',
    barColor: 'from-slate-400 to-slate-500',
    textColor: 'text-slate-500 dark:text-slate-400'
  }
})

const loadCurrentMetric = computed(() => {
  return wrapSensorAsMetric(findSensorByKeywords(['arus load', 'load_current', 'arus beban'], ['baterai', 'batt']))
})

const loadCurrentThresholds = computed(() => {
  const metric = loadCurrentMetric.value
  const min = metric?.min_threshold != null ? Number(metric.min_threshold) : 0.0
  const max = metric?.max_threshold != null ? Number(metric.max_threshold) : 2.5
  return { min, max }
})

const loadCurrentPercent = computed(() => {
  const arus = power.value?.arus_out != null ? Number(power.value.arus_out) : null
  if (arus == null) return 0
  const { min, max } = loadCurrentThresholds.value
  const range = max - min
  if (range <= 0) return 0
  const pct = ((arus - min) / range) * 100
  return Math.min(Math.max(Math.round(pct), arus > 0 ? 5 : 0), 100)
})

const loadStatusInfo = computed(() => {
  const arus = power.value?.arus_out != null ? Number(power.value.arus_out) : null
  const { max } = loadCurrentThresholds.value

  if (arus == null) {
    return {
      barColor: 'from-slate-400 to-slate-500',
      textColor: 'text-slate-500 dark:text-slate-400',
      dotColor: 'bg-slate-400',
      statusText: 'Standby'
    }
  }

  // Evaluasi semantik konsumsi arus terhadap ambang batas beban:
  // > max: Overload (Merah/Rose)
  // > 80% max: Beban Tinggi (Amber/Kuning)
  // <= 80% max: Normal 12V Output (Hijau/Teal)
  if (max != null && arus > max) {
    return {
      barColor: 'from-rose-500 to-red-600',
      textColor: 'text-rose-600 dark:text-rose-400',
      dotColor: 'bg-rose-500',
      statusText: 'Overload'
    }
  }
  if (max != null && arus > max * 0.8) {
    return {
      barColor: 'from-amber-400 to-amber-500',
      textColor: 'text-amber-600 dark:text-amber-400',
      dotColor: 'bg-amber-500',
      statusText: 'Beban Tinggi'
    }
  }
  return {
    barColor: 'from-emerald-400 to-teal-500',
    textColor: 'text-emerald-600 dark:text-emerald-400',
    dotColor: 'bg-emerald-500',
    statusText: arus > 0 ? '12V Output' : 'Standby'
  }
})

// Sensor tambahan yang belum terangkum di dalam widget Bento Grid utama (fallback otomatis)
const additionalSensors = computed(() => {
  const capturedFields = new Set<string>()

  npkSensors.value.forEach((s: any) => { if (s?.thingspeak_field) capturedFields.add(s.thingspeak_field) })
  if (phMetric.value?.thingspeak_field) capturedFields.add(phMetric.value.thingspeak_field)
  if (soilTempMetric.value?.thingspeak_field) capturedFields.add(soilTempMetric.value.thingspeak_field)
  if (ecMetric.value?.thingspeak_field) capturedFields.add(ecMetric.value.thingspeak_field)
  if (avgMoistureMetric.value?.thingspeak_field) capturedFields.add(avgMoistureMetric.value.thingspeak_field)
  soilProbes.value.forEach((s: any) => { if (s?.thingspeak_field) capturedFields.add(s.thingspeak_field) })
  if (enclosureTempMetric.value?.thingspeak_field) capturedFields.add(enclosureTempMetric.value.thingspeak_field)
  if (airTempMetric.value?.thingspeak_field) capturedFields.add(airTempMetric.value.thingspeak_field)
  if (humidityMetric.value?.thingspeak_field) capturedFields.add(humidityMetric.value.thingspeak_field)

  sensors.value.forEach((s: any) => {
    const t = (s.type || '').toLowerCase()
    const n = (s.name || '').toLowerCase()
    if (['actuator', 'batt_volt', 'load_volt', 'batt_current', 'load_current', 'load_power', 'power'].includes(t) ||
        n.includes('aktuator') || n.includes('baterai') || n.includes('daya')) {
      if (s.thingspeak_field) capturedFields.add(s.thingspeak_field)
    }
  })

  return sensors.value
    .filter((s: any) => s.enabled !== false && !capturedFields.has(s.thingspeak_field))
    .map((s: any) => wrapSensorAsMetric(s))
    .filter(Boolean)
})

// --- Kartu ambang operator --------------------------------------------------
// Ambang di sini berasal dari konfigurasi sensor di database -- keputusan
// operator lahan, bukan kelas dari pustaka. Kalau operator belum mengisinya,
// kartu TIDAK mengarang batas sendiri.
//
// Sebelumnya tiap kartu punya angka cadangan (pH 5.8/7.2, EC 600/1800, suhu
// tanah 18/32, suhu udara 18/34, lembap 45/88, probe 35/75, lengas 40/70) yang
// tidak punya sumber, lalu ikut terbawa ke laporan PDF seolah kriteria agronomi.
// Klasifikasi terhadap standar terbit datang dari backend (soil_health).
// Lihat CLAUDE.md, bagian "Soil health interpretation".

const GRADIEN_NETRAL = 'bg-gradient-to-br from-slate-400 via-slate-500 to-slate-600'
const GRADIEN_OPTIMAL = 'bg-gradient-to-br from-[#00b200] via-[#008a00] to-[#006400]'

type WarnaKartu = { gradient: string; shadow: string }

const kartuAmbang = (
  metric: any,
  label: { rendah: string; optimal: string; tinggi: string },
  warna: { rendah: WarnaKartu; optimal: WarnaKartu; tinggi: WarnaKartu }
) => {
  const min = metric?.min_threshold ?? null
  const max = metric?.max_threshold ?? null
  const v = getLiveVal(metric)
  const netral = { gradient: GRADIEN_NETRAL, shadow: 'shadow-slate-500/20' }

  if (min == null && max == null) {
    return { text: 'Ambang belum diatur', ...netral, isAlert: false, min, max, unset: true }
  }
  if (v == null) {
    // Dulu kasus ini mengembalikan 'Optimal' berwarna hijau -- tidak ada
    // pembacaan ditampilkan sebagai kondisi baik.
    return { text: 'Tidak ada pembacaan', ...netral, isAlert: false, min, max, unset: false }
  }

  const num = Number(v)
  if (min != null && num < min) {
    return { text: label.rendah, ...warna.rendah, isAlert: true, min, max, unset: false }
  }
  if (max != null && num > max) {
    return { text: label.tinggi, ...warna.tinggi, isAlert: true, min, max, unset: false }
  }
  return { text: label.optimal, ...warna.optimal, isAlert: false, min, max, unset: false }
}

const W_OPTIMAL: WarnaKartu = { gradient: GRADIEN_OPTIMAL, shadow: 'shadow-[#00b200]/20' }
const W_DINGIN: WarnaKartu = { gradient: 'bg-gradient-to-br from-cyan-500 via-sky-500 to-blue-600', shadow: 'shadow-sky-500/25' }
const W_PANAS: WarnaKartu = { gradient: 'bg-gradient-to-br from-rose-500 via-red-600 to-rose-700 animate-pulse', shadow: 'shadow-rose-500/30' }
const W_KERING: WarnaKartu = { gradient: 'bg-gradient-to-br from-amber-400 via-amber-500 to-orange-500', shadow: 'shadow-amber-500/25' }

const phCardState = computed(() => kartuAmbang(
  phMetric.value,
  { rendah: 'Asam', optimal: 'Dalam ambang', tinggi: 'Basa' },
  {
    rendah: { gradient: 'bg-gradient-to-br from-orange-500 via-amber-600 to-rose-600', shadow: 'shadow-orange-500/25' },
    optimal: W_OPTIMAL,
    tinggi: { gradient: 'bg-gradient-to-br from-indigo-500 via-purple-500 to-violet-600', shadow: 'shadow-purple-500/25' },
  }
))
const phStatus = computed(() => phCardState.value)

const soilTempCardState = computed(() => kartuAmbang(
  soilTempMetric.value,
  { rendah: 'Dingin', optimal: 'Dalam ambang', tinggi: 'Panas' },
  { rendah: W_DINGIN, optimal: W_OPTIMAL, tinggi: W_PANAS }
))
const soilTempStatus = computed(() => soilTempCardState.value)

const ecCardState = computed(() => kartuAmbang(
  ecMetric.value,
  { rendah: 'Rendah', optimal: 'Dalam ambang', tinggi: 'Pekat' },
  {
    rendah: W_KERING,
    optimal: { gradient: 'bg-gradient-to-br from-lime-500 via-emerald-500 to-teal-600', shadow: 'shadow-lime-500/20' },
    tinggi: W_PANAS,
  }
))
const ecStatus = computed(() => ecCardState.value)

const enclosureTempCardState = computed(() => kartuAmbang(
  enclosureTempMetric.value,
  { rendah: 'Sejuk', optimal: 'Dalam ambang', tinggi: 'Panas' },
  { rendah: W_DINGIN, optimal: W_OPTIMAL, tinggi: W_PANAS }
))
const enclosureTempStatus = computed(() => enclosureTempCardState.value)
const thermalStatus = computed(() => ({
  safeLimit: enclosureTempMetric.value?.max_threshold || 55,
  insight: enclosureTempCardState.value?.text || 'Normal'
}))

const airTempCardState = computed(() => kartuAmbang(
  airTempMetric.value,
  { rendah: 'Sejuk', optimal: 'Dalam ambang', tinggi: 'Panas' },
  { rendah: W_DINGIN, optimal: W_OPTIMAL, tinggi: W_PANAS }
))
const airTempStatus = computed(() => airTempCardState.value)

const humidityCardState = computed(() => kartuAmbang(
  humidityMetric.value,
  { rendah: 'Kering', optimal: 'Dalam ambang', tinggi: 'Tinggi' },
  {
    rendah: W_KERING,
    optimal: { gradient: 'bg-gradient-to-br from-sky-400 via-cyan-500 to-blue-600', shadow: 'shadow-sky-500/20' },
    tinggi: { gradient: 'bg-gradient-to-br from-blue-600 via-indigo-600 to-slate-800', shadow: 'shadow-indigo-500/25' },
  }
))
const humidityStatus = computed(() => humidityCardState.value)

// Bar probe ikut ambang probe itu sendiri; tanpa ambang, warnanya netral.
const getProbeBarGradient = (probe: any) => {
  const min = probe?.min_threshold ?? null
  const max = probe?.max_threshold ?? null
  const v = getLiveVal(probe)
  if (v == null || (min == null && max == null)) return 'from-slate-400 via-slate-500 to-slate-600'
  const num = Number(v)
  if (min != null && num < min) return 'from-amber-400 via-orange-400 to-amber-500'
  if (max != null && num > max) return 'from-blue-600 via-indigo-500 to-indigo-700'
  return 'from-sky-400 via-cyan-400 to-blue-600'
}

const soilMoistureStatus = computed(() => {
  const nilai = realTimeAvgMoisture.value
  if (nilai == null) {
    return { text: 'Tidak ada pembacaan', bg: 'bg-slate-500/15', border: 'border-slate-500/30', textClass: 'text-slate-700 dark:text-slate-300' }
  }
  // Vonis kelembapan yang bersandar pustaka ada di backend (soil_health), dan
  // butuh kerapatan isi untuk jadi WFPS. Di sini cuma label netral.
  return { text: nilai + '%', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', textClass: 'text-emerald-700 dark:text-emerald-400' }
})

// Mini-map logic with reactive watch & 1:1 square ratio
const miniMapContainer = ref<HTMLElement | null>(null)
const miniMapReady = ref(false)
const nodeCoords = ref<{ lat: number; lng: number } | null>(null)
const nodeLocation = ref<string>('')
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
      html: `<div style="width:40px;height:52px"><svg width="40" height="52" viewBox="0 0 24 32" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 20 12 20s12-11 12-20C24 5.373 18.627 0 12 0z" fill="#ef4444"/><circle cx="12" cy="12" r="5" fill="white"/></svg></div>`,
      className: '', iconSize: [40, 52], iconAnchor: [20, 52],
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
    if (node.location) {
      nodeLocation.value = node.location
    }
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

// Comprehensive Sensor Statistics for PDF Reports & Analytics
const reportSensorStats = computed(() => {
  const nonActuators = (sensors.value || []).filter(s => s && s.name !== 'Status aktuator')
  const feeds = chartData.value || []

  return nonActuators.map(s => {
    const channelId = s.channel_id ? String(s.channel_id).toLowerCase() : ''
    const tsField = (s.thingspeak_field || s.field_key || s.channel_field || '').toLowerCase()
    const compositeKey = channelId && tsField ? `${channelId}_${tsField}` : ''

    const rawVals = feeds.map((f: any) => {
      let val = compositeKey ? f[compositeKey] : undefined
      if (val === undefined && s.field_key) val = f[s.field_key]
      if (val === undefined && s.thingspeak_field) val = f[s.thingspeak_field]
      if (val === undefined && s.name) val = f[s.name]
      if (val === undefined) {
        const entry = Object.entries(f).find(([k]) => {
          if (tsField && (k.toLowerCase() === tsField || k.toLowerCase().endsWith(`_${tsField}`))) return true
          if (s.name && k.toLowerCase() === s.name.toLowerCase()) return true
          return false
        })
        if (entry) val = entry[1]
      }
      return parseFloat(val)
    }).filter((v: number) => Number.isFinite(v))

    const lastVal = rawVals.length ? Number(rawVals[rawVals.length - 1].toFixed(1)) : getLiveVal(s)
    const min = rawVals.length ? Number(Math.min(...rawVals).toFixed(1)) : (getLiveVal(s) ?? '--')
    const max = rawVals.length ? Number(Math.max(...rawVals).toFixed(1)) : (getLiveVal(s) ?? '--')
    const avg = rawVals.length ? Number((rawVals.reduce((a, b) => a + b, 0) / rawVals.length).toFixed(1)) : (getLiveVal(s) ?? '--')

    return {
      id: s.id,
      name: s.name,
      unit: s.unit || '',
      type: getSensorCategory(s),
      lastVal,
      avg,
      min,
      max,
      min_threshold: s.min_threshold,
      max_threshold: s.max_threshold
    }
  })
})

// Dynamic Reactive Analytics Data based on selectedCategory & selectedRange
const analyticsData = computed(() => {
  // Explicitly reference latestTelemetry and telemetryHistory to guarantee real-time reactivity on WS messages
  const liveFeed = latestTelemetry.value
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

  // Calculate statistics per active sensor in current category, merging live WS values
  const sensorStats = catSensors.map((s: any) => {
    const key = `${s.channel_id}_${s.thingspeak_field}`
    const rawVals = feeds.map((f: any) => parseFloat(f[key])).filter((v: number) => Number.isFinite(v))
    const liveVal = getLiveVal(s)
    
    if (!rawVals.length && liveVal == null) {
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

    const current = liveVal != null ? Number(Number(liveVal).toFixed(1)) : (rawVals.length ? Number(rawVals[rawVals.length - 1].toFixed(1)) : null)
    const min = rawVals.length ? Number(Math.min(...rawVals).toFixed(1)) : current
    const max = rawVals.length ? Number(Math.max(...rawVals).toFixed(1)) : current
    const sum = rawVals.reduce((a: number, b: number) => a + b, 0)
    const avg = rawVals.length ? Number((sum / rawVals.length).toFixed(1)) : current
    const first = rawVals.length ? rawVals[0] : current
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

  // Helper for precise sensor type recognition without false substring matches
  const checkPH = (n: string) => {
    if (n.includes('phosphor') || n.includes('phospor') || n.includes('fosfor') || n.includes('photo')) return false
    return n === 'ph' || n.startsWith('ph ') || n.endsWith(' ph') || n.includes(' ph ') || n.includes('(ph)') || n.includes('keasaman')
  }
  const checkNitrogen = (n: string) => n.includes('nitrogen') || n.includes('nitrat') || n === 'n'
  const checkPhosphorus = (n: string) => n.includes('phosphor') || n.includes('phospor') || n.includes('fosfor') || n.includes('phosphat') || n === 'p'
  const checkPotassium = (n: string) => n.includes('potassium') || n.includes('kalium') || n === 'k'
  const checkEnclosureTemp = (n: string) => n.includes('dalam') || n.includes('enclosure') || n.includes('box') || n.includes('casing')
  const checkAirTemp = (n: string) => (n.includes('suhu') || n.includes('temp')) && (n.includes('luar') || n.includes('udara') || n.includes('ambient'))
  const checkSoilMoisture = (n: string) => (n.includes('tanah') || n.includes('soil') || n.includes('probe')) && (n.includes('lembab') || n.includes('moist'))
  const checkAirHumidity = (n: string) => (n.includes('udara') || n.includes('air') || n.includes('ambient') || n.includes('humidity')) && !n.includes('tanah') && !n.includes('soil')

  // Real-time Active Anomalies & Historical Notes Evaluator
  const activeAnomalies: { sensor: any; severity: 'critical' | 'warning'; message: string }[] = []
  const historicalNotes: { sensor: any; message: string }[] = []

  sensorStats.forEach((stat: any) => {
    const s = catSensors.find((cs: any) => cs.id === stat.id) || stat
    const sName = (stat.name || '').toLowerCase()
    const currentVal = stat.current

    if (currentVal == null) return

    // 1. Check Active Real-Time Database Thresholds
    if (s.max_threshold != null && currentVal > s.max_threshold) {
      const isExtreme = currentVal > s.max_threshold * 1.2
      activeAnomalies.push({
        sensor: stat,
        severity: isExtreme ? 'critical' : 'warning',
        message: `${stat.name} saat ini ${currentVal} ${stat.unit} (melebihi ambang batas maksimal ${s.max_threshold} ${stat.unit}).`
      })
      return
    }
    if (s.min_threshold != null && currentVal < s.min_threshold) {
      const isExtreme = currentVal < s.min_threshold * 0.8
      activeAnomalies.push({
        sensor: stat,
        severity: isExtreme ? 'critical' : 'warning',
        message: `${stat.name} saat ini ${currentVal} ${stat.unit} (di bawah batas minimal ${s.min_threshold} ${stat.unit}).`
      })
      return
    }

    // 2. Intelligent Agronomic Real-Time Standard Fallbacks
    if (checkPH(sName)) {
      if (currentVal < 5.0 || currentVal > 8.5) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'critical',
          message: `Nilai pH saat ini (${currentVal}) tergolong ekstrem. Segera lakukan penyesuaian media tanah.`
        })
      } else if (currentVal < 5.8 || currentVal > 7.5) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Nilai pH saat ini (${currentVal}) berada di luar ambang netral ideal 6.0–7.0.`
        })
      }
    } else if (checkNitrogen(sName)) {
      if (currentVal < 20) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Nitrogen saat ini rendah (${currentVal} mg/kg). Pertimbangkan pemupukan N pada siklus berikutnya.`
        })
      } else if (currentVal > 80) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Nitrogen saat ini tinggi (${currentVal} mg/kg). Hindari akumulasi pupuk berlebih.`
        })
      }
    } else if (checkPhosphorus(sName)) {
      if (currentVal < 15) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Fosfor saat ini (${currentVal} mg/kg) di bawah target optimal untuk perkembangan akar.`
        })
      } else if (currentVal > 60) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Fosfor saat ini (${currentVal} mg/kg) tergolong tinggi.`
        })
      }
    } else if (checkPotassium(sName)) {
      if (currentVal < 20) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Kalium saat ini (${currentVal} mg/kg) di bawah target untuk ketahanan tanaman.`
        })
      } else if (currentVal > 60) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kadar Kalium saat ini (${currentVal} mg/kg) tergolong tinggi.`
        })
      }
    } else if (checkEnclosureTemp(sName)) {
      if (currentVal > 45) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'critical',
          message: `Suhu box panel IoT mencapai ${currentVal}°C (di atas batas aman 45°C). Pastikan kipas & ventilasi beroperasi.`
        })
      }
    } else if (checkAirTemp(sName)) {
      if (currentVal > 38) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Suhu udara lingkungan saat ini tinggi (${currentVal}°C).`
        })
      }
    } else if (checkSoilMoisture(sName)) {
      if (currentVal < 25) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kelembaban tanah saat ini rendah (${currentVal}%). Rekomendasikan pengairan/irigasi.`
        })
      }
    } else if (checkAirHumidity(sName)) {
      if (currentVal < 35) {
        activeAnomalies.push({
          sensor: stat,
          severity: 'warning',
          message: `Kelembaban udara lingkungan rendah (${currentVal}%). Kondisi cenderung kering.`
        })
      }
    }

    // Check historical peak notice if currently normal
    if (s.max_threshold != null && stat.max != null && stat.max > s.max_threshold && currentVal <= s.max_threshold) {
      historicalNotes.push({
        sensor: stat,
        message: `${stat.name} sempat menyentuh puncak ${stat.max} ${stat.unit} pada rentang ${rangeLabel.value}, namun saat ini telah kembali normal (${currentVal} ${stat.unit}).`
      })
    }
  })

  // Determine Semantic Wrapper Colors and Status
  const criticalAnomaly = activeAnomalies.find(a => a.severity === 'critical')
  const warningAnomaly = activeAnomalies.find(a => a.severity === 'warning')
  const recentHistoricalNote = historicalNotes[0]

  let defaultBadgeText = 'Status Optimal'
  let defaultBadgeColor = 'bg-emerald-500/15 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
  let defaultBoxClass = 'bg-emerald-500/10 dark:bg-emerald-950/30 border-emerald-500/20 text-emerald-900 dark:text-emerald-300'
  let defaultIconClass = 'text-emerald-600 dark:text-emerald-400'
  let defaultIcon = Check
  let defaultInsightText = recentHistoricalNote?.message || `Seluruh telemetri dalam rentang ${rangeLabel.value} terpantau stabil dalam batas operasional normal.`

  // 1. Kategori NPK
  if (selectedCategory.value === 'npk') {
    // Dicocokkan lewat kata utuh, bukan huruf tunggal.
    //
    // Sebelumnya P dicari dengan includes('phosphor') || includes('p'). Sensornya
    // bernama "Fosfor" -- tidak mengandung 'p' MAUPUN 'phosphor' -- jadi pStat
    // selalu undefined dan rasio NPK selamanya menampilkan "P: 0%" walau kartu
    // Fosfor di atasnya menunjukkan angka yang benar. Pencocokan huruf tunggal
    // ('n', 'p') juga rapuh: ia bisa menyambar sensor lain yang kebetulan
    // mengandung huruf itu.
    const cocok = (s: any, kata: string[]) => {
      const n = (s?.name || '').toLowerCase()
      return kata.some(k => n.includes(k))
    }
    const nStat = sensorStats.find((s: any) => cocok(s, ['nitrogen', 'nitrat']))
    const pStat = sensorStats.find((s: any) => cocok(s, ['fosfor', 'phosphor', 'fosfat', 'phosphat']))
    const kStat = sensorStats.find((s: any) => cocok(s, ['kalium', 'potassium']))
    
    // null berarti sensornya gagal dibaca, bukan kadar hara nol -- tapi rasio
    // butuh angka, jadi 0 dipakai HANYA sebagai lebar bar, dan teks rasio di
    // bawah menampilkan '--' supaya bedanya tetap kelihatan.
    const angka = (st: any) => {
      const v = st?.current ?? st?.avg
      return v == null ? null : Number(Number(v).toFixed(1))
    }
    const nRaw = angka(nStat)
    const pRaw = angka(pStat)
    const kRaw = angka(kStat)
    const nVal = nRaw ?? 0
    const pVal = pRaw ?? 0
    const kVal = kRaw ?? 0
    const teks = (v: number | null) => (v == null ? '--' : String(v))
    const total = (nVal + pVal + kVal) || 1

    const distributionWidget = {
      title: 'Rasio Keseimbangan NPK',
      subtitle: `${teks(nRaw)} : ${teks(pRaw)} : ${teks(kRaw)}`,
      segments: [
        { label: `N: ${Math.round((nVal / total) * 100)}%`, percent: Math.round((nVal / total) * 100), color: 'bg-emerald-500', textClass: 'text-emerald-600 dark:text-emerald-400' },
        { label: `P: ${Math.round((pVal / total) * 100)}%`, percent: Math.round((pVal / total) * 100), color: 'bg-blue-500', textClass: 'text-blue-600 dark:text-blue-400' },
        { label: `K: ${Math.round((kVal / total) * 100)}%`, percent: Math.round((kVal / total) * 100), color: 'bg-purple-500', textClass: 'text-purple-600 dark:text-purple-400' }
      ]
    }

    defaultBadgeText = recentHistoricalNote ? 'Stabil Normal' : 'Nutrisi Seimbang'
    defaultInsightText = recentHistoricalNote?.message || `Keseimbangan NPK dalam rentang ${rangeLabel.value} terpantau stabil. Rasio N:P:K (${teks(nRaw)} : ${teks(pRaw)} : ${teks(kRaw)}).`

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
    // Find Box / Enclosure Temp strictly
    const encStat = sensorStats.find((s: any) => {
      const n = (s.name || '').toLowerCase()
      return n.includes('dalam') || n.includes('box') || n.includes('panel') || n.includes('enclosure') || n.includes('casing')
    })

    // Find Outdoor / Ambient Temp strictly
    const airStat = sensorStats.find((s: any) => {
      const n = (s.name || '').toLowerCase()
      return (n.includes('suhu') || n.includes('temp')) && (n.includes('luar') || n.includes('udara') || n.includes('lingkungan') || n.includes('ambient') || n.includes('air')) && !n.includes('dalam') && !n.includes('box') && !n.includes('tanah')
    })

    // General Temperature Sensor (if only 1 generic temp sensor exists)
    const genericTempStat = sensorStats.find((s: any) => (s.name || '').toLowerCase().includes('suhu') || (s.name || '').toLowerCase().includes('temp'))
    const humidityStat = sensorStats.find((s: any) => (s.name || '').toLowerCase().includes('lembab') || (s.name || '').toLowerCase().includes('humidity'))
    
    const encVal = encStat ? Number((encStat.current ?? encStat.avg ?? 0).toFixed(1)) : null
    const airVal = airStat ? Number((airStat.current ?? airStat.avg ?? 0).toFixed(1)) : null
    const genericTempVal = genericTempStat ? Number((genericTempStat.current ?? genericTempStat.avg ?? 0).toFixed(1)) : null
    const humVal = humidityStat ? Number((humidityStat.current ?? humidityStat.avg ?? 0).toFixed(1)) : null

    let title = 'Ikhtisar Mikroklimat & Suhu'
    let subtitle = 'Data Sensor Terhubung'
    let segments: any[] = []

    if (encVal != null && airVal != null) {
      title = 'Perbandingan Suhu Box vs Lingkungan'
      const diff = Math.abs(encVal - airVal).toFixed(1)
      subtitle = `Selisih: ${diff}°C`
      
      const tTotal = (encVal + airVal) || 1
      segments = [
        { label: `Box: ${encVal}°C`, percent: Math.round((encVal / tTotal) * 100), color: 'bg-rose-500', textClass: 'text-rose-600 dark:text-rose-400' },
        { label: `Luar: ${airVal}°C`, percent: Math.round((airVal / tTotal) * 100), color: 'bg-amber-500', textClass: 'text-amber-600 dark:text-amber-400' }
      ]
    } else if (genericTempVal != null && humVal != null) {
      title = 'Kondisi Udara & Kelembaban'
      subtitle = `Suhu: ${genericTempVal}°C | Lembab: ${humVal}%`
      segments = [
        { label: `Suhu: ${genericTempVal}°C`, percent: 50, color: 'bg-amber-500', textClass: 'text-amber-600 dark:text-amber-400' },
        { label: `Lembab: ${humVal}%`, percent: 50, color: 'bg-sky-500', textClass: 'text-sky-600 dark:text-sky-400' }
      ]
    } else if (genericTempVal != null) {
      title = `Monitoring ${genericTempStat?.name || 'Suhu'}`
      subtitle = `Rata-rata: ${genericTempVal}°C`
      segments = [
        { label: `${genericTempStat?.name || 'Suhu'}: ${genericTempVal}°C`, percent: 100, color: 'bg-amber-500', textClass: 'text-amber-600 dark:text-amber-400' }
      ]
    } else {
      title = 'Monitoring Sensor Lingkungan'
      subtitle = `${sensorStats.length} Sensor Aktif`
      segments = sensorStats.slice(0, 3).map((st: any, idx: number) => ({
        label: `${st.name}: ${st.current ?? st.avg ?? '--'}${st.unit}`,
        percent: Math.round(100 / Math.min(sensorStats.length, 3)),
        color: idx === 0 ? 'bg-amber-500' : (idx === 1 ? 'bg-sky-500' : 'bg-emerald-500'),
        textClass: idx === 0 ? 'text-amber-600' : (idx === 1 ? 'text-sky-600' : 'text-emerald-600')
      }))
    }

    const distributionWidget = {
      title,
      subtitle,
      segments
    }

    defaultBadgeText = 'Termal & Uptime Aman'
    defaultInsightText = `Suhu operasional box panel (${encVal ?? genericTempVal ?? '--'}°C) berada di bawah batas aman. Manajemen termal perangkat stabil selama ${rangeLabel.value}.`

    return {
      hasData: true,
      dataPoints: feeds.length,
      summaryTitle: 'Analisis IoT & Lingkungan',
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

  // 4. Kategori Kelistrikan & Daya (Tegangan, Arus, Daya)
  if (selectedCategory.value === 'power') {
    const battVoltStat = sensorStats.find((s: any) => s.name.toLowerCase().includes('tegangan baterai') || s.name.toLowerCase().includes('batt'))
    const loadVoltStat = sensorStats.find((s: any) => s.name.toLowerCase().includes('tegangan load') || s.name.toLowerCase().includes('load'))
    const loadPowerStat = sensorStats.find((s: any) => s.name.toLowerCase().includes('daya') && !s.name.toLowerCase().includes('daya hantar'))
    const netPow = power.value?.net_power != null ? Number(Number(power.value.net_power).toFixed(2)) : null

    const vBatt = battVoltStat ? Number((battVoltStat.current ?? battVoltStat.avg ?? 0).toFixed(2)) : null
    const vLoad = loadVoltStat ? Number((loadVoltStat.current ?? loadVoltStat.avg ?? 0).toFixed(2)) : null
    const pLoad = loadPowerStat ? Number((loadPowerStat.current ?? loadPowerStat.avg ?? 0).toFixed(2)) : null

    const distributionWidget = {
      title: 'Neraca & Aliran Daya',
      subtitle: netPow != null ? `${netPow > 0 ? '+' : ''}${netPow} W (${power.value?.status_aliran === 'surplus' ? 'Surplus' : 'Defisit'})` : 'INA226 Dual Monitor',
      segments: [
        { 
          label: `Baterai: ${vBatt ?? '--'}V`, 
          percent: 50, 
          color: 'bg-emerald-500', 
          textClass: 'text-emerald-600 dark:text-emerald-400' 
        },
        { 
          label: `Beban: ${vLoad ?? '--'}V (${pLoad ?? '--'}W)`, 
          percent: 50, 
          color: 'bg-amber-500', 
          textClass: 'text-amber-600 dark:text-amber-400' 
        }
      ]
    }

    defaultBadgeText = power.value?.status_aliran === 'surplus' ? 'Surplus Terjaga' : (power.value?.status_aliran === 'defisit' ? 'Konsumsi Aki' : 'Daya Stabil')
    defaultInsightText = `Pemantauan sistem daya 12V DC INA226. Tegangan aki rata-rata ${vBatt ?? '--'}V dengan suplai beban ${pLoad ?? '--'}W.`

    return {
      hasData: true,
      dataPoints: feeds.length,
      summaryTitle: 'Analisis Sistem Manajemen Daya',
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

  // 5. Kategori Semua Sensor
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
        <Card class="relative overflow-hidden">
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
        <Card class="relative overflow-hidden w-full aspect-square flex flex-col group">
          <div ref="miniMapContainer" data-lenis-prevent class="w-full h-full absolute inset-0 z-0" />
          
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
        <Card v-if="aktuator" class="relative overflow-hidden">
          <div class="p-4 sm:p-4.5 flex flex-col gap-3.5">
            <!-- Header: Title, Icon -->
            <div class="flex items-center gap-3">
              <img src="/actuator-icon.svg" alt="Status Aktuator" class="w-6 h-6 sm:w-7 sm:h-7 object-contain dark:invert shrink-0" />
              <h4 class="text-base sm:text-lg font-extrabold tracking-tight text-foreground leading-tight">Status Aktuator</h4>
            </div>

            <!-- 3 Expanded State Chips with Actuator Animations (Vertical Stack: Icon -> Name -> Badge) -->
            <div class="grid grid-cols-3 gap-2">
              <div 
                v-for="a in actuatorList" 
                :key="a.id"
                :class="[
                  'py-3 px-2 rounded-xl text-xs sm:text-sm font-medium border flex flex-col items-center justify-center gap-2 transition-all duration-200 text-center min-h-[96px] sm:min-h-[105px] select-none hover:-translate-y-0.5 cursor-default',
                  a.aktif 
                    ? a.activeBg 
                    : 'bg-slate-50 dark:bg-slate-900/50 border-slate-200/80 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-700'
                ]"
              >
                <!-- 1. Large Animated Icon on Top (Centered Horizontal) -->
                <div class="flex items-center justify-center h-8 sm:h-9">
                  <component 
                    :is="a.icon" 
                    :class="['w-7 h-7 sm:w-8 sm:h-8 transition-all', a.aktif ? a.iconActiveClass : a.iconInactiveClass]" 
                  />
                </div>

                <!-- 2. Actuator Name in the Middle -->
                <span class="text-xs sm:text-sm font-extrabold text-foreground tracking-tight leading-tight -mt-0.5">{{ a.nama }}</span>
                
                <!-- 3. ON / OFF Pill Badge at the Bottom -->
                <span 
                  :class="[
                    'text-[10px] sm:text-xs font-black tracking-wider px-2.5 py-0.5 rounded-md leading-tight uppercase',
                    a.aktif 
                      ? a.badgeActiveClass 
                      : 'bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-bold'
                  ]"
                >
                  {{ a.aktif ? 'ON' : 'OFF' }}
                </span>
              </div>
            </div>
          </div>
        </Card>

        <!-- CARD 4: KONDISI IOT (Suhu & Kelembaban Box Panel / Lingkungan) -->
        <Card class="relative overflow-hidden flex flex-col">
          <div class="p-4 flex flex-col gap-3 flex-1 justify-between">
            <!-- Portlet Header -->
            <div class="flex items-center justify-between pb-2 border-b border-border/40">
              <div class="flex items-center gap-3">
                <img src="/iot-icon.svg" alt="Kondisi IoT" class="w-6 h-6 sm:w-7 sm:h-7 object-contain dark:invert shrink-0" />
                <h4 class="text-base sm:text-lg font-extrabold tracking-tight text-foreground leading-tight">Kondisi IoT</h4>
              </div>
            </div>

            <!-- 1 Baris: 3 Kartu Kondisi IoT (Suhu Dalam Panel, Suhu Luar, Kelembaban Udara) -->
            <div class="grid grid-cols-3 gap-2">
              <!-- 1. Suhu Dalam Panel (Enclosure) -->
              <div 
                :class="[
                  'relative overflow-hidden p-2.5 sm:p-3 rounded-2xl text-white shadow-xs border border-white/20 flex flex-col justify-between group hover:scale-[1.01] transition-transform',
                  enclosureTempCardState.gradient,
                  enclosureTempCardState.shadow
                ]"
              >
                <DotPattern :width="12" :height="12" :cx="6" :cy="6" :cr="1" class="text-white/20" />
                <div class="relative z-10 flex flex-col justify-between h-full">
                  <div>
                    <span class="text-[10px] sm:text-[11px] font-semibold text-white/95 line-clamp-2 leading-tight block" :title="enclosureTempMetric?.name || 'Suhu Dalam Panel'">
                      {{ enclosureTempMetric?.name || 'Suhu Dalam Panel' }}
                    </span>
                    <div class="flex items-baseline gap-1 mt-1.5">
                      <span class="text-xl sm:text-2xl font-black tracking-tight text-white font-mono">
                        {{ getLiveVal(enclosureTempMetric) ?? '--' }}
                      </span>
                      <span class="text-xs font-bold text-white/90">
                        {{ enclosureTempMetric?.unit || '°C' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 2. Suhu Luar / Ambient -->
              <div 
                :class="[
                  'relative overflow-hidden p-2.5 sm:p-3 rounded-2xl text-white shadow-xs border border-white/20 flex flex-col justify-between group hover:scale-[1.01] transition-transform',
                  airTempCardState.gradient,
                  airTempCardState.shadow
                ]"
              >
                <DotPattern :width="12" :height="12" :cx="6" :cy="6" :cr="1" class="text-white/20" />
                <div class="relative z-10 flex flex-col justify-between h-full">
                  <div>
                    <span class="text-[10px] sm:text-[11px] font-semibold text-white/95 line-clamp-2 leading-tight block" :title="airTempMetric?.name || 'Suhu Luar'">
                      {{ airTempMetric?.name || 'Suhu Luar' }}
                    </span>
                    <div class="flex items-baseline gap-1 mt-1.5">
                      <span class="text-xl sm:text-2xl font-black tracking-tight text-white font-mono">
                        {{ getLiveVal(airTempMetric) ?? '--' }}
                      </span>
                      <span class="text-xs font-bold text-white/90">
                        {{ airTempMetric?.unit || '°C' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 3. Kelembaban Udara -->
              <div 
                :class="[
                  'relative overflow-hidden p-2.5 sm:p-3 rounded-2xl text-white shadow-xs border border-white/20 flex flex-col justify-between group hover:scale-[1.01] transition-transform',
                  humidityCardState.gradient,
                  humidityCardState.shadow
                ]"
              >
                <DotPattern :width="12" :height="12" :cx="6" :cy="6" :cr="1" class="text-white/20" />
                <div class="relative z-10 flex flex-col justify-between h-full">
                  <div>
                    <span class="text-[10px] sm:text-[11px] font-semibold text-white/95 line-clamp-2 leading-tight block" :title="humidityMetric?.name || 'Kelembaban'">
                      {{ humidityMetric?.name || 'Kelembaban' }}
                    </span>
                    <div class="flex items-baseline gap-1 mt-1.5">
                      <span class="text-xl sm:text-2xl font-black tracking-tight text-white font-mono">
                        {{ getLiveVal(humidityMetric) ?? '--' }}
                      </span>
                      <span class="text-xs font-bold text-white/90">
                        {{ humidityMetric?.unit || '%' }}
                      </span>
                    </div>
                  </div>
                </div>
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
          <Card class="lg:col-span-8 relative overflow-hidden flex flex-col min-h-[460px]">
            <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-30 pointer-events-none"></div>
            <CardContent class="p-4 relative z-10 flex flex-col gap-2 flex-1">
              
              <!-- Chart Header: Category Pills + Time Range -->
              <div class="flex flex-wrap items-center justify-between gap-3 pb-2.5 border-b border-border/40">
                
                <!-- Category Dropdown Selector -->
                <div class="relative" ref="categoryDropdownRef">
                  <button
                    type="button"
                    @click.stop="isCategoryDropdownOpen = !isCategoryDropdownOpen"
                    class="h-9.5 sm:h-10 px-3.5 sm:px-4 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200/80 dark:hover:bg-slate-700/80 border border-slate-200/90 dark:border-slate-700/90 text-foreground text-xs sm:text-sm md:text-base font-extrabold flex items-center gap-2.5 transition-all cursor-pointer shadow-2xs select-none active:scale-95"
                    :title="`Kategori: ${currentCategoryMeta.fullLabel}`"
                  >
                    <!-- Soft Tinted Icon Container with Colored Icon Lines -->
                    <div :class="['w-6 h-6 sm:w-7 sm:h-7 rounded-lg flex items-center justify-center shrink-0 border shadow-2xs transition-colors', currentCategoryMeta.wrapperClass]">
                      <div 
                        v-if="!currentCategoryMeta.isLucide" 
                        :class="['w-3.5 h-3.5 sm:w-4 sm:h-4 transition-colors', currentCategoryMeta.iconColorClass]"
                        :style="{
                          mask: `url(${currentCategoryMeta.icon}) no-repeat center / contain`,
                          WebkitMask: `url(${currentCategoryMeta.icon}) no-repeat center / contain`
                        }"
                      />
                      <component :is="currentCategoryMeta.lucideIcon || Layers" v-else :class="['w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0 transition-colors', currentCategoryMeta.iconTextColorClass]" />
                    </div>

                    <!-- Selected Category Label -->
                    <span class="tracking-tight">{{ currentCategoryMeta.fullLabel }}</span>

                    <!-- Chevron -->
                    <ChevronDown 
                      class="w-4 h-4 text-muted-foreground transition-transform duration-200" 
                      :class="isCategoryDropdownOpen ? 'rotate-180 text-foreground' : ''" 
                    />
                  </button>

                  <!-- Dropdown Menu Popover (Enlarged) -->
                  <div
                    v-if="isCategoryDropdownOpen"
                    class="absolute left-0 top-full mt-2 w-[calc(100vw-2.5rem)] max-w-[350px] sm:w-[350px] z-50 rounded-2xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200/90 dark:border-slate-800 shadow-2xl p-2 sm:p-2.5 flex flex-col gap-1.5 animate-in fade-in zoom-in-95 duration-150 select-none"
                  >
                    <div class="px-3.5 py-1.5 text-xs font-black text-muted-foreground uppercase tracking-wider">
                      Pilih Kategori
                    </div>

                    <button
                      v-for="cat in categoryOptions"
                      :key="cat.id"
                      type="button"
                      @click="selectCategory(cat.id)"
                      :class="[
                        'w-full px-3.5 py-3 rounded-2xl text-left flex items-center justify-between gap-3 transition-all cursor-pointer group active:scale-[0.98]',
                        selectedCategory === cat.id 
                          ? 'bg-slate-100/90 dark:bg-slate-800 border border-slate-300/80 dark:border-slate-700 shadow-2xs font-black text-foreground' 
                          : 'text-foreground/80 hover:text-foreground hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-transparent font-medium'
                      ]"
                    >
                      <div class="flex items-center gap-3.5 min-w-0">
                        <div :class="['w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border shadow-2xs group-hover:scale-105 transition-all', cat.wrapperClass]">
                          <div 
                            v-if="!cat.isLucide" 
                            :class="['w-5 h-5 transition-colors', cat.iconColorClass]"
                            :style="{
                              mask: `url(${cat.icon}) no-repeat center / contain`,
                              WebkitMask: `url(${cat.icon}) no-repeat center / contain`
                            }"
                          />
                          <component :is="cat.lucideIcon || Layers" v-else :class="['w-5 h-5 shrink-0 transition-colors', cat.iconTextColorClass]" />
                        </div>
                        <div class="min-w-0">
                          <div class="font-extrabold text-foreground leading-tight text-sm sm:text-base">{{ cat.fullLabel }}</div>
                          <div class="text-xs text-muted-foreground font-medium mt-0.5">{{ cat.desc }}</div>
                        </div>
                      </div>

                      <Check v-if="selectedCategory === cat.id" class="w-5 h-5 text-foreground shrink-0 stroke-[2.5]" />
                    </button>
                  </div>
                </div>

                <!-- Time Range Selector (Enlarged) -->
                <div class="flex items-center gap-1 sm:gap-1.5 bg-slate-100 dark:bg-slate-800 p-1 sm:p-1.5 rounded-xl border border-slate-200/80 dark:border-slate-700/80 text-xs sm:text-sm">
                  <button
                    @click="changeRange('1d')"
                    :class="[
                      'px-3 sm:px-3.5 py-1.5 rounded-lg font-extrabold transition-all cursor-pointer flex items-center gap-2 text-xs sm:text-sm active:scale-95',
                      selectedRange === '1d' 
                        ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    24J
                  </button>
                  <button
                    @click="changeRange('1w')"
                    :class="[
                      'px-3 sm:px-3.5 py-1.5 rounded-lg font-extrabold transition-all cursor-pointer text-xs sm:text-sm active:scale-95',
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
                      'px-3 sm:px-3.5 py-1.5 rounded-lg font-extrabold transition-all cursor-pointer text-xs sm:text-sm active:scale-95',
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
                      'px-2.5 sm:px-3 py-1.5 rounded-lg font-extrabold transition-all cursor-pointer text-xs sm:text-sm active:scale-95',
                      selectedRange === 'custom' 
                        ? 'bg-white dark:bg-card text-foreground border border-border/80 shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                    title="Rentang Kustom"
                  >
                    <Calendar class="w-4.5 h-4.5" />
                  </button>
                </div>

                <!-- Export & PDF Report Action Buttons (Only Visible When Logged In) -->
                <div v-if="authStore.isAuthenticated()" class="flex items-center gap-2 ml-auto sm:ml-0">
                  <button
                    @click="isExportModalOpen = true"
                    type="button"
                    class="h-9.5 sm:h-10 px-3.5 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 text-xs sm:text-sm font-bold flex items-center gap-2 shadow-2xs transition-all cursor-pointer hover:scale-[1.02] active:scale-95"
                    title="Export data telemetri ke format CSV (Excel)"
                  >
                    <ExcelIcon />
                    <span class="hidden md:inline">Export CSV</span>
                  </button>

                  <button
                    @click="isReportModalOpen = true"
                    type="button"
                    class="h-9.5 sm:h-10 px-3.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-700 dark:text-rose-300 border border-rose-500/30 text-xs sm:text-sm font-bold flex items-center gap-2 shadow-2xs transition-all cursor-pointer hover:scale-[1.02] active:scale-95"
                    title="Buat dan cetak Laporan Resmi PDF"
                  >
                    <PdfIcon />
                    <span class="hidden md:inline">Laporan PDF</span>
                  </button>
                </div>
              </div>

              <!-- Custom Date Picker -->
              <div v-if="selectedRange === 'custom'" class="flex flex-wrap items-center gap-3 p-2 bg-muted/30 dark:bg-muted/10 border border-border/50 rounded-xl shadow-[inset_0_1px_1px_rgba(255,255,255,0.6)] dark:shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] text-xs sm:text-sm animate-slide-up">
                <div class="flex items-center bg-background rounded-lg border border-border/80 shadow-sm overflow-hidden">
                  <div class="flex items-center px-3 bg-muted/50 border-r border-border/80 h-8">
                    <Calendar class="w-3.5 h-3.5 text-muted-foreground mr-1.5" />
                    <span class="text-muted-foreground font-semibold text-xs">Dari</span>
                  </div>
                  <Input type="date" v-model="customStartDate" class="h-8 text-xs sm:text-sm border-0 w-32 sm:w-36 rounded-none focus-visible:ring-0 focus-visible:ring-offset-0 px-2 shadow-none" />
                </div>
                
                <div class="flex items-center bg-background rounded-lg border border-border/80 shadow-sm overflow-hidden">
                  <div class="flex items-center px-3 bg-muted/50 border-r border-border/80 h-8">
                    <Calendar class="w-3.5 h-3.5 text-muted-foreground mr-1.5" />
                    <span class="text-muted-foreground font-semibold text-xs">Sampai</span>
                  </div>
                  <Input type="date" v-model="customEndDate" class="h-8 text-xs sm:text-sm border-0 w-32 sm:w-36 rounded-none focus-visible:ring-0 focus-visible:ring-offset-0 px-2 shadow-none" />
                </div>
                
                <Button size="sm" variant="default" class="h-8 text-xs px-4 shadow-[inset_0_1px_1px_rgba(255,255,255,0.2)] font-bold rounded-lg transition-transform active:scale-95" @click="applyCustomDate" :disabled="!customStartDate">
                  <Check class="w-3.5 h-3.5 mr-1.5" />
                  Terapkan
                </Button>
              </div>

              <!-- Chart Visual Canvas (Fills 100% of Stretched Card Height) -->
              <div class="w-full flex-1 flex flex-col min-h-[350px] pt-1">
                <SensorLineChart 
                  :key="selectedCategory"
                  :data="chartData" 
                  :title="`Tren ${selectedCategory === 'npk' ? 'Unsur Hara NPK' : (selectedCategory === 'soil' ? 'Kondisi Tanah' : (selectedCategory === 'environment' ? 'Kondisi IoT' : (selectedCategory === 'power' ? 'Sistem Manajemen Daya' : 'Sensor')))}`" 
                  :sensors="activeCategorySensors" 
                  :is-loading="isArchiveLoading || isLoading || (!isInitialLoaded && chartData.length === 0)"
                />
              </div>
            </CardContent>
          </Card>

          <!-- RIGHT COL (lg:col-span-4): Dynamic Category-Aware Analytics & Insights Card (Enlarged Typography) -->
          <Card class="lg:col-span-4 relative overflow-hidden flex flex-col min-h-[460px]">
            <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-primary/5 pointer-events-none"></div>
            <CardContent class="p-4 sm:p-4.5 relative z-10 flex flex-col justify-between gap-3 flex-1 h-full">
              
              <!-- Header: Horizontal Split with Compact Badge -->
              <div class="pb-2.5 border-b border-border/40 flex items-center justify-between w-full gap-2">
                <div class="flex items-center gap-2.5 min-w-0">
                  <Sparkles class="w-5 h-5 sm:w-6 sm:h-6 text-foreground shrink-0" />
                  <h4 class="text-base sm:text-lg font-bold text-foreground tracking-tight truncate">
                    {{ analyticsData.summaryTitle }}
                  </h4>
                </div>
                <div class="shrink-0 inline-flex items-center gap-1.5 text-[10px] sm:text-xs font-semibold text-muted-foreground border border-border/60 bg-background/50 px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-full shadow-sm">
                  <span>{{ rangeLabel }}</span>
                  <span class="text-border">|</span>
                  <span class="font-mono text-emerald-600 dark:text-emerald-400">{{ analyticsData.dataPoints }} Data</span>
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
                  class="p-2.5 sm:p-3 rounded-xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between gap-2.5 hover:-translate-y-1 hover:shadow-md transition-all duration-300"
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

        <!-- ROW 3: Dua Portlet Berdampingan (Kondisi Tanah & Sistem Daya Kelistrikan) -->
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-3.5">
          
          <!-- PORTLET 1: KONDISI TANAH -->
          <Card class="relative overflow-hidden flex flex-col">
            <div class="p-4 flex flex-col gap-3 flex-1 justify-between">
              <!-- Portlet Header -->
              <div class="flex items-center justify-between pb-2 border-b border-border/40">
                <div class="flex items-center gap-3">
                  <img src="/soil-icon.svg" alt="Kondisi Tanah" class="w-6 h-6 sm:w-7 sm:h-7 object-contain dark:invert shrink-0" />
                  <h4 class="text-base sm:text-lg font-extrabold tracking-tight text-foreground leading-tight">Kondisi Tanah</h4>
                </div>
              </div>

              <!-- Multi-Probe Moisture Comparison Widget -->
              <div class="bg-slate-50/80 dark:bg-slate-900/50 rounded-2xl p-3 sm:p-3.5 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-3 flex-1">
                <!-- Header: Judul & Rata-rata Menonjol -->
                <div class="flex items-center justify-between gap-3">
                  <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-xl bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                      <Droplets class="w-5 h-5 stroke-[2.5]" />
                    </div>
                    <p class="text-sm sm:text-base font-semibold text-slate-800 dark:text-slate-100 tracking-wide leading-tight">
                      Rata-rata Kelembapan Tanah
                    </p>
                  </div>

                  <!-- Moisture Value Display (Teks Besar) -->
                  <div class="flex items-baseline gap-1 shrink-0">
                    <span v-if="soilProbes.length > 1" class="text-xs sm:text-sm font-bold text-blue-600 dark:text-blue-400 mr-0.5">Avg:</span>
                    <span class="text-2xl sm:text-3xl font-black text-blue-600 dark:text-blue-400 font-mono tracking-tight">
                      {{ realTimeAvgMoisture != null ? `${realTimeAvgMoisture}%` : '--' }}
                    </span>
                  </div>
                </div>

                <!-- 3 Baris Probe Horizontal dengan Bar Tebal Bergradien Air (Cyan → Biru) -->
                <div class="space-y-2.5">
                  <div 
                    v-for="(probe, idx) in soilProbes" 
                    :key="probe.id || idx" 
                    class="space-y-1"
                  >
                    <div class="flex justify-between items-center text-xs">
                      <span class="text-slate-600 dark:text-slate-400 font-semibold flex items-center gap-1.5">
                        <span class="w-1.5 h-1.5 rounded-full bg-sky-500"></span>
                        {{ probe.name }}
                      </span>
                      <span class="font-extrabold font-mono text-slate-800 dark:text-slate-200">
                        {{ getLiveVal(probe) ?? '--' }}{{ probe.unit || '%' }}
                      </span>
                    </div>
                    <!-- Dynamic High-Gloss Water Gradient Bar -->
                    <div class="h-2.5 w-full bg-slate-200/80 dark:bg-slate-800/90 rounded-full overflow-hidden p-0.5 flex items-center">
                      <div 
                        :class="['h-full bg-gradient-to-r rounded-full transition-all duration-500 shadow-xs', getProbeBarGradient(probe)]" 
                        :style="{ width: `${Math.min(Math.max(Number(getLiveVal(probe) || 0), 0), 100)}%` }"
                      />
                    </div>
                  </div>
                  <!-- Tampilan bar utama ketika data dikirim sebagai nilai tunggal / probe NPK -->
                  <div v-if="!soilProbes.length" class="pt-1">
                    <div class="h-3 w-full bg-slate-200/80 dark:bg-slate-800/90 rounded-full overflow-hidden p-0.5 flex items-center">
                      <div 
                        class="h-full bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full transition-all duration-500 shadow-xs" 
                        :style="{ width: `${Math.min(Math.max(Number(realTimeAvgMoisture || 0), 0), 100)}%` }"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Compact Mini Metrics: pH, Suhu Tanah, EC (Dynamic 3-State Semantic Gradient Cards) -->
              <div class="grid grid-cols-3 gap-2 sm:gap-2.5">
                <!-- pH Tanah Card (Dynamic 3-State: Asam: Oranye-Merah | Optimal: Emerald | Basa: Ungu/Indigo) -->
                <div 
                  :class="[
                    'relative overflow-hidden p-2.5 sm:p-3 rounded-2xl text-white shadow-xs border border-white/20 flex flex-col justify-between min-h-[92px] sm:min-h-[96px] group hover:scale-[1.01] transition-transform',
                    phCardState.gradient,
                    phCardState.shadow
                  ]"
                >
                  <DotPattern :width="12" :height="12" :cx="6" :cy="6" :cr="1" class="text-white/20" />
                  <div class="flex items-start justify-between gap-1.5 relative z-10">
                    <span class="text-[11px] sm:text-xs font-semibold text-white/95 line-clamp-2 leading-tight flex-1 drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">
                      {{ phMetric?.name || 'pH Tanah' }}
                    </span>
                    <!-- Unified Status & Threshold Capsule -->
                    <div 
                      :class="[
                        'bg-white/25 hover:bg-white/30 backdrop-blur-md text-white border border-white/40 shadow-2xs transition-all shrink-0 select-none',
                        phCardState.isAlert 
                          ? 'px-2 py-0.5 rounded-xl flex flex-col items-center gap-0.5' 
                          : 'px-2 py-0.5 rounded-full flex items-center'
                      ]"
                    >
                      <span class="text-[10px] sm:text-[11px] font-extrabold tracking-wide leading-tight drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">{{ phStatus.text }}</span>
                      <span v-if="phCardState.isAlert" class="text-[9px] sm:text-[10px] font-bold text-white/95 border-t border-white/25 pt-0.5 tracking-tight whitespace-nowrap">
                        {{ phCardState.min }}–{{ phCardState.max }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-baseline gap-1 mt-1 relative z-10">
                    <span class="text-xl sm:text-2xl font-extrabold tracking-tight text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.2)]">
                      {{ getLiveVal(phMetric) ?? '--' }}
                    </span>
                    <span class="text-xs font-bold text-white/90 drop-shadow-[0_1px_1px_rgba(0,0,0,0.1)]">
                      {{ phMetric?.unit || 'pH' }}
                    </span>
                  </div>
                </div>

                <!-- Suhu Tanah Card (Dynamic 3-State: Dingin: Biru Ice | Optimal: Oranye Hangat | Panas: Merah Rose Alert) -->
                <div 
                  :class="[
                    'relative overflow-hidden p-2.5 sm:p-3 rounded-2xl text-white shadow-xs border border-white/20 flex flex-col justify-between min-h-[92px] sm:min-h-[96px] group hover:scale-[1.01] transition-transform',
                    soilTempCardState.gradient,
                    soilTempCardState.shadow
                  ]"
                >
                  <DotPattern :width="12" :height="12" :cx="6" :cy="6" :cr="1" class="text-white/20" />
                  <div class="flex items-start justify-between gap-1.5 relative z-10">
                    <span class="text-[11px] sm:text-xs font-semibold text-white/95 line-clamp-2 leading-tight flex-1 drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">
                      {{ soilTempMetric?.name || 'Suhu Tanah' }}
                    </span>
                    <!-- Unified Status & Threshold Capsule -->
                    <div 
                      :class="[
                        'bg-white/25 hover:bg-white/30 backdrop-blur-md text-white border border-white/40 shadow-2xs transition-all shrink-0 select-none',
                        soilTempCardState.isAlert 
                          ? 'px-2 py-0.5 rounded-xl flex flex-col items-center gap-0.5' 
                          : 'px-2 py-0.5 rounded-full flex items-center'
                      ]"
                    >
                      <span class="text-[10px] sm:text-[11px] font-extrabold tracking-wide leading-tight drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">{{ soilTempStatus.text }}</span>
                      <span v-if="soilTempCardState.isAlert" class="text-[9px] sm:text-[10px] font-bold text-white/95 border-t border-white/25 pt-0.5 tracking-tight whitespace-nowrap">
                        {{ soilTempCardState.min }}–{{ soilTempCardState.max }}°
                      </span>
                    </div>
                  </div>
                  <div class="flex items-baseline gap-1 mt-1 relative z-10">
                    <span class="text-xl sm:text-2xl font-extrabold tracking-tight text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.2)]">
                      {{ getLiveVal(soilTempMetric) ?? '--' }}
                    </span>
                    <span class="text-xs font-bold text-white/90 drop-shadow-[0_1px_1px_rgba(0,0,0,0.1)]">
                      {{ soilTempMetric?.unit || '°C' }}
                    </span>
                  </div>
                </div>

                <!-- EC (Electrical Conductivity) Card (Dynamic 3-State: Rendah: Amber | Optimal: Lime/Emerald | Pekat: Merah Salin) -->
                <div 
                  :class="[
                    'relative overflow-hidden p-2.5 sm:p-3 rounded-2xl text-white shadow-xs border border-white/20 flex flex-col justify-between min-h-[92px] sm:min-h-[96px] group hover:scale-[1.01] transition-transform',
                    ecCardState.gradient,
                    ecCardState.shadow
                  ]"
                >
                  <DotPattern :width="12" :height="12" :cx="6" :cy="6" :cr="1" class="text-white/20" />
                  <div class="flex items-start justify-between gap-1.5 relative z-10">
                    <span class="text-[11px] sm:text-xs font-semibold text-white/95 line-clamp-2 leading-tight flex-1 drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">
                      {{ ecMetric?.name || 'eC Tanah' }}
                    </span>
                    <!-- Unified Status & Threshold Capsule -->
                    <div 
                      :class="[
                        'bg-white/25 hover:bg-white/30 backdrop-blur-md text-white border border-white/40 shadow-2xs transition-all shrink-0 select-none',
                        ecCardState.isAlert 
                          ? 'px-2 py-0.5 rounded-xl flex flex-col items-center gap-0.5' 
                          : 'px-2 py-0.5 rounded-full flex items-center'
                      ]"
                    >
                      <span class="text-[10px] sm:text-[11px] font-extrabold tracking-wide leading-tight drop-shadow-[0_1px_1px_rgba(0,0,0,0.15)]">{{ ecStatus.text }}</span>
                      <span v-if="ecCardState.isAlert" class="text-[9px] sm:text-[10px] font-bold text-white/95 border-t border-white/25 pt-0.5 tracking-tight whitespace-nowrap">
                        {{ ecCardState.min }}–{{ ecCardState.max }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-baseline gap-1 mt-1 relative z-10">
                    <span class="text-xl sm:text-2xl font-extrabold tracking-tight text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.2)]">
                      {{ getLiveVal(ecMetric) ?? '--' }}
                    </span>
                    <span class="text-xs font-bold text-white/90 drop-shadow-[0_1px_1px_rgba(0,0,0,0.1)]">
                      {{ ecMetric?.unit || 'µS/cm' }}
                    </span>
                  </div>
                </div>
              </div>

            </div>
          </Card>

          <!-- PORTLET 2: SISTEM SOLAR PANEL (INA226) -->
          <Card class="relative overflow-hidden flex flex-col">
            <div class="p-4 flex flex-col gap-3 flex-1 justify-between">
              <!-- Portlet Header -->
              <div class="flex items-center justify-between pb-2 border-b border-border/40">
                <div class="flex items-center gap-3">
                  <Zap class="w-6 h-6 sm:w-7 sm:h-7 text-foreground stroke-[2.2] shrink-0" />
                  <h4 class="text-base sm:text-lg font-extrabold tracking-tight text-foreground leading-tight">
                    Sistem Manajemen Daya
                  </h4>
                </div>
              </div>

              <!-- Top Section: Status Sistem 3D, Baterai 12V & Beban Sistem (Kolom 1 compact, Kolom 2 & 3 ekspansif) -->
              <div class="grid grid-cols-1 sm:grid-cols-[100px_1fr_1fr] gap-2.5 flex-1">
                
                <!-- KOTAK 1: STATUS SISTEM (3D Jumbo Micro-Animation) -->
                <PowerStateBadge 
                  :status="power?.status_aliran" 
                  :label="power?.battery_status_text" 
                />

                <!-- KOTAK 2: BATERAI 12V -->
                <div class="bg-slate-50/80 dark:bg-slate-900/50 rounded-2xl p-3 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-2.5">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-1.5">
                      <component :is="power?.is_charging ? BatteryCharging : Battery" class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                      <span class="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">Baterai 12V</span>
                    </div>
                    <span 
                      class="text-[10px] font-mono font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md border shadow-2xs select-none"
                      :class="power?.i2c_0x40_active 
                        ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/25 dark:border-emerald-500/30' 
                        : 'text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/80 border-slate-200 dark:border-slate-700'"
                      title="Status Sensor Baterai (I2C 0x40)"
                    >
                      {{ power?.i2c_0x40_active ? 'Aktif' : 'Standby' }}
                    </span>
                  </div>

                  <!-- Tegangan Utama Baterai & Level % di Kanan Atas Bar -->
                  <div class="space-y-1">
                    <div class="flex items-baseline justify-between">
                      <div class="flex items-baseline gap-1">
                        <span class="text-2xl sm:text-3xl font-black font-mono tracking-tight text-slate-800 dark:text-slate-100">
                          {{ power?.tegangan_in != null ? Number(power.tegangan_in).toFixed(2) : '--' }}
                        </span>
                        <span class="text-xs font-extrabold text-slate-500 dark:text-slate-400">V</span>
                      </div>
                      <span v-if="batteryLevelPercent != null" class="text-base sm:text-lg font-mono font-black transition-colors duration-300" :class="batteryStatusInfo.textColor">
                        {{ batteryLevelPercent }}%
                      </span>
                    </div>
                    <!-- Level Gauge Bar -->
                    <div class="space-y-0.5">
                      <div class="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          :class="['h-full bg-gradient-to-r rounded-full transition-all duration-500', batteryStatusInfo.barColor]"
                          :style="{ width: `${batteryLevelPercent ?? 0}%` }"
                        />
                      </div>
                      <div class="flex justify-between text-[9px] text-muted-foreground font-mono">
                        <span>11.0V</span>
                        <span>13.8V</span>
                      </div>
                    </div>
                  </div>

                  <!-- Sub: Arus & Daya Baterai -->
                  <div class="grid grid-cols-2 gap-1.5 pt-2 border-t border-slate-200/60 dark:border-slate-800/60 text-center">
                    <div class="bg-white/70 dark:bg-slate-800/50 rounded-lg p-1.5 border border-slate-200/50 dark:border-slate-700/50">
                      <p class="text-[9px] font-bold text-muted-foreground uppercase">Arus</p>
                      <p class="text-xs font-mono font-black text-foreground mt-0.5">
                        {{ power?.arus_in != null ? `${Number(power.arus_in) > 0 ? '+' : ''}${Number(power.arus_in).toFixed(3)} A` : '--' }}
                      </p>
                    </div>
                    <div class="bg-white/70 dark:bg-slate-800/50 rounded-lg p-1.5 border border-slate-200/50 dark:border-slate-700/50">
                      <p class="text-[9px] font-bold text-muted-foreground uppercase">Daya</p>
                      <p class="text-xs font-mono font-black text-foreground mt-0.5">
                        {{ power?.daya_in != null ? `${Number(power.daya_in) > 0 ? '+' : ''}${Number(power.daya_in).toFixed(2)} W` : '--' }}
                      </p>
                    </div>
                  </div>
                </div>

                <!-- KOTAK 2: BEBAN SISTEM -->
                <div class="bg-slate-50/80 dark:bg-slate-900/50 rounded-2xl p-3 border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between gap-2.5">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-1.5">
                      <Zap class="w-4 h-4 text-amber-600 dark:text-amber-400" />
                      <span class="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">Load Sistem</span>
                    </div>
                    <span 
                      class="text-[10px] font-mono font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-md border shadow-2xs select-none"
                      :class="power?.i2c_0x41_active 
                        ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/25 dark:border-emerald-500/30' 
                        : 'text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/80 border-slate-200 dark:border-slate-700'"
                      title="Status Sensor Beban (I2C 0x41)"
                    >
                      {{ power?.i2c_0x41_active ? 'Aktif' : 'Standby' }}
                    </span>
                  </div>

                  <!-- Arus Load Utama (Highlight) & Indikator Output Beban -->
                  <div class="space-y-1">
                    <div class="flex items-baseline justify-between">
                      <div class="flex items-baseline gap-1">
                        <span class="text-2xl sm:text-3xl font-black font-mono tracking-tight text-slate-800 dark:text-slate-100">
                          {{ power?.arus_out != null ? Number(power.arus_out).toFixed(3) : '--' }}
                        </span>
                        <span class="text-xs font-extrabold text-slate-500 dark:text-slate-400">A</span>
                      </div>
                      <span class="text-xs font-mono font-extrabold uppercase tracking-wide flex items-center gap-1 transition-colors duration-300" :class="loadStatusInfo.textColor">
                        <span class="w-1.5 h-1.5 rounded-full animate-pulse" :class="loadStatusInfo.dotColor"></span>
                        {{ loadStatusInfo.statusText }}
                      </span>
                    </div>
                    <!-- Visual Range Threshold Arus Beban (Simetris dengan Bar Baterai) -->
                    <div class="space-y-0.5">
                      <div class="h-1.5 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          :class="['h-full bg-gradient-to-r rounded-full transition-all duration-500', loadStatusInfo.barColor]"
                          :style="{ width: `${loadCurrentPercent}%` }"
                          :title="`Arus Beban: ${power?.arus_out != null ? Number(power.arus_out).toFixed(3) : '--'} A (Ambang: ${loadCurrentThresholds.min}A - ${loadCurrentThresholds.max}A)`"
                        />
                      </div>
                      <div class="flex justify-between text-[9px] text-muted-foreground font-mono">
                        <span>{{ loadCurrentThresholds.min.toFixed(1) }}A</span>
                        <span>{{ loadCurrentThresholds.max.toFixed(1) }}A</span>
                      </div>
                    </div>
                  </div>

                  <!-- Sub: Tegangan & Daya Beban -->
                  <div class="grid grid-cols-2 gap-1.5 pt-2 border-t border-slate-200/60 dark:border-slate-800/60 text-center">
                    <div class="bg-white/70 dark:bg-slate-800/50 rounded-lg p-1.5 border border-slate-200/50 dark:border-slate-700/50">
                      <p class="text-[9px] font-bold text-muted-foreground uppercase">Tegangan</p>
                      <p class="text-xs font-mono font-black text-foreground mt-0.5">
                        {{ power?.tegangan_out != null ? `${Number(power.tegangan_out).toFixed(2)} V` : '--' }}
                      </p>
                    </div>
                    <div class="bg-white/70 dark:bg-slate-800/50 rounded-lg p-1.5 border border-slate-200/50 dark:border-slate-700/50">
                      <p class="text-[9px] font-bold text-muted-foreground uppercase">Daya</p>
                      <p class="text-xs font-mono font-black text-foreground mt-0.5">
                        {{ power?.daya_out != null ? `${Number(power.daya_out).toFixed(2)} W` : '--' }}
                      </p>
                    </div>
                  </div>
                </div>

              </div>

              <!-- Bottom Section: Neraca Daya (1 Baris Bersih & Netral) -->
              <div class="bg-slate-50/80 dark:bg-slate-900/50 rounded-2xl px-3.5 py-2.5 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between gap-2.5">
                <!-- Neraca Daya Bersih Tanpa Background Warna -->
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Neraca Daya:</span>
                  <div 
                    class="flex items-center gap-1.5 text-sm font-black tracking-tight"
                    :class="[
                      power?.net_power > 0 
                        ? 'text-emerald-600 dark:text-emerald-400' 
                        : power?.net_power < 0 
                          ? 'text-amber-600 dark:text-amber-400' 
                          : 'text-slate-600 dark:text-slate-400'
                    ]"
                  >
                    <span class="font-mono">
                      {{ power?.net_power != null ? `${power.net_power > 0 ? '+' : ''}${Number(power.net_power).toFixed(2)} W` : '--' }}
                    </span>
                    <span>
                      {{ power?.status_label || 'Status Daya' }}
                    </span>
                  </div>
                </div>
              </div>

            </div>
          </Card>
        </div>

        <!-- Sensor & Metrik Tambahan (Jaring Pengaman Otomatis jika ada parameter baru) -->
          <div v-if="additionalSensors.length" class="mt-4 pt-4 border-t border-slate-200/80 dark:border-slate-800 space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg">📌</span>
                <h4 class="text-base font-extrabold tracking-tight text-foreground">
                  Sensor &amp; Metrik Tambahan
                </h4>
                <Badge variant="outline" class="text-[11px] font-mono px-2 py-0.5">
                  {{ additionalSensors.length }} Parameter
                </Badge>
              </div>
              <span class="text-xs text-muted-foreground italic">
                Metrik aktif di database yang belum terdaftar di widget utama
              </span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              <SensorCard
                v-for="s in additionalSensors"
                :key="s.id || s.field_key"
                :title="s.name"
                :value="getLiveVal(s)"
                :unit="s.unit"
                :type="s.type"
                :status="s.status"
                :min-threshold="s.min_threshold"
                :max-threshold="s.max_threshold"
              />
            </div>
          </div>

        </div>

      </div>

    </div>

  <!-- Export Telemetry Modal (CSV) -->
  <ExportTelemetryModal
    :open="isExportModalOpen"
    @update:open="isExportModalOpen = $event"
    :node-id="nodeId"
    :node-name="nodeName || 'Stasiun Agro'"
    :sensors="sensors"
    :current-feeds="chartData"
  />

  <!-- Executive PDF Report Preview & Generator Modal -->
  <ReportPreviewModal
    :open="isReportModalOpen"
    @update:open="isReportModalOpen = $event"
    :node-id="nodeId"
    :node-name="nodeName || 'Stasiun Agro'"
    :location="nodeLocation || 'Kebun Pertanian / Greenhouse'"
    :coordinates="nodeCoords ? `${nodeCoords.lat.toFixed(4)}, ${nodeCoords.lng.toFixed(4)}` : '-7.6846, 110.3400'"
    :sensors="sensors"
    :current-feeds="chartData"
    :initial-range="selectedRange"
    :initial-category="selectedCategory"
    :summary-metrics="(analyticsData?.metrics || []).slice(0, 3).map(mm => mm.name)"
    :range-label="rangeLabel"
    :npk-ratio="analyticsData?.distributionWidget?.subtitle"
    :soil-avg-moisture="getLiveVal(avgMoistureMetric)"
    :ph-val="getLiveVal(phMetric)"
    :ec-val="getLiveVal(ecMetric)"
    :enclosure-temp="getLiveVal(enclosureTempMetric)"
    :enclosure-safe-limit="thermalStatus?.safeLimit || 55"
    :agronomy-insight="analyticsData?.insightText"
    :thermal-insight="thermalStatus?.insight"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import { useNodes } from '@/composables/useNodes'
import { useAuthStore } from '@/stores/auth'
import { useTelemetryStore } from '@/stores/telemetry'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { MapPin, Edit2, Save, X, Search, Compass, ChevronRight } from 'lucide-vue-next'
import { reverseGeocode } from '@/lib/geocoding'

const ELINS_CENTER: [number, number] = [-7.7679423, 110.3765989]

const router = useRouter()
const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()
const { nodesQuery, updateNodeMutation } = useNodes()

const nodes = computed(() => nodesQuery.data.value ?? [])
const searchQuery = ref('')
const activeNodeId = ref<string | null>(null)

const filteredNodes = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return nodes.value
  return nodes.value.filter((n: any) => 
    (n.name && n.name.toLowerCase().includes(q)) || 
    (n.node_id && n.node_id.toLowerCase().includes(q)) ||
    (n.location && n.location.toLowerCase().includes(q))
  )
})

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
const markers: Record<string, L.Marker> = {}

const editMode = ref(false)
const editingNode = ref<string | null>(null)
const editLat = ref('')
const editLng = ref('')

const isNodeOnline = (node: any) => {
  return telemetryStore.isNodeOnline(node.node_id, node.last_seen)
}

const makeIcon = (online: boolean) =>
  L.divIcon({
    html: `<div style="position:relative;width:28px;height:36px;display:flex;align-items:center;justify-content:center;">
      ${online ? '<span style="position:absolute;top:5px;left:4px;width:20px;height:20px;border-radius:50%;background:rgba(16,185,129,0.45);animation:ping 2s cubic-bezier(0,0,0.2,1) infinite;"></span>' : ''}
      <svg width="24" height="32" viewBox="0 0 24 32" fill="none" xmlns="http://www.w3.org/2000/svg" style="position:relative;z-index:10;filter:drop-shadow(0 3px 6px rgba(0,0,0,0.28));">
        <path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 20 12 20s12-11 12-20C24 5.373 18.627 0 12 0z" fill="${online ? '#10b981' : '#ef4444'}"/>
        <circle cx="12" cy="12" r="4.5" fill="white"/>
      </svg>
    </div>`,
    className: '',
    iconSize: [28, 36],
    iconAnchor: [14, 36],
    popupAnchor: [0, -36],
  })

const getSensorValue = (feed: any, nameQuery: string, sensors: any[]) => {
  const sensor = sensors.find(s => s.name.toLowerCase().includes(nameQuery.toLowerCase()))
  if (!sensor || !feed) return '—'
  const key = `${sensor.channel_id}_${sensor.thingspeak_field}`
  const val = feed[key]
  return val != null ? `${parseFloat(val).toFixed(1)} ${sensor.unit}` : '—'
}

const buildPopupHtml = (node: any, online: boolean, feed: any, sensors: any[]) => {
  const n = getSensorValue(feed, 'Nitrogen', sensors)
  const p = getSensorValue(feed, 'Phosphorus', sensors)
  const k = getSensorValue(feed, 'Potassium', sensors)
  const hasData = feed != null

  return `<div style="min-width:210px;font-family:system-ui,-apple-system,sans-serif;padding:6px 4px">
    <div style="font-weight:700;font-size:15px;color:#0f172a;margin-bottom:4px;display:flex;align-items:center;justify-content:space-between">
      <span>${node.name || 'IoT Node'}</span>
    </div>
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px">
      <span style="width:8px;height:8px;border-radius:50%;background:${online ? '#22c55e' : '#ef4444'};display:inline-block"></span>
      <span style="font-size:12px;font-weight:600;color:${online ? '#16a34a' : '#dc2626'}">${online ? 'Online' : 'Offline'}</span>
      ${!hasData ? '<span style="font-size:11px;color:#94a3b8;margin-left:auto">(Sinkronisasi...)</span>' : ''}
    </div>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:8px 10px;margin-bottom:12px">
      <table style="width:100%;font-size:13px;border-collapse:collapse">
        <tr style="border-bottom:1px solid #f1f5f9">
          <td style="padding:4px 0;color:#64748b;font-weight:500">🌿 Nitrogen</td>
          <td style="padding:4px 0;font-weight:700;text-align:right;color:#0f172a">${n}</td>
        </tr>
        <tr style="border-bottom:1px solid #f1f5f9">
          <td style="padding:4px 0;color:#64748b;font-weight:500">🧪 Phosphorus</td>
          <td style="padding:4px 0;font-weight:700;text-align:right;color:#0f172a">${p}</td>
        </tr>
        <tr>
          <td style="padding:4px 0;color:#64748b;font-weight:500">⚡ Potassium</td>
          <td style="padding:4px 0;font-weight:700;text-align:right;color:#0f172a">${k}</td>
        </tr>
      </table>
    </div>
    <a href="/nodes/${node.id || node.node_id}" style="display:block;padding:8px 10px;background:#16a34a;color:white;border-radius:6px;text-decoration:none;font-size:12px;font-weight:600;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,0.05)">Buka Dashboard Node &rarr;</a>
  </div>`
}

const nodeSensorsMap = ref<Record<string, any[]>>({})

const addOrUpdateMarker = async (node: any) => {
  if (node.latitude == null || node.longitude == null) return
  const online = isNodeOnline(node)
  const latLng: [number, number] = [node.latitude, node.longitude]
  
  const cachedFeed = telemetryStore.telemetryHistory[node.node_id]?.[0] ?? null
  const cachedSensors = nodeSensorsMap.value[node.node_id] || []
  const initialHtml = buildPopupHtml(node, online, cachedFeed, cachedSensors)

  if (markers[node.node_id]) {
    markers[node.node_id].setLatLng(latLng)
    markers[node.node_id].setIcon(makeIcon(online))
    if (!markers[node.node_id].getPopup()) {
      markers[node.node_id].bindPopup(initialHtml, { maxWidth: 280 })
    }
  } else {
    const marker = L.marker(latLng, { icon: makeIcon(online), draggable: false })
    marker.bindPopup(initialHtml, { maxWidth: 280 })

    const updatePopup = async () => {
      const fullNode = nodes.value.find((n: any) => n.node_id === node.node_id) || node
      const [sensors, history] = await Promise.all([
        telemetryStore.fetchSensors(node.node_id),
        telemetryStore.fetchHistory(node.node_id)
      ])
      nodeSensorsMap.value[node.node_id] = sensors
      const feed = history?.[0] ?? null
      const onlineNow = isNodeOnline(fullNode)
      marker.setIcon(makeIcon(onlineNow))
      marker.getPopup()?.setContent(buildPopupHtml(fullNode, onlineNow, feed, sensors))
    }

    marker.on('click', updatePopup)
    marker.on('popupopen', updatePopup)

    marker.addTo(map!)
    markers[node.node_id] = marker
  }
}

// React to global telemetry updates
watch(() => telemetryStore.telemetryHistory, (historyMap) => {
  Object.keys(historyMap).forEach((nodeId) => {
    const marker = markers[nodeId]
    const fullNode = nodes.value.find((n: any) => n.node_id === nodeId)
    if (marker && fullNode) {
      const onlineNow = isNodeOnline(fullNode)
      marker.setIcon(makeIcon(onlineNow))
      if (marker.isPopupOpen()) {
        const sensors = nodeSensorsMap.value[nodeId] || []
        const feed = historyMap[nodeId]?.[0] ?? null
        marker.getPopup()?.setContent(buildPopupHtml(fullNode, onlineNow, feed, sensors))
      }
    }
  })
}, { deep: true })

const enableDrag = (node: any) => {
  const marker = markers[node.node_id]
  if (!marker) return
  marker.dragging?.enable()
  marker.off('dragend')
  marker.on('dragend', async () => {
    const pos = marker.getLatLng()
    const lat = Number(pos.lat.toFixed(6))
    const lng = Number(pos.lng.toFixed(6))

    const autoPlaceName = await reverseGeocode(lat, lng)
    const updatePayload: any = { latitude: lat, longitude: lng }
    if (autoPlaceName) {
      updatePayload.location = autoPlaceName
    }
    updateNodeMutation.mutate({ id: node.node_id, data: updatePayload })
  })
}

const disableDrag = (nodeId: string) => {
  const marker = markers[nodeId]
  if (!marker) return
  marker.dragging?.disable()
  marker.off('dragend')
}

watch(editMode, (on) => {
  nodes.value.filter((n: any) => n.latitude != null).forEach((n: any) => {
    if (on) enableDrag(n)
    else disableDrag(n.node_id)
  })
  if (!on) editingNode.value = null
})

const flyToNode = (node: any) => {
  activeNodeId.value = node.node_id
  if (node.latitude == null || node.longitude == null) return
  map?.flyTo([node.latitude, node.longitude], 19, { duration: 1.2 })
  setTimeout(() => markers[node.node_id]?.openPopup(), 1300)
}

const getRawSensorNum = (feed: any, nameQuery: string, sensors: any[]) => {
  const sensor = sensors.find(s => s.name.toLowerCase().includes(nameQuery.toLowerCase()))
  if (!sensor || !feed) return null
  const key = `${sensor.channel_id}_${sensor.thingspeak_field}`
  const val = feed[key]
  return val != null && val !== '' ? parseFloat(val).toFixed(1) : null
}

const getNodeMetrics = (nodeId: string) => {
  const feed = telemetryStore.telemetryHistory[nodeId]?.[0]
  const sensors = nodeSensorsMap.value[nodeId] || []
  if (!feed) return null
  const n = getRawSensorNum(feed, 'Nitrogen', sensors)
  const p = getRawSensorNum(feed, 'Phosphorus', sensors)
  const k = getRawSensorNum(feed, 'Potassium', sensors)
  const tempLuar = getRawSensorNum(feed, 'Air Temp', sensors) 
    || getRawSensorNum(feed, 'Suhu Udara', sensors)
    || getRawSensorNum(feed, 'Suhu Lingkungan', sensors)
    || getRawSensorNum(feed, 'Suhu Luar', sensors)
  const tempDalam = getRawSensorNum(feed, 'Enclosure Temp', sensors)
    || getRawSensorNum(feed, 'Suhu Kotak', sensors)
    || getRawSensorNum(feed, 'Suhu Box', sensors)
    || getRawSensorNum(feed, 'Suhu Panel', sensors)
    || getRawSensorNum(feed, 'Temperature', sensors)
    || getRawSensorNum(feed, 'Suhu', sensors)
  return { n, p, k, tempLuar, tempDalam }
}

const startEditCoords = (node: any) => {
  editingNode.value = node.node_id
  editLat.value = node.latitude != null ? String(node.latitude) : ''
  editLng.value = node.longitude != null ? String(node.longitude) : ''
}

const saveCoords = async (node: any) => {
  const lat = parseFloat(editLat.value)
  const lng = parseFloat(editLng.value)
  if (isNaN(lat) || isNaN(lng)) return

  const autoPlaceName = await reverseGeocode(lat, lng)
  const updatePayload: any = { latitude: lat, longitude: lng }
  if (autoPlaceName) {
    updatePayload.location = autoPlaceName
  }

  updateNodeMutation.mutate(
    { id: node.node_id, data: updatePayload },
    {
      onSuccess: () => {
        editingNode.value = null
        if (markers[node.node_id]) {
          markers[node.node_id].setLatLng([lat, lng])
        } else {
          addOrUpdateMarker({ ...node, latitude: lat, longitude: lng, ...(autoPlaceName ? { location: autoPlaceName } : {}) })
        }
        map?.flyTo([lat, lng], 19, { duration: 1.0 })
      },
    }
  )
}

onMounted(() => {
  // World bounds to prevent panning into grey empty areas
  const worldBounds = L.latLngBounds(L.latLng(-85.06, -180), L.latLng(85.06, 180))

  map = L.map(mapContainer.value!, { 
    zoomControl: false,
    minZoom: 3,
    maxZoom: 21,
    maxBounds: worldBounds,
    maxBoundsViscosity: 1.0, // 1.0 = hard boundary, map won't bounce outside valid world
  }).setView(ELINS_CENTER, 18)
  
  // Google Maps Hybrid (Satellite + Labels)
  L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
    attribution: '&copy; Google Maps', 
    minZoom: 3,
    maxZoom: 21,
    bounds: worldBounds,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
  }).addTo(map)

  // Zoom control positioned on topright to prevent overlap with node sidebar
  L.control.zoom({ position: 'topright' }).addTo(map)

  // Add scale control (metric only, wider)
  L.control.scale({ imperial: false, position: 'bottomleft', maxWidth: 250 }).addTo(map)

  nodes.value.forEach(async (n: any) => {
    addOrUpdateMarker(n)
    const sensors = await telemetryStore.fetchSensors(n.node_id)
    nodeSensorsMap.value[n.node_id] = sensors
    telemetryStore.fetchHistory(n.node_id)
  })
})

watch(nodes, (list) => {
  list.forEach(async (n: any) => {
    addOrUpdateMarker(n)
    if (!nodeSensorsMap.value[n.node_id]) {
      const sensors = await telemetryStore.fetchSensors(n.node_id)
      nodeSensorsMap.value[n.node_id] = sensors
    }
  })
})

onUnmounted(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <DashboardLayout noPadding>
    <div class="relative overflow-hidden w-full h-screen">
      <!-- Map -->
      <div ref="mapContainer" data-lenis-prevent class="absolute inset-0 z-0 w-full h-full" />

      <!-- Watermark -->
      <div class="absolute bottom-7 right-0 z-10 pointer-events-none opacity-50 bg-black/40 text-white px-4 py-1.5 rounded-l-lg backdrop-blur-sm border-y border-l border-white/10 font-medium text-[11px] tracking-wide">
        G-Connect Smart Farming
      </div>

      <!-- Floating Node Locations Sidebar -->
      <aside class="absolute top-3 left-3 right-3 sm:right-auto sm:top-5 sm:left-5 max-h-[45vh] md:max-h-[75vh] w-auto sm:w-[340px] z-10 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl rounded-2xl shadow-2xl border border-border/80 dark:border-slate-800 flex flex-col overflow-hidden transition-all duration-300">
        <!-- Header -->
        <div class="p-4 border-b border-slate-100 dark:border-slate-800">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2.5">
              <div class="shrink-0 flex items-center justify-center">
                <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <linearGradient id="mapPinRedGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stop-color="#f87171" />
                      <stop offset="50%" stop-color="#ef4444" />
                      <stop offset="100%" stop-color="#dc2626" />
                    </linearGradient>
                  </defs>
                  <path 
                    d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" 
                    fill="url(#mapPinRedGrad)" 
                    stroke="#991b1b" 
                    stroke-width="1.6" 
                    stroke-linecap="round" 
                    stroke-linejoin="round"
                  />
                  <circle 
                    cx="12" 
                    cy="9" 
                    r="2.5" 
                    fill="#ffffff" 
                    stroke="#991b1b" 
                    stroke-width="1.4" 
                  />
                </svg>
              </div>
              <h3 class="font-extrabold text-base text-foreground tracking-tight leading-none">Lokasi Node Lapangan</h3>
            </div>

            <span class="text-xs font-bold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 leading-none">
              {{ filteredNodes.length }} Node
            </span>
          </div>

          <!-- Mini Search Input -->
          <div class="mt-3 relative">
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="Cari node..." 
              class="w-full h-8 pl-8 pr-3 rounded-xl bg-slate-100 dark:bg-slate-800/90 border border-border/80 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary transition-all"
            />
            <Search class="w-3.5 h-3.5 text-muted-foreground absolute left-2.5 top-2.5" />
            <button 
              v-if="searchQuery" 
              @click="searchQuery = ''" 
              class="absolute right-2.5 top-2 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- Node List -->
        <div class="flex-1 overflow-y-auto p-3 space-y-2.5 max-h-[calc(45vh-130px)] md:max-h-[calc(75vh-160px)]">
          <div v-if="filteredNodes.length === 0" class="py-8 text-center text-xs text-muted-foreground">
            Tidak ada node ditemukan.
          </div>

          <div
            v-for="node in filteredNodes"
            :key="node.node_id"
            :class="[
              'rounded-xl border transition-all p-3 relative group/item',
              activeNodeId === node.node_id 
                ? 'border-primary/50 bg-primary/5 dark:bg-primary/10 shadow-xs' 
                : 'border-border/80 bg-slate-50/60 dark:bg-slate-900/40 hover:bg-slate-100/80 dark:hover:bg-slate-800/60'
            ]"
          >
            <!-- Left Active Highlight Indicator -->
            <div 
              v-if="activeNodeId === node.node_id" 
              class="absolute left-0 top-2 bottom-2 w-1 bg-primary rounded-r-full"
            ></div>

            <!-- Header Row: Online Dot + Name + ID Badge -->
            <div 
              class="flex items-center justify-between gap-2 pl-1 cursor-pointer"
              @click="flyToNode(node)"
            >
              <div class="flex items-center gap-2 min-w-0">
                <span class="relative flex h-2 w-2 shrink-0">
                  <span v-if="isNodeOnline(node)" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span :class="['relative inline-flex rounded-full h-2 w-2', isNodeOnline(node) ? 'bg-emerald-500' : 'bg-rose-500']"></span>
                </span>
                <span class="font-extrabold text-xs text-foreground group-hover/item:text-primary transition-colors truncate">
                  {{ node.name }}
                </span>
              </div>

              <div class="flex items-center gap-1 shrink-0">
                <Badge v-if="node.latitude == null" variant="outline" class="text-[9px] py-0 px-1.5 font-semibold text-amber-600 border-amber-500/30">
                  No GPS
                </Badge>
                <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-border/80">
                  {{ node.node_id }}
                </span>
              </div>
            </div>

            <!-- Quick Live Sensor Metric Strip with Unified Neutral Style -->
            <div 
              v-if="getNodeMetrics(node.node_id) && !editMode" 
              class="mt-2 pl-1 flex items-center gap-1.5 flex-wrap cursor-pointer"
              @click="flyToNode(node)"
            >
              <!-- NPK Pill (Neutral) -->
              <div 
                v-if="getNodeMetrics(node.node_id)?.n != null"
                class="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700 flex items-center gap-1 shadow-2xs"
                title="Nutrisi Tanah (Nitrogen / Phosphorus / Potassium)"
              >
                <span class="font-bold text-slate-900 dark:text-slate-100">NPK:</span>
                <span class="font-bold text-slate-800 dark:text-slate-200 font-mono">
                  {{ getNodeMetrics(node.node_id)?.n }}/{{ getNodeMetrics(node.node_id)?.p }}/{{ getNodeMetrics(node.node_id)?.k }}
                </span>
                <span class="text-[9px] text-slate-600 dark:text-slate-400 font-medium">mg/kg</span>
              </div>

              <!-- Suhu Lingkungan Pill (Neutral) -->
              <div 
                v-if="getNodeMetrics(node.node_id)?.tempLuar != null"
                class="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700 flex items-center gap-1 shadow-2xs"
                title="Suhu Lingkungan (Udara Luar)"
              >
                <span class="font-bold text-slate-900 dark:text-slate-100">Suhu Lingkungan:</span>
                <span class="font-bold text-slate-800 dark:text-slate-200 font-mono">{{ getNodeMetrics(node.node_id)?.tempLuar }}°C</span>
              </div>

              <!-- Suhu Dalam Panel Pill (Neutral) -->
              <div 
                v-if="getNodeMetrics(node.node_id)?.tempDalam != null"
                class="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700 flex items-center gap-1 shadow-2xs"
                title="Suhu Dalam Panel (Box Kontrol)"
              >
                <span class="font-bold text-slate-900 dark:text-slate-100">Suhu Dalam Panel:</span>
                <span class="font-bold text-slate-800 dark:text-slate-200 font-mono">{{ getNodeMetrics(node.node_id)?.tempDalam }}°C</span>
              </div>
            </div>

            <!-- Edit Coordinates Form or Coordinate Info -->
            <template v-if="editMode">
              <div v-if="editingNode === node.node_id" class="mt-2 space-y-2 pl-1">
                <div class="flex gap-1.5">
                  <Input v-model="editLat" placeholder="Latitude" class="h-7 text-xs bg-white dark:bg-slate-800 font-mono" />
                  <Input v-model="editLng" placeholder="Longitude" class="h-7 text-xs bg-white dark:bg-slate-800 font-mono" />
                </div>
                <div class="flex gap-1.5">
                  <Button size="sm" class="h-7 text-xs font-bold flex-1 bg-primary text-primary-foreground hover:bg-primary/90 cursor-pointer" @click="saveCoords(node)">
                    <Save class="w-3 h-3 mr-1" />Simpan
                  </Button>
                  <Button size="sm" variant="outline" class="h-7 w-7 p-0 cursor-pointer" @click="editingNode = null">
                    <X class="w-3 h-3" />
                  </Button>
                </div>
              </div>
              <div v-else class="mt-2 pl-1 flex items-center justify-between">
                <span class="text-[10px] font-mono text-muted-foreground flex-1 truncate">
                  📍 {{ node.latitude != null ? `${node.latitude.toFixed(5)}, ${node.longitude.toFixed(5)}` : 'Belum ada pin' }}
                </span>
                <Button size="sm" variant="outline" class="h-6 px-2 text-[10px] font-bold gap-1 cursor-pointer border-border/80" @click="startEditCoords(node)">
                  <Edit2 class="w-3 h-3" />
                  <span>Ubah</span>
                </Button>
              </div>
            </template>

            <!-- Normal Coordinates Row & Focus Action -->
            <div 
              v-else-if="node.latitude != null" 
              class="mt-2 pl-1 flex items-center justify-between text-[10px] text-muted-foreground font-mono cursor-pointer"
              @click="flyToNode(node)"
            >
              <span class="truncate">📍 {{ node.latitude.toFixed(5) }}, {{ node.longitude.toFixed(5) }}</span>
              <span class="text-[10px] text-primary font-bold group-hover/item:translate-x-0.5 transition-transform flex items-center gap-0.5 shrink-0 ml-2">
                Fokus <ChevronRight class="w-3 h-3" />
              </span>
            </div>
          </div>
        </div>

        <!-- Bottom Footer -->
        <div class="p-3 border-t border-border/80 dark:border-slate-800 flex flex-col gap-1.5 bg-slate-50/50 dark:bg-slate-900/50">
          <Button 
            class="w-full h-8 rounded-xl font-bold text-xs cursor-pointer shadow-2xs" 
            :variant="editMode ? 'default' : 'outline'" 
            size="sm" 
            @click="editMode = !editMode"
          >
            <Edit2 class="w-3.5 h-3.5 mr-1.5" />
            {{ editMode ? 'Selesai Edit' : 'Edit Posisi Pin' }}
          </Button>
          <p v-if="editMode" class="text-[10px] text-muted-foreground text-center font-medium">
            Geser pin di peta atau masukkan koordinat manual
          </p>
        </div>
      </aside>
    </div>
  </DashboardLayout>
</template>

<style scoped>
:deep(.leaflet-container) {
  width: 100%;
  height: 100%;
  font-family: inherit;
}

/* Modernize Zoom Control */
:deep(.leaflet-control-zoom) {
  border: 1px solid rgba(226, 232, 240, 0.9) !important;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  margin-top: 20px !important;
  margin-right: 20px !important;
  backdrop-filter: blur(8px) !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
}

:deep(.leaflet-control-zoom a) {
  background-color: rgba(255, 255, 255, 0.95) !important;
  color: #0f172a !important;
  width: 36px !important;
  height: 36px !important;
  min-width: 36px !important;
  min-height: 36px !important;
  max-width: 36px !important;
  max-height: 36px !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-align: center !important;
  text-indent: 0 !important;
  line-height: 1 !important;
  font-size: 19px !important;
  font-weight: 700 !important;
  text-decoration: none !important;
  transition: all 0.2s ease !important;
  border: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

:deep(.leaflet-control-zoom a:hover) {
  background-color: #f8fafc !important;
  color: #16a34a !important;
}

:deep(.leaflet-control-zoom a:first-child) {
  border-bottom: 1px solid rgba(226, 232, 240, 0.9) !important;
}

/* Modernize Scale Control */
:deep(.leaflet-control-scale) {
  margin-left: 24px !important;
  margin-bottom: 24px !important;
}

:deep(.leaflet-control-scale-line) {
  background: transparent !important;
  color: #000 !important;
  border: 3px solid #000 !important;
  border-top: none !important;
  border-radius: 0 !important;
  font-weight: 700 !important;
  font-size: 14px !important;
  padding: 4px 6px 2px !important;
  box-shadow: none !important;
  /* Add subtle white stroke to text/borders to ensure visibility on dark satellite areas */
  text-shadow: 1px 1px 2px rgba(255,255,255,0.9), -1px -1px 2px rgba(255,255,255,0.9), 1px -1px 2px rgba(255,255,255,0.9), -1px 1px 2px rgba(255,255,255,0.9) !important;
  filter: drop-shadow(0 0 2px rgba(255,255,255,0.8));
}
</style>

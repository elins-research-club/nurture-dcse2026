<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import L from 'leaflet'
import { useNodes } from '@/composables/useNodes'
import { useAuthStore } from '@/stores/auth'
import { useWebSocket } from '@/composables/useWebSocket'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { MapPin, Edit2, Save, X } from 'lucide-vue-next'

const API_BASE_URL = 'http://localhost:8000/api/v1'
const ELINS_CENTER: [number, number] = [-7.7679423, 110.3765989]

const router = useRouter()
const authStore = useAuthStore()
const { nodesQuery, updateNodeMutation } = useNodes()

const wsUrl = 'ws://localhost:8000/ws/dashboard'
const { lastMessage } = useWebSocket(wsUrl)

const nodes = computed(() => nodesQuery.data.value ?? [])

const mapContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
const markers: Record<string, L.Marker> = {}

const editMode = ref(false)
const editingNode = ref<string | null>(null)
const editLat = ref('')
const editLng = ref('')

const isNodeOnline = (node: any) => {
  if (!node.last_seen) return false
  return (Date.now() - new Date(node.last_seen).getTime()) < 15 * 60 * 1000
}

const makeIcon = (online: boolean) =>
  L.divIcon({
    html: `<div style="width:24px;height:32px">
      <svg width="24" height="32" viewBox="0 0 24 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 20 12 20s12-11 12-20C24 5.373 18.627 0 12 0z" fill="${online ? '#22c55e' : '#ef4444'}"/>
        <circle cx="12" cy="12" r="5" fill="white"/>
      </svg>
    </div>`,
    className: '',
    iconSize: [24, 32],
    iconAnchor: [12, 32],
    popupAnchor: [0, -34],
  })

const fetchNodeTelemetry = async (nodeId: string) => {
  try {
    const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/telemetry/history?results=1`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!res.ok) return null
    const data = await res.json()
    return data.feeds?.[0] ?? null
  } catch { return null }
}

const fetchNodeSensors = async (nodeId: string) => {
  try {
    const res = await fetch(`${API_BASE_URL}/nodes/${nodeId}/sensors/`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!res.ok) return []
    return await res.json()
  } catch { return [] }
}

const getSensorValue = (feed: any, nameQuery: string, sensors: any[]) => {
  const sensor = sensors.find(s => s.name.toLowerCase().includes(nameQuery.toLowerCase()))
  if (!sensor || !feed) return '&#8212;'
  const key = `${sensor.channel_id}_${sensor.thingspeak_field}`
  const val = feed[key]
  return val != null ? `${parseFloat(val).toFixed(1)} ${sensor.unit}` : '&#8212;'
}

const buildPopupHtml = (node: any, online: boolean, feed: any) => {
  const sensors = node.sensors ?? []
  const n = getSensorValue(feed, 'Nitrogen', sensors)
  const p = getSensorValue(feed, 'Phosphorus', sensors)
  const k = getSensorValue(feed, 'Potassium', sensors)
  return `<div style="min-width:200px;font-family:sans-serif;padding:4px">
    <div style="font-weight:700;font-size:14px;margin-bottom:6px">${node.name}</div>
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px">
      <span style="width:8px;height:8px;border-radius:50%;background:${online ? '#22c55e' : '#ef4444'};display:inline-block"></span>
      <span style="font-size:12px;color:${online ? '#16a34a' : '#dc2626'}">${online ? 'Online' : 'Offline'}</span>
    </div>
    <table style="width:100%;font-size:12px;border-collapse:collapse">
      <tr><td style="padding:3px 4px;color:#6b7280">N</td><td style="padding:3px 4px;font-weight:600">${n}</td></tr>
      <tr><td style="padding:3px 4px;color:#6b7280">P</td><td style="padding:3px 4px;font-weight:600">${p}</td></tr>
      <tr><td style="padding:3px 4px;color:#6b7280">K</td><td style="padding:3px 4px;font-weight:600">${k}</td></tr>
    </table>
    <div style="margin-top:10px">
      <a href="/nodes/${node.node_id}" style="display:block;padding:5px 8px;background:#2563eb;color:white;border-radius:6px;text-decoration:none;font-size:12px;text-align:center">View Detail &rarr;</a>
    </div>
  </div>`
}

const addOrUpdateMarker = async (node: any) => {
  if (node.latitude == null || node.longitude == null) return
  const online = isNodeOnline(node)
  const latLng: [number, number] = [node.latitude, node.longitude]
  if (markers[node.node_id]) {
    markers[node.node_id].setLatLng(latLng)
    markers[node.node_id].setIcon(makeIcon(online))
  } else {
    const marker = L.marker(latLng, { icon: makeIcon(online), draggable: false })
    marker.on('click', async () => {
      marker.getPopup()?.setContent('<div style="padding:10px;color:#888;font-size:12px">Loading...</div>')
      marker.openPopup()
      
      const fullNode = nodes.value.find((n: any) => n.node_id === node.node_id) || node
      
      const [feed, sensors] = await Promise.all([
        fetchNodeTelemetry(node.node_id),
        fullNode.sensors ? Promise.resolve(fullNode.sensors) : fetchNodeSensors(node.node_id)
      ])
      
      fullNode.sensors = sensors // Cache it so we don't fetch again next time
      
      marker.getPopup()?.setContent(buildPopupHtml(fullNode, online, feed))
    })
    marker.bindPopup('', { maxWidth: 260 })
    marker.addTo(map!)
    markers[node.node_id] = marker
  }
}

// WebSocket listener for realtime popup updates
watch(lastMessage, (msg) => {
  if (!msg || msg.event !== 'sensor_update') return
  
  const nodeId = msg.node_id
  const marker = markers[nodeId]
  
  // If we receive data, the node is definitely online
  if (marker) {
    marker.setIcon(makeIcon(true))
  }

  // Update popup HTML instantly if it's currently open
  if (marker && marker.isPopupOpen()) {
    const fullNode = nodes.value.find((n: any) => n.node_id === nodeId)
    if (fullNode) {
      marker.getPopup()?.setContent(buildPopupHtml(fullNode, true, msg.data))
    }
  }
})

const enableDrag = (node: any) => {
  const marker = markers[node.node_id]
  if (!marker) return
  marker.setDraggable(true)
  marker.on('dragend', () => {
    const pos = marker.getLatLng()
    updateNodeMutation.mutate({ id: node.node_id, data: { latitude: pos.lat, longitude: pos.lng } })
  })
}

const disableDrag = (nodeId: string) => {
  const marker = markers[nodeId]
  if (!marker) return
  marker.setDraggable(false)
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
  if (node.latitude == null || node.longitude == null) return
  map?.flyTo([node.latitude, node.longitude], 19, { duration: 1.2 })
  setTimeout(() => markers[node.node_id]?.openPopup(), 1300)
}

const startEditCoords = (node: any) => {
  editingNode.value = node.node_id
  editLat.value = node.latitude ?? ''
  editLng.value = node.longitude ?? ''
}

const saveCoords = (node: any) => {
  const lat = parseFloat(editLat.value)
  const lng = parseFloat(editLng.value)
  if (isNaN(lat) || isNaN(lng)) return
  updateNodeMutation.mutate(
    { id: node.node_id, data: { latitude: lat, longitude: lng } },
    {
      onSuccess: () => {
        editingNode.value = null
        if (markers[node.node_id]) {
          markers[node.node_id].setLatLng([lat, lng])
        } else {
          addOrUpdateMarker({ ...node, latitude: lat, longitude: lng })
        }
        map?.flyTo([lat, lng], 19, { duration: 1.0 })
      },
    }
  )
}

onMounted(() => {
  map = L.map(mapContainer.value!, { zoomControl: true }).setView(ELINS_CENTER, 18)
  
  // Google Maps Hybrid (Satellite + Labels)
  L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
    attribution: '&copy; Google Maps', 
    maxZoom: 21,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
  }).addTo(map)

  // Add scale control (metric only, wider)
  L.control.scale({ imperial: false, position: 'bottomleft', maxWidth: 250 }).addTo(map)

  nodes.value.forEach((n: any) => addOrUpdateMarker(n))
})

watch(nodes, (list) => {
  list.forEach((n: any) => addOrUpdateMarker(n))
})

onUnmounted(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <DashboardLayout noPadding>
    <div class="relative overflow-hidden w-full h-[calc(100vh-0px)]">
      <!-- Map -->
      <div ref="mapContainer" class="absolute inset-0 z-0" />

      <!-- Watermark -->
      <div class="absolute bottom-7 right-0 z-10 pointer-events-none opacity-50 bg-black/40 text-white px-4 py-1.5 rounded-l-lg backdrop-blur-sm border-y border-l border-white/10 font-medium text-[11px] tracking-wide">
        G-Connect Smart Farming
      </div>

      <!-- Sidebar -->
      <aside class="absolute top-4 left-4 max-h-[calc(100vh-32px)] md:max-h-[60vh] w-72 z-10 bg-card/95 backdrop-blur rounded-xl shadow-xl border border-border/50 flex flex-col overflow-hidden">
        <div class="p-4 border-b border-border/50">
          <h2 class="font-semibold text-base flex items-center gap-2">
            <MapPin class="w-4 h-4 text-primary" />
            Node Locations
          </h2>
          <p class="text-xs text-muted-foreground mt-0.5">Click to teleport to node</p>
        </div>

        <div class="flex-1 overflow-y-auto p-3 space-y-2">
          <div
            v-for="node in nodes"
            :key="node.node_id"
            class="rounded-lg border border-border/50 bg-background/80 p-3 space-y-2"
          >
            <div
              class="flex items-center gap-2"
              :class="node.latitude != null ? 'cursor-pointer hover:text-primary' : 'opacity-50'"
              @click="flyToNode(node)"
            >
              <div class="w-2 h-2 rounded-full flex-shrink-0" :class="isNodeOnline(node) ? 'bg-green-500' : 'bg-red-400'" />
              <span class="font-medium text-sm flex-1 truncate">{{ node.name }}</span>
              <Badge v-if="node.latitude == null" variant="outline" class="text-[10px] py-0">No pin</Badge>
            </div>

            <template v-if="editMode">
              <div v-if="editingNode === node.node_id" class="space-y-1.5">
                <div class="flex gap-1.5">
                  <Input v-model="editLat" placeholder="Latitude" class="h-7 text-xs bg-background" />
                  <Input v-model="editLng" placeholder="Longitude" class="h-7 text-xs bg-background" />
                </div>
                <div class="flex gap-1.5">
                  <Button size="sm" class="h-6 text-xs flex-1" @click="saveCoords(node)">
                    <Save class="w-3 h-3 mr-1" />Save
                  </Button>
                  <Button size="sm" variant="outline" class="h-6 w-6 p-0" @click="editingNode = null">
                    <X class="w-3 h-3" />
                  </Button>
                </div>
              </div>
              <div v-else class="flex items-center gap-1.5">
                <span class="text-[11px] text-muted-foreground flex-1">
                  {{ node.latitude != null ? `${node.latitude.toFixed(5)}, ${node.longitude.toFixed(5)}` : 'No coordinates' }}
                </span>
                <Button size="sm" variant="ghost" class="h-6 w-6 p-0" @click="startEditCoords(node)">
                  <Edit2 class="w-3 h-3" />
                </Button>
              </div>
            </template>
            <div v-else-if="node.latitude != null" class="text-[11px] text-muted-foreground">
              {{ node.latitude.toFixed(5) }}, {{ node.longitude.toFixed(5) }}
            </div>
          </div>
        </div>

        <div class="p-3 border-t border-border/50">
          <Button class="w-full" :variant="editMode ? 'default' : 'outline'" size="sm" @click="editMode = !editMode">
            <Edit2 class="w-3.5 h-3.5 mr-1.5" />
            {{ editMode ? 'Exit Edit Mode' : 'Edit Node Locations' }}
          </Button>
          <p v-if="editMode" class="text-[10px] text-muted-foreground text-center mt-1.5">
            Drag markers or input coordinates manually
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

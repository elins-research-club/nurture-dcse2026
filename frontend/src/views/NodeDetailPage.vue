<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import NodeDashboard from '@/components/dashboard/NodeDashboard.vue'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Trash2, Edit, MapPin, Navigation, Loader2, ChevronRight, Clock, LayoutDashboard, Sliders, Radio, ChevronDown, Key, Calendar, Activity, Layers, Plus } from 'lucide-vue-next'
import L from 'leaflet'
import { reverseGeocode } from '@/lib/geocoding'
import { useNodes } from '@/composables/useNodes'
import { useTelemetryStore } from '@/stores/telemetry'
import type { NodeDeviceWithData } from '@/types'

import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import AddChannelDialog from '@/components/dashboard/AddChannelDialog.vue'
import { useChannels } from '@/composables/useChannels'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const nodeId = route.params.id as string

const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()
const nodes = ref<NodeDeviceWithData[]>([])

const activeNode = computed(() => {
  return nodes.value.find(n => n.id === nodeId)
})

const nodeStringId = computed(() => activeNode.value?.node_id || '')

const { nodesQuery, updateNodeMutation, deleteNodeMutation } = useNodes()
const { channelsQuery, deleteChannelMutation } = useChannels(nodeStringId)

// Sensors mapping & live telemetry for 8-Field Accordion
const sensors = ref<any[]>([])

const isSensorModalOpen = ref(false)
const isSavingSensor = ref(false)
const editingSensor = ref({
  id: null as string | null,
  channelId: '',
  fieldNum: 1,
  name: '',
  unit: '',
  minThreshold: '' as string | number,
  maxThreshold: '' as string | number,
})

const openSensorModal = (channel: any, fieldNum: number) => {
  const existing = getFieldSensor(channel, fieldNum)
  editingSensor.value = {
    id: existing?.id || null,
    channelId: channel.id,
    fieldNum,
    name: existing?.name || '',
    unit: existing?.unit || '',
    minThreshold: existing?.min_threshold ?? '',
    maxThreshold: existing?.max_threshold ?? '',
  }
  isSensorModalOpen.value = true
}

const saveSensorMapping = async () => {
  if (!nodeStringId.value) return
  isSavingSensor.value = true
  try {
    const payload = {
      name: editingSensor.value.name.trim() || `Field ${editingSensor.value.fieldNum}`,
      unit: editingSensor.value.unit.trim(),
      thingspeak_field: `field${editingSensor.value.fieldNum}`,
      min_threshold: editingSensor.value.minThreshold === '' ? null : Number(editingSensor.value.minThreshold),
      max_threshold: editingSensor.value.maxThreshold === '' ? null : Number(editingSensor.value.maxThreshold),
    }

    if (editingSensor.value.id) {
      await fetch(`/api/v1/nodes/${nodeStringId.value}/sensors/${editingSensor.value.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
    } else {
      await fetch(`/api/v1/nodes/${nodeStringId.value}/sensors/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...payload,
          channel_id: editingSensor.value.channelId,
          type: 'general'
        })
      })
    }
    await loadSensors()
    telemetryStore.fetchSensors(nodeStringId.value)
    isSensorModalOpen.value = false
  } catch (e) {
    console.error(e)
  } finally {
    isSavingSensor.value = false
  }
}

const loadSensors = async () => {
  if (nodeStringId.value) {
    const data = await telemetryStore.fetchSensors(nodeStringId.value)
    if (data && data.length > 0) {
      sensors.value = data
    } else if (activeNode.value?.id) {
      const data2 = await telemetryStore.fetchSensors(activeNode.value.id)
      sensors.value = data2 || []
    }
  }
}

watch(nodeStringId, (id) => {
  if (id) loadSensors()
}, { immediate: true })

const getFieldSensor = (channel: any, fieldNum: number) => {
  if (!channel) return null
  const channelUuid = String(channel.id || '')
  const tsChannelId = String(channel.channel_id || '')
  const fieldKey = `field${fieldNum}`
  
  return sensors.value.find(s => {
    const sChan = String(s.channel_id || '')
    const sField = String(s.thingspeak_field || '').toLowerCase().trim()
    const matchesChannel = sChan === channelUuid || sChan === tsChannelId
    const matchesField = sField === fieldKey || sField === String(fieldNum) || sField === `field ${fieldNum}`
    return matchesChannel && matchesField
  })
}

const getFieldLiveValue = (channel: any, fieldNum: number) => {
  const feed = telemetryStore.telemetryHistory[nodeStringId.value]?.[0]
  if (!feed || !channel) return null
  const fieldKey = `field${fieldNum}`
  const key1 = `${channel.id}_${fieldKey}`
  const key2 = `${channel.channel_id}_${fieldKey}`
  const val = feed[key1] ?? feed[key2]
  return val != null && val !== '' ? (typeof val === 'number' ? val.toFixed(1) : val) : null
}

const maskApiKey = (key?: string) => {
  if (!key || key === 'N/A') return '••••••••'
  return key.length > 4 ? `••••••••${key.slice(-4)}` : '••••••••'
}

const expandedChannels = ref<(string | number)[]>([])

const toggleChannelExpand = (channelId: string | number) => {
  const index = expandedChannels.value.indexOf(channelId)
  if (index >= 0) {
    expandedChannels.value.splice(index, 1)
  } else {
    expandedChannels.value.push(channelId)
  }
}

watch(() => channelsQuery.data.value, (channels) => {
  if (channels?.length && expandedChannels.value.length === 0) {
    expandedChannels.value = channels.map((c: any) => c.id)
  }
}, { immediate: true })

watch(() => nodesQuery.data.value, (newData) => {
  if (newData) {
    nodes.value = [...newData]
  }
}, { immediate: true })

const goBack = () => {
  router.push('/nodes')
}

// Delete Node state
const isDeleteModalOpen = ref(false)
const confirmDeleteNode = async () => {
  if (!activeNode.value) return
  try {
    await deleteNodeMutation.mutateAsync(activeNode.value.node_id)
    isDeleteModalOpen.value = false
    router.push('/nodes')
  } catch (e) {
    alert('Failed to delete node.')
  }
}

// Edit state with Interactive Minimap & Auto-Geocoding
const isEditModalOpen = ref(false)
const editName = ref('')
const editLocation = ref('')
const editLat = ref<number | null>(null)
const editLng = ref<number | null>(null)
const isGeocoding = ref(false)

const editMapContainer = ref<HTMLElement | null>(null)
let editMap: L.Map | null = null
let editMarker: L.Marker | null = null

const DEFAULT_LAT_LNG: [number, number] = [-7.7679423, 110.3765989] // ELINS UGM

const updateLocationFromCoords = async (lat: number, lng: number) => {
  isGeocoding.value = true
  try {
    const placeName = await reverseGeocode(lat, lng)
    if (placeName) {
      editLocation.value = placeName
    }
  } finally {
    isGeocoding.value = false
  }
}

const initEditMinimap = () => {
  if (!editMapContainer.value) return
  if (editMap) {
    editMap.remove()
    editMap = null
    editMarker = null
  }

  const initialLat = editLat.value ?? DEFAULT_LAT_LNG[0]
  const initialLng = editLng.value ?? DEFAULT_LAT_LNG[1]
  const center: [number, number] = [initialLat, initialLng]

  editMap = L.map(editMapContainer.value, {
    zoomControl: true,
    attributionControl: false,
    minZoom: 3,
    maxZoom: 21,
  }).setView(center, 18)

  // Satellite Tile Layer
  L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
    maxZoom: 21,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
  }).addTo(editMap)

  // Custom Red Pin Icon
  const pinIcon = L.divIcon({
    html: `<div style="width:28px;height:36px;cursor:grab;filter:drop-shadow(0 4px 6px rgba(0,0,0,0.3))">
      <svg width="28" height="36" viewBox="0 0 24 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 0C5.373 0 0 5.373 0 12c0 9 12 20 12 20s12-11 12-20C24 5.373 18.627 0 12 0z" fill="#ef4444" stroke="#991b1b" stroke-width="1.6"/>
        <circle cx="12" cy="12" r="4.5" fill="white"/>
      </svg>
    </div>`,
    className: '',
    iconSize: [28, 36],
    iconAnchor: [14, 36],
  })

  editMarker = L.marker(center, {
    icon: pinIcon,
    draggable: true
  }).addTo(editMap)

  // Drag Pin -> update coords & auto-lookup
  editMarker.on('dragend', () => {
    const pos = editMarker!.getLatLng()
    editLat.value = Number(pos.lat.toFixed(6))
    editLng.value = Number(pos.lng.toFixed(6))
    updateLocationFromCoords(editLat.value, editLng.value)
  })

  // Click on map -> move pin & auto-lookup
  editMap.on('click', (e: L.LeafletMouseEvent) => {
    const pos = e.latlng
    editMarker?.setLatLng(pos)
    editLat.value = Number(pos.lat.toFixed(6))
    editLng.value = Number(pos.lng.toFixed(6))
    updateLocationFromCoords(editLat.value, editLng.value)
  })

  setTimeout(() => {
    editMap?.invalidateSize()
  }, 250)
}

const openEditModal = () => {
  if (!activeNode.value) return
  editName.value = activeNode.value.name
  editLocation.value = activeNode.value.location || ''
  editLat.value = activeNode.value.latitude ?? DEFAULT_LAT_LNG[0]
  editLng.value = activeNode.value.longitude ?? DEFAULT_LAT_LNG[1]
  isEditModalOpen.value = true

  setTimeout(() => {
    initEditMinimap()
  }, 180)
}

const saveEdit = async () => {
  if (!activeNode.value) return
  try {
    await updateNodeMutation.mutateAsync({
      id: activeNode.value.node_id,
      data: {
        name: editName.value,
        location: editLocation.value,
        latitude: editLat.value,
        longitude: editLng.value
      }
    })
    isEditModalOpen.value = false
  } catch (e) {
    alert('Failed to update node.')
  }
}

// Delete Channel state
const isDeleteChannelModalOpen = ref(false)
const channelToDelete = ref<string | null>(null)
const requestDeleteChannel = (id: string) => {
  channelToDelete.value = id
  isDeleteChannelModalOpen.value = true
}

const confirmDeleteChannel = async () => {
  if (!channelToDelete.value) return
  try {
    await deleteChannelMutation.mutateAsync(channelToDelete.value)
    isDeleteChannelModalOpen.value = false
    channelToDelete.value = null
  } catch (e) {
    alert('Failed to delete channel.')
  }
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6">
      
      <!-- Minimalist Linear / Vercel Developer Style Header -->
      <div v-if="activeNode" class="flex flex-col space-y-3">
        <!-- Top Breadcrumbs & Actions Row -->
        <div class="flex items-center justify-between gap-4 flex-wrap">
          <!-- Breadcrumb Path -->
          <nav class="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground font-medium">
            <button 
              @click="goBack" 
              class="hover:text-foreground transition-colors flex items-center gap-1 cursor-pointer font-semibold"
            >
              <span>Daftar Node</span>
            </button>
            <ChevronRight class="w-3.5 h-3.5 text-muted-foreground/60 shrink-0" />
            <span class="text-foreground font-bold truncate max-w-[200px] sm:max-w-none">
              {{ activeNode.name }}
            </span>
          </nav>

          <!-- Top Right Actions Group -->
          <div class="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              class="rounded-xl h-8.5 px-3 font-bold text-xs gap-1.5 border-border/80 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer shadow-2xs"
              @click="openEditModal"
            >
              <Edit class="w-3.5 h-3.5 text-muted-foreground" />
              <span>Edit</span>
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              class="rounded-xl h-8.5 px-3 font-bold text-xs gap-1.5 border-rose-200 dark:border-rose-900/50 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 cursor-pointer shadow-2xs"
              @click="isDeleteModalOpen = true"
            >
              <Trash2 class="w-3.5 h-3.5" />
              <span>Hapus</span>
            </Button>
          </div>
        </div>

        <!-- Main Title & Device Meta Info -->
        <div class="flex flex-col gap-2">
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            {{ activeNode.name }}
          </h1>

          <!-- Metadata Badges Strip -->
          <div class="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
            <!-- Node ID Chip -->
            <span class="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700">
              {{ activeNode.node_id }}
            </span>

            <!-- Radio Signal -->
            <span class="flex items-center gap-1 font-medium text-slate-600 dark:text-slate-400">
              <Radio class="w-3 h-3 text-primary/70" /> 2.4 GHz
            </span>

            <span class="text-slate-300 dark:text-slate-700">•</span>

            <!-- Location & GPS -->
            <div class="flex items-center gap-1.5 font-medium">
              <MapPin class="w-3.5 h-3.5 text-rose-500 shrink-0" />
              <span class="font-semibold text-foreground">{{ activeNode.location || 'Lokasi Belum Dikonfigurasi' }}</span>
              <span v-if="activeNode.latitude != null" class="font-mono text-[11px] text-muted-foreground">
                ({{ activeNode.latitude.toFixed(4) }}, {{ activeNode.longitude.toFixed(4) }})
              </span>
            </div>

            <!-- Last Seen Timestamp -->
            <template v-if="telemetryStore.getNodeLastSeen(activeNode.node_id, activeNode.last_seen)">
              <span class="text-slate-300 dark:text-slate-700 hidden sm:inline">•</span>
              <span class="hidden sm:flex items-center gap-1 text-[11px]">
                <Clock class="w-3 h-3 text-muted-foreground/80" />
                <span>Update: {{ new Date(telemetryStore.getNodeLastSeen(activeNode.node_id, activeNode.last_seen)!).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }}</span>
              </span>
            </template>
          </div>
        </div>
      </div>
      
      <!-- Edit Node Dialog with Interactive Minimap -->
      <Dialog v-model:open="isEditModalOpen">
        <DialogContent class="sm:max-w-xl max-h-[92vh] overflow-y-auto rounded-2xl">
          <DialogHeader>
            <DialogTitle class="text-xl font-bold text-foreground">Edit Node & Lokasi</DialogTitle>
            <DialogDescription>
              Ubah rincian informasi dan sesuaikan posisi pin koordinat untuk <strong class="font-mono text-foreground">{{ activeNode?.node_id }}</strong>
            </DialogDescription>
          </DialogHeader>

          <div class="space-y-4 py-2">
            <!-- Node Name -->
            <div class="space-y-1.5">
              <Label class="text-xs font-bold text-foreground">Nama Node</Label>
              <Input v-model="editName" placeholder="Contoh: IoT Lab ELINS" class="rounded-xl h-9" />
            </div>

            <!-- Minimap Satellite Picker -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <MapPin class="w-3.5 h-3.5 text-rose-500" />
                  <span>Pilih Posisi di Peta Satelit</span>
                </Label>
                <span class="text-[10px] text-muted-foreground font-medium">Klik peta atau geser pin</span>
              </div>

              <!-- Minimap Box Container -->
              <div class="w-full h-52 sm:h-60 rounded-2xl border border-slate-200 dark:border-slate-700 relative overflow-hidden shadow-inner bg-slate-900">
                <div ref="editMapContainer" class="w-full h-full z-0" />
                
                <!-- Floating Coordinates Chip -->
                <div class="absolute bottom-2.5 left-2.5 z-10 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md text-white font-mono text-[11px] font-semibold border border-white/20 shadow-sm flex items-center gap-1.5">
                  <Navigation class="w-3 h-3 text-emerald-400" />
                  <span>{{ editLat != null ? `${editLat.toFixed(5)}, ${editLng?.toFixed(5)}` : 'Geser pin di peta' }}</span>
                </div>
              </div>
            </div>

            <!-- Location Name Input with Auto-Geocoding Status -->
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <span>Nama Lokasi</span>
                  <span v-if="isGeocoding" class="inline-flex items-center gap-1 text-[10px] text-muted-foreground font-semibold animate-pulse">
                    <Loader2 class="w-3 h-3 animate-spin" /> Mengambil nama dari satelit...
                  </span>
                </Label>
                <button
                  type="button"
                  v-if="editLat != null && editLng != null"
                  @click="updateLocationFromCoords(editLat, editLng)"
                  class="text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors cursor-pointer hover:underline"
                >
                  Deteksi Ulang dari Peta
                </button>
              </div>

              <div class="relative">
                <Input 
                  v-model="editLocation" 
                  placeholder="Contoh: Student Internet Center FMIPA UGM" 
                  class="rounded-xl h-9 pl-8 text-xs sm:text-sm font-semibold"
                />
                <MapPin class="w-4 h-4 text-rose-500 absolute left-2.5 top-2.5" />
              </div>

              <p class="text-[10px] text-muted-foreground">
                Nama lokasi otomatis terisi saat pin digeser di peta, dan dapat Anda edit atau timpa secara manual jika nama satelit kurang pas.
              </p>
            </div>
          </div>

          <DialogFooter class="gap-2 sm:gap-0 pt-2 border-t border-border/80">
            <Button variant="outline" class="rounded-xl font-semibold text-xs cursor-pointer" @click="isEditModalOpen = false">Batal</Button>
            <Button 
              class="rounded-xl font-bold text-xs bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs cursor-pointer"
              @click="saveEdit" 
              :disabled="updateNodeMutation.isPending.value || isGeocoding"
            >
              <Loader2 v-if="updateNodeMutation.isPending.value" class="w-3.5 h-3.5 animate-spin mr-1.5" />
              {{ updateNodeMutation.isPending.value ? 'Menyimpan...' : 'Simpan Perubahan' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <!-- Delete Node Dialog -->
      <Dialog v-model:open="isDeleteModalOpen">
        <DialogContent class="sm:max-w-md p-6 aspect-[4/3] flex flex-col">
          <DialogHeader class="text-center sm:text-center">
            <DialogTitle class="text-destructive w-full">Delete Node</DialogTitle>
          </DialogHeader>
          <div class="flex-1 py-6 text-sm text-muted-foreground flex flex-col items-center justify-center gap-6">
            <div class="w-24 h-24 rounded-full bg-destructive/10 flex items-center justify-center shrink-0">
              <Trash2 class="w-12 h-12 text-destructive" />
            </div>
            <div class="text-center px-4">
              Are you sure you want to delete <strong class="text-foreground font-semibold">{{ activeNode?.name }}</strong>?<br><br>
              This action cannot be undone. All data will be lost.
            </div>
          </div>
          <DialogFooter class="gap-2 sm:gap-0 mt-0 mt-auto">
            <Button variant="outline" @click="isDeleteModalOpen = false" class="w-full sm:w-auto">Cancel</Button>
            <Button variant="destructive" @click="confirmDeleteNode" :disabled="deleteNodeMutation.isPending.value" class="w-full sm:w-auto">
              {{ deleteNodeMutation.isPending.value ? 'Deleting...' : 'Delete Node' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <!-- Delete Channel Dialog -->
      <Dialog v-model:open="isDeleteChannelModalOpen">
        <DialogContent class="sm:max-w-md p-6 aspect-[4/3] flex flex-col">
          <DialogHeader class="text-center sm:text-center">
            <DialogTitle class="text-destructive w-full">Remove Channel</DialogTitle>
          </DialogHeader>
          <div class="flex-1 py-6 text-sm text-muted-foreground flex flex-col items-center justify-center gap-6">
            <div class="w-24 h-24 rounded-full bg-destructive/10 flex items-center justify-center shrink-0">
              <Trash2 class="w-12 h-12 text-destructive" />
            </div>
            <div class="text-center px-4">
              Stop fetching data from this channel?<br><br>
              You can always re-add it later.
            </div>
          </div>
          <DialogFooter class="gap-2 sm:gap-0 mt-0 mt-auto">
            <Button variant="outline" @click="isDeleteChannelModalOpen = false" class="w-full sm:w-auto">Cancel</Button>
            <Button variant="destructive" @click="confirmDeleteChannel" :disabled="deleteChannelMutation.isPending.value" class="w-full sm:w-auto">
              {{ deleteChannelMutation.isPending.value ? 'Removing...' : 'Remove Channel' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <!-- Edit Sensor / Field Mapping Dialog -->
      <Dialog v-model:open="isSensorModalOpen">
        <DialogContent class="sm:max-w-md p-6 rounded-2xl">
          <DialogHeader>
            <DialogTitle class="flex items-center gap-2 text-base sm:text-lg font-extrabold text-foreground">
              <Sliders class="w-5 h-5 text-primary" />
              <span>Pemetaan Sensor — Field {{ editingSensor.fieldNum }}</span>
            </DialogTitle>
            <DialogDescription class="text-xs text-muted-foreground">
              Sesuaikan nama parameter sensor, satuan, dan ambang batas yang dikirimkan hardware pada field ini.
            </DialogDescription>
          </DialogHeader>

          <div class="space-y-3.5 py-3">
            <div class="space-y-1.5">
              <Label class="text-xs font-bold text-foreground">Nama Sensor / Parameter</Label>
              <Input 
                v-model="editingSensor.name" 
                placeholder="Contoh: Nitrogen, Oksigen, Suhu Tanah" 
                class="rounded-xl h-9 text-xs sm:text-sm font-semibold"
              />
            </div>

            <div class="space-y-1.5">
              <Label class="text-xs font-bold text-foreground">Satuan Nilai</Label>
              <Input 
                v-model="editingSensor.unit" 
                placeholder="Contoh: mg/kg, ppm, %, °C" 
                class="rounded-xl h-9 text-xs sm:text-sm font-mono"
              />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1.5">
                <Label class="text-xs font-bold text-foreground">Batas Minimum (Opsional)</Label>
                <Input 
                  type="number"
                  step="any"
                  v-model="editingSensor.minThreshold" 
                  placeholder="Tanpa Batas" 
                  class="rounded-xl h-9 text-xs sm:text-sm"
                />
              </div>

              <div class="space-y-1.5">
                <Label class="text-xs font-bold text-foreground">Batas Maksimum (Opsional)</Label>
                <Input 
                  type="number"
                  step="any"
                  v-model="editingSensor.maxThreshold" 
                  placeholder="Tanpa Batas" 
                  class="rounded-xl h-9 text-xs sm:text-sm"
                />
              </div>
            </div>
          </div>

          <DialogFooter class="gap-2 sm:gap-0 pt-2 border-t border-border/80">
            <Button variant="outline" class="rounded-xl font-semibold text-xs cursor-pointer" @click="isSensorModalOpen = false">Batal</Button>
            <Button 
              class="rounded-xl font-bold text-xs bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs cursor-pointer"
              @click="saveSensorMapping" 
              :disabled="isSavingSensor"
            >
              <Loader2 v-if="isSavingSensor" class="w-3.5 h-3.5 animate-spin mr-1.5" />
              {{ isSavingSensor ? 'Menyimpan...' : 'Simpan Pemetaan' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <div v-if="!activeNode && !nodesQuery.isLoading.value" class="py-12 text-center text-destructive">
        Node not found.
      </div>
      
      <!-- Linear / Underline Tabs Navigation -->
      <Tabs defaultValue="dashboard" class="w-full" v-if="activeNode">
        <TabsList class="flex w-full justify-start gap-8 !border-0 !border-b !border-border/80 !bg-transparent !p-0 !rounded-none !shadow-none !overflow-visible h-auto mb-6">
          <TabsTrigger 
            value="dashboard" 
            class="relative pb-3 pt-1 px-3 sm:px-4 !rounded-none !bg-transparent !shadow-none !ring-0 border-0 border-b-2 border-transparent data-[state=active]:!border-primary data-[state=active]:!text-primary data-[state=active]:!bg-transparent data-[state=active]:!shadow-none font-bold text-xs sm:text-sm text-muted-foreground hover:text-foreground transition-all flex items-center justify-center gap-2 cursor-pointer -mb-px"
          >
            <LayoutDashboard class="w-4 h-4" />
            <span>Dashboard Telemetri</span>
          </TabsTrigger>
          <TabsTrigger 
            value="configuration" 
            class="relative pb-3 pt-1 px-3 sm:px-4 !rounded-none !bg-transparent !shadow-none !ring-0 border-0 border-b-2 border-transparent data-[state=active]:!border-primary data-[state=active]:!text-primary data-[state=active]:!bg-transparent data-[state=active]:!shadow-none font-bold text-xs sm:text-sm text-muted-foreground hover:text-foreground transition-all flex items-center justify-center gap-2 cursor-pointer -mb-px"
          >
            <Sliders class="w-4 h-4" />
            <span>Konfigurasi Channel</span>
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="dashboard" class="space-y-6 mt-0">
          <NodeDashboard :node-id="nodeStringId" />
        </TabsContent>

        <TabsContent value="configuration" class="space-y-6 mt-0">
          <!-- Single Unified Card Wrapper -->
          <div class="rounded-2xl border border-border/80 bg-white dark:bg-card shadow-xs overflow-hidden">
            
            <!-- Unified Header Row -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5">
              <div>
                <!-- flex-wrap + whitespace-nowrap: di layar sempit judul dan pil
                     berebut satu baris, dan pilnya yang kalah -- teksnya terlipat
                     jadi "2 Channel / Terhubung". Sekarang pilnya utuh dan turun
                     ke baris bawah kalau memang tidak muat. -->
                <h3 class="text-base sm:text-lg font-bold text-foreground flex flex-wrap items-center gap-2.5">
                  <span>ThingSpeak Cloud Channels</span>
                  <span class="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold border border-slate-200/80 dark:border-slate-700 whitespace-nowrap shrink-0">
                    {{ channelsQuery.data.value?.length || 0 }} Channel Terhubung
                  </span>
                </h3>
              </div>

              <AddChannelDialog :nodeId="nodeStringId">
                <template #trigger>
                  <Button class="rounded-xl font-bold text-xs gap-1.5 shadow-xs shrink-0 cursor-pointer">
                    <Plus class="w-4 h-4" />
                    <span>Tambah Channel</span>
                  </Button>
                </template>
              </AddChannelDialog>
            </div>
            
            <!-- Loading State -->
            <div v-if="channelsQuery.isLoading.value" class="py-12 text-center text-muted-foreground border-t border-border/80">
              <Loader2 class="w-6 h-6 animate-spin mx-auto mb-2 text-primary" />
              <p class="text-xs font-semibold">Memuat data kanal...</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="!channelsQuery.data.value?.length" class="py-16 text-center text-muted-foreground border-t border-border/80 space-y-3">
              <div class="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center mx-auto text-slate-400">
                <Layers class="w-6 h-6" />
              </div>
              <div class="space-y-1">
                <h4 class="font-bold text-foreground text-sm">Belum Ada Channel Terhubung</h4>
                <p class="text-xs max-w-sm mx-auto">Tambahkan channel ThingSpeak untuk menghubungkan sensor dan memulai pembacaan data telemetri.</p>
              </div>
              <AddChannelDialog :nodeId="nodeStringId">
                <template #trigger>
                  <Button size="sm" class="rounded-xl text-xs font-bold gap-1.5 mt-2 cursor-pointer">
                    <Plus class="w-3.5 h-3.5" />
                    <span>Tambah Channel Pertama</span>
                  </Button>
                </template>
              </AddChannelDialog>
            </div>

            <!-- Channels Accordion List Inside Single Wrapper (Divided by subtle borders) -->
            <div v-else class="divide-y divide-border/80 border-t border-border/80">
              <div 
                v-for="channel in channelsQuery.data.value" 
                :key="channel.id" 
                class="transition-all duration-200 group"
              >
                <!-- Clickable Accordion Header -->
                <div 
                  @click="toggleChannelExpand(channel.id)" 
                  class="p-4 sm:p-5 flex items-center justify-between gap-4 cursor-pointer hover:bg-slate-50/80 dark:hover:bg-slate-900/40 transition-colors select-none"
                >
                  <div class="flex items-center gap-3.5 min-w-0">
                    <!-- Expand Chevron -->
                    <button 
                      type="button" 
                      class="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 flex items-center justify-center shrink-0 transition-transform duration-200 group-hover:bg-slate-200 dark:group-hover:bg-slate-700"
                      :class="expandedChannels.includes(channel.id) ? 'rotate-180 text-primary' : ''"
                    >
                      <ChevronDown class="w-4 h-4" />
                    </button>

                    <!-- Channel Title & Metadata -->
                    <div class="min-w-0">
                      <div class="flex items-center gap-2.5 flex-wrap">
                        <h4 class="font-bold text-sm sm:text-base text-foreground leading-tight truncate">
                          {{ channel.label || `Channel ${channel.channel_id}` }}
                        </h4>
                        <!-- ThingSpeak Channel ID Badge -->
                        <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700">
                          ID: {{ channel.channel_id }}
                        </span>
                        <!-- Status Badge -->
                        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Polling Aktif
                        </span>
                      </div>

                      <div class="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground flex-wrap">
                        <span class="flex items-center gap-1 font-mono text-[11px]">
                          <Key class="w-3 h-3 text-slate-400" /> Read Key: <span class="font-semibold text-foreground">{{ maskApiKey(channel.read_api_key) }}</span>
                        </span>
                        <span class="text-slate-300 dark:text-slate-700">•</span>
                        <span class="flex items-center gap-1 text-[11px]">
                          <Calendar class="w-3 h-3 text-slate-400" /> Ditambahkan {{ new Date(channel.created_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }) }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <!-- Actions Right (Delete Button) -->
                  <div class="flex items-center gap-2 shrink-0">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      class="h-8.5 px-3 rounded-xl text-xs font-bold text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-900/50 hover:bg-rose-50 dark:hover:bg-rose-950/40 cursor-pointer shadow-2xs gap-1.5" 
                      @click.stop="requestDeleteChannel(channel.id)"
                      title="Hapus Kanal"
                    >
                      <Trash2 class="w-3.5 h-3.5" />
                      <span class="hidden sm:inline">Hapus</span>
                    </Button>
                  </div>
                </div>

                <!-- Dropdown Accordion Panel: 8-Field Mapping Details -->
                <div 
                  v-show="expandedChannels.includes(channel.id)" 
                  class="px-5 pb-5 pt-3 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30 space-y-3 transition-all"
                >
                  <div class="flex items-center justify-between">
                    <span class="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                      Pemetaan Field Sensor
                    </span>
                    <span class="text-[10px] text-muted-foreground font-mono">Field 1–8</span>
                  </div>

                  <!-- 8 Fields Grid -->
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div 
                      v-for="fieldNum in 8" 
                      :key="fieldNum"
                      class="p-2.5 rounded-xl border bg-white dark:bg-card transition-all cursor-pointer hover:border-primary/60 hover:shadow-xs group/field relative select-none"
                      :class="getFieldSensor(channel, fieldNum) ? 'border-slate-200 dark:border-slate-700 shadow-2xs' : 'border-dashed border-slate-200/80 dark:border-slate-800 opacity-70 hover:opacity-100 hover:border-solid'"
                      @click="openSensorModal(channel, fieldNum)"
                      title="Klik untuk ubah nama atau batas sensor field ini"
                    >
                      <div class="flex items-center justify-between gap-1 mb-1">
                        <span class="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 group-hover/field:bg-primary/10 group-hover/field:text-primary transition-colors">
                          Field {{ fieldNum }}
                        </span>
                        <div class="flex items-center gap-1">
                          <span v-if="getFieldSensor(channel, fieldNum)" class="w-1.5 h-1.5 rounded-full bg-emerald-500" title="Sensor Terhubung"></span>
                          <span v-else class="text-[9px] text-muted-foreground font-semibold">+ Petakan</span>
                        </div>
                      </div>

                      <div v-if="getFieldSensor(channel, fieldNum)">
                        <div class="font-bold text-xs text-foreground line-clamp-2 leading-tight group-hover/field:text-primary transition-colors" :title="getFieldSensor(channel, fieldNum)?.name">
                          {{ getFieldSensor(channel, fieldNum)?.name }}
                        </div>
                        <div class="text-[10px] text-muted-foreground mt-0.5 flex items-center justify-between font-mono">
                          <span>{{ getFieldSensor(channel, fieldNum)?.unit || '—' }}</span>
                          <span v-if="getFieldLiveValue(channel, fieldNum) != null" class="font-bold text-emerald-600 dark:text-emerald-400">
                            {{ getFieldLiveValue(channel, fieldNum) }}
                          </span>
                        </div>
                      </div>

                      <div v-else class="text-xs text-muted-foreground/60 italic py-1 text-center group-hover/field:text-primary transition-colors">
                        + Petakan Sensor
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>

          </div>
        </TabsContent>
      </Tabs>
    </div>
  </DashboardLayout>
</template>

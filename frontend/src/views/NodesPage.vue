<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import AddNodeDialog from '@/components/dashboard/AddNodeDialog.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import { Card, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useNodes } from '@/composables/useNodes'
import { useTelemetryStore } from '@/stores/telemetry'
import type { NodeDeviceWithData } from '@/types'
import { Cpu, Radio, MapPin, Clock, ArrowRight, Plus, RefreshCw, AlertTriangle, Layers } from 'lucide-vue-next'

const router = useRouter()
const { nodesQuery } = useNodes()
const telemetryStore = useTelemetryStore()

const nodesList = ref<NodeDeviceWithData[]>([])
const nodeSensorsMap = ref<Record<string, any[]>>({})

watch(() => nodesQuery.data.value, (newData) => {
  if (newData) {
    nodesList.value = [...newData]
    newData.forEach(async (node) => {
      if (!nodeSensorsMap.value[node.node_id]) {
        const sensors = await telemetryStore.fetchSensors(node.node_id)
        nodeSensorsMap.value[node.node_id] = sensors
      }
      telemetryStore.fetchHistory(node.node_id)
    })
  }
}, { immediate: true })

const getRawSensorNum = (feed: any, nameQuery: string, sensors: any[]) => {
  const sensor = sensors?.find(s => s.name.toLowerCase().includes(nameQuery.toLowerCase()))
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

const goToNodeDetail = (id: number) => {
  router.push(`/nodes/${id}`)
}

const goToMapWithNode = (event: Event) => {
  event.stopPropagation()
  router.push('/map')
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6">
      
      <!-- Page Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-2.5">
            <span>Daftar Node Lapangan</span>
          </h2>
        </div>
        
        <div class="flex items-center gap-2.5">
          <AddNodeDialog>
            <template #trigger>
              <Button size="sm" class="h-9 px-4 rounded-xl font-bold text-xs gap-1.5 shadow-2xs cursor-pointer">
                <Plus class="w-4 h-4" />
                <span>Tambah Node Baru</span>
              </Button>
            </template>
          </AddNodeDialog>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="nodesQuery.isLoading.value" class="py-20 text-center text-muted-foreground">
        <div class="flex items-center justify-center gap-2.5 animate-pulse">
          <RefreshCw class="animate-spin h-6 w-6 text-primary" />
          <span class="text-sm font-semibold">Memuat daftar node...</span>
        </div>
      </div>
      
      <!-- Error State -->
      <div v-else-if="nodesQuery.isError.value" class="py-16 text-center text-destructive border border-rose-200 bg-rose-50/50 rounded-2xl">
        <AlertTriangle class="w-10 h-10 mx-auto mb-2 text-rose-500 animate-bounce" />
        <p class="font-bold text-base">Gagal memuat data node</p>
        <p class="text-xs sm:text-sm text-muted-foreground mt-1">Periksa koneksi server atau hubungi administrator sistem.</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="nodesList.length === 0" class="py-20 text-center border border-dashed border-border/80 rounded-2xl bg-card/40">
        <div class="mx-auto flex max-w-[420px] flex-col items-center justify-center text-center">
          <div class="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-4 shadow-2xs">
            <Layers class="w-7 h-7" />
          </div>
          <h3 class="text-lg font-bold text-foreground">Belum Ada Node Terdaftar</h3>
          <p class="mb-5 mt-1 text-xs sm:text-sm text-muted-foreground">
            Sistem belum mendeteksi perangkat IoT. Tambahkan stasiun node baru untuk memulai pemantauan telemetri kebun.
          </p>
          <AddNodeDialog>
            <template #trigger>
              <Button class="rounded-xl font-bold text-xs gap-1.5 shadow-2xs">
                <Plus class="w-4 h-4" />
                <span>Tambah Node Pertama</span>
              </Button>
            </template>
          </AddNodeDialog>
        </div>
      </div>
      
      <!-- Node Bento Cards Grid View -->
      <div v-else class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Card 
          v-for="(node, idx) in nodesList" 
          :key="node.id" 
          class="animate-stagger-card rounded-2xl border border-border/80 bg-white dark:bg-card shadow-xs hover:shadow-xl hover:border-primary/40 hover:-translate-y-1.5 transition-all duration-300 cursor-pointer overflow-hidden flex flex-col justify-between group active:scale-[0.99]"
          :style="{ animationDelay: `${idx * 75}ms` }"
          @click="goToNodeDetail(node.id)"
        >
          <div class="p-5 flex flex-col gap-4">
            
            <!-- Header Row: Name & ID + Status Badge -->
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <CardTitle class="text-base sm:text-lg font-bold text-foreground group-hover:text-primary transition-colors leading-tight truncate">
                  {{ node.name }}
                </CardTitle>
                
                <div class="flex items-center gap-2 mt-1.5 flex-wrap">
                  <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700">
                    {{ node.node_id }}
                  </span>
                  <span class="text-[11px] text-muted-foreground flex items-center gap-1 font-medium">
                    <Radio class="w-3 h-3 text-primary/70" /> 2.4 GHz
                  </span>
                </div>
              </div>

              <!-- Online / Offline Badge -->
              <div class="shrink-0">
                <StatusBadge 
                  :is-active="telemetryStore.isNodeOnline(node.node_id, node.last_seen)" 
                  :last-seen="telemetryStore.getNodeLastSeen(node.node_id, node.last_seen)" 
                />
              </div>
            </div>

            <!-- Unified Location & Live Sensor Metrics Card Wrapper -->
            <div class="rounded-xl bg-slate-50/80 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 p-3 space-y-2.5">
              <!-- Location & GPS Top Row -->
              <div class="flex items-center justify-between gap-2 pb-2 border-b border-slate-200/60 dark:border-slate-800/80 text-xs">
                <div class="flex items-center gap-1.5 min-w-0">
                  <MapPin class="w-3.5 h-3.5 text-rose-500 shrink-0" />
                  <span class="font-bold text-foreground truncate">{{ node.location || 'Lokasi Belum Dikonfigurasi' }}</span>
                </div>
                <span v-if="node.latitude != null" class="text-[10px] font-mono text-muted-foreground shrink-0 font-medium">
                  {{ node.latitude.toFixed(4) }}, {{ node.longitude.toFixed(4) }}
                </span>
              </div>

              <!-- Live Sensor Metrics 3-Column Strip -->
              <!-- grid-rows-subgrid: tiap kolom "mewarisi" 3 baris grid induk (label/nilai/satuan)
                   sehingga tinggi tiap baris otomatis mengikuti sel tertinggi di baris itu --
                   solusi pasti sejajar, tidak bergantung tebakan tinggi piksel label. -->
              <div class="grid grid-cols-3 grid-rows-[auto_auto_auto] gap-1 text-center divide-x divide-slate-200/60 dark:divide-slate-800/80">
                <!-- Metric 1: NPK -->
                <div class="px-1 grid row-span-3 grid-rows-subgrid">
                  <div class="text-[10px] leading-tight font-bold text-muted-foreground flex items-center justify-center gap-1">
                    <span>🌿</span> NPK
                  </div>
                  <div class="text-xs font-extrabold text-foreground mt-0.5 font-mono self-start">
                    <template v-if="getNodeMetrics(node.node_id)?.n != null">
                      {{ getNodeMetrics(node.node_id)?.n }}/{{ getNodeMetrics(node.node_id)?.p }}/{{ getNodeMetrics(node.node_id)?.k }}
                    </template>
                    <template v-else>—</template>
                  </div>
                  <div class="text-[9px] text-muted-foreground mt-0.5 font-medium self-start">mg/kg</div>
                </div>

                <!-- Metric 2: Suhu Lingkungan -->
                <div class="px-1 grid row-span-3 grid-rows-subgrid">
                  <div class="text-[10px] leading-tight font-bold text-muted-foreground flex items-center justify-center gap-1" title="Suhu Lingkungan (Udara Luar)">
                    <span>🌡️</span> Suhu Lingkungan
                  </div>
                  <div class="text-xs font-extrabold text-foreground mt-0.5 font-mono self-start">
                    {{ getNodeMetrics(node.node_id)?.tempLuar != null ? getNodeMetrics(node.node_id)?.tempLuar : '—' }}
                  </div>
                  <div class="text-[9px] text-muted-foreground mt-0.5 font-medium self-start">°C</div>
                </div>

                <!-- Metric 3: Suhu Dalam Panel -->
                <div class="px-1 grid row-span-3 grid-rows-subgrid">
                  <div class="text-[10px] leading-tight font-bold text-muted-foreground flex items-center justify-center gap-1" title="Suhu Dalam Panel (Box Kontrol)">
                    <span>🎛️</span> Suhu Dalam Panel
                  </div>
                  <div class="text-xs font-extrabold text-foreground mt-0.5 font-mono self-start">
                    {{ getNodeMetrics(node.node_id)?.tempDalam != null ? getNodeMetrics(node.node_id)?.tempDalam : '—' }}
                  </div>
                  <div class="text-[9px] text-muted-foreground mt-0.5 font-medium self-start">°C</div>
                </div>
              </div>
            </div>

          </div>

          <!-- Card Footer: Last Seen Clock + Interactive Action Buttons -->
          <div class="px-5 py-3.5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between gap-2 text-xs">
            <div class="flex items-center gap-1.5 text-muted-foreground text-[11px] truncate" title="Waktu pembaruan data terakhir">
              <Clock class="w-3.5 h-3.5 shrink-0" />
              <span>Update: {{ telemetryStore.getNodeLastSeen(node.node_id, node.last_seen) ? new Date(telemetryStore.getNodeLastSeen(node.node_id, node.last_seen)!).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'Belum ada data' }}</span>
            </div>

            <div class="flex items-center gap-1.5 shrink-0">
              <Button 
                variant="outline" 
                size="sm" 
                class="h-7 px-2.5 rounded-lg text-xs font-bold gap-1 border-border/80 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer shadow-none"
                @click="goToMapWithNode($event)"
                title="Lihat posisi node di peta satelit"
              >
                <MapPin class="w-3 h-3 text-rose-500" />
                <span>Peta</span>
              </Button>
              
              <Button 
                size="sm" 
                class="h-7 px-3 rounded-lg text-xs font-bold gap-1 bg-primary text-primary-foreground hover:bg-primary/90 shadow-2xs cursor-pointer group-hover:translate-x-0.5 transition-transform"
              >
                <span>Pantau</span>
                <ArrowRight class="w-3 h-3" />
              </Button>
            </div>
          </div>

        </Card>
      </div>

    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import ExcelIcon from '@/components/icons/ExcelIcon.vue'
import { 
  Download, Loader2, Calendar, 
  Layers, CheckCircle2, Sliders, Clock
} from 'lucide-vue-next'
import { exportTelemetryToCSV } from '@/lib/csvExporter'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  open: boolean
  nodeId: string
  nodeName: string
  sensors: any[]
  currentFeeds?: any[]
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
}>()

const authStore = useAuthStore()

// State
const selectedPreset = ref<'1d' | '1w' | '1M' | 'custom'>('1w')
const customStart = ref('')
const customEnd = ref('')
const selectedAggregation = ref<'raw' | '5' | '15' | '60' | '1440'>('raw')
const selectedDomain = ref<'all' | 'npk' | 'soil' | 'iot'>('all')
const isExporting = ref(false)
const exportSuccess = ref(false)
const exportedCount = ref(0)
const errorMessage = ref('')

// Presets
const presets = [
  { id: '1d', label: '24 Jam Terakhir' },
  { id: '1w', label: '7 Hari Terakhir' },
  { id: '1M', label: '30 Hari Terakhir' },
  { id: 'custom', label: 'Rentang Kustom' }
]

// Aggregation Options
const aggregations = [
  { id: 'raw', label: 'Data Mentah (Semua Titik)', desc: 'Setiap transmisi data asli' },
  { id: '5', label: 'Rata-rata 5 Menit', desc: 'Agregasi interval 5 menit' },
  { id: '15', label: 'Rata-rata 15 Menit', desc: 'Agregasi interval 15 menit' },
  { id: '60', label: 'Rata-rata 1 Jam', desc: 'Agregasi interval 60 menit' },
  { id: '1440', label: 'Rata-rata Harian', desc: '1 titik ringkasan per hari' }
]

// Domain Options
const domains = [
  { id: 'all', label: 'Semua Sensor' },
  { id: 'npk', label: 'NPK (N, P, K)' },
  { id: 'soil', label: 'Kondisi Tanah (Moisture, pH, Temp, EC)' },
  { id: 'iot', label: 'Kondisi IoT & Panel' }
]

// Filter active sensors by chosen domain
const filteredSensors = computed(() => {
  if (!props.sensors || props.sensors.length === 0) return []
  if (selectedDomain.value === 'all') return props.sensors

  return props.sensors.filter(s => {
    const name = (s.name || '').toLowerCase()
    if (selectedDomain.value === 'npk') {
      return name.includes('nitrogen') || name.includes('phosphor') || name.includes('kalium') || name.includes('npk') || name.includes('potassium')
    }
    if (selectedDomain.value === 'soil') {
      return name.includes('kelembaban') || name.includes('moisture') || name.includes('ph') || name.includes('ec') || name.includes('suhu tanah') || name.includes('soil')
    }
    if (selectedDomain.value === 'iot') {
      return name.includes('panel') || name.includes('box') || name.includes('enclosure') || name.includes('udara') || name.includes('baterai') || name.includes('rssi') || name.includes('suhu lingkungan')
    }
    return true
  })
})

const handleExport = async () => {
  if (isExporting.value) return
  isExporting.value = true
  errorMessage.value = ''
  exportSuccess.value = false

  try {
    const params = new URLSearchParams()
    
    if (selectedPreset.value !== 'custom') {
      params.set('range', selectedPreset.value)
    } else {
      if (customStart.value) params.set('start', new Date(customStart.value).toISOString())
      if (customEnd.value) params.set('end', new Date(customEnd.value).toISOString())
    }

    if (selectedAggregation.value !== 'raw') {
      params.set('average', selectedAggregation.value)
    }

    // Up to 8000 points
    params.set('results', '8000')

    const response = await fetch(`/api/v1/nodes/${props.nodeId}/telemetry/history?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })

    if (!response.ok) {
      throw new Error(`Gagal mengambil data telemetri (${response.status})`)
    }

    const data = await response.json()
    const feeds = data.feeds || []

    if (!feeds.length) {
      throw new Error('Tidak ada titik data yang ditemukan pada rentang waktu yang dipilih.')
    }

    // Export to CSV
    const result = exportTelemetryToCSV({
      nodeName: props.nodeName,
      nodeCode: props.nodeId,
      feeds,
      sensors: filteredSensors.value,
      timeRangeLabel: selectedPreset.value === 'custom' ? 'custom_range' : selectedPreset.value,
      filenamePrefix: `telemetry_${selectedDomain.value}`
    })

    exportedCount.value = result.count
    exportSuccess.value = true

    setTimeout(() => {
      emit('update:open', false)
      exportSuccess.value = false
    }, 1800)

  } catch (err: any) {
    console.error('Export telemetry error:', err)
    errorMessage.value = err.message || 'Terjadi kesalahan saat memproses ekspor CSV.'
  } finally {
    isExporting.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[560px] p-6 rounded-2xl border border-border/80 shadow-2xl bg-white dark:bg-card">
      <DialogHeader class="space-y-1.5 border-b border-border/50 pb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center shrink-0 shadow-xs">
            <ExcelIcon class="w-6 h-6" />
          </div>
          <div>
            <DialogTitle class="text-lg sm:text-xl font-extrabold text-foreground tracking-tight">
              Export Telemetri Sensor (CSV)
            </DialogTitle>
            <DialogDescription class="text-xs text-muted-foreground font-medium">
              Unduh data time-series lengkap stasiun <strong class="text-foreground font-bold">{{ nodeName }}</strong> untuk Excel & analisis statistik.
            </DialogDescription>
          </div>
        </div>
      </DialogHeader>

      <div class="space-y-4 py-3">
        <!-- 1. Rentang Waktu (Presets & Custom) -->
        <div class="space-y-2">
          <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
            <Calendar class="w-3.5 h-3.5 text-primary" />
            <span>1. Rentang Waktu Data</span>
          </Label>
          
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <button
              v-for="p in presets"
              :key="p.id"
              type="button"
              @click="selectedPreset = p.id as any"
              :class="[
                'py-2 px-2.5 rounded-xl text-xs font-bold border transition-all text-center cursor-pointer',
                selectedPreset === p.id 
                  ? 'bg-primary/15 border-primary text-primary shadow-xs' 
                  : 'bg-slate-50 dark:bg-slate-800/60 border-border/70 text-muted-foreground hover:text-foreground hover:bg-slate-100 dark:hover:bg-slate-800'
              ]"
            >
              {{ p.label }}
            </button>
          </div>

          <!-- Custom Date Range Inputs -->
          <div v-if="selectedPreset === 'custom'" class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1.5">
            <div>
              <label class="text-[11px] font-semibold text-muted-foreground block mb-1">Dari Tanggal:</label>
              <input 
                type="date" 
                v-model="customStart"
                class="w-full h-9 px-3 rounded-lg border border-border/80 bg-background text-xs font-medium text-foreground focus:ring-1 focus:ring-primary focus:outline-none"
              />
            </div>
            <div>
              <label class="text-[11px] font-semibold text-muted-foreground block mb-1">Sampai Tanggal:</label>
              <input 
                type="date" 
                v-model="customEnd"
                class="w-full h-9 px-3 rounded-lg border border-border/80 bg-background text-xs font-medium text-foreground focus:ring-1 focus:ring-primary focus:outline-none"
              />
            </div>
          </div>
        </div>

        <!-- 2. Resolusi Agregasi Waktu -->
        <div class="space-y-2">
          <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
            <Clock class="w-3.5 h-3.5 text-primary" />
            <span>2. Resolusi & Agregasi Data</span>
          </Label>

          <select 
            v-model="selectedAggregation"
            class="w-full h-9 px-3 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:ring-1 focus:ring-primary focus:outline-none cursor-pointer"
          >
            <option v-for="a in aggregations" :key="a.id" :value="a.id">
              {{ a.label }} ({{ a.desc }})
            </option>
          </select>
        </div>

        <!-- 3. Domain Parameter Sensor -->
        <div class="space-y-2">
          <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
            <Layers class="w-3.5 h-3.5 text-primary" />
            <span>3. Filter Domain Parameter ({{ filteredSensors.length }} Sensor Dipilih)</span>
          </Label>

          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="d in domains"
              :key="d.id"
              type="button"
              @click="selectedDomain = d.id as any"
              :class="[
                'py-2 px-2.5 rounded-xl text-xs font-semibold border transition-all text-left truncate cursor-pointer',
                selectedDomain === d.id 
                  ? 'bg-emerald-500/15 border-emerald-500 text-emerald-700 dark:text-emerald-400 font-bold shadow-xs' 
                  : 'bg-slate-50 dark:bg-slate-800/60 border-border/70 text-muted-foreground hover:text-foreground'
              ]"
            >
              {{ d.label }}
            </button>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs font-medium">
          {{ errorMessage }}
        </div>

        <!-- Success Toast -->
        <div v-if="exportSuccess" class="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold flex items-center gap-2 animate-bounce">
          <CheckCircle2 class="w-4 h-4" />
          <span>Berhasil mengunduh {{ exportedCount }} baris data telemetri!</span>
        </div>
      </div>

      <DialogFooter class="border-t border-border/50 pt-4 flex flex-row items-center justify-between sm:justify-between gap-3">
        <Button 
          variant="ghost" 
          size="sm"
          class="text-xs font-semibold text-muted-foreground hover:text-foreground cursor-pointer"
          @click="emit('update:open', false)"
        >
          Tutup
        </Button>

        <Button
          type="button"
          @click="handleExport"
          :disabled="isExporting"
          class="h-10 px-5 rounded-xl font-bold text-xs sm:text-sm bg-emerald-600 hover:bg-emerald-700 text-white shadow-md cursor-pointer gap-2 transition-all active:scale-[0.98]"
        >
          <Loader2 v-if="isExporting" class="w-4 h-4 animate-spin text-white" />
          <Download v-else class="w-4 h-4 text-white" />
          <span>{{ isExporting ? 'Memproses Data...' : 'Download File CSV' }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

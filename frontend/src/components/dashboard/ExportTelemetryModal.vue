<script setup lang="ts">
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import Lenis from 'lenis'
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
  Layers, CheckCircle2, Clock, 
  ArrowRight, ArrowLeft, Check, Sparkles,
  FileSpreadsheet, Database
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

// Wizard Navigation Step (1: Time Range, 2: Aggregation, 3: Domain & Export)
const currentStep = ref(1)
const step2ScrollRef = ref<HTMLElement | null>(null)
let modalLenis: Lenis | null = null
let modalRafId: number | null = null

const cleanupModalLenis = () => {
  if (modalRafId !== null) {
    cancelAnimationFrame(modalRafId)
    modalRafId = null
  }
  if (modalLenis) {
    modalLenis.destroy()
    modalLenis = null
  }
}

// Reset to Step 1 & Lock Background Scroll whenever modal opens
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    currentStep.value = 1
    errorMessage.value = ''
    exportSuccess.value = false
    document.body.style.overflow = 'hidden'
  } else {
    cleanupModalLenis()
    document.body.style.overflow = ''
  }
}, { immediate: true })

// Lenis Smooth Scroll on Step 2
watch(currentStep, async (step) => {
  cleanupModalLenis()

  if (step === 2) {
    await nextTick()
    if (step2ScrollRef.value) {
      modalLenis = new Lenis({
        wrapper: step2ScrollRef.value,
        content: (step2ScrollRef.value.firstElementChild as HTMLElement) || step2ScrollRef.value,
        duration: 1.0,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        orientation: 'vertical',
        smoothWheel: true,
        wheelMultiplier: 1.1,
        touchMultiplier: 1.5,
      })

      function raf(time: number) {
        modalLenis?.raf(time)
        modalRafId = requestAnimationFrame(raf)
      }
      modalRafId = requestAnimationFrame(raf)
    }
  }
})

onUnmounted(() => {
  cleanupModalLenis()
  document.body.style.overflow = ''
})

// State Form Options
const selectedPreset = ref<'1d' | '1w' | '1M' | 'custom'>('1w')
const customStart = ref('')
const customEnd = ref('')
const selectedAggregation = ref<'raw' | '5' | '15' | '60' | '1440'>('raw')
const selectedDomain = ref<'all' | 'npk' | 'soil' | 'iot'>('all')
const isExporting = ref(false)
const exportSuccess = ref(false)
const exportedCount = ref(0)
const errorMessage = ref('')

// Wizard Steps Definition
const wizardSteps = [
  { step: 1, title: 'Periode', icon: Calendar },
  { step: 2, title: 'Resolusi', icon: Clock },
  { step: 3, title: 'Kategori & Unduh', icon: Layers }
]

// Presets
const presets = [
  { id: '1d', label: '24 Jam Terakhir', desc: 'Data rekaman 1 hari terakhir' },
  { id: '1w', label: '7 Hari Terakhir', desc: 'Arsip telemetri 1 minggu' },
  { id: '1M', label: '30 Hari Terakhir', desc: 'Arsip tren 1 bulan penuh' },
  { id: 'custom', label: 'Rentang Kustom', desc: 'Tentukan tanggal spesifik' }
]

// Aggregation Options
const aggregations = [
  { id: 'raw', label: 'Data Mentah (Semua Titik)', desc: 'Setiap transmisi data asli (resolusi tinggi)' },
  { id: '5', label: 'Rata-rata 5 Menit', desc: 'Agregasi rata-rata per 5 menit' },
  { id: '15', label: 'Rata-rata 15 Menit', desc: 'Agregasi rata-rata per 15 menit' },
  { id: '60', label: 'Rata-rata 1 Jam', desc: 'Ringkasan rata-rata per 60 menit' },
  { id: '1440', label: 'Rata-rata Harian', desc: '1 titik ringkasan rata-rata per hari' }
]

// Domain Options
const domains = [
  { id: 'all', label: 'Semua Sensor', icon: '🌿', desc: 'Seluruh parameter tanah, iklim, & perangkat' },
  { id: 'npk', label: 'Unsur Hara NPK', icon: '🧪', desc: 'Nitrogen (N), Fosfor (P), Kalium (K)' },
  { id: 'soil', label: 'Kondisi Tanah', icon: '🌱', desc: 'Moisture, pH Tanah, Suhu Tanah, EC' },
  { id: 'iot', label: 'Kondisi IoT & Panel', icon: '⚡', desc: 'Suhu Enclosure Box, Status Suplai & Modbus' }
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

// Readable summary labels for Step 3
const selectedPresetLabel = computed(() => {
  if (selectedPreset.value === 'custom') {
    if (customStart.value && customEnd.value) return `${customStart.value} s/d ${customEnd.value}`
    return 'Rentang Kustom'
  }
  return presets.find(p => p.id === selectedPreset.value)?.label || selectedPreset.value
})

const selectedAggregationLabel = computed(() => {
  return aggregations.find(a => a.id === selectedAggregation.value)?.label || 'Data Mentah'
})

const selectedDomainLabel = computed(() => {
  return domains.find(d => d.id === selectedDomain.value)?.label || 'Semua Sensor'
})

// Wizard Step Navigation
const nextStep = () => {
  errorMessage.value = ''
  if (currentStep.value === 1 && selectedPreset.value === 'custom') {
    if (!customStart.value || !customEnd.value) {
      errorMessage.value = 'Silakan pilih tanggal mulai dan tanggal akhir terlebih dahulu.'
      return
    }
    if (new Date(customStart.value) > new Date(customEnd.value)) {
      errorMessage.value = 'Tanggal mulai tidak boleh lebih baru dari tanggal akhir.'
      return
    }
  }
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  errorMessage.value = ''
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

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
    <DialogContent class="sm:max-w-[540px] p-6 rounded-2xl border border-border/80 shadow-2xl bg-white dark:bg-card overflow-hidden">
      <DialogHeader class="pb-1">
        <DialogTitle class="text-base sm:text-lg font-extrabold text-foreground tracking-tight flex items-center gap-2.5">
          <ExcelIcon class="w-7 h-7 shrink-0" />
          <span>Export Telemetri (CSV)</span>
        </DialogTitle>
        <DialogDescription class="text-xs text-muted-foreground font-medium">
          Ikuti tahapan berikut untuk mengunduh data stasiun <strong class="text-foreground font-bold">{{ nodeName }}</strong>.
        </DialogDescription>
      </DialogHeader>

      <!-- VISUAL CHECKPOINT STEPPER (Same as Add New Node) -->
      <div class="flex items-center justify-between py-3 px-1 border-b border-border/50 select-none">
        <!-- Step 1: Periode -->
        <div class="flex items-center text-xs sm:text-sm shrink-0" :class="currentStep >= 1 ? 'text-primary' : 'text-muted-foreground'">
          <div 
            class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-full border-2 text-xs sm:text-sm font-bold transition-colors shrink-0"
            :class="currentStep >= 1 ? 'border-primary bg-primary text-primary-foreground shadow-xs' : 'border-muted-foreground text-muted-foreground'"
          >
            1
          </div>
          <span class="ml-2 font-semibold">Periode</span>
        </div>

        <!-- Connector Line 1 -->
        <div class="mx-2 sm:mx-3 h-[2px] flex-1 transition-colors" :class="currentStep >= 2 ? 'bg-primary' : 'bg-muted dark:bg-slate-800'"></div>

        <!-- Step 2: Resolusi -->
        <div class="flex items-center text-xs sm:text-sm shrink-0" :class="currentStep >= 2 ? 'text-primary' : 'text-muted-foreground'">
          <div 
            class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-full border-2 text-xs sm:text-sm font-bold transition-colors shrink-0"
            :class="currentStep >= 2 ? 'border-primary bg-primary text-primary-foreground shadow-xs' : 'border-muted text-muted-foreground bg-background'"
          >
            2
          </div>
          <span class="ml-2 font-semibold">Resolusi</span>
        </div>

        <!-- Connector Line 2 -->
        <div class="mx-2 sm:mx-3 h-[2px] flex-1 transition-colors" :class="currentStep >= 3 ? 'bg-primary' : 'bg-muted dark:bg-slate-800'"></div>

        <!-- Step 3: Kategori -->
        <div class="flex items-center text-xs sm:text-sm shrink-0" :class="currentStep >= 3 ? 'text-primary' : 'text-muted-foreground'">
          <div 
            class="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-full border-2 text-xs sm:text-sm font-bold transition-colors shrink-0"
            :class="currentStep >= 3 ? 'border-primary bg-primary text-primary-foreground shadow-xs' : 'border-muted text-muted-foreground bg-background'"
          >
            3
          </div>
          <span class="ml-2 font-semibold">Kategori</span>
        </div>
      </div>

      <!-- Wizard Step Content (Fixed Stable Height: Zero Layout Shift) -->
      <div class="py-4 h-[285px] flex flex-col justify-between overflow-hidden">
        <Transition name="wizard-fade" mode="out-in">
          <!-- STEP 1: Rentang Waktu -->
          <div v-if="currentStep === 1" key="step1" class="space-y-3 h-full flex flex-col justify-between">
            <div class="space-y-2.5">
              <Label class="text-sm font-bold text-foreground flex items-center gap-2">
                <Calendar class="w-4 h-4 text-primary" />
                <span>Pilih Periode Waktu Telemetri</span>
              </Label>

              <!-- 4 Presets Grid (Adapts height smoothly when custom is active) -->
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="p in presets"
                  :key="p.id"
                  type="button"
                  @click="selectedPreset = p.id as any"
                  :class="[
                    'rounded-xl border transition-all duration-150 cursor-pointer flex items-center justify-between relative',
                    selectedPreset === 'custom' ? 'py-2.5 px-3' : 'py-3.5 px-4',
                    selectedPreset === p.id 
                      ? 'bg-primary/10 border-primary shadow-xs ring-1 ring-primary/40 text-primary font-bold' 
                      : 'bg-slate-50 dark:bg-slate-800/60 border-border/70 text-foreground hover:bg-slate-100 dark:hover:bg-slate-800 font-semibold'
                  ]"
                >
                  <span class="text-xs sm:text-sm">{{ p.label }}</span>
                  <div 
                    class="w-4 h-4 sm:w-5 sm:h-5 rounded-full border flex items-center justify-center shrink-0"
                    :class="selectedPreset === p.id ? 'bg-primary border-primary text-primary-foreground shadow-xs' : 'border-border bg-background'"
                  >
                    <Check v-if="selectedPreset === p.id" class="w-2.5 h-2.5 sm:w-3 sm:h-3 stroke-[3]" />
                  </div>
                </button>
              </div>
            </div>

            <!-- Custom Date Range Inputs (Fits in fixed reserved space) -->
            <div 
              v-if="selectedPreset === 'custom'" 
              class="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/70 border border-border/80 space-y-2 animate-in fade-in-50 duration-200"
            >
              <div class="grid grid-cols-2 gap-2.5">
                <div>
                  <label class="text-[11px] font-semibold text-muted-foreground block mb-1">Dari Tanggal:</label>
                  <input 
                    type="date" 
                    v-model="customStart"
                    class="w-full h-8 px-2.5 rounded-lg border border-border/80 bg-background text-xs sm:text-sm font-medium text-foreground focus:ring-1 focus:ring-primary focus:outline-none"
                  />
                </div>
                <div>
                  <label class="text-[11px] font-semibold text-muted-foreground block mb-1">Sampai Tanggal:</label>
                  <input 
                    type="date" 
                    v-model="customEnd"
                    class="w-full h-8 px-2.5 rounded-lg border border-border/80 bg-background text-xs sm:text-sm font-medium text-foreground focus:ring-1 focus:ring-primary focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <!-- Hint box when preset is active (Maintains consistent height) -->
            <div 
              v-else 
              class="p-3 rounded-xl bg-slate-50 dark:bg-slate-900/40 border border-border/60 text-xs text-muted-foreground flex items-center gap-2.5"
            >
              <FileSpreadsheet class="w-4 h-4 text-primary shrink-0" />
              <span>Arsip telemetri akan disiapkan sesuai rentang waktu yang Anda pilih di atas.</span>
            </div>
          </div>

          <!-- STEP 2: Resolusi & Agregasi Data -->
          <div v-else-if="currentStep === 2" key="step2" class="space-y-2.5 h-full flex flex-col justify-between">
            <div>
              <Label class="text-sm font-bold text-foreground flex items-center gap-2">
                <Clock class="w-4 h-4 text-primary" />
                <span>Pilih Resolusi & Agregasi Data</span>
              </Label>
            </div>

            <div 
              ref="step2ScrollRef" 
              data-lenis-prevent
              class="flex-1 max-h-[225px] overflow-y-auto overscroll-contain pr-1.5"
            >
              <div class="space-y-2 pb-1">
                <button
                  v-for="a in aggregations"
                  :key="a.id"
                  type="button"
                  @click="selectedAggregation = a.id as any"
                  :class="[
                    'w-full py-2.5 px-3.5 rounded-xl border text-left transition-all duration-150 cursor-pointer flex items-center justify-between',
                    selectedAggregation === a.id 
                      ? 'bg-primary/10 border-primary shadow-xs ring-1 ring-primary/40' 
                      : 'bg-slate-50 dark:bg-slate-800/60 border-border/70 text-muted-foreground hover:text-foreground hover:bg-slate-100 dark:hover:bg-slate-800'
                  ]"
                >
                  <div class="flex flex-col pr-2">
                    <span class="text-sm font-bold text-foreground">{{ a.label }}</span>
                    <span class="text-xs text-muted-foreground">{{ a.desc }}</span>
                  </div>
                  <div 
                    class="w-5 h-5 rounded-full border flex items-center justify-center shrink-0"
                    :class="selectedAggregation === a.id ? 'bg-primary border-primary text-primary-foreground shadow-xs' : 'border-border bg-background'"
                  >
                    <Check v-if="selectedAggregation === a.id" class="w-3 h-3 stroke-[3]" />
                  </div>
                </button>
              </div>
            </div>
          </div>

          <!-- STEP 3: Filter Kategori & Review Download -->
          <div v-else-if="currentStep === 3" key="step3" class="space-y-3.5">
            <div>
              <Label class="text-sm font-bold text-foreground">
                Filter Kategori Sensor ({{ filteredSensors.length }} Terpilih)
              </Label>
            </div>

            <!-- Domain Pills Selector -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <button
                v-for="d in domains"
                :key="d.id"
                type="button"
                @click="selectedDomain = d.id as any"
                :class="[
                  'p-3 rounded-xl border text-left transition-all duration-150 cursor-pointer flex items-center gap-2.5',
                  selectedDomain === d.id 
                    ? 'bg-emerald-500/15 border-emerald-500 text-emerald-700 dark:text-emerald-400 font-bold shadow-xs' 
                    : 'bg-slate-50 dark:bg-slate-800/60 border-border/70 text-muted-foreground hover:text-foreground'
                ]"
              >
                <span class="text-xl">{{ d.icon }}</span>
                <span class="text-sm font-bold truncate">{{ d.label }}</span>
              </button>
            </div>

            <!-- Final Export Summary Card -->
            <div class="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 space-y-2 text-xs shadow-inner">
              <div class="flex items-center justify-between text-xs border-b border-border/40 pb-1.5">
                <span class="text-muted-foreground font-medium">Format Dokumen:</span>
                <span class="font-extrabold text-foreground">Microsoft Excel CSV (.csv)</span>
              </div>
              <div class="grid grid-cols-3 gap-2 text-center pt-0.5">
                <div class="p-2 rounded-xl bg-white dark:bg-card border border-border/60">
                  <span class="text-[11px] text-muted-foreground block font-medium">Periode</span>
                  <strong class="text-xs sm:text-sm font-extrabold text-foreground truncate block">{{ selectedPresetLabel }}</strong>
                </div>
                <div class="p-2 rounded-xl bg-white dark:bg-card border border-border/60">
                  <span class="text-[11px] text-muted-foreground block font-medium">Resolusi</span>
                  <strong class="text-xs sm:text-sm font-extrabold text-foreground truncate block">{{ selectedAggregationLabel }}</strong>
                </div>
                <div class="p-2 rounded-xl bg-white dark:bg-card border border-border/60">
                  <span class="text-[11px] text-muted-foreground block font-medium">Kategori</span>
                  <strong class="text-xs sm:text-sm font-extrabold text-emerald-600 truncate block">{{ filteredSensors.length }} Sensor</strong>
                </div>
              </div>
            </div>
          </div>
        </Transition>

        <!-- Error Message -->
        <div v-if="errorMessage" class="mt-3 p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs font-semibold animate-in fade-in-50">
          {{ errorMessage }}
        </div>

        <!-- Success Toast -->
        <div v-if="exportSuccess" class="mt-3 p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold flex items-center gap-2 animate-bounce">
          <CheckCircle2 class="w-4 h-4 shrink-0" />
          <span>Berhasil mengunduh {{ exportedCount }} baris data telemetri!</span>
        </div>
      </div>

      <!-- Modal Footer with Wizard Navigation Controls -->
      <DialogFooter class="border-t border-border/50 pt-4 flex flex-row items-center justify-between sm:justify-between gap-3">
        <!-- Back / Close Button -->
        <Button 
          v-if="currentStep === 1"
          variant="ghost" 
          size="sm"
          class="text-xs sm:text-sm font-semibold text-muted-foreground hover:text-foreground cursor-pointer"
          @click="emit('update:open', false)"
        >
          Tutup
        </Button>
        <Button 
          v-else
          variant="outline" 
          size="sm"
          class="text-xs sm:text-sm font-semibold border-border/80 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer gap-1.5"
          @click="prevStep"
        >
          <ArrowLeft class="w-4 h-4" />
          <span>Kembali</span>
        </Button>

        <!-- Next / Download Button -->
        <Button
          v-if="currentStep < 3"
          type="button"
          @click="nextStep"
          class="h-10 px-5 rounded-xl font-bold text-xs sm:text-sm bg-primary hover:bg-primary/90 text-primary-foreground shadow-xs cursor-pointer gap-2 transition-all active:scale-[0.98]"
        >
          <span>Lanjut ke Langkah {{ currentStep + 1 }}</span>
          <ArrowRight class="w-4 h-4" />
        </Button>

        <Button
          v-else
          type="button"
          @click="handleExport"
          :disabled="isExporting"
          class="h-10 px-6 rounded-xl font-bold text-xs sm:text-sm bg-emerald-600 hover:bg-emerald-700 text-white shadow-md cursor-pointer gap-2 transition-all active:scale-[0.98]"
        >
          <Loader2 v-if="isExporting" class="w-4 h-4 animate-spin text-white" />
          <Download v-else class="w-4 h-4 text-white" />
          <span>{{ isExporting ? 'Memproses Data...' : 'Download File CSV' }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.wizard-fade-enter-active,
.wizard-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.wizard-fade-enter-from {
  opacity: 0;
  transform: translateX(10px);
}

.wizard-fade-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>

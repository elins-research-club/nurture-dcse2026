<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
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
import PdfIcon from '@/components/icons/PdfIcon.vue'
import { 
  Download, Printer, Loader2, Sparkles, 
  CheckCircle2, User, FileSignature, Calendar, Layers
} from 'lucide-vue-next'
import { generateExecutivePDFReport, downloadExecutivePDFReport, type PDFReportOptions } from '@/lib/pdfReportGenerator'
import { useTelemetryStore } from '@/stores/telemetry'
import { filterSensorsByCategory } from '@/lib/sensorTaxonomy'

const props = withDefaults(defineProps<{
  open: boolean
  nodeId: string
  nodeName: string
  location?: string
  coordinates?: string
  sensors?: any[]
  currentFeeds?: any[]
  initialRange?: '1d' | '1w' | '1M' | 'custom'
  initialCategory?: 'all' | 'npk' | 'soil' | 'environment'
  summaryMetrics?: string[]
  rangeLabel?: string
  npkRatio?: string
  soilAvgMoisture?: string | number
  phVal?: string | number
  ecVal?: string | number
  enclosureTemp?: string | number
  enclosureSafeLimit?: string | number
  agronomyInsight?: string
  thermalInsight?: string
}>(), {
  initialRange: '1d',
  initialCategory: 'all',
  sensors: () => [],
  currentFeeds: () => []
})

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
}>()

const telemetryStore = useTelemetryStore()

const authorName = ref('')
const customNotes = ref('')
const isGenerating = ref(false)
const isSuccess = ref(false)
const isLoadingFeeds = ref(false)

// Select Options
const rangeOptions = [
  { id: '1d' as const, label: '24 Jam Terakhir' },
  { id: '1w' as const, label: '7 Hari Terakhir' },
  { id: '1M' as const, label: '30 Hari Terakhir' }
]

const categoryOptions = [
  { id: 'all' as const, label: 'Semua Parameter' },
  { id: 'npk' as const, label: 'Unsur Hara NPK' },
  { id: 'soil' as const, label: 'Kondisi Tanah' },
  { id: 'environment' as const, label: 'IoT & Lingkungan' },
  { id: 'power' as const, label: 'Sistem Kelistrikan' }
]

// State for Dropdowns
const selectedRange = ref<'1d' | '1w' | '1M' | 'custom'>('1d')
const selectedCategory = ref<'all' | 'npk' | 'soil' | 'environment' | 'power'>('all')
const modalFeeds = ref<any[]>([])

// Fetch Feeds when Range Changes
const loadFeedsForRange = async (range: '1d' | '1w' | '1M' | 'custom') => {
  if (range === props.initialRange && props.currentFeeds && props.currentFeeds.length > 0) {
    modalFeeds.value = props.currentFeeds
    return
  }

  isLoadingFeeds.value = true
  try {
    const feeds = await telemetryStore.fetchHistory(props.nodeId, { range, force: true })
    modalFeeds.value = feeds || []
  } catch (e) {
    console.error('[ReportPreviewModal] Failed to fetch feeds for range:', e)
    modalFeeds.value = props.currentFeeds || []
  } finally {
    isLoadingFeeds.value = false
  }
}

// Body Scroll Locking & Initial State Sync
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    document.body.style.overflow = 'hidden'
    selectedRange.value = props.initialRange || '1d'
    selectedCategory.value = props.initialCategory || 'all'
    modalFeeds.value = props.currentFeeds || []
    loadFeedsForRange(selectedRange.value)
  } else {
    document.body.style.overflow = ''
  }
}, { immediate: true })

// Watch for dropdown changes
watch(selectedRange, (newRange) => {
  if (props.open) {
    loadFeedsForRange(newRange)
  }
})

onUnmounted(() => {
  document.body.style.overflow = ''
})

// Range Label Computed
const selectedRangeLabel = computed(() => {
  return rangeOptions.find(r => r.id === selectedRange.value)?.label || '24 Jam Terakhir'
})

// Category Label Computed
const selectedCategoryLabel = computed(() => {
  return categoryOptions.find(c => c.id === selectedCategory.value)?.label || 'Semua Parameter'
})

// Filtered Sensors by chosen category
const filteredSensors = computed(() =>
  filterSensorsByCategory(props.sensors || [], selectedCategory.value)
)

// Computed Statistics from Feeds
const computedStats = computed(() => {
  const feeds = modalFeeds.value || []
  return filteredSensors.value.map(s => {
    const channelId = s.channel_id ? String(s.channel_id).toLowerCase() : ''
    const tsField = (s.thingspeak_field || s.field_key || s.channel_field || '').toLowerCase()
    const compositeKey = channelId && tsField ? `${channelId}_${tsField}` : ''

    const rawVals = feeds.map((f: any) => {
      // Resolve strictly by the channel-scoped key, exactly as the dashboard does.
      // The previous fallback chain ended in an endsWith('_' + field) scan that
      // could match the SAME field number on a DIFFERENT channel, which is how EC
      // readings ended up as the max of a moisture probe column.
      let val = compositeKey ? f[compositeKey] : undefined
      if (val === undefined && s.field_key) val = f[s.field_key]
      if (val === undefined && s.name) val = f[s.name]
      return parseFloat(val)
    }).filter((v: number) => Number.isFinite(v))

    const lastVal = rawVals.length ? Number(rawVals[rawVals.length - 1].toFixed(1)) : '--'
    const min = rawVals.length ? Number(Math.min(...rawVals).toFixed(1)) : '--'
    const max = rawVals.length ? Number(Math.max(...rawVals).toFixed(1)) : '--'
    const avg = rawVals.length ? Number((rawVals.reduce((a, b) => a + b, 0) / rawVals.length).toFixed(1)) : '--'

    const domainName = (s.name?.toLowerCase().includes('nitrogen') || s.name?.toLowerCase().includes('phosphor') || s.name?.toLowerCase().includes('kalium')) ? 'NPK' : (s.name?.toLowerCase().includes('panel') || s.name?.toLowerCase().includes('udara') ? 'IoT' : 'Tanah')

    return {
      id: s.id,
      name: s.name,
      unit: s.unit || '',
      type: s.type,
      domain: domainName,
      lastVal,
      avg,
      min,
      max,
      minThreshold: s.min_threshold,
      maxThreshold: s.max_threshold,
      status: 'Optimal'
    }
  })
})

const handleGeneratePDF = async (isPrint = false) => {
  if (isGenerating.value) return
  isGenerating.value = true
  isSuccess.value = false

  try {
    const reportOptions: PDFReportOptions = {
      nodeName: props.nodeName,
      nodeCode: props.nodeId,
      location: props.location,
      coordinates: props.coordinates || (props.location && props.location.includes(',') ? props.location : undefined),
      rangeLabel: selectedRangeLabel.value,
      categoryLabel: selectedCategoryLabel.value,
      // Only mirror the dashboard's ikhtisar while the report still covers the
      // same category; once the user picks another, those names no longer apply.
      highlightParams: selectedCategory.value === props.initialCategory ? props.summaryMetrics : undefined,
      dataPointsCount: modalFeeds.value.length || 100,
      generatedBy: authorName.value.trim() || 'Pengelola Lahan / Pengguna',
      notes: customNotes.value,
      stats: computedStats.value,
      npkRatio: props.npkRatio || 'Seimbang',
      soilAvgMoisture: props.soilAvgMoisture,
      phVal: props.phVal,
      ecVal: props.ecVal,
      enclosureTemp: props.enclosureTemp,
      enclosureSafeLimit: props.enclosureSafeLimit || 55,
      agronomyInsight: props.agronomyInsight,
      thermalInsight: props.thermalInsight
    }

    const doc = await generateExecutivePDFReport(reportOptions)
    
    const now = new Date()
    const dateStr = now.toISOString().slice(0, 10)
    const cleanNode = (props.nodeId || 'stasiun').toLowerCase().replace(/[^a-z0-9_-]/g, '_')
    const cleanCategory = selectedCategory.value
    const filename = `Laporan_Telemetri_${cleanNode}_${cleanCategory}_${dateStr}.pdf`

    if (isPrint) {
      doc.autoPrint()
      const blobUrl = doc.output('bloburl', { filename })
      const win = window.open(blobUrl, '_blank')
      if (win) {
        win.document.title = filename.replace('.pdf', '')
      }
    } else {
      downloadExecutivePDFReport(doc, filename)
    }

    isSuccess.value = true
    setTimeout(() => {
      emit('update:open', false)
      isSuccess.value = false
    }, 1500)

  } catch (err) {
    console.error('PDF Generation error:', err)
    alert('Terjadi kesalahan saat membuat dokumen PDF.')
  } finally {
    isGenerating.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[540px] p-6 rounded-2xl border border-border/80 shadow-2xl bg-white dark:bg-card overflow-hidden">
      <DialogHeader class="pb-1">
        <DialogTitle class="text-base sm:text-lg font-extrabold text-foreground tracking-tight flex items-center gap-2.5">
          <PdfIcon class="w-7 h-7 shrink-0" />
          <span>Export Laporan (PDF)</span>
        </DialogTitle>
        <DialogDescription class="text-xs text-muted-foreground font-medium">
          Unduh dokumen evaluasi & ringkasan telemetri stasiun <strong class="text-foreground font-bold">{{ nodeName }}</strong>.
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-3.5 py-2">
        <!-- Interactive Dropdowns (Synced by Default with Dashboard) -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <!-- Periode Dropdown -->
          <div class="space-y-1.5">
            <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
              <Calendar class="w-3.5 h-3.5 text-primary" />
              <span>Periode Laporan</span>
            </Label>
            <select 
              v-model="selectedRange"
              class="w-full h-10 px-3 rounded-xl border border-border/80 bg-background text-xs sm:text-sm font-semibold text-foreground focus:ring-1 focus:ring-primary focus:outline-none cursor-pointer"
            >
              <option v-for="r in rangeOptions" :key="r.id" :value="r.id">
                {{ r.label }}
              </option>
            </select>
          </div>

          <!-- Kategori Sensor Dropdown -->
          <div class="space-y-1.5">
            <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
              <Layers class="w-3.5 h-3.5 text-primary" />
              <span>Kategori Parameter</span>
            </Label>
            <select 
              v-model="selectedCategory"
              class="w-full h-10 px-3 rounded-xl border border-border/80 bg-background text-xs sm:text-sm font-semibold text-foreground focus:ring-1 focus:ring-primary focus:outline-none cursor-pointer"
            >
              <option v-for="c in categoryOptions" :key="c.id" :value="c.id">
                {{ c.label }} {{ c.id === 'all' ? `(${sensors?.length || 15})` : '' }}
              </option>
            </select>
          </div>
        </div>

        <!-- Sleek Minimal Summary Strip -->
        <div class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-border/60 text-xs font-semibold text-muted-foreground">
          <div class="flex items-center gap-1.5">
            <span>Sampel:</span>
            <strong class="text-emerald-600 flex items-center gap-1">
              <Loader2 v-if="isLoadingFeeds" class="w-3 h-3 animate-spin" />
              <span>{{ modalFeeds.length }} Titik</span>
            </strong>
          </div>
          <div class="h-3 w-px bg-border/60"></div>
          <div class="flex items-center gap-1.5">
            <span>Sensor:</span>
            <strong class="text-foreground">{{ computedStats.length }} Param</strong>
          </div>
          <div class="h-3 w-px bg-border/60"></div>
          <div class="flex items-center gap-1.5">
            <span>Format:</span>
            <strong class="text-foreground">Dokumen A4</strong>
          </div>
        </div>

        <!-- Inputs: Author Name & Custom Notes -->
        <div class="space-y-3">
          <div class="space-y-1.5">
            <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
              <User class="w-3.5 h-3.5 text-primary" />
              <span>Nama Penanggung Jawab / Peneliti <span class="text-muted-foreground font-normal">(Opsional)</span></span>
            </Label>
            <input 
              type="text" 
              v-model="authorName"
              placeholder="e.g. Pemilik Kebun / Tim Peneliti / Pengelola Lahan"
              class="w-full h-10 px-3.5 rounded-xl border border-border/80 bg-background text-xs sm:text-sm font-semibold text-foreground focus:ring-1 focus:ring-primary focus:outline-none"
            />
          </div>

          <div class="space-y-1.5">
            <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
              <FileSignature class="w-3.5 h-3.5 text-primary" />
              <span>Catatan Tambahan / Keterangan Lahan <span class="text-muted-foreground font-normal">(Opsional)</span></span>
            </Label>
            <textarea 
              v-model="customNotes"
              rows="2"
              placeholder="Tuliskan catatan khusus atau rekomendasi tindakan lapangan jika ada..."
              class="w-full p-2.5 rounded-xl border border-border/80 bg-background text-xs sm:text-sm font-medium text-foreground focus:ring-1 focus:ring-primary focus:outline-none resize-none"
            ></textarea>
          </div>
        </div>

        <!-- Success Toast -->
        <div v-if="isSuccess" class="p-2.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold flex items-center gap-2 animate-bounce">
          <CheckCircle2 class="w-4 h-4 shrink-0" />
          <span>Dokumen PDF Laporan Berhasil Dibuat!</span>
        </div>
      </div>

      <DialogFooter class="border-t border-border/50 pt-3.5 flex flex-row items-center justify-between sm:justify-between gap-3">
        <Button 
          variant="ghost" 
          size="sm"
          class="text-xs sm:text-sm font-semibold text-muted-foreground hover:text-foreground cursor-pointer"
          @click="emit('update:open', false)"
        >
          Tutup
        </Button>

        <div class="flex items-center gap-2.5">
          <Button
            type="button"
            variant="outline"
            @click="handleGeneratePDF(true)"
            :disabled="isGenerating || isLoadingFeeds"
            class="h-10 px-4 rounded-xl font-bold text-xs sm:text-sm border-border/80 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer gap-2 transition-all"
          >
            <Printer class="w-4 h-4" />
            <span>Cetak</span>
          </Button>

          <Button
            type="button"
            @click="handleGeneratePDF(false)"
            :disabled="isGenerating || isLoadingFeeds"
            class="h-10 px-5 rounded-xl font-bold text-xs sm:text-sm bg-emerald-600 hover:bg-emerald-700 text-white shadow-md cursor-pointer gap-2 transition-all active:scale-[0.98]"
          >
            <Loader2 v-if="isGenerating" class="w-4 h-4 animate-spin text-white" />
            <Download v-else class="w-4 h-4 text-white" />
            <span>{{ isGenerating ? 'Merender PDF...' : 'Download PDF' }}</span>
          </Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

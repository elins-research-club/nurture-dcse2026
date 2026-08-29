<script setup lang="ts">
import { ref } from 'vue'
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
  CheckCircle2, Building, User, FileSignature
} from 'lucide-vue-next'
import { generateExecutivePDFReport, downloadExecutivePDFReport, type PDFReportOptions } from '@/lib/pdfReportGenerator'

const props = defineProps<{
  open: boolean
  nodeId: string
  nodeName: string
  location?: string
  stats: any[]
  rangeLabel: string
  dataPointsCount: number
  npkRatio?: string
  soilAvgMoisture?: string | number
  phVal?: string | number
  ecVal?: string | number
  enclosureTemp?: string | number
  enclosureSafeLimit?: string | number
  agronomyInsight?: string
  thermalInsight?: string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
}>()

const authorName = ref('Tim Peneliti Laboratorium ELINS UGM')
const customNotes = ref('')
const isGenerating = ref(false)
const isSuccess = ref(false)

const handleGeneratePDF = async (isPrint = false) => {
  if (isGenerating.value) return
  isGenerating.value = true
  isSuccess.value = false

  try {
    const reportOptions: PDFReportOptions = {
      nodeName: props.nodeName,
      nodeCode: props.nodeId,
      location: props.location,
      rangeLabel: props.rangeLabel,
      dataPointsCount: props.dataPointsCount || 100,
      generatedBy: authorName.value || 'Administrator Sistem',
      notes: customNotes.value,
      stats: props.stats.map(s => ({
        name: s.name,
        unit: s.unit || '',
        domain: s.type === 'npk' ? 'NPK' : (s.name?.toLowerCase().includes('panel') ? 'IoT' : 'Tanah'),
        lastVal: s.latestVal ?? s.lastVal ?? s.value ?? '--',
        avg: s.avg ?? s.mean ?? '--',
        min: s.min ?? '--',
        max: s.max ?? '--',
        minThreshold: s.min_threshold,
        maxThreshold: s.max_threshold,
        status: 'Optimal'
      })),
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
    const filename = `Laporan_Evaluasi_GConnect_${cleanNode}_${dateStr}.pdf`

    if (isPrint) {
      doc.autoPrint()
      const blobUrl = doc.output('bloburl')
      window.open(blobUrl, '_blank')
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
    <DialogContent class="sm:max-w-[620px] p-6 rounded-2xl border border-border/80 shadow-2xl bg-white dark:bg-card max-h-[90vh] overflow-y-auto">
      <DialogHeader class="space-y-1.5 border-b border-border/50 pb-4">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-center justify-center shrink-0 shadow-xs">
            <PdfIcon class="w-6 h-6" />
          </div>
          <div>
            <DialogTitle class="text-lg sm:text-xl font-extrabold text-foreground tracking-tight">
              Executive PDF Agronomy Report
            </DialogTitle>
            <DialogDescription class="text-xs text-muted-foreground font-medium">
              Cetak laporan berkala resmi stasiun <strong class="text-foreground font-bold">{{ nodeName }}</strong> berstandar evaluasi akademik & industri.
            </DialogDescription>
          </div>
        </div>
      </DialogHeader>

      <div class="space-y-4 py-3">
        <!-- Live Document Preview Snapshot Card -->
        <div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 space-y-3 shadow-inner">
          <div class="flex items-center justify-between border-b border-border/50 pb-2">
            <div class="flex items-center gap-2 text-xs font-bold text-primary">
              <Building class="w-4 h-4" />
              <span>Kop Resmi Laboratorium ELINS DIKE UGM</span>
            </div>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
              Format A4 Siap Cetak
            </span>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
            <div class="p-2 rounded-xl bg-white dark:bg-card border border-border/60">
              <span class="text-[10px] text-muted-foreground block font-medium">Stasiun</span>
              <strong class="font-extrabold text-foreground truncate block">{{ nodeName }}</strong>
            </div>
            <div class="p-2 rounded-xl bg-white dark:bg-card border border-border/60">
              <span class="text-[10px] text-muted-foreground block font-medium">Periode</span>
              <strong class="font-extrabold text-foreground truncate block">{{ rangeLabel }}</strong>
            </div>
            <div class="p-2 rounded-xl bg-white dark:bg-card border border-border/60">
              <span class="text-[10px] text-muted-foreground block font-medium">Data Agregasi</span>
              <strong class="font-extrabold text-emerald-600 block">{{ dataPointsCount }} Titik</strong>
            </div>
            <div class="p-2 rounded-xl bg-white dark:bg-card border border-border/60">
              <span class="text-[10px] text-muted-foreground block font-medium">Total Sensor</span>
              <strong class="font-extrabold text-foreground block">{{ stats.length }} Param</strong>
            </div>
          </div>

          <!-- Highlight Preview Items -->
          <div class="text-[11px] text-muted-foreground space-y-1 bg-white/60 dark:bg-card/60 p-2.5 rounded-xl border border-border/40">
            <p>✓ <strong>KPI Eksekutif:</strong> Rata-rata Kelembaban ({{ soilAvgMoisture || '--' }}%), Rasio NPK ({{ npkRatio || 'Seimbang' }}), pH/EC, dan Suhu Panel ({{ enclosureTemp || '--' }}°C).</p>
            <p>✓ <strong>Tabel Statistik Lengkap:</strong> Nilai Terakhir, Rata-rata, Min, Max, dan Ambang Batas.</p>
            <p>✓ <strong>Rekomendasi Agronomi & IoT:</strong> Analisis kesuburan tanah dan keamanan termal otomatis.</p>
          </div>
        </div>

        <!-- Inputs: Author Name & Custom Notes -->
        <div class="space-y-3">
          <div class="space-y-1">
            <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
              <User class="w-3.5 h-3.5 text-primary" />
              <span>Nama Penilai / Penyusun Laporan (Kredensial Penandatangan)</span>
            </Label>
            <input 
              type="text" 
              v-model="authorName"
              placeholder="e.g. Tim Peneliti Laboratorium ELINS UGM"
              class="w-full h-9 px-3 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:ring-1 focus:ring-primary focus:outline-none"
            />
          </div>

          <div class="space-y-1">
            <Label class="text-xs font-bold text-foreground flex items-center gap-1.5">
              <FileSignature class="w-3.5 h-3.5 text-primary" />
              <span>Catatan Tambahan / Instruksi Lapangan (Opsional)</span>
            </Label>
            <textarea 
              v-model="customNotes"
              rows="2"
              placeholder="Contoh: Lakukan penambahan pupuk NPK granul pada bedeng 2 dan periksa saluran valve irigasi."
              class="w-full p-2.5 rounded-xl border border-border/80 bg-background text-xs font-medium text-foreground focus:ring-1 focus:ring-primary focus:outline-none resize-none"
            ></textarea>
          </div>
        </div>

        <!-- Success Toast -->
        <div v-if="isSuccess" class="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold flex items-center gap-2 animate-bounce">
          <CheckCircle2 class="w-4 h-4" />
          <span>Dokumen PDF Laporan Resmi Berhasil Dibuat!</span>
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

        <div class="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            @click="handleGeneratePDF(true)"
            :disabled="isGenerating"
            class="h-10 px-3.5 rounded-xl font-bold text-xs border-border/80 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer gap-1.5 transition-all"
          >
            <Printer class="w-4 h-4" />
            <span class="hidden sm:inline">Cetak Langsung</span>
          </Button>

          <Button
            type="button"
            @click="handleGeneratePDF(false)"
            :disabled="isGenerating"
            class="h-10 px-4 rounded-xl font-bold text-xs sm:text-sm bg-primary hover:bg-primary/90 text-primary-foreground shadow-md cursor-pointer gap-2 transition-all active:scale-[0.98]"
          >
            <Loader2 v-if="isGenerating" class="w-4 h-4 animate-spin" />
            <Download v-else class="w-4 h-4" />
            <span>{{ isGenerating ? 'Merender PDF...' : 'Download PDF' }}</span>
          </Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import ExportTelemetryModal from '@/components/dashboard/ExportTelemetryModal.vue'
import ReportPreviewModal from '@/components/dashboard/ReportPreviewModal.vue'
import { useEventLogs, type EventLog } from '@/composables/useEventLogs'
import { useNodes } from '@/composables/useNodes'
import { useTelemetryStore } from '@/stores/telemetry'
import { useAuthStore } from '@/stores/auth'
import ExcelIcon from '@/components/icons/ExcelIcon.vue'
import PdfIcon from '@/components/icons/PdfIcon.vue'
import { 
  Info, AlertTriangle, XCircle, Clock, ChevronLeft, ChevronRight, 
  ChevronsLeft, ChevronsRight, RefreshCw, Loader2, ScrollText, Download
} from 'lucide-vue-next'

const currentPage = ref(1)
const pageSize = ref<number>(25)
const selectedLevel = ref<string | undefined>(undefined)
const isExportingCSV = ref(false)
const isExportingPDF = ref(false)

const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()
const { nodesQuery } = useNodes()
const nodes = computed(() => nodesQuery.data?.value || [])

const selectedNodeId = ref<string>('')
const selectedSensors = ref<any[]>([])
const isTelemetryExportOpen = ref(false)
const isAgronomyReportOpen = ref(false)

// Auto-select first node
watch(nodes, (nodeList) => {
  if (nodeList && nodeList.length > 0 && !selectedNodeId.value) {
    selectedNodeId.value = nodeList[0].node_id
  }
}, { immediate: true })

const selectedNode = computed(() => {
  if (!nodes.value || !nodes.value.length) return null
  return nodes.value.find((n: any) => n.node_id === selectedNodeId.value) || nodes.value[0] || null
})

watch(selectedNodeId, async (id) => {
  if (id) {
    selectedSensors.value = await telemetryStore.fetchSensors(id)
  } else {
    selectedSensors.value = []
  }
}, { immediate: true })

const pageSizeOptions = [25, 50, 100]

const { logsQuery, totalCount, totalPages } = useEventLogs({
  page: currentPage,
  pageSize: pageSize,
  level: selectedLevel
})

// Reset to page 1 when page size or level filter changes
watch([pageSize, selectedLevel], () => {
  currentPage.value = 1
})

const changePage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    
    // Smooth scrolling up on layout container & window
    const mainEl = document.querySelector('main')
    if (mainEl) {
      mainEl.scrollTo({ top: 0, behavior: 'smooth' })
    }
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  let s = dateString
  if (!s.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(s)) {
    s += 'Z'
  }
  const date = new Date(s)
  return new Intl.DateTimeFormat('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).format(date) + ' WIB'
}

const startItem = computed(() => {
  if (totalCount.value === 0) return 0
  return (currentPage.value - 1) * pageSize.value + 1
})

const endItem = computed(() => {
  return Math.min(currentPage.value * pageSize.value, totalCount.value)
})

// Generate visible page numbers for pagination
const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const pages: (number | string)[] = []
  if (current <= 4) {
    pages.push(1, 2, 3, 4, 5, '...', total)
  } else if (current >= total - 3) {
    pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total)
  } else {
    pages.push(1, '...', current - 1, current, current + 1, '...', total)
  }
  return pages
})

// Helper to fetch all logs for export based on filter
const fetchExportLogs = async (): Promise<EventLog[]> => {
  const params = new URLSearchParams()
  params.set('skip', '0')
  params.set('limit', String(Math.max(totalCount.value || 1000, 1000)))
  if (selectedLevel.value) {
    params.set('level', selectedLevel.value)
  }

  const headers: Record<string, string> = {}
  if (authStore.token) {
    headers['Authorization'] = `Bearer ${authStore.token}`
  }

  const response = await fetch(`/api/v1/event-logs/?${params.toString()}`, {
    headers
  })

  if (!response.ok) {
    throw new Error('Gagal mengambil data event logs')
  }

  return await response.json()
}

const exportToCSV = async () => {
  if (isExportingCSV.value) return
  isExportingCSV.value = true
  try {
    const data = await fetchExportLogs()
    if (!data.length) {
      alert('Tidak ada data log untuk diekspor.')
      return
    }

    // CSV Headers
    const headers = ['No', 'Waktu (WIB)', 'Tingkat (Level)', 'Kode Stasiun', 'Nama Stasiun', 'Pesan Log']
    
    // CSV Rows
    const rows = data.map((log, index) => {
      const formattedTime = formatDate(log.created_at)
      const level = log.level || 'INFO'
      const nodeCode = log.node_code || '-'
      const nodeName = log.node_name || '-'
      const message = `"${(log.message || '').replace(/"/g, '""')}"`
      
      return [
        index + 1,
        `"${formattedTime}"`,
        `"${level}"`,
        `"${nodeCode}"`,
        `"${nodeName}"`,
        message
      ].join(',')
    })

    // Prepend UTF-8 BOM (\uFEFF) for Excel compatibility
    const csvContent = '\uFEFF' + [headers.join(','), ...rows].join('\r\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    
    const link = document.createElement('a')
    const now = new Date()
    const timestampStr = now.toISOString().slice(0, 10) + '_' + String(now.getHours()).padStart(2, '0') + '-' + String(now.getMinutes()).padStart(2, '0')
    const filterTag = selectedLevel.value ? selectedLevel.value.toLowerCase() : 'all'
    link.setAttribute('href', url)
    link.setAttribute('download', `gconnect_event_logs_${filterTag}_${timestampStr}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Export CSV error:', err)
    alert('Terjadi kesalahan saat mengunduh CSV. Silakan coba lagi.')
  } finally {
    isExportingCSV.value = false
  }
}

const exportToPDF = async () => {
  if (isExportingPDF.value) return
  isExportingPDF.value = true
  try {
    const data = await fetchExportLogs()
    if (!data.length) {
      alert('Tidak ada data log untuk diekspor ke PDF.')
      return
    }

    const [{ default: jsPDF }, { default: autoTable }] = await Promise.all([
      import('jspdf'),
      import('jspdf-autotable')
    ])

    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    })

    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 14
    let y = margin

    // Top Header Banner
    doc.setFillColor(15, 23, 42) // Slate 900
    doc.roundedRect(margin, y, pageWidth - (margin * 2), 22, 2.5, 2.5, 'F')

    // Title & Subtitle in Header
    doc.setTextColor(255, 255, 255)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(13)
    doc.text('G-CONNECT — LAPORAN LOG & RIWAYAT SISTEM', margin + 6, y + 9)

    doc.setTextColor(148, 163, 184) // Slate 400
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.text('Platform Smart Farming IoT Lab ELINS UGM — Dokumen Resmi Riwayat Aktivitas & Event', margin + 6, y + 16)

    y += 26

    // Metadata Summary Box
    doc.setFillColor(248, 250, 252) // Slate 50
    doc.setDrawColor(226, 232, 240) // Slate 200
    doc.roundedRect(margin, y, pageWidth - (margin * 2), 16, 2, 2, 'FD')

    const now = new Date()
    const printTimeStr = new Intl.DateTimeFormat('id-ID', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    }).format(now) + ' WIB'

    // Left Column Metadata
    doc.setFontSize(8)
    doc.setTextColor(71, 85, 105) // Slate 600
    doc.setFont('helvetica', 'normal')
    doc.text('Waktu Cetak: ', margin + 5, y + 6)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(15, 23, 42)
    doc.text(printTimeStr, margin + 25, y + 6)

    doc.setFont('helvetica', 'normal')
    doc.setTextColor(71, 85, 105)
    doc.text('Level Filter: ', margin + 5, y + 11.5)
    doc.setFont('helvetica', 'bold')
    const filterLabel = selectedLevel.value ? selectedLevel.value : 'SEMUA TINGKAT (ALL)'
    if (selectedLevel.value === 'ERROR') {
      doc.setTextColor(225, 29, 72) // Rose
    } else if (selectedLevel.value === 'WARNING') {
      doc.setTextColor(217, 119, 6) // Amber
    } else if (selectedLevel.value === 'INFO') {
      doc.setTextColor(37, 99, 235) // Blue
    } else {
      doc.setTextColor(15, 23, 42)
    }
    doc.text(filterLabel, margin + 25, y + 11.5)

    // Right Column Metadata
    const col2X = pageWidth / 2 + 5
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(71, 85, 105)
    doc.text('Total Entri Log: ', col2X, y + 6)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(15, 23, 42)
    doc.text(`${data.length} Baris Aktivitas`, col2X + 26, y + 6)

    doc.setFont('helvetica', 'normal')
    doc.setTextColor(71, 85, 105)
    doc.text('Dicetak Oleh: ', col2X, y + 11.5)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(15, 23, 42)
    doc.text(authStore.user?.username || 'Administrator', col2X + 26, y + 11.5)

    y += 20

    // AutoTable for Log Records
    const tableHeaders = [['No', 'Waktu (WIB)', 'Level', 'Kode Node', 'Nama Stasiun', 'Pesan Log / Kejadian']]
    const tableBody = data.map((log, index) => {
      return [
        String(index + 1),
        formatDate(log.created_at),
        log.level || 'INFO',
        log.node_code || '-',
        log.node_name || '-',
        log.message || '-'
      ]
    })

    autoTable(doc, {
      startY: y,
      head: tableHeaders,
      body: tableBody,
      theme: 'grid',
      headStyles: {
        fillColor: [15, 23, 42],
        textColor: [255, 255, 255],
        fontStyle: 'bold',
        fontSize: 7.5,
        halign: 'left',
        cellPadding: 2.2
      },
      bodyStyles: {
        fontSize: 7,
        textColor: [30, 41, 59],
        cellPadding: 2,
        valign: 'middle'
      },
      alternateRowStyles: {
        fillColor: [248, 250, 252]
      },
      columnStyles: {
        0: { cellWidth: 8, halign: 'center' },
        1: { cellWidth: 32 },
        2: { cellWidth: 16, halign: 'center', fontStyle: 'bold' },
        3: { cellWidth: 22, fontStyle: 'bold' },
        4: { cellWidth: 28 },
        5: { cellWidth: 'auto' }
      },
      didParseCell: (cellData) => {
        if (cellData.section === 'body' && cellData.column.index === 2) {
          const raw = String(cellData.cell.raw).toUpperCase()
          if (raw === 'ERROR') {
            cellData.cell.styles.textColor = [225, 29, 72] // Rose
          } else if (raw === 'WARNING') {
            cellData.cell.styles.textColor = [217, 119, 6] // Amber
          } else if (raw === 'INFO') {
            cellData.cell.styles.textColor = [37, 99, 235] // Blue
          }
        }
      },
      didDrawPage: (dataInfo) => {
        const totalPagesCount = (doc as any).internal.getNumberOfPages()
        const currentPageNum = dataInfo.pageNumber
        doc.setFontSize(7)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(148, 163, 184)
        doc.text(
          'G-CONNECT Smart Farming System — Dokumen Log Resmi',
          margin,
          pageHeight - 7
        )
        doc.text(
          `Halaman ${currentPageNum} dari ${totalPagesCount}`,
          pageWidth - margin - 20,
          pageHeight - 7
        )
      },
      margin: { left: margin, right: margin, bottom: 14 }
    })

    const timestampStr = now.toISOString().slice(0, 10) + '_' + String(now.getHours()).padStart(2, '0') + '-' + String(now.getMinutes()).padStart(2, '0')
    const filterTag = selectedLevel.value ? selectedLevel.value.toLowerCase() : 'all'
    doc.save(`gconnect_event_logs_${filterTag}_${timestampStr}.pdf`)
  } catch (err) {
    console.error('Export PDF error:', err)
    alert('Terjadi kesalahan saat membuat dokumen PDF. Silakan coba lagi.')
  } finally {
    isExportingPDF.value = false
  }
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-5">
      
      <!-- Page Header -->
      <div class="flex flex-col gap-1">
        <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">Logs & Ekspor Data</h2>
        <p class="text-xs sm:text-sm text-muted-foreground">
          Pusat unduh data telemetri pertanian, cetak laporan agronomi resmi, dan riwayat log aktivitas sistem.
        </p>
      </div>

      <!-- SECTION 1: PUSAT EKSPOR DATA TELEMETRI & LAPORAN AGRONOMI -->
      <Card class="border border-border/80 bg-white dark:bg-card shadow-xs rounded-2xl overflow-hidden">
        <div class="p-5 sm:p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-5 bg-gradient-to-r from-emerald-500/5 via-teal-500/5 to-transparent">
          <div class="space-y-2 max-w-xl">
            <div class="flex items-center gap-2.5">
              <div class="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0 shadow-2xs">
                <Download class="w-5 h-5 stroke-[2.2]" />
              </div>
              <div>
                <h3 class="text-lg sm:text-xl font-black tracking-tight text-foreground">
                  Ekspor Telemetri & Laporan Agronomi
                </h3>
                <p class="text-xs sm:text-sm text-muted-foreground leading-tight">
                  Unduh time-series sensor ke format CSV atau cetak Laporan Eksekutif Agronomi (PDF)
                </p>
              </div>
            </div>

            <!-- Selected Node Info Chip -->
            <div v-if="selectedNode" class="flex flex-wrap items-center gap-2 pt-1 text-xs">
              <span class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono font-bold border border-slate-200 dark:border-slate-700">
                ID: {{ selectedNode.node_id }}
              </span>
              <span v-if="selectedNode.location" class="text-muted-foreground flex items-center gap-1">
                <span>📍 {{ selectedNode.location }}</span>
              </span>
              <span class="text-muted-foreground">
                • {{ selectedSensors.length }} sensor terkonfigurasi
              </span>
            </div>
          </div>

          <!-- Stasiun Selector & Action Buttons Container -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <!-- Stasiun Dropdown Selector -->
            <div class="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/90 border border-slate-200/90 dark:border-slate-700 px-3 py-1.5 rounded-xl shadow-2xs">
              <span class="text-xs font-bold text-muted-foreground whitespace-nowrap">Stasiun:</span>
              <select 
                v-model="selectedNodeId" 
                class="bg-transparent text-xs sm:text-sm font-extrabold text-foreground focus:outline-none cursor-pointer py-1 max-w-[200px] truncate"
                :disabled="!nodes.length"
              >
                <option v-if="!nodes.length" value="">Memuat stasiun...</option>
                <option 
                  v-for="node in nodes" 
                  :key="node.node_id" 
                  :value="node.node_id"
                  class="bg-white dark:bg-slate-900 text-foreground"
                >
                  {{ node.name || node.node_id }} ({{ node.node_id }})
                </option>
              </select>
            </div>

            <!-- Export Telemetri CSV Button (Green) -->
            <Button
              @click="isTelemetryExportOpen = true"
              :disabled="!selectedNode"
              variant="outline"
              class="h-10 px-4 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-700 dark:text-emerald-300 font-bold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-2xs border border-emerald-500/30 cursor-pointer hover:scale-[1.02] active:scale-95 transition-all"
              title="Buka Wizard Ekspor Telemetri (CSV)"
            >
              <ExcelIcon />
              <span>Export Telemetri (CSV)</span>
            </Button>

            <!-- Laporan Agronomi PDF Button (Rose) -->
            <Button
              @click="isAgronomyReportOpen = true"
              :disabled="!selectedNode"
              variant="outline"
              class="h-10 px-4 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-700 dark:text-rose-300 font-bold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-2xs border border-rose-500/30 cursor-pointer hover:scale-[1.02] active:scale-95 transition-all"
              title="Pratinjau & Cetak Laporan Resmi PDF"
            >
              <PdfIcon />
              <span>Laporan Agronomi (PDF)</span>
            </Button>
          </div>
        </div>
      </Card>
      
      <!-- SECTION 2: RIWAYAT LOG AKTIVITAS & PERINGATAN SISTEM -->
      <Card class="border border-border/80 bg-white dark:bg-card shadow-xs rounded-2xl">
        <!-- Card Header with Filter Pills, Actions & Count -->
        <CardHeader class="p-5 border-b border-border/60 flex flex-col lg:flex-row lg:items-center justify-between gap-4 space-y-0">
          <div class="flex items-center gap-2.5">
            <ScrollText class="w-5 h-5 text-primary" />
            <CardTitle class="text-base sm:text-lg font-bold text-foreground">Riwayat Log Aktivitas Sistem</CardTitle>
            
            <span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              {{ totalCount }} Total
            </span>
          </div>

          <div class="flex items-center gap-2.5 flex-wrap">
            <!-- Filter Pills -->
            <div class="flex items-center bg-slate-100 dark:bg-slate-800 p-1.5 rounded-2xl border border-border/80 text-sm gap-1 shadow-2xs">
              <button
                @click="selectedLevel = undefined"
                :class="[
                  'px-3 py-1 rounded-xl font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 text-xs hover:-translate-y-0.5 active:scale-95 group',
                  selectedLevel === undefined 
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 border border-slate-300/90 dark:border-slate-700 shadow-xs' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                ]"
              >
                <span class="group-hover:scale-105 transition-transform duration-200">Semua</span>
              </button>

              <button
                @click="selectedLevel = 'INFO'"
                :class="[
                  'px-3 py-1 rounded-xl font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 text-xs hover:-translate-y-0.5 active:scale-95 group',
                  selectedLevel === 'INFO' 
                    ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 border border-slate-300/90 dark:border-slate-700 shadow-xs' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                ]"
              >
                <Info class="w-3.5 h-3.5 text-blue-500 transition-transform duration-200 group-hover:rotate-12 group-hover:scale-110" />
                <span>Info</span>
              </button>

              <button
                @click="selectedLevel = 'WARNING'"
                :class="[
                  'px-3 py-1 rounded-xl font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 text-xs hover:-translate-y-0.5 active:scale-95 group',
                  selectedLevel === 'WARNING' 
                    ? 'bg-white dark:bg-slate-900 text-amber-600 dark:text-amber-400 border border-slate-300/90 dark:border-slate-700 shadow-xs' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                ]"
              >
                <AlertTriangle class="w-3.5 h-3.5 text-amber-500 transition-transform duration-200 group-hover:-rotate-12 group-hover:scale-110" />
                <span>Warning</span>
              </button>

              <button
                @click="selectedLevel = 'ERROR'"
                :class="[
                  'px-3 py-1 rounded-xl font-bold transition-all duration-200 cursor-pointer flex items-center gap-1.5 text-xs hover:-translate-y-0.5 active:scale-95 group',
                  selectedLevel === 'ERROR' 
                    ? 'bg-white dark:bg-slate-900 text-rose-600 dark:text-rose-400 border border-slate-300/90 dark:border-slate-700 shadow-xs' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                ]"
              >
                <XCircle class="w-3.5 h-3.5 text-rose-500 transition-transform duration-200 group-hover:rotate-90 group-hover:scale-110" />
                <span>Error</span>
              </button>
            </div>

            <!-- Refresh Button -->
            <Button 
              variant="outline" 
              size="sm" 
              class="h-9 px-3 rounded-xl text-xs font-semibold gap-1.5 shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-105 active:scale-95 transition-all duration-200 group"
              @click="logsQuery.refetch()"
              :disabled="logsQuery.isFetching.value"
            >
              <RefreshCw :class="['w-3.5 h-3.5 transition-transform duration-300 group-hover:rotate-90', logsQuery.isFetching.value ? 'animate-spin' : '']" />
              <span>Refresh</span>
            </Button>

            <!-- Export Log CSV Button -->
            <Button
              @click="exportToCSV"
              :disabled="isExportingCSV || isExportingPDF || totalCount === 0"
              variant="outline"
              class="h-9 px-3 rounded-xl bg-slate-100 hover:bg-slate-200/80 dark:bg-slate-800 dark:hover:bg-slate-700 text-foreground font-bold text-xs flex items-center gap-1.5 shadow-2xs border border-border cursor-pointer active:scale-95 transition-all"
              title="Download rekaman log aktivitas dalam format CSV"
            >
              <Loader2 v-if="isExportingCSV" class="w-3.5 h-3.5 animate-spin text-muted-foreground" />
              <Download v-else class="w-3.5 h-3.5 text-muted-foreground" />
              <span>{{ isExportingCSV ? 'Mengekspor...' : 'Export Log CSV' }}</span>
            </Button>

            <!-- Cetak Log PDF Button -->
            <Button
              @click="exportToPDF"
              :disabled="isExportingCSV || isExportingPDF || totalCount === 0"
              variant="outline"
              class="h-9 px-3 rounded-xl bg-slate-100 hover:bg-slate-200/80 dark:bg-slate-800 dark:hover:bg-slate-700 text-foreground font-bold text-xs flex items-center gap-1.5 shadow-2xs border border-border cursor-pointer active:scale-95 transition-all"
              title="Cetak rekaman log aktivitas dalam format PDF"
            >
              <Loader2 v-if="isExportingPDF" class="w-3.5 h-3.5 animate-spin text-muted-foreground" />
              <Download v-else class="w-3.5 h-3.5 text-muted-foreground" />
              <span>{{ isExportingPDF ? 'Membuat PDF...' : 'Cetak Log PDF' }}</span>
            </Button>
          </div>
        </CardHeader>

        <CardContent class="p-5 flex flex-col gap-4">
          
          <!-- Loading State -->
          <div v-if="logsQuery.isLoading.value" class="py-16 text-center text-muted-foreground">
            <div class="flex items-center justify-center gap-2.5 animate-pulse">
              <RefreshCw class="animate-spin h-6 w-6 text-primary" />
              <span class="text-sm font-semibold">Memuat log peristiwa...</span>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="logsQuery.isError.value" class="py-12 text-center text-destructive border border-rose-200 bg-rose-50/50 rounded-2xl">
            <AlertTriangle class="w-10 h-10 mx-auto mb-2.5 text-rose-500 animate-bounce" />
            <p class="font-bold text-base">Gagal memuat log peristiwa</p>
            <p class="text-xs sm:text-sm text-muted-foreground mt-1">Periksa koneksi jaringan atau hubungi administrator.</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="!logsQuery.data.value || logsQuery.data.value.length === 0" class="py-16 text-center text-muted-foreground border border-dashed rounded-2xl">
            <ScrollText class="w-10 h-10 mx-auto mb-2.5 opacity-40 text-primary" />
            <p class="font-bold text-base text-foreground">Tidak ada log peristiwa yang ditemukan</p>
            <p class="text-xs sm:text-sm text-muted-foreground mt-1">Belum ada aktivitas atau filter yang dipilih tidak memiliki rekaman.</p>
          </div>
          
          <!-- ═══════════════ MICRO-ANIMATION 4: STAGGERED CASCADE LIST ═══════════════ -->
          <div v-else class="space-y-3">
            <div 
              v-for="(log, idx) in logsQuery.data.value" 
              :key="log.id"
              class="animate-alert-cascade flex items-start gap-4 p-4 rounded-2xl border border-slate-200/90 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/40 hover:bg-white dark:hover:bg-slate-800/80 hover:border-primary/40 hover:translate-x-1.5 hover:shadow-md transition-all duration-200 group cursor-default"
              :style="{ animationDelay: `${(idx % 12) * 35}ms` }"
            >
              <!-- ═══════════════ MICRO-ANIMATION 5: LEVEL ICON BEACON & HOVER ROTATION ═══════════════ -->
              <div class="shrink-0 mt-0.5 relative">
                <!-- ERROR Live Beacon Ping Ring -->
                <span v-if="log.level === 'ERROR'" class="animate-ping absolute -inset-0.5 rounded-xl bg-rose-500/40 opacity-75"></span>
                <!-- WARNING Pulse Beacon Ring -->
                <span v-if="log.level === 'WARNING'" class="animate-pulse absolute -inset-0.5 rounded-xl bg-amber-500/30 opacity-60"></span>

                <div v-if="log.level === 'INFO'" class="w-9 h-9 rounded-xl bg-blue-500/10 dark:bg-blue-500/20 border border-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-110 group-hover:rotate-6 transition-transform duration-200 shadow-2xs relative z-10">
                  <Info class="w-5 h-5" />
                </div>
                <div v-else-if="log.level === 'WARNING'" class="w-9 h-9 rounded-xl bg-amber-500/10 dark:bg-amber-500/20 border border-amber-500/20 flex items-center justify-center text-amber-600 dark:text-amber-400 group-hover:scale-110 group-hover:-rotate-6 transition-transform duration-200 shadow-2xs relative z-10">
                  <AlertTriangle class="w-5 h-5" />
                </div>
                <div v-else-if="log.level === 'ERROR'" class="w-9 h-9 rounded-xl bg-rose-500/10 dark:bg-rose-500/20 border border-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400 group-hover:scale-110 group-hover:rotate-12 transition-transform duration-200 shadow-2xs relative z-10">
                  <XCircle class="w-5 h-5" />
                </div>
                <div v-else class="w-9 h-9 rounded-xl bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-400 group-hover:scale-110 transition-transform duration-200 shadow-2xs relative z-10">
                  <Info class="w-5 h-5" />
                </div>
              </div>
              
              <!-- Content -->
              <div class="flex-1 min-w-0 space-y-1.5">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                  <p class="font-bold text-sm sm:text-base text-foreground break-words leading-snug group-hover:text-primary transition-colors duration-200">
                    {{ log.message }}
                  </p>
                  <div class="flex items-center text-xs sm:text-sm text-muted-foreground whitespace-nowrap shrink-0 font-medium group-hover:text-slate-700 dark:group-hover:text-slate-300 transition-colors duration-200">
                    <Clock class="w-3.5 h-3.5 mr-1.5 text-primary group-hover:rotate-45 transition-transform duration-300" />
                    <span>{{ formatDate(log.created_at) }}</span>
                  </div>
                </div>

                <div class="flex items-center gap-2 pt-0.5">
                  <span 
                    :class="[
                      'text-[11px] font-extrabold px-2.5 py-0.5 rounded-full border uppercase tracking-wider transition-transform duration-200 group-hover:scale-105',
                      log.level === 'INFO' ? 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/30' :
                      log.level === 'WARNING' ? 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30' :
                      log.level === 'ERROR' ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30' :
                      'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700'
                    ]"
                  >
                    {{ log.level }}
                  </span>

                  <!-- Human readable Node name / code (e.g. IoT Lab ELINS or NODE001) -->
                  <span 
                    v-if="log.node_name || log.node_code" 
                    class="text-[11px] font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2.5 py-0.5 rounded-full border border-slate-200 dark:border-slate-700 shadow-xs transition-transform duration-200 group-hover:scale-105"
                  >
                    Node: <strong class="font-bold text-foreground">{{ log.node_name || log.node_code }}</strong>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- ═══════════════ MICRO-ANIMATION 6: SPRING PAGINATION CONTROLS ═══════════════ -->
          <div class="flex flex-col lg:flex-row items-center justify-between gap-4 pt-4 border-t border-border/60 text-xs sm:text-sm text-muted-foreground font-medium">
            
            <!-- Left: Items Info & Page Size Options -->
            <div class="flex flex-wrap items-center gap-y-2 gap-x-4 sm:gap-x-6 w-full lg:w-auto justify-between sm:justify-start">
              <span class="text-muted-foreground whitespace-nowrap">
                Menampilkan <strong class="text-foreground font-bold">{{ startItem }} - {{ endItem }}</strong> dari <strong class="text-foreground font-bold">{{ totalCount }}</strong> log
              </span>

              <!-- Subtle Divider to prevent cramped layout -->
              <span class="hidden md:inline-block h-3.5 w-px bg-border/80"></span>

              <!-- Page Size Selection (25, 50, 100) -->
              <div class="flex items-center gap-2">
                <span class="text-muted-foreground whitespace-nowrap">Tampilkan:</span>
                <div class="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1 border border-border/80 gap-1 shadow-2xs">
                  <button
                    v-for="size in pageSizeOptions"
                    :key="size"
                    @click="pageSize = size"
                    :class="[
                      'px-2.5 py-0.5 rounded-lg font-bold text-xs transition-all duration-200 cursor-pointer hover:scale-105 active:scale-95',
                      pageSize === size 
                        ? 'bg-white dark:bg-slate-900 text-foreground border border-slate-200 dark:border-slate-700 shadow-xs' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    {{ size }}
                  </button>
                </div>
                <span class="text-muted-foreground whitespace-nowrap">/ hal</span>
              </div>
            </div>

            <!-- Right: Pagination Navigation with Micro-Spring -->
            <div class="flex items-center gap-1.5">
              <!-- First Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-9 w-9 rounded-xl shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-110 active:scale-90 hover:-translate-x-0.5 transition-all duration-200 group"
                :disabled="currentPage <= 1 || logsQuery.isLoading.value"
                @click="changePage(1)"
                title="Halaman Pertama"
              >
                <ChevronsLeft class="w-4 h-4 transition-transform duration-200 group-hover:-translate-x-0.5" />
              </Button>

              <!-- Previous Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-9 w-9 rounded-xl shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-110 active:scale-90 hover:-translate-x-0.5 transition-all duration-200 group"
                :disabled="currentPage <= 1 || logsQuery.isLoading.value"
                @click="changePage(currentPage - 1)"
                title="Halaman Sebelumnya"
              >
                <ChevronLeft class="w-4 h-4 transition-transform duration-200 group-hover:-translate-x-0.5" />
              </Button>

              <!-- Page Number Buttons -->
              <template v-for="(p, idx) in visiblePages" :key="idx">
                <span v-if="p === '...'" class="px-1.5 text-slate-400 font-bold">
                  ...
                </span>
                <button
                  v-else
                  @click="changePage(Number(p))"
                  :class="[
                    'h-9 min-w-[2.25rem] px-2.5 rounded-xl font-bold text-xs sm:text-sm transition-all duration-200 cursor-pointer border hover:scale-110 active:scale-90 hover:-translate-y-0.5',
                    currentPage === p 
                      ? 'bg-primary text-primary-foreground border-primary shadow-xs' 
                      : 'bg-white dark:bg-card text-foreground border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800'
                  ]"
                >
                  {{ p }}
                </button>
              </template>

              <!-- Next Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-9 w-9 rounded-xl shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-110 active:scale-90 hover:translate-x-0.5 transition-all duration-200 group"
                :disabled="currentPage >= totalPages || logsQuery.isLoading.value"
                @click="changePage(currentPage + 1)"
                title="Halaman Selanjutnya"
              >
                <ChevronRight class="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </Button>

              <!-- Last Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-9 w-9 rounded-xl shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-110 active:scale-90 hover:translate-x-0.5 transition-all duration-200 group"
                :disabled="currentPage >= totalPages || logsQuery.isLoading.value"
                @click="changePage(totalPages)"
                title="Halaman Terakhir"
              >
                <ChevronsRight class="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </Button>
            </div>

          </div>

        </CardContent>
      </Card>
    </div>

    <!-- Export Telemetry Modal (CSV) -->
    <ExportTelemetryModal
      v-if="selectedNode"
      :open="isTelemetryExportOpen"
      @update:open="isTelemetryExportOpen = $event"
      :node-id="selectedNode.node_id"
      :node-name="selectedNode.name || 'Stasiun Agro'"
      :sensors="selectedSensors"
    />

    <!-- Executive PDF Report Preview & Generator Modal -->
    <ReportPreviewModal
      v-if="selectedNode"
      :open="isAgronomyReportOpen"
      @update:open="isAgronomyReportOpen = $event"
      :node-id="selectedNode.node_id"
      :node-name="selectedNode.name || 'Stasiun Agro'"
      :location="selectedNode.location || 'Kebun Pertanian / Greenhouse'"
      :coordinates="selectedNode.latitude && selectedNode.longitude ? `${selectedNode.latitude}, ${selectedNode.longitude}` : undefined"
      :sensors="selectedSensors"
      initial-range="1d"
      initial-category="all"
    />
  </DashboardLayout>
</template>

<style scoped>
@keyframes alertSlideUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-alert-cascade {
  animation: alertSlideUp 0.38s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes bounceSubtle {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}

</style>

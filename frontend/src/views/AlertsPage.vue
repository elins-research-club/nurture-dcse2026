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
  ChevronsLeft, ChevronsRight, RefreshCw, ScrollText
} from 'lucide-vue-next'

const currentPage = ref(1)
const pageSize = ref<number>(25)
const selectedLevel = ref<string | undefined>(undefined)

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


</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-5">
      
      <!-- Page Header -->
      <div class="flex flex-col gap-1">
        <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">Logs & Ekspor Data</h2>
      </div>


      
      <!-- SECTION 2: RIWAYAT LOG AKTIVITAS & PERINGATAN SISTEM -->
      <Card class="border border-border/80 bg-white dark:bg-card shadow-xs rounded-2xl">
        <!-- Card Header with Filter Pills, Actions & Count -->
        <CardHeader class="px-4 py-3 sm:px-5 sm:py-3.5 border-b border-border/60 flex flex-row items-center justify-between gap-3 space-y-0 overflow-x-auto">
          <div class="flex items-center gap-2.5 shrink-0">
            <ScrollText class="w-5 h-5 text-primary shrink-0" />
            <CardTitle class="text-sm sm:text-base font-bold text-foreground whitespace-nowrap">Riwayat Log Aktivitas Sistem</CardTitle>
            
            <span class="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 shrink-0 whitespace-nowrap">
              {{ totalCount }} Total
            </span>
          </div>

          <div class="flex items-center justify-end gap-1.5 sm:gap-2 flex-nowrap shrink-0 ml-auto">
            <!-- Filter Pills -->
            <div class="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl border border-border/80 text-xs gap-0.5 shadow-2xs shrink-0">
              <button
                @click="selectedLevel = undefined"
                :class="[
                  'px-2.5 py-1 rounded-lg font-bold transition-all duration-200 cursor-pointer flex items-center gap-1 text-xs hover:-translate-y-0.5 active:scale-95 group whitespace-nowrap',
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
                  'px-2.5 py-1 rounded-lg font-bold transition-all duration-200 cursor-pointer flex items-center gap-1 text-xs hover:-translate-y-0.5 active:scale-95 group whitespace-nowrap',
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
                  'px-2.5 py-1 rounded-lg font-bold transition-all duration-200 cursor-pointer flex items-center gap-1 text-xs hover:-translate-y-0.5 active:scale-95 group whitespace-nowrap',
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
                  'px-2.5 py-1 rounded-lg font-bold transition-all duration-200 cursor-pointer flex items-center gap-1 text-xs hover:-translate-y-0.5 active:scale-95 group whitespace-nowrap',
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
              class="h-8 px-2.5 rounded-xl text-xs font-semibold gap-1.5 shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-105 active:scale-95 transition-all duration-200 group shrink-0 whitespace-nowrap"
              @click="logsQuery.refetch()"
              :disabled="logsQuery.isFetching.value"
            >
              <RefreshCw :class="['w-3.5 h-3.5 transition-transform duration-300 group-hover:rotate-90', logsQuery.isFetching.value ? 'animate-spin' : '']" />
              <span>Refresh</span>
            </Button>

            <div class="h-5 w-px bg-border/80 hidden sm:block mx-0.5 shrink-0"></div>

            <!-- Stasiun Dropdown Selector -->
            <div class="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/90 border border-slate-200/90 dark:border-slate-700 px-2 py-1 rounded-xl shadow-2xs shrink-0">
              <span class="text-xs font-bold text-muted-foreground whitespace-nowrap">Stasiun:</span>
              <select 
                v-model="selectedNodeId" 
                class="bg-transparent text-xs font-extrabold text-foreground focus:outline-none cursor-pointer py-0.5 max-w-[125px] xl:max-w-[150px] truncate"
                :disabled="!nodes.length"
              >
                <option v-if="!nodes.length" value="">Memuat stasiun...</option>
                <option 
                  v-for="node in nodes" 
                  :key="node.node_id" 
                  :value="node.node_id"
                  class="bg-white dark:bg-slate-900 text-foreground"
                >
                  {{ (node.name || node.node_id).trim() }} ({{ node.node_id }})
                </option>
              </select>
            </div>

            <!-- Export Telemetri CSV Button (Green) -->
            <Button
              @click="isTelemetryExportOpen = true"
              :disabled="!selectedNode"
              variant="outline"
              class="h-8 px-2.5 rounded-xl bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-700 dark:text-emerald-300 font-bold text-xs flex items-center justify-center gap-1.5 shadow-2xs border border-emerald-500/30 cursor-pointer hover:scale-[1.02] active:scale-95 transition-all shrink-0 whitespace-nowrap"
              title="Buka Wizard Ekspor Telemetri (CSV)"
            >
              <ExcelIcon />
              <span>Export (CSV)</span>
            </Button>

            <!-- Laporan Agronomi PDF Button (Rose) -->
            <Button
              @click="isAgronomyReportOpen = true"
              :disabled="!selectedNode"
              variant="outline"
              class="h-8 px-2.5 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-700 dark:text-rose-300 font-bold text-xs flex items-center justify-center gap-1.5 shadow-2xs border border-rose-500/30 cursor-pointer hover:scale-[1.02] active:scale-95 transition-all shrink-0 whitespace-nowrap"
              title="Pratinjau & Cetak Laporan Resmi PDF"
            >
              <PdfIcon />
              <span>Laporan (PDF)</span>
            </Button>
          </div>
        </CardHeader>

        <CardContent class="p-3.5 sm:p-4 flex flex-col gap-3">
          
          <!-- Loading State -->
          <div v-if="logsQuery.isLoading.value" class="py-10 text-center text-muted-foreground">
            <div class="flex items-center justify-center gap-2 animate-pulse">
              <RefreshCw class="animate-spin h-5 w-5 text-primary" />
              <span class="text-xs font-semibold">Memuat log peristiwa...</span>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="logsQuery.isError.value" class="py-8 text-center text-destructive border border-rose-200 bg-rose-50/50 rounded-xl">
            <AlertTriangle class="w-7 h-7 mx-auto mb-2 text-rose-500 animate-bounce" />
            <p class="font-bold text-sm">Gagal memuat log peristiwa</p>
            <p class="text-xs text-muted-foreground mt-0.5">Periksa koneksi jaringan atau hubungi administrator.</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="!logsQuery.data.value || logsQuery.data.value.length === 0" class="py-10 text-center text-muted-foreground border border-dashed rounded-xl">
            <ScrollText class="w-7 h-7 mx-auto mb-2 opacity-40 text-primary" />
            <p class="font-bold text-sm text-foreground">Tidak ada log peristiwa yang ditemukan</p>
            <p class="text-xs text-muted-foreground mt-0.5">Belum ada aktivitas atau filter yang dipilih tidak memiliki rekaman.</p>
          </div>
          
          <!-- ═══════════════ MICRO-ANIMATION 4: STAGGERED CASCADE LIST ═══════════════ -->
          <div v-else class="space-y-2">
            <div 
              v-for="(log, idx) in logsQuery.data.value" 
              :key="log.id"
              class="animate-alert-cascade flex items-start gap-3 p-2.5 sm:p-3 rounded-xl border border-slate-200/90 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/40 hover:bg-white dark:hover:bg-slate-800/80 hover:border-primary/40 hover:translate-x-1 hover:shadow-sm transition-all duration-200 group cursor-default"
              :style="{ animationDelay: `${(idx % 12) * 35}ms` }"
            >
              <!-- ═══════════════ MICRO-ANIMATION 5: LEVEL ICON BEACON & HOVER ROTATION ═══════════════ -->
              <div class="shrink-0 mt-0.5 relative">
                <!-- ERROR Live Beacon Ping Ring -->
                <span v-if="log.level === 'ERROR'" class="animate-ping absolute -inset-0.5 rounded-lg bg-rose-500/40 opacity-75"></span>
                <!-- WARNING Pulse Beacon Ring -->
                <span v-if="log.level === 'WARNING'" class="animate-pulse absolute -inset-0.5 rounded-lg bg-amber-500/30 opacity-60"></span>

                <div v-if="log.level === 'INFO'" class="w-7 h-7 rounded-lg bg-blue-500/10 dark:bg-blue-500/20 border border-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-400 group-hover:scale-110 group-hover:rotate-6 transition-transform duration-200 shadow-2xs relative z-10">
                  <Info class="w-3.5 h-3.5" />
                </div>
                <div v-else-if="log.level === 'WARNING'" class="w-7 h-7 rounded-lg bg-amber-500/10 dark:bg-amber-500/20 border border-amber-500/20 flex items-center justify-center text-amber-600 dark:text-amber-400 group-hover:scale-110 group-hover:-rotate-6 transition-transform duration-200 shadow-2xs relative z-10">
                  <AlertTriangle class="w-3.5 h-3.5" />
                </div>
                <div v-else-if="log.level === 'ERROR'" class="w-7 h-7 rounded-lg bg-rose-500/10 dark:bg-rose-500/20 border border-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400 group-hover:scale-110 group-hover:rotate-12 transition-transform duration-200 shadow-2xs relative z-10">
                  <XCircle class="w-3.5 h-3.5" />
                </div>
                <div v-else class="w-7 h-7 rounded-lg bg-slate-200 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-400 group-hover:scale-110 transition-transform duration-200 shadow-2xs relative z-10">
                  <Info class="w-3.5 h-3.5" />
                </div>
              </div>
              
              <!-- Content -->
              <div class="flex-1 min-w-0 space-y-1">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <p class="font-bold text-xs sm:text-[13px] text-foreground break-words leading-snug group-hover:text-primary transition-colors duration-200">
                    {{ log.message }}
                  </p>
                  <div class="flex items-center text-[11px] text-muted-foreground whitespace-nowrap shrink-0 font-medium group-hover:text-slate-700 dark:group-hover:text-slate-300 transition-colors duration-200">
                    <Clock class="w-3 h-3 mr-1 text-primary group-hover:rotate-45 transition-transform duration-300" />
                    <span>{{ formatDate(log.created_at) }}</span>
                  </div>
                </div>

                <div class="flex items-center gap-1.5 pt-0.5">
                  <span 
                    :class="[
                      'text-[9.5px] font-extrabold px-2 py-0.5 rounded-full border uppercase tracking-wider transition-transform duration-200 group-hover:scale-105',
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
                    class="text-[9.5px] font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-slate-700 shadow-xs transition-transform duration-200 group-hover:scale-105"
                  >
                    Node: <strong class="font-bold text-foreground">{{ log.node_name || log.node_code }}</strong>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- ═══════════════ MICRO-ANIMATION 6: SPRING PAGINATION CONTROLS ═══════════════ -->
          <div class="flex flex-col lg:flex-row items-center justify-between gap-3 pt-3 border-t border-border/60 text-[11px] sm:text-xs text-muted-foreground font-medium">
            
            <!-- Left: Items Info & Page Size Options -->
            <div class="flex flex-wrap items-center gap-y-1.5 gap-x-3 sm:gap-x-4 w-full lg:w-auto justify-between sm:justify-start">
              <span class="text-muted-foreground whitespace-nowrap">
                Menampilkan <strong class="text-foreground font-bold">{{ startItem }} - {{ endItem }}</strong> dari <strong class="text-foreground font-bold">{{ totalCount }}</strong> log
              </span>

              <!-- Subtle Divider to prevent cramped layout -->
              <span class="hidden md:inline-block h-3 w-px bg-border/80"></span>

              <!-- Page Size Selection (25, 50, 100) -->
              <div class="flex items-center gap-1.5">
                <span class="text-muted-foreground whitespace-nowrap">Tampilkan:</span>
                <div class="flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg p-0.5 border border-border/80 gap-0.5 shadow-2xs">
                  <button
                    v-for="size in pageSizeOptions"
                    :key="size"
                    @click="pageSize = size"
                    :class="[
                      'px-2 py-0.5 rounded-md font-bold text-[11px] transition-all duration-200 cursor-pointer hover:scale-105 active:scale-95',
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
            <div class="flex items-center gap-1">
              <!-- First Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-7 w-7 rounded-lg shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-110 active:scale-90 hover:-translate-x-0.5 transition-all duration-200 group"
                :disabled="currentPage <= 1 || logsQuery.isLoading.value"
                @click="changePage(1)"
                title="Halaman Pertama"
              >
                <ChevronsLeft class="w-3.5 h-3.5 transition-transform duration-200 group-hover:-translate-x-0.5" />
              </Button>

              <!-- Previous Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-7 w-7 rounded-lg shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-110 active:scale-90 hover:-translate-x-0.5 transition-all duration-200 group"
                :disabled="currentPage <= 1 || logsQuery.isLoading.value"
                @click="changePage(currentPage - 1)"
                title="Halaman Sebelumnya"
              >
                <ChevronLeft class="w-3.5 h-3.5 transition-transform duration-200 group-hover:-translate-x-0.5" />
              </Button>

              <!-- Page Number Buttons -->
              <template v-for="(p, idx) in visiblePages" :key="idx">
                <span v-if="p === '...'" class="px-1 text-slate-400 font-bold text-xs">
                  ...
                </span>
                <button
                  v-else
                  @click="changePage(Number(p))"
                  :class="[
                    'h-7 min-w-[1.75rem] px-2 rounded-lg font-bold text-xs transition-all duration-200 cursor-pointer border hover:scale-110 active:scale-90 hover:-translate-y-0.5',
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
                class="h-7 w-7 rounded-lg shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-110 active:scale-90 hover:translate-x-0.5 transition-all duration-200 group"
                :disabled="currentPage >= totalPages || logsQuery.isLoading.value"
                @click="changePage(currentPage + 1)"
                title="Halaman Selanjutnya"
              >
                <ChevronRight class="w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
              </Button>

              <!-- Last Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-7 w-7 rounded-lg shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer hover:scale-110 active:scale-90 hover:translate-x-0.5 transition-all duration-200 group"
                :disabled="currentPage >= totalPages || logsQuery.isLoading.value"
                @click="changePage(totalPages)"
                title="Halaman Terakhir"
              >
                <ChevronsRight class="w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
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

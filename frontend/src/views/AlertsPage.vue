<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useEventLogs } from '@/composables/useEventLogs'
import { 
  Info, AlertTriangle, XCircle, Clock, ChevronLeft, ChevronRight, 
  ChevronsLeft, ChevronsRight, Bell, RefreshCw
} from 'lucide-vue-next'

const currentPage = ref(1)
const pageSize = ref<number>(25)
const selectedLevel = ref<string | undefined>(undefined)

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
    <div class="flex flex-col space-y-4">
      
      <!-- Page Header (Subtitle removed) -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 class="text-2xl font-bold tracking-tight text-foreground">Alerts & Event Logs</h2>
        </div>

        <!-- Level Filter Tabs (Clean Light & Dark Mode Pills) -->
        <div class="flex items-center bg-slate-200/90 dark:bg-slate-800 p-1 rounded-xl border border-slate-300/80 dark:border-slate-700 text-xs">
          <button
            @click="selectedLevel = undefined"
            :class="[
              'px-3 py-1 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5',
              selectedLevel === undefined 
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 border border-slate-300/90 dark:border-slate-700 shadow-none' 
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
            ]"
          >
            <span>Semua</span>
          </button>
          <button
            @click="selectedLevel = 'INFO'"
            :class="[
              'px-3 py-1 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5',
              selectedLevel === 'INFO' 
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 border border-slate-300/90 dark:border-slate-700 shadow-none' 
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
            ]"
          >
            <Info class="w-3.5 h-3.5 text-blue-500" />
            <span>Info</span>
          </button>
          <button
            @click="selectedLevel = 'WARNING'"
            :class="[
              'px-3 py-1 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5',
              selectedLevel === 'WARNING' 
                ? 'bg-white dark:bg-slate-900 text-amber-600 dark:text-amber-400 border border-slate-300/90 dark:border-slate-700 shadow-none' 
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
            ]"
          >
            <AlertTriangle class="w-3.5 h-3.5 text-amber-500" />
            <span>Warning</span>
          </button>
          <button
            @click="selectedLevel = 'ERROR'"
            :class="[
              'px-3 py-1 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5',
              selectedLevel === 'ERROR' 
                ? 'bg-white dark:bg-slate-900 text-rose-600 dark:text-rose-400 border border-slate-300/90 dark:border-slate-700 shadow-none' 
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
            ]"
          >
            <XCircle class="w-3.5 h-3.5 text-rose-500" />
            <span>Error</span>
          </button>
        </div>
      </div>
      
      <!-- Main Content Card -->
      <Card class="border border-border/80 bg-white dark:bg-card shadow-none">
        <!-- Card Header with Count & Refresh -->
        <CardHeader class="p-4 border-b border-border/60 flex flex-row items-center justify-between space-y-0">
          <div class="flex items-center gap-2">
            <Bell class="w-4 h-4 text-primary" />
            <CardTitle class="text-base font-bold">Riwayat Log Peristiwa</CardTitle>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              {{ totalCount }} Total
            </span>
          </div>

          <Button 
            variant="outline" 
            size="sm" 
            class="h-8 text-xs gap-1.5 shadow-none border-border/80 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer"
            @click="logsQuery.refetch()"
            :disabled="logsQuery.isFetching.value"
          >
            <RefreshCw :class="['w-3 h-3', logsQuery.isFetching.value ? 'animate-spin' : '']" />
            <span>Refresh</span>
          </Button>
        </CardHeader>

        <CardContent class="p-4 flex flex-col gap-4">
          
          <!-- Loading State -->
          <div v-if="logsQuery.isLoading.value" class="py-16 text-center text-muted-foreground">
            <div class="flex items-center justify-center gap-2 animate-pulse">
              <RefreshCw class="animate-spin h-5 w-5 text-primary" />
              <span>Memuat log peristiwa...</span>
            </div>
          </div>

          <!-- Error State -->
          <div v-else-if="logsQuery.isError.value" class="py-12 text-center text-destructive border border-rose-200 bg-rose-50/50 rounded-xl">
            <AlertTriangle class="w-8 h-8 mx-auto mb-2 text-rose-500" />
            <p class="font-semibold text-sm">Gagal memuat log peristiwa</p>
            <p class="text-xs text-muted-foreground mt-1">Periksa koneksi jaringan atau hubungi administrator.</p>
          </div>

          <!-- Empty State -->
          <div v-else-if="!logsQuery.data.value || logsQuery.data.value.length === 0" class="py-16 text-center text-muted-foreground border border-dashed rounded-xl">
            <Bell class="w-8 h-8 mx-auto mb-2 opacity-40 text-primary" />
            <p class="font-semibold text-sm">Tidak ada log peristiwa yang ditemukan</p>
            <p class="text-xs text-muted-foreground mt-1">Belum ada aktivitas atau filter yang dipilih tidak memiliki rekaman.</p>
          </div>
          
          <!-- Log List -->
          <div v-else class="space-y-2.5">
            <div 
              v-for="log in logsQuery.data.value" 
              :key="log.id"
              class="flex items-start gap-3.5 p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-100/70 transition-colors"
            >
              <!-- Icon by Level -->
              <div class="shrink-0 mt-0.5">
                <div v-if="log.level === 'INFO'" class="w-7 h-7 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-600">
                  <Info class="w-4 h-4" />
                </div>
                <div v-else-if="log.level === 'WARNING'" class="w-7 h-7 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600">
                  <AlertTriangle class="w-4 h-4" />
                </div>
                <div v-else-if="log.level === 'ERROR'" class="w-7 h-7 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-600">
                  <XCircle class="w-4 h-4" />
                </div>
                <div v-else class="w-7 h-7 rounded-lg bg-slate-200 flex items-center justify-center text-slate-600">
                  <Info class="w-4 h-4" />
                </div>
              </div>
              
              <!-- Content -->
              <div class="flex-1 min-w-0 space-y-1">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <p class="font-semibold text-sm text-foreground break-words">
                    {{ log.message }}
                  </p>
                  <div class="flex items-center text-xs text-muted-foreground whitespace-nowrap shrink-0">
                    <Clock class="w-3 h-3 mr-1 text-primary" />
                    <span>{{ formatDate(log.created_at) }}</span>
                  </div>
                </div>

                <div class="flex items-center gap-2 pt-0.5">
                  <span 
                    :class="[
                      'text-[10px] font-bold px-2 py-0.2 rounded-full border uppercase tracking-wider',
                      log.level === 'INFO' ? 'bg-blue-500/10 text-blue-700 border-blue-500/30' :
                      log.level === 'WARNING' ? 'bg-amber-500/10 text-amber-700 border-amber-500/30' :
                      log.level === 'ERROR' ? 'bg-rose-500/10 text-rose-700 border-rose-500/30' :
                      'bg-slate-200 text-slate-700 border-slate-300'
                    ]"
                  >
                    {{ log.level }}
                  </span>

                  <!-- Human readable Node name / code (e.g. IoT Lab ELINS or NODE001) -->
                  <span 
                    v-if="log.node_name || log.node_code" 
                    class="text-[10px] font-medium text-slate-700 bg-white px-2 py-0.5 rounded-full border border-slate-200 shadow-none"
                  >
                    Node: <strong class="font-semibold text-foreground">{{ log.node_name || log.node_code }}</strong>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- ═══════════════ PAGINATION CONTROLS (25, 50, 100) ═══════════════ -->
          <div class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-3 border-t border-border/60 text-xs text-muted-foreground">
            
            <!-- Left: Items Info & Page Size Options -->
            <div class="flex flex-wrap items-center gap-3 w-full sm:w-auto justify-between sm:justify-start">
              <span>
                Menampilkan <strong class="text-foreground">{{ startItem }} - {{ endItem }}</strong> dari <strong class="text-foreground">{{ totalCount }}</strong> log
              </span>

              <!-- Page Size Selection (25, 50, 100) -->
              <div class="flex items-center gap-1.5">
                <span class="text-muted-foreground">Tampilkan:</span>
                <div class="flex items-center bg-slate-100 rounded-lg p-0.5 border border-slate-200">
                  <button
                    v-for="size in pageSizeOptions"
                    :key="size"
                    @click="pageSize = size"
                    :class="[
                      'px-2 py-0.5 rounded-md font-semibold text-xs transition-all cursor-pointer',
                      pageSize === size 
                        ? 'bg-white text-foreground border border-slate-200 shadow-none' 
                        : 'text-muted-foreground hover:text-foreground'
                    ]"
                  >
                    {{ size }}
                  </button>
                </div>
                <span>/ hal</span>
              </div>
            </div>

            <!-- Right: Pagination Navigation -->
            <div class="flex items-center gap-1">
              <!-- First Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-8 w-8 shadow-none border-border/80 hover:bg-slate-50 cursor-pointer"
                :disabled="currentPage <= 1 || logsQuery.isLoading.value"
                @click="changePage(1)"
                title="Halaman Pertama"
              >
                <ChevronsLeft class="w-3.5 h-3.5" />
              </Button>

              <!-- Previous Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-8 w-8 shadow-none border-border/80 hover:bg-slate-50 cursor-pointer"
                :disabled="currentPage <= 1 || logsQuery.isLoading.value"
                @click="changePage(currentPage - 1)"
                title="Halaman Sebelumnya"
              >
                <ChevronLeft class="w-3.5 h-3.5" />
              </Button>

              <!-- Page Number Buttons -->
              <template v-for="(p, idx) in visiblePages" :key="idx">
                <span v-if="p === '...'" class="px-1 text-slate-400 font-semibold">
                  ...
                </span>
                <button
                  v-else
                  @click="changePage(Number(p))"
                  :class="[
                    'h-8 min-w-[2rem] px-2 rounded-lg font-semibold text-xs transition-all cursor-pointer border',
                    currentPage === p 
                      ? 'bg-primary text-primary-foreground border-primary' 
                      : 'bg-white text-foreground border-border/80 hover:bg-slate-50'
                  ]"
                >
                  {{ p }}
                </button>
              </template>

              <!-- Next Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-8 w-8 shadow-none border-border/80 hover:bg-slate-50 cursor-pointer"
                :disabled="currentPage >= totalPages || logsQuery.isLoading.value"
                @click="changePage(currentPage + 1)"
                title="Halaman Selanjutnya"
              >
                <ChevronRight class="w-3.5 h-3.5" />
              </Button>

              <!-- Last Page -->
              <Button
                variant="outline"
                size="icon"
                class="h-8 w-8 shadow-none border-border/80 hover:bg-slate-50 cursor-pointer"
                :disabled="currentPage >= totalPages || logsQuery.isLoading.value"
                @click="changePage(totalPages)"
                title="Halaman Terakhir"
              >
                <ChevronsRight class="w-3.5 h-3.5" />
              </Button>
            </div>

          </div>

        </CardContent>
      </Card>
    </div>
  </DashboardLayout>
</template>

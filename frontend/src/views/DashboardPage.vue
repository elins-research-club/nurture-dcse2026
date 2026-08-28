<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import NodeDashboard from '@/components/dashboard/NodeDashboard.vue'
import DashboardPreloader from '@/components/ui/DashboardPreloader.vue'
import { useNodes } from '@/composables/useNodes'
import { useAuthStore } from '@/stores/auth'
import type { NodeDeviceWithData } from '@/types'
import { 
  Search, 
  MapPin, 
  Radio, 
  Check, 
  Plus, 
  Layers, 
  CornerDownLeft, 
  ChevronDown
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const { nodesQuery } = useNodes()

const nodes = ref<NodeDeviceWithData[]>([])
const selectedNodeId = ref<number | null>(null)

const isPaletteOpen = ref(false)
const searchQuery = ref('')
const searchInput = ref<HTMLInputElement | null>(null)
const highlightedIndex = ref(0)

// When API data loads, update local state
watch(() => nodesQuery.data.value, (newData) => {
  if (newData) {
    nodes.value = [...newData]
    if (!selectedNodeId.value && nodes.value.length > 0) {
      selectedNodeId.value = nodes.value[0].id
    }
  }
}, { immediate: true })

const activeNode = computed(() => {
  return nodes.value.find(n => n.id === selectedNodeId.value) || nodes.value[0] || null
})

const filteredNodes = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return nodes.value
  return nodes.value.filter(n => 
    (n.name || '').toLowerCase().includes(q) ||
    (n.node_id || '').toLowerCase().includes(q) ||
    (n.location || '').toLowerCase().includes(q)
  )
})

watch(isPaletteOpen, async (val) => {
  if (val) {
    searchQuery.value = ''
    const activeIdx = filteredNodes.value.findIndex(n => n.id === selectedNodeId.value)
    highlightedIndex.value = activeIdx >= 0 ? activeIdx : 0
    await nextTick()
    setTimeout(() => {
      searchInput.value?.focus()
    }, 50)
  }
})

watch(searchQuery, () => {
  highlightedIndex.value = 0
})

const openPalette = () => {
  isPaletteOpen.value = true
}

const closePalette = () => {
  isPaletteOpen.value = false
}

const selectNode = (node: NodeDeviceWithData) => {
  selectedNodeId.value = node.id
  closePalette()
}

// Global Keyboard Shortcut (Ctrl+K / Cmd+K)
const handleGlobalKeyDown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    isPaletteOpen.value = !isPaletteOpen.value
  } else if (e.key === 'Escape' && isPaletteOpen.value) {
    closePalette()
  }
}

// In-Palette Keyboard Navigation
const handleModalKeyDown = (e: KeyboardEvent) => {
  if (!isPaletteOpen.value || !filteredNodes.value.length) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    highlightedIndex.value = (highlightedIndex.value + 1) % filteredNodes.value.length
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    highlightedIndex.value = (highlightedIndex.value - 1 + filteredNodes.value.length) % filteredNodes.value.length
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const target = filteredNodes.value[highlightedIndex.value]
    if (target) {
      selectNode(target)
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeyDown)
})
</script>

<template>
  <DashboardLayout compactZoom>
    <!-- Public Mode Navbar Slot: Node Switcher Pill in Top Navigation (Blended BG with outline & shadow - Enlarged by 25%) -->
    <template #header-center v-if="!authStore.isAuthenticated() && nodes.length > 1">
      <button 
        type="button"
        @click="openPalette"
        class="inline-flex items-center justify-between gap-3.5 w-full max-w-md sm:max-w-xl px-5 py-2 rounded-2xl bg-transparent hover:bg-slate-500/5 dark:hover:bg-white/5 border border-border/90 hover:border-primary/50 transition-all duration-200 cursor-pointer shadow-xs hover:shadow-sm group min-h-[42px]"
        title="Klik atau tekan Ctrl+K untuk beralih stasiun"
      >
        <div class="flex items-center gap-2.5 min-w-0">
          <!-- Pulse Dot -->
          <div class="w-3.5 h-3.5 rounded-full bg-emerald-500 shadow-xs shadow-emerald-500/50 shrink-0"></div>
          
          <span class="font-extrabold text-sm sm:text-base text-foreground group-hover:text-primary transition-colors truncate">
            {{ activeNode?.name || 'Pilih Stasiun' }}
          </span>

          <span v-if="activeNode?.node_id" class="text-xs font-mono font-bold px-2 py-0.5 rounded-md bg-slate-100/80 dark:bg-slate-800/80 text-slate-700 dark:text-slate-200 border border-slate-200/90 dark:border-slate-700/90 shrink-0">
            {{ activeNode.node_id }}
          </span>

          <span v-if="activeNode?.location" class="hidden lg:inline-flex items-center gap-1.5 text-xs text-muted-foreground font-semibold shrink-0">
            <MapPin class="w-3.5 h-3.5 text-muted-foreground/80" />
            <span class="truncate max-w-[140px]">{{ activeNode.location }}</span>
          </span>
        </div>

        <div class="flex items-center gap-2 shrink-0">
          <ChevronDown class="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-transform" />
          <span class="hidden sm:inline-flex px-2 py-0.5 rounded-md bg-slate-100/80 dark:bg-slate-800/80 border border-slate-200/90 dark:border-slate-700/90 text-xs font-mono font-bold text-slate-600 dark:text-slate-300 group-hover:border-primary/40 group-hover:text-primary transition-colors">
            Ctrl K
          </span>
        </div>
      </button>
    </template>

    <div class="flex flex-col space-y-4">
      <!-- Loading State Preloader -->
      <DashboardPreloader v-if="nodesQuery.isLoading.value || nodesQuery.isPending.value || (!nodes.length && !nodesQuery.isError.value)" />
      
      <!-- Error State -->
      <div v-else-if="nodesQuery.isError.value" class="py-12 text-center text-destructive">
        Gagal memuat data. Silakan periksa koneksi jaringan.
      </div>
      
      <!-- No Data State -->
      <div v-else-if="!nodes.length" class="py-12 text-center text-muted-foreground border border-dashed rounded-xl">
        Tidak ada node ditemukan. Tambahkan node untuk memulai pemantauan.
      </div>
      
      <template v-else>
        <!-- Authenticated Admin Mode: In-Body Trigger Bar (Only shown when logged in and > 1 node) -->
        <div v-if="authStore.isAuthenticated() && nodes.length > 1" class="flex items-center justify-between gap-3 flex-wrap">
          <button 
            type="button"
            @click="openPalette"
            class="inline-flex items-center gap-3 px-3.5 py-2 rounded-2xl bg-white dark:bg-card border border-border/90 hover:border-primary/50 hover:bg-slate-50 dark:hover:bg-slate-900/60 transition-all duration-200 cursor-pointer shadow-2xs group"
            title="Klik atau tekan Ctrl+K untuk beralih stasiun"
          >
            <!-- Station Live Indicator Dot -->
            <div class="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-xs shadow-emerald-500/50 shrink-0"></div>

            <!-- Node Details -->
            <div class="flex items-center gap-2 text-left">
              <span class="font-extrabold text-sm text-foreground group-hover:text-primary transition-colors">
                {{ activeNode?.name || 'Pilih Stasiun' }}
              </span>
              
              <span v-if="activeNode?.node_id" class="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                {{ activeNode.node_id }}
              </span>

              <span v-if="activeNode?.location" class="hidden sm:inline-flex items-center gap-1 text-[11px] text-muted-foreground font-medium">
                <MapPin class="w-3 h-3 text-muted-foreground/80" />
                <span>{{ activeNode.location }}</span>
              </span>
            </div>

            <ChevronDown class="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground transition-transform" />

            <!-- Shortcut Pill Badge -->
            <div class="hidden sm:inline-flex items-center gap-1 ml-1 px-2 py-0.5 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[10px] font-mono font-bold text-slate-500 dark:text-slate-400 group-hover:border-primary/40 group-hover:text-primary transition-colors">
              <span>Ctrl</span>
              <span>K</span>
            </div>
          </button>

          <!-- Subtitle / Total Nodes Counter -->
          <div class="hidden md:flex items-center gap-2 text-xs text-muted-foreground font-medium">
            <Radio class="w-3.5 h-3.5 text-primary" />
            <span>{{ nodes.length }} Stasiun Terhubung di Lapangan</span>
          </div>
        </div>
        
        <!-- Active Node Dashboard Component -->
        <div v-if="activeNode">
          <NodeDashboard :node-id="activeNode.node_id" :node-name="activeNode.name" />
        </div>

        <!-- Spotlight Command Palette Modal (Teleported to body) -->
        <Teleport to="body">
          <div 
            v-if="isPaletteOpen" 
            class="fixed inset-0 z-50 flex items-start justify-center p-4 sm:p-6 sm:pt-20 bg-slate-950/60 backdrop-blur-sm transition-all"
            @click="closePalette"
          >
            <div 
              class="w-full max-w-xl rounded-2xl bg-white dark:bg-slate-900 border border-border/80 shadow-2xl overflow-hidden flex flex-col max-h-[80vh] animate-in zoom-in-95 duration-150"
              @click.stop
              @keydown="handleModalKeyDown"
            >
              <!-- Search Header Input -->
              <div class="relative border-b border-border/80 px-4 py-3.5 flex items-center gap-3 bg-slate-50/50 dark:bg-slate-900/50">
                <Search class="w-4 h-4 text-muted-foreground shrink-0" />
                <input 
                  ref="searchInput"
                  v-model="searchQuery"
                  type="text" 
                  placeholder="Cari stasiun node berdasarkan nama, ID, atau lokasi..."
                  class="w-full bg-transparent text-sm font-semibold text-foreground placeholder:text-muted-foreground/60 focus:outline-none"
                />
                <button 
                  type="button"
                  @click="closePalette" 
                  class="px-1.5 py-0.5 rounded-md bg-slate-200 dark:bg-slate-800 text-[10px] font-mono font-bold text-muted-foreground hover:text-foreground cursor-pointer"
                >
                  ESC
                </button>
              </div>

              <!-- Node List Body -->
              <div class="p-2 overflow-y-auto space-y-1 divide-y-0">
                <div class="px-2.5 py-1.5 flex items-center justify-between text-[10px] font-mono font-bold tracking-wider text-muted-foreground uppercase">
                  <span>Daftar Node Lapangan</span>
                  <span class="text-primary">{{ filteredNodes.length }} Stasiun</span>
                </div>

                <!-- Empty State -->
                <div v-if="!filteredNodes.length" class="py-12 text-center text-muted-foreground space-y-2">
                  <Layers class="w-8 h-8 mx-auto text-muted-foreground/40" />
                  <p class="text-xs font-semibold">Tidak ada stasiun node yang cocok dengan pencarian "{{ searchQuery }}".</p>
                </div>

                <!-- List Items -->
                <div 
                  v-for="(node, index) in filteredNodes"
                  :key="node.id"
                  @click="selectNode(node)"
                  @mouseenter="highlightedIndex = index"
                  :class="[
                    'p-3 rounded-xl flex items-center justify-between cursor-pointer transition-all duration-150',
                    highlightedIndex === index 
                      ? 'bg-slate-100 dark:bg-slate-800/80 border border-primary/30 shadow-2xs' 
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/40 border border-transparent',
                    node.id === selectedNodeId ? 'bg-primary/5 dark:bg-primary/10 border-primary/20' : ''
                  ]"
                >
                  <div class="flex items-center gap-3">
                    <!-- Dot Indicator -->
                    <div class="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-xs shrink-0"></div>

                    <div>
                      <div class="flex items-center gap-2">
                        <span class="font-extrabold text-xs sm:text-sm text-foreground">
                          {{ node.name }}
                        </span>
                        <span class="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                          {{ node.node_id }}
                        </span>
                      </div>
                      
                      <div class="flex items-center gap-2 text-[11px] text-muted-foreground mt-0.5 font-medium">
                        <span v-if="node.location" class="flex items-center gap-1">
                          <MapPin class="w-3 h-3 text-muted-foreground/70" />
                          <span>{{ node.location }}</span>
                        </span>
                        <span v-else>Lokasi belum diatur</span>
                      </div>
                    </div>
                  </div>

                  <!-- Active Badge or Select Indicator -->
                  <div class="flex items-center gap-2">
                    <div v-if="node.id === selectedNodeId" class="flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-bold text-xs">
                      <Check class="w-3.5 h-3.5" />
                      <span>Aktif</span>
                    </div>
                    <div v-else-if="highlightedIndex === index" class="hidden sm:flex items-center gap-1 text-[10px] font-mono text-muted-foreground">
                      <span>Pilih</span>
                      <CornerDownLeft class="w-3 h-3" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Footer Guidance -->
              <div class="px-4 py-2.5 border-t border-border/80 bg-slate-50 dark:bg-slate-900/60 flex items-center justify-between text-xs text-muted-foreground">
                <div class="hidden sm:flex items-center gap-3 text-[11px] font-mono">
                  <span class="flex items-center gap-1">
                    <kbd class="px-1 rounded bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px]">↑↓</kbd> Navigasi
                  </span>
                  <span class="flex items-center gap-1">
                    <kbd class="px-1 rounded bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px]">↵</kbd> Pilih
                  </span>
                  <span class="flex items-center gap-1">
                    <kbd class="px-1 rounded bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-[10px]">ESC</kbd> Tutup
                  </span>
                </div>

                <a 
                  href="/nodes"
                  @click="closePalette"
                  class="font-bold text-primary hover:underline text-xs flex items-center gap-1 cursor-pointer ml-auto"
                >
                  <Plus class="w-3.5 h-3.5" />
                  <span>Kelola Seluruh Node Lapangan</span>
                </a>
              </div>

            </div>
          </div>
        </Teleport>
      </template>
    </div>
  </DashboardLayout>
</template>

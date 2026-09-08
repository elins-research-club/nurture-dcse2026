<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LayoutDashboard, Network, Settings, LogOut, ChevronLeft, ChevronRight, ScrollText, MapPin, BookmarkCheck, Trash2 } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

const props = defineProps<{ collapsed: boolean }>()
const emit = defineEmits(['update:collapsed'])

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isLogoutModalOpen = ref(false)

const toggleCollapse = () => {
  emit('update:collapsed', !props.collapsed)
}

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Alat IoT', path: '/nodes', icon: Network },
  { name: 'Peta Lahan', path: '/map', icon: MapPin },
  { name: 'Logs & Ekspor Data', path: '/logs', icon: ScrollText },
  { name: 'Pengaturan', path: '/settings', icon: Settings },
]

const navigate = (path: string) => {
  router.push(path)
}

const handleSoftLogout = () => {
  isLogoutModalOpen.value = false
  authStore.logout(false)
}

const handleFullLogout = () => {
  isLogoutModalOpen.value = false
  authStore.logout(true)
}

const isActive = (path: string) => {
  if (path === '/nodes' && route.path.startsWith('/nodes')) return true
  if (path === '/logs' && (route.path.startsWith('/logs') || route.path.startsWith('/alerts'))) return true
  return route.path === path
}
</script>

<template>
  <aside :class="[
    'hidden md:flex border-r border-border/80 bg-white dark:bg-card flex-col h-screen fixed left-0 top-0 shadow-none z-40 transition-[width] duration-300 ease-in-out overflow-hidden select-none',
    collapsed ? 'w-[68px]' : 'w-[230px]'
  ]">
    <div 
      class="h-20 flex items-center border-b border-border/60 relative whitespace-nowrap overflow-hidden px-3.5"
    >
      <button 
        @click="toggleCollapse"
        class="w-11 h-11 flex items-center justify-center shrink-0 cursor-pointer group focus:outline-none select-none" 
        title="Toggle Sidebar"
      >
        <img 
          src="/logo-icon.webp" 
          alt="G-CONNECT Logo" 
          class="w-8 h-8 object-contain shrink-0 transition-all duration-300 ease-out group-hover:drop-shadow-[0_0_12px_rgba(239,68,68,0.75)] group-hover:scale-105 group-active:scale-95" 
        />
      </button>

      <div 
        class="overflow-hidden transition-opacity duration-200 ease-in-out ml-3 min-w-0"
        :class="collapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'"
      >
        <h1 class="text-xl font-extrabold text-foreground tracking-tight whitespace-nowrap">
          G-CONNECT
        </h1>
      </div>
    </div>

    <!-- Navigation links -->
    <nav class="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto overflow-x-hidden">
      <button
        v-for="item in navItems"
        :key="item.path"
        @click="navigate(item.path)"
        :class="[
          'w-full flex items-center h-11 px-3 rounded-xl font-medium transition-colors duration-150 relative group cursor-pointer text-left overflow-hidden',
          isActive(item.path)
            ? 'bg-primary/10 text-primary font-semibold'
            : 'text-muted-foreground hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-foreground'
        ]"
        :title="collapsed ? item.name : undefined"
      >
        <div 
          v-if="isActive(item.path)" 
          class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full"
        ></div>
        <div class="w-5 h-5 flex items-center justify-center shrink-0">
          <component :is="item.icon" class="w-5 h-5" />
        </div>
        <span 
          class="whitespace-nowrap transition-opacity duration-200 ease-in-out text-sm ml-3 overflow-hidden"
          :class="collapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'"
        >
          {{ item.name }}
        </span>
      </button>
    </nav>

    <!-- Logout section -->
    <div class="p-3 border-t border-border/60">
      <button
        @click="isLogoutModalOpen = true"
        class="w-full flex items-center h-11 px-3 rounded-xl font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors duration-150 group cursor-pointer overflow-hidden"
        :title="collapsed ? 'Logout' : undefined"
      >
        <div class="w-5 h-5 flex items-center justify-center shrink-0">
          <LogOut class="w-5 h-5" />
        </div>
        <span 
          class="whitespace-nowrap transition-opacity duration-200 ease-in-out text-sm ml-3 overflow-hidden"
          :class="collapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'"
        >
          Logout
        </span>
      </button>
    </div>
  </aside>

  <!-- Logout Confirmation Dialog -->
  <Dialog :open="isLogoutModalOpen" @update:open="isLogoutModalOpen = $event">
    <DialogContent class="sm:max-w-[420px] p-6 rounded-2xl border border-border/80 shadow-2xl bg-white dark:bg-card">
      <div class="flex flex-col items-center pt-2">
        <!-- Large Centered Logout Icon with Soft Glow Ring -->
        <div class="w-16 h-16 sm:w-18 sm:h-18 rounded-2xl bg-rose-500/10 dark:bg-rose-500/20 border border-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400 mb-4 shadow-inner">
          <LogOut class="w-8 h-8 sm:w-9 sm:h-9" />
        </div>

        <DialogHeader class="text-center sm:text-center space-y-1.5 w-full">
          <DialogTitle class="text-lg sm:text-xl font-extrabold text-foreground tracking-tight text-center">
            {{ authStore.isRemembered ? 'Pilihan Keluar Sesi' : 'Konfirmasi Logout' }}
          </DialogTitle>
          <DialogDescription class="text-xs sm:text-sm text-muted-foreground text-center leading-relaxed font-medium">
            <template v-if="authStore.isRemembered">
              Akun Anda saat ini tersimpan di peramban ini. Silakan tentukan metode keluar sesi:
            </template>
            <template v-else>
              Apakah Anda yakin ingin keluar dari sesi sistem monitoring <strong class="text-foreground font-bold">G-CONNECT</strong>?
            </template>
          </DialogDescription>
        </DialogHeader>

        <!-- Remembered Session Action Choices -->
        <div v-if="authStore.isRemembered" class="w-full space-y-2.5 mt-6">
          <!-- Choice 1: Soft Logout (Keep Remembered) -->
          <button
            @click="handleSoftLogout"
            class="w-full p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10 dark:bg-emerald-500/10 dark:hover:bg-emerald-500/15 text-left transition-all cursor-pointer group flex items-center gap-3 active:scale-[0.99]"
          >
            <div class="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0">
              <BookmarkCheck class="w-4 h-4" />
            </div>
            <p class="text-xs sm:text-sm font-bold text-foreground group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
              Logout Saja (Tetap Ingat Saya)
            </p>
          </button>

          <!-- Choice 2: Full Logout (Wipe All) -->
          <button
            @click="handleFullLogout"
            class="w-full p-3 rounded-xl border border-rose-500/30 bg-rose-500/5 hover:bg-rose-500/10 dark:bg-rose-500/10 dark:hover:bg-rose-500/15 text-left transition-all cursor-pointer group flex items-center gap-3 active:scale-[0.99]"
          >
            <div class="w-8 h-8 rounded-lg bg-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400 shrink-0">
              <Trash2 class="w-4 h-4" />
            </div>
            <p class="text-xs sm:text-sm font-bold text-rose-600 dark:text-rose-400">
              Logout & Hapus Kredensial
            </p>
          </button>

          <Button 
            variant="ghost" 
            size="sm"
            class="w-full h-8 text-xs font-semibold text-muted-foreground hover:text-foreground cursor-pointer mt-1"
            @click="isLogoutModalOpen = false"
          >
            Batal
          </Button>
        </div>

        <!-- Normal Standard Logout Actions -->
        <div v-else class="grid grid-cols-2 gap-3 w-full mt-6">
          <Button 
            variant="outline" 
            class="h-10 rounded-xl font-bold border-border/80 hover:bg-slate-100 dark:hover:bg-slate-800 text-foreground cursor-pointer text-xs sm:text-sm transition-all"
            @click="isLogoutModalOpen = false"
          >
            Batal
          </Button>
          <Button 
            variant="destructive" 
            class="h-10 rounded-xl font-bold bg-rose-600 hover:bg-rose-700 text-white shadow-sm cursor-pointer text-xs sm:text-sm gap-1.5 transition-all"
            @click="handleFullLogout"
          >
            <LogOut class="w-4 h-4" />
            <span>Logout</span>
          </Button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

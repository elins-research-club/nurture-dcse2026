<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LayoutDashboard, Network, Settings, LogOut, ChevronLeft, ChevronRight, Bell, MapPin } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ref } from 'vue'

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
  { name: 'Nodes', path: '/nodes', icon: Network },
  { name: 'Map', path: '/map', icon: MapPin },
  { name: 'Alerts', path: '/alerts', icon: Bell },
  { name: 'Settings', path: '/settings', icon: Settings },
]

const navigate = (path: string) => {
  router.push(path)
}

const confirmLogout = () => {
  isLogoutModalOpen.value = false
  authStore.logout()
  router.push('/dashboard')
}

const isActive = (path: string) => {
  if (path === '/nodes' && route.path.startsWith('/nodes')) return true
  return route.path === path
}
</script>

<template>
  <aside :class="[
    'border-r border-border/80 bg-white dark:bg-card flex flex-col h-screen fixed left-0 top-0 shadow-none z-40 transition-all duration-300 ease-in-out',
    collapsed ? 'w-[68px]' : 'w-64'
  ]">
    <div 
      class="h-20 flex items-center border-b border-border/60 relative whitespace-nowrap overflow-hidden"
      :class="collapsed ? 'justify-center px-0' : 'px-5'"
    >
      <button 
        @click="toggleCollapse"
        class="w-10 h-10 flex items-center justify-center shrink-0 cursor-pointer transition-transform duration-200 active:scale-95" 
        title="Toggle Sidebar"
      >
        <img src="/logo-icon.webp" alt="G-CONNECT Logo" class="w-8 h-8 object-contain" />
      </button>

      <h1 
        v-if="!collapsed"
        class="text-xl font-extrabold text-foreground tracking-tight ml-3 whitespace-nowrap"
      >
        G-CONNECT
      </h1>
    </div>

    <!-- Navigation links -->
    <nav class="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto overflow-x-hidden">
      <button
        v-for="item in navItems"
        :key="item.path"
        @click="navigate(item.path)"
        :class="[
          'w-full flex items-center gap-3.5 px-3 py-3 rounded-xl font-medium transition-colors duration-200 relative group cursor-pointer text-left',
          isActive(item.path)
            ? 'bg-primary/10 text-primary font-semibold'
            : 'text-muted-foreground hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-foreground'
        ]"
      >
        <div 
          v-if="isActive(item.path)" 
          class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full"
        ></div>
        <component :is="item.icon" class="w-5 h-5 shrink-0" />
        <span 
          class="whitespace-nowrap transition-all duration-200 text-sm"
          :class="collapsed ? 'opacity-0 translate-x-4 pointer-events-none' : 'opacity-100 translate-x-0'"
        >
          {{ item.name }}
        </span>
      </button>
    </nav>

    <!-- Logout section -->
    <div class="p-3 border-t border-border/60">
      <button
        @click="isLogoutModalOpen = true"
        class="w-full flex items-center gap-3.5 px-3 py-3 rounded-xl font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors duration-200 group cursor-pointer"
      >
        <LogOut class="w-5 h-5 shrink-0" />
        <span 
          class="whitespace-nowrap transition-all duration-200 text-sm"
          :class="collapsed ? 'opacity-0 translate-x-4 pointer-events-none' : 'opacity-100 translate-x-0'"
        >
          Logout
        </span>
      </button>
    </div>
  </aside>

  <!-- Logout Confirmation Dialog -->
  <Dialog :open="isLogoutModalOpen" @update:open="isLogoutModalOpen = $event">
    <DialogContent class="sm:max-w-[380px] p-6 rounded-2xl border border-border/80 shadow-2xl bg-white dark:bg-card">
      <div class="flex flex-col items-center pt-2">
        <!-- Large Centered Logout Icon with Soft Glow Ring -->
        <div class="w-16 h-16 sm:w-18 sm:h-18 rounded-2xl bg-rose-500/10 dark:bg-rose-500/20 border border-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400 mb-4 shadow-inner">
          <LogOut class="w-8 h-8 sm:w-9 sm:h-9" />
        </div>

        <DialogHeader class="text-center sm:text-center space-y-1.5 w-full">
          <DialogTitle class="text-lg sm:text-xl font-extrabold text-foreground tracking-tight text-center">
            Konfirmasi Logout
          </DialogTitle>
          <DialogDescription class="text-xs sm:text-sm text-muted-foreground text-center leading-relaxed font-medium">
            Apakah Anda yakin ingin keluar dari sesi sistem monitoring <strong class="text-foreground font-bold">G-CONNECT</strong>?
          </DialogDescription>
        </DialogHeader>

        <!-- Action Buttons -->
        <div class="grid grid-cols-2 gap-3 w-full mt-6">
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
            @click="confirmLogout"
          >
            <LogOut class="w-4 h-4" />
            <span>Logout</span>
          </Button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

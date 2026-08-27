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
  authStore.logout()
}

const isActive = (path: string) => {
  if (path === '/nodes' && route.path.startsWith('/nodes')) return true
  return route.path === path
}
</script>

<template>
  <aside :class="[
    'border-r border-border/80 bg-white dark:bg-card flex flex-col h-screen fixed left-0 top-0 shadow-none z-40 transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]',
    collapsed ? 'w-20' : 'w-64'
  ]">
    <div class="h-20 flex items-center border-b border-border/60 relative px-5 whitespace-nowrap overflow-hidden">
      <button 
        @click="toggleCollapse"
        class="w-10 h-10 flex items-center justify-center shrink-0 cursor-pointer hover:scale-105 active:scale-95 transition-transform duration-300" 
        title="Toggle Sidebar"
      >
        <img src="/logo-icon.webp" alt="G-CONNECT Logo" class="w-8 h-8 object-contain" />
      </button>

      <h1 
        class="text-xl font-extrabold text-foreground tracking-tight ml-3 transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] overflow-hidden" 
        :class="collapsed ? 'opacity-0 max-w-0 scale-90 translate-x-2' : 'opacity-100 max-w-[150px] scale-100 translate-x-0'"
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
          'w-full flex items-center gap-3.5 px-3.5 py-3 rounded-xl font-medium transition-all duration-300 relative group cursor-pointer text-left',
          isActive(item.path)
            ? 'bg-primary/10 text-primary font-semibold'
            : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
        ]"
      >
        <div 
          v-if="isActive(item.path)" 
          class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary rounded-r-full"
        ></div>
        <component :is="item.icon" class="w-5 h-5 shrink-0 transition-transform duration-300 group-hover:scale-110" />
        <span 
          class="whitespace-nowrap transition-all duration-300 text-sm"
          :class="collapsed ? 'opacity-0 translate-x-4 pointer-events-none' : 'opacity-100 translate-x-0'"
        >
          {{ item.name }}
        </span>
      </button>
    </nav>

    <!-- Logout section -->
    <div class="p-4 border-t border-border/60">
      <button
        @click="isLogoutModalOpen = true"
        class="w-full flex items-center gap-3.5 px-3.5 py-3 rounded-xl font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all duration-300 group cursor-pointer"
      >
        <LogOut class="w-5 h-5 shrink-0 transition-transform duration-300 group-hover:-translate-x-1" />
        <span 
          class="whitespace-nowrap transition-all duration-300 text-sm"
          :class="collapsed ? 'opacity-0 translate-x-4 pointer-events-none' : 'opacity-100 translate-x-0'"
        >
          Logout
        </span>
      </button>
    </div>
  </aside>

  <!-- Logout Confirmation Dialog -->
  <Dialog :open="isLogoutModalOpen" @update:open="isLogoutModalOpen = $event">
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Konfirmasi Logout</DialogTitle>
      </DialogHeader>
      <div class="py-4">
        <p class="text-sm text-muted-foreground">Apakah Anda yakin ingin keluar dari sistem G-CONNECT?</p>
      </div>
      <DialogFooter class="flex gap-2 justify-end">
        <Button variant="outline" @click="isLogoutModalOpen = false">Batal</Button>
        <Button variant="destructive" @click="confirmLogout">Logout</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

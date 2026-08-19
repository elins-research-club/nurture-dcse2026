<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LayoutDashboard, Network, Settings, LogOut, ChevronLeft, ChevronRight, Leaf, Bell } from 'lucide-vue-next'
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
    'border-r border-border/50 bg-background/80 backdrop-blur-xl flex flex-col h-screen fixed left-0 top-0 shadow-[4px_0_24px_rgba(0,0,0,0.02)] dark:shadow-[4px_0_24px_rgba(0,0,0,0.2)] z-40 transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]',
    collapsed ? 'w-20' : 'w-64'
  ]">
    <div class="h-20 flex items-center border-b border-border/50 relative px-5 whitespace-nowrap overflow-hidden">
      <button 
        @click="toggleCollapse"
        class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-emerald-600 flex items-center justify-center shadow-lg shadow-primary/20 shrink-0 cursor-pointer hover:scale-105 transition-transform" 
        title="Toggle Sidebar"
      >
        <Leaf class="w-5 h-5 text-primary-foreground" />
      </button>
      <h1 class="text-xl font-extrabold text-foreground tracking-tight ml-3 transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] overflow-hidden" :class="collapsed ? 'opacity-0 max-w-0 scale-90 translate-x-2' : 'opacity-100 max-w-[150px] scale-100 translate-x-0'">
        G-CONNECT
      </h1>
    </div>
    
    <nav class="flex-1 px-3 py-6 space-y-2 overflow-y-auto overflow-x-hidden">
      <button
        v-for="item in navItems"
        :key="item.path"
        @click="navigate(item.path)"
        class="w-full flex items-center rounded-2xl text-sm font-medium transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] relative group border border-transparent p-2"
        :class="[
          isActive(item.path) 
            ? 'text-primary bg-gradient-to-b from-primary/20 to-primary/5 font-semibold' 
            : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
        ]"
      >
        <div class="w-10 h-10 flex shrink-0 items-center justify-center">
          <component :is="item.icon" class="w-5 h-5 relative z-10" :class="isActive(item.path) ? 'text-primary' : ''" />
        </div>
        <span class="relative z-10 whitespace-nowrap transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] overflow-hidden text-left pl-2" :class="collapsed ? 'opacity-0 max-w-0 scale-90 translate-x-2' : 'opacity-100 max-w-[150px] scale-100 translate-x-0'">{{ item.name }}</span>
      </button>
    </nav>
    
    <div class="p-4 border-t border-border/50 overflow-hidden whitespace-nowrap">
      <button
        @click="isLogoutModalOpen = true"
        class="w-full flex items-center rounded-xl text-sm font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors group p-2"
      >
        <div class="w-8 h-8 flex shrink-0 items-center justify-center">
          <LogOut class="w-4 h-4 transition-transform group-hover:-translate-x-1" />
        </div>
        <span class="overflow-hidden whitespace-nowrap transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] text-left pl-2" :class="collapsed ? 'opacity-0 max-w-0 scale-90 translate-x-2' : 'opacity-100 max-w-[150px] scale-100 translate-x-0'">Logout</span>
      </button>
    </div>

    <!-- Logout Confirmation Modal -->
    <Dialog v-model:open="isLogoutModalOpen">
      <DialogContent class="sm:max-w-md p-6 aspect-[4/3] flex flex-col">
        <DialogHeader class="text-center sm:text-center">
          <DialogTitle class="text-destructive w-full">Log out of G-CONNECT?</DialogTitle>
        </DialogHeader>
        <div class="flex-1 py-6 text-sm text-muted-foreground flex flex-col items-center justify-center gap-6">
          <div class="w-24 h-24 rounded-full bg-destructive/10 flex items-center justify-center shrink-0">
            <LogOut class="w-12 h-12 text-destructive" />
          </div>
          <div class="text-center px-4">
            You will need to sign in again to access the dashboard and manage your smart farming nodes.
          </div>
        </div>
        <DialogFooter class="gap-2 sm:gap-0 mt-0 mt-auto">
          <Button variant="outline" @click="isLogoutModalOpen = false" class="w-full sm:w-auto">Cancel</Button>
          <Button variant="destructive" @click="confirmLogout" class="w-full sm:w-auto">
            Log out
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </aside>
</template>

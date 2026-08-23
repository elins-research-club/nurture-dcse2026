<script setup lang="ts">
import { useLocalStorage } from '@vueuse/core'
import Sidebar from './Sidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'

const props = defineProps<{
  noPadding?: boolean
}>()

const isCollapsed = useLocalStorage('sidebar-collapsed', false)
const authStore = useAuthStore()
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col">
    <header v-if="!authStore.isAuthenticated()" class="sticky top-0 z-50 w-full border-b bg-background/95 p-4 flex justify-between items-center">
      <div class="font-bold">G-CONNECT</div>
      <Button size="sm" @click="$router.push('/login')">Login</Button>
    </header>

    <div class="flex flex-1">
      <Sidebar v-if="authStore.isAuthenticated()" v-model:collapsed="isCollapsed" />
      <main :class="[
        'flex-1 transition-all duration-300',
        !props.noPadding ? 'p-6 overflow-y-auto' : 'overflow-hidden flex flex-col',
        authStore.isAuthenticated() ? (isCollapsed ? 'ml-20' : 'ml-64') : 'ml-0'
      ]">
        <slot />
      </main>
    </div>
  </div>
</template>

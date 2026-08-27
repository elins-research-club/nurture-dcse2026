<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  noPadding?: boolean
}>()

const isCollapsed = ref(true)
const authStore = useAuthStore()
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col font-sans">
    <!-- Clean Minimalist Sidebar -->
    <Sidebar 
      v-if="authStore.isAuthenticated()" 
      :collapsed="isCollapsed" 
      @update:collapsed="isCollapsed = $event" 
    />

    <!-- Main Content Container with dynamic left margin matching Sidebar state -->
    <div class="flex-1 flex flex-col min-w-0 transition-all duration-300">
      <main :class="[
        'flex-1 transition-all duration-300 bg-background',
        !props.noPadding ? 'p-6 overflow-y-auto' : 'overflow-hidden flex flex-col',
        authStore.isAuthenticated() ? (isCollapsed ? 'ml-20' : 'ml-64') : 'ml-0'
      ]">
        <slot />
      </main>
    </div>
  </div>
</template>

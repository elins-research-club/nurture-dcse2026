<script setup lang="ts">
import { useLocalStorage } from '@vueuse/core'
import Sidebar from './Sidebar.vue'

const isCollapsed = useLocalStorage('sidebar-collapsed', false)
</script>

<template>
  <div class="min-h-screen bg-background flex">
    <Sidebar v-model:collapsed="isCollapsed" />
    <main :class="['flex-1 p-6 overflow-y-auto min-h-screen transition-all duration-300', isCollapsed ? 'ml-20' : 'ml-64']">
      <slot />
    </main>
  </div>
</template>

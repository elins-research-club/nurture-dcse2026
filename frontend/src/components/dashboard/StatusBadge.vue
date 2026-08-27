<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  isActive: boolean
  lastSeen?: string
}>()

const status = computed(() => {
  if (!props.isActive) return 'offline'
  if (!props.lastSeen) return 'online'
  
  try {
    const dateStr = props.lastSeen.endsWith('Z') ? props.lastSeen : props.lastSeen + 'Z'
    const lastSeenDate = new Date(dateStr)
    const now = new Date()
    const diffMinutes = (now.getTime() - lastSeenDate.getTime()) / (1000 * 60)
    
    if (diffMinutes > 15) return 'offline'
    if (diffMinutes > 5) return 'warning'
    return 'online'
  } catch {
    return props.isActive ? 'online' : 'offline'
  }
})

const badgeClass = computed(() => {
  switch (status.value) {
    case 'online':
      return 'bg-emerald-500/15 border-emerald-500/30 text-emerald-700 dark:text-emerald-400'
    case 'warning':
      return 'bg-amber-500/15 border-amber-500/30 text-amber-700 dark:text-amber-400'
    case 'offline':
      return 'bg-rose-500/15 border-rose-500/30 text-rose-700 dark:text-rose-400'
    default:
      return 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
  }
})

const dotClass = computed(() => {
  switch (status.value) {
    case 'online':
      return 'bg-emerald-500 animate-pulse'
    case 'warning':
      return 'bg-amber-500'
    case 'offline':
      return 'bg-rose-500'
    default:
      return 'bg-slate-400'
  }
})

const label = computed(() => {
  switch (status.value) {
    case 'online': return 'Online'
    case 'warning': return 'Delayed'
    case 'offline': return 'Offline'
    default: return 'Offline'
  }
})
</script>

<template>
  <div :class="['inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold border transition-colors shadow-none', badgeClass]">
    <!-- Micro Animation Pulse Dot Container -->
    <span class="relative flex h-2 w-2 items-center justify-center shrink-0">
      <!-- Expanding Ripple Wave (Active during Online/Warning) -->
      <span 
        v-if="status === 'online'" 
        class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"
      ></span>
      <span 
        v-else-if="status === 'warning'" 
        class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"
      ></span>
      <!-- Core Solid Dot -->
      <span :class="['relative inline-flex rounded-full h-1.5 w-1.5', dotClass]"></span>
    </span>
    <span>{{ label }}</span>
  </div>
</template>

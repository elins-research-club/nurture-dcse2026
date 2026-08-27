<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  isActive: boolean
  lastSeen?: string
}>()

const status = computed(() => {
  if (!props.isActive) return 'offline'
  if (!props.lastSeen) return 'unknown'
  
  const lastSeenDate = new Date(props.lastSeen.endsWith('Z') ? props.lastSeen : props.lastSeen + 'Z')
  const now = new Date()
  const diffMinutes = (now.getTime() - lastSeenDate.getTime()) / (1000 * 60)
  
  if (diffMinutes > 15) return 'offline'
  if (diffMinutes > 5) return 'warning'
  return 'online'
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
      return 'bg-slate-100 border-slate-200 text-slate-600'
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
    default: return 'Unknown'
  }
})
</script>

<template>
  <div :class="['inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border transition-colors shadow-none', badgeClass]">
    <div :class="['w-1.5 h-1.5 rounded-full', dotClass]" />
    <span>{{ label }}</span>
  </div>
</template>

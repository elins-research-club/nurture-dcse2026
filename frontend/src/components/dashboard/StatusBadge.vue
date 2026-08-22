<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from '@/components/ui/badge'

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

const variant = computed(() => {
  switch (status.value) {
    case 'online': return 'success'
    case 'warning': return 'warning'
    case 'offline': return 'destructive'
    default: return 'secondary'
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
  <Badge :variant="variant">{{ label }}</Badge>
</template>

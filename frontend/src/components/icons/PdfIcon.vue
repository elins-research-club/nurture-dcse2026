<script setup lang="ts">
import { cn } from '@/lib/utils'

defineProps<{
  class?: string
}>()
</script>

<template>
  <img 
    src="/pdf-icon.svg" 
    alt="PDF Icon" 
    :class="cn('w-6 h-6 object-contain shrink-0', $props.class)" 
  />
</template>

<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <div
    :class="
      cn(
        'rounded-2xl border border-border/80 bg-white dark:bg-card text-card-foreground shadow-none',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>

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
        'rounded-2xl border border-border/50 bg-card/90 backdrop-blur-xl text-card-foreground shadow-sm dark:shadow-[0_4px_24px_rgba(0,0,0,0.2)]',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>

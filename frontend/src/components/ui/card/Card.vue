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
        'rounded-2xl border border-border/80 bg-white dark:bg-card text-card-foreground shadow-[inset_0_1px_1px_rgba(255,255,255,0.9),0_2px_8px_-2px_rgba(0,0,0,0.04)] dark:shadow-[inset_0_1px_1px_rgba(255,255,255,0.06),0_2px_8px_-2px_rgba(0,0,0,0.3)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[inset_0_1px_1px_rgba(255,255,255,1),0_8px_24px_-4px_rgba(0,0,0,0.07)] dark:hover:shadow-[inset_0_1px_1px_rgba(255,255,255,0.1),0_8px_24px_-4px_rgba(0,0,0,0.4)]',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>

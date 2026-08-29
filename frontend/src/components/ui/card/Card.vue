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
        'rounded-2xl border border-white/80 dark:border-white/10 ring-1 ring-slate-900/5 dark:ring-white/5 bg-white/80 dark:bg-slate-900/80 backdrop-blur-2xl backdrop-saturate-150 text-card-foreground shadow-[inset_0_1.5px_0_0_rgba(255,255,255,1),inset_0_0_20px_0_rgba(255,255,255,0.35),0_6px_24px_-4px_rgba(15,23,42,0.07)] dark:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.12),inset_0_0_20px_0_rgba(255,255,255,0.02),0_6px_24px_-4px_rgba(0,0,0,0.35)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[inset_0_1.5px_0_0_rgba(255,255,255,1),inset_0_0_24px_0_rgba(255,255,255,0.5),0_12px_32px_-4px_rgba(15,23,42,0.1)] dark:hover:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.18),0_12px_32px_-4px_rgba(0,0,0,0.45)]',
        props.class,
      )
    "
  >
    <slot />
  </div>
</template>

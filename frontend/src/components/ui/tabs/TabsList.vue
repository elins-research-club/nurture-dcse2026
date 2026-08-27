<script setup lang="ts">
import { TabsList, type TabsListProps } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps<TabsListProps & { class?: string }>()
</script>

<template>
  <TabsList
    v-bind="props"
    :class="cn('inline-flex items-center justify-center rounded-xl bg-white dark:bg-card border border-border/80 p-1 text-muted-foreground shadow-sm overflow-hidden', props.class)"
  >
    <slot />
  </TabsList>
</template>

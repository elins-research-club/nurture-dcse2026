<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { Droplet, Thermometer, Sun, Beaker, Battery } from 'lucide-vue-next'
import { formatValue } from '@/lib/utils'

const props = defineProps<{
  title: string
  value: number | null | undefined
  unit: string
  type: 'temperature' | 'humidity' | 'soil' | 'ph' | 'npk' | 'light' | 'battery'
}>()

const iconMap = {
  temperature: Thermometer,
  humidity: Droplet,
  soil: Droplet,
  ph: Beaker,
  npk: Beaker,
  light: Sun,
  battery: Battery
}

const colorClass = computed(() => {
  switch (props.type) {
    case 'temperature': return 'text-orange-500'
    case 'humidity': return 'text-blue-500'
    case 'soil': return 'text-amber-700'
    case 'ph': return 'text-purple-500'
    case 'npk': return 'text-emerald-600'
    case 'light': return 'text-yellow-500'
    case 'battery': return 'text-green-500'
    default: return 'text-primary'
  }
})

const Icon = computed(() => iconMap[props.type] || Beaker)
</script>

<template>
  <Card class="relative overflow-hidden group hover:-translate-y-1 transition-all duration-300 hover:shadow-xl dark:hover:shadow-[0_8px_30px_rgba(0,229,114,0.08)] hover:border-primary/30">
    <!-- Subtle gradient background that appears on hover -->
    <div class="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
    
    <CardContent class="p-6 flex items-center justify-between relative z-10">
      <div>
        <p class="text-sm font-medium text-muted-foreground group-hover:text-foreground/80 transition-colors">{{ title }}</p>
        <div class="flex items-baseline gap-1 mt-2">
          <h3 class="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-foreground to-foreground/70">
            {{ value !== null && value !== undefined ? value : '--' }}
          </h3>
          <span class="text-sm text-muted-foreground font-medium ml-1">{{ unit }}</span>
        </div>
      </div>
      <div 
        :class="[
          'w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-500 shadow-inner group-hover:scale-110', 
          colorClass,
          'bg-background border border-border/50 group-hover:border-transparent'
        ]"
      >
        <component :is="Icon" class="w-7 h-7 drop-shadow-md transition-transform group-hover:rotate-6" />
      </div>
    </CardContent>
  </Card>
</template>

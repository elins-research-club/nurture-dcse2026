<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { Droplet, Thermometer, Sun, Beaker, Battery } from 'lucide-vue-next'
import { formatValue } from '@/lib/utils'

const props = withDefaults(defineProps<{
  title: string
  value: number | null | undefined
  unit: string
  type: 'temperature' | 'humidity' | 'soil' | 'ph' | 'npk' | 'light' | 'battery'
  size?: 'default' | 'lg'
  accentGradient?: string
}>(), {
  size: 'default',
})

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

const isLg = computed(() => props.size === 'lg')
</script>

<template>
  <Card :class="[
    'relative overflow-hidden group hover:-translate-y-1 transition-all duration-300 hover:shadow-xl dark:hover:shadow-[0_8px_30px_rgba(0,229,114,0.08)] hover:border-primary/30',
  ]">
    <!-- Accent gradient background -->
    <div :class="[
      'absolute inset-0 transition-opacity duration-500 pointer-events-none',
      accentGradient ? 'opacity-100' : 'opacity-0 group-hover:opacity-100',
      accentGradient || 'bg-gradient-to-br from-primary/5 to-transparent'
    ]" :style="accentGradient ? { background: accentGradient } : {}"></div>
    
    <CardContent :class="['flex items-center justify-between relative z-10', isLg ? 'p-5' : 'p-4']">
      <div>
        <p :class="['font-medium text-muted-foreground group-hover:text-foreground/80 transition-colors', isLg ? 'text-sm' : 'text-sm']">{{ title }}</p>
        <div class="flex items-baseline gap-1 mt-1">
          <h3 :class="[
            'font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-foreground to-foreground/70',
            isLg ? 'text-3xl' : 'text-2xl'
          ]">
            {{ value !== null && value !== undefined ? value : '--' }}
          </h3>
          <span :class="['text-muted-foreground font-medium ml-1', isLg ? 'text-sm' : 'text-xs']">{{ unit }}</span>
        </div>
      </div>
      <div 
        :class="[
          'rounded-xl flex items-center justify-center transition-all duration-500 shadow-inner group-hover:scale-110', 
          colorClass,
          'bg-background border border-border/50 group-hover:border-transparent',
          isLg ? 'w-14 h-14' : 'w-12 h-12'
        ]"
      >
        <component :is="Icon" :class="['drop-shadow-md transition-transform group-hover:rotate-6', isLg ? 'w-7 h-7' : 'w-6 h-6']" />
      </div>
    </CardContent>
  </Card>
</template>

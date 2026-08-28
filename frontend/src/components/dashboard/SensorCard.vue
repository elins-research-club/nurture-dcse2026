<script setup lang="ts">
import { computed } from 'vue'
import { Card, CardContent } from '@/components/ui/card'
import { 
  Droplet, Thermometer, Sun, Beaker, Battery, 
  Check, ArrowDownRight, ArrowUpRight
} from 'lucide-vue-next'
import { formatValue } from '@/lib/utils'

const props = withDefaults(defineProps<{
  title: string
  value: number | null | undefined
  unit: string
  type: 'temperature' | 'humidity' | 'soil' | 'ph' | 'npk' | 'light' | 'battery'
  size?: 'default' | 'lg'
  accentGradient?: string
  minThreshold?: number | null
  maxThreshold?: number | null
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

const Icon = computed(() => iconMap[props.type] || Beaker)
const isLg = computed(() => props.size === 'lg')

// Determine threshold status (Rendah: Soft Sky Blue / Ideal: Soft Mint Emerald / Tinggi: Soft Rose Coral)
const thresholdStatus = computed(() => {
  if (props.value === null || props.value === undefined) return null

  let min = props.minThreshold
  let max = props.maxThreshold

  // Default agronomic thresholds for NPK if not configured in DB
  if (min == null && max == null && props.type === 'npk') {
    const t = props.title.toLowerCase()
    if (t.includes('nitrogen') || t.includes('nitrat')) {
      min = 20
      max = 60
    } else if (t.includes('phosphorus') || t.includes('fosfor')) {
      min = 20
      max = 40
    } else if (t.includes('potassium') || t.includes('kalium')) {
      min = 20
      max = 40
    }
  }

  // Only calculate threshold for sensors with defined min/max or NPK
  if (min == null && max == null) return null

  const val = Number(props.value)
  if (isNaN(val)) return null

  if (min != null && val < min) {
    return {
      status: 'low',
      label: 'Rendah',
      icon: ArrowDownRight,
      // Bright Vibrant Sky Blue gradient
      gradient: 'linear-gradient(135deg, #38BDF8 0%, #0EA5E9 45%, #0284C7 100%)',
      shadowClass: 'shadow-md shadow-sky-400/20 hover:shadow-lg hover:shadow-sky-400/30'
    }
  }
  if (max != null && val > max) {
    return {
      status: 'high',
      label: 'Tinggi',
      icon: ArrowUpRight,
      // Bright Vibrant Coral Rose gradient
      gradient: 'linear-gradient(135deg, #FB7185 0%, #F43F5E 45%, #E11D48 100%)',
      shadowClass: 'shadow-md shadow-rose-400/20 hover:shadow-lg hover:shadow-rose-400/30'
    }
  }
  return {
    status: 'ideal',
    label: 'Ideal',
    icon: Check,
    // Bright & Fresh Emerald Green gradient
    gradient: 'linear-gradient(135deg, #34D399 0%, #10B981 45%, #059669 100%)',
    shadowClass: 'shadow-md shadow-emerald-400/20 hover:shadow-lg hover:shadow-emerald-400/30'
  }
})
</script>

<template>
  <!-- Full Soft Gradient Card when Threshold Status is Active (NPK / Threshold Sensors) -->
  <div 
    v-if="thresholdStatus"
    :class="[
      'relative overflow-hidden rounded-2xl p-4 transition-all duration-300 select-none text-white border-0 shadow-none',
      thresholdStatus.shadowClass
    ]"
    :style="{ background: thresholdStatus.gradient }"
  >
    <!-- Soft Glass Inner Glow / Lighting Reflection -->
    <div 
      class="absolute inset-0 pointer-events-none opacity-20"
      style="background: radial-gradient(circle at 85% 15%, rgba(255, 255, 255, 0.4) 0%, transparent 60%);"
    ></div>

    <!-- Tactile Analog Grain / Noise Texture Overlay -->
    <div class="absolute inset-0 pointer-events-none opacity-80 mix-blend-overlay bg-grain-texture"></div>
    
    <div class="flex items-center justify-between relative z-10">
      <div>
        <p class="font-semibold text-sm sm:text-base text-white tracking-wide drop-shadow-[0_1px_2px_rgba(0,0,0,0.35)]">{{ title }}</p>
        <div class="flex items-baseline gap-1.5 mt-0.5">
          <h3 class="font-black tracking-tight text-white text-3xl sm:text-4xl drop-shadow-[0_1.5px_3px_rgba(0,0,0,0.4)]">
            {{ value !== null && value !== undefined ? value : '--' }}
          </h3>
          <span class="text-white/95 font-bold text-sm drop-shadow-[0_1px_2px_rgba(0,0,0,0.35)]">{{ unit }}</span>
        </div>
      </div>

      <!-- Bright Frosted Glass Status Capsule -->
      <div class="px-3.5 py-1.5 rounded-full bg-white/30 hover:bg-white/35 backdrop-blur-md text-white flex items-center gap-1.5 text-xs sm:text-sm font-bold shrink-0 border border-white/50 shadow-sm">
        <component :is="thresholdStatus.icon" class="w-4 h-4 stroke-[2.5] text-white" />
        <span class="tracking-wide">{{ thresholdStatus.label }}</span>
      </div>
    </div>
  </div>

  <!-- Standard Clean Card (Fallback for Non-Threshold Generic Sensors) -->
  <Card 
    v-else
    class="relative overflow-hidden group transition-all duration-200 shadow-none border border-border/80 bg-white dark:bg-card"
  >
    <CardContent :class="['flex items-center justify-between relative z-10', isLg ? 'p-5' : 'p-4']">
      <div>
        <p :class="['font-medium text-muted-foreground group-hover:text-foreground/80 transition-colors', isLg ? 'text-base' : 'text-sm sm:text-base']">{{ title }}</p>
        <div class="flex items-baseline gap-1 mt-1">
          <h3 :class="[
            'font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-foreground to-foreground/70',
            isLg ? 'text-4xl' : 'text-3xl'
          ]">
            {{ value !== null && value !== undefined ? value : '--' }}
          </h3>
          <span :class="['text-muted-foreground font-medium ml-1', isLg ? 'text-base' : 'text-sm']">{{ unit }}</span>
        </div>
      </div>

      <div 
        :class="[
          'rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-105 bg-slate-50 dark:bg-slate-900/50 border border-border/50', 
          isLg ? 'w-14 h-14' : 'w-11 h-11'
        ]"
      >
        <component :is="Icon" :class="['drop-shadow-sm transition-transform group-hover:rotate-6 text-primary', isLg ? 'w-7 h-7' : 'w-5.5 h-5.5']" />
      </div>
    </CardContent>
  </Card>
</template>

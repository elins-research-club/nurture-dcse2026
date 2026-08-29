<script setup lang="ts">
import { computed } from 'vue'
import { DotPattern } from '@/components/ui/dot-pattern'
import { 
  Droplet, Thermometer, Sun, Beaker, Battery, 
  Check, ArrowDownRight, ArrowUpRight, Activity
} from 'lucide-vue-next'

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

// Determine threshold status (Rendah / Ideal / Tinggi) for the capsule badge
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

  if (min == null && max == null) return null

  const val = Number(props.value)
  if (isNaN(val)) return null

  if (min != null && val < min) {
    return {
      status: 'low',
      label: 'Rendah',
      icon: ArrowDownRight
    }
  }
  if (max != null && val > max) {
    return {
      status: 'high',
      label: 'Tinggi',
      icon: ArrowUpRight
    }
  }
  return {
    status: 'ideal',
    label: 'Ideal',
    icon: Check
  }
})

// Semantic gradient based on status, fallback to identity
const semanticTheme = computed(() => {
  const status = thresholdStatus.value?.status

  if (status === 'low') {
    return {
      gradient: 'linear-gradient(135deg, #F59E0B 0%, #D97706 45%, #B45309 100%)', // Amber
      shadowClass: 'shadow-md shadow-amber-500/20 hover:shadow-lg hover:shadow-amber-500/30'
    }
  }

  if (status === 'high') {
    return {
      gradient: 'linear-gradient(135deg, #EF4444 0%, #DC2626 45%, #B91C1C 100%)', // Red
      shadowClass: 'shadow-md shadow-red-500/20 hover:shadow-lg hover:shadow-red-500/30'
    }
  }

  if (status === 'ideal') {
    return {
      gradient: 'linear-gradient(135deg, #00B200 0%, #008A00 45%, #006400 100%)', // Ideal Green
      shadowClass: 'shadow-md shadow-[#00b200]/20 hover:shadow-lg hover:shadow-[#00b200]/30'
    }
  }

  const t = (props.title || '').toLowerCase()
  const type = (props.type || '').toLowerCase()

  // 1. Nitrogen (N) -> Emerald Green
  if (t.includes('nitrogen') || t.includes('nitrat') || t === 'n') {
    return {
      gradient: 'linear-gradient(135deg, #34D399 0%, #10B981 45%, #059669 100%)',
      shadowClass: 'shadow-md shadow-emerald-400/20 hover:shadow-lg hover:shadow-emerald-400/30'
    }
  }

  // 2. Phosphorus (P) -> Ocean Blue
  if (t.includes('phosphorus') || t.includes('fosfor') || t === 'p') {
    return {
      gradient: 'linear-gradient(135deg, #60A5FA 0%, #3B82F6 45%, #1D4ED8 100%)',
      shadowClass: 'shadow-md shadow-blue-400/20 hover:shadow-lg hover:shadow-blue-400/30'
    }
  }

  // 3. Potassium (K) -> Royal Purple
  if (t.includes('potassium') || t.includes('kalium') || t === 'k') {
    return {
      gradient: 'linear-gradient(135deg, #A78BFA 0%, #8B5CF6 45%, #6D28D9 100%)',
      shadowClass: 'shadow-md shadow-purple-400/20 hover:shadow-lg hover:shadow-purple-400/30'
    }
  }

  // 4. pH -> Amber / Gold
  if (t.includes('ph') || type === 'ph') {
    return {
      gradient: 'linear-gradient(135deg, #FBBF24 0%, #F59E0B 45%, #D97706 100%)',
      shadowClass: 'shadow-md shadow-amber-400/20 hover:shadow-lg hover:shadow-amber-400/30'
    }
  }

  // 5. Suhu / Temperature -> Warm Rose / Orange
  if (t.includes('suhu') || t.includes('temp') || type === 'temperature') {
    return {
      gradient: 'linear-gradient(135deg, #FB923C 0%, #F43F5E 45%, #E11D48 100%)',
      shadowClass: 'shadow-md shadow-rose-400/20 hover:shadow-lg hover:shadow-rose-400/30'
    }
  }

  // 6. Kelembaban / Moisture -> Cyan / Sky Blue
  if (t.includes('kelembaban') || t.includes('lembab') || t.includes('moisture') || type === 'humidity' || type === 'soil') {
    return {
      gradient: 'linear-gradient(135deg, #38BDF8 0%, #0EA5E9 45%, #0284C7 100%)',
      shadowClass: 'shadow-md shadow-sky-400/20 hover:shadow-lg hover:shadow-sky-400/30'
    }
  }

  // 7. EC -> Lime / Emerald
  if (t.includes('ec') || t.includes('daya hantar')) {
    return {
      gradient: 'linear-gradient(135deg, #A3E635 0%, #84CC16 45%, #4D7C0F 100%)',
      shadowClass: 'shadow-md shadow-lime-400/20 hover:shadow-lg hover:shadow-lime-400/30'
    }
  }

  if (props.accentGradient) {
    return {
      gradient: props.accentGradient,
      shadowClass: 'shadow-md shadow-primary/20'
    }
  }

  return {
    gradient: 'linear-gradient(135deg, #34D399 0%, #10B981 45%, #059669 100%)',
    shadowClass: 'shadow-md shadow-emerald-400/20'
  }
})
</script>

<template>
  <!-- Full Semantic Gradient Card with High Polish & Visual Identity -->
  <div 
    :class="[
      'relative overflow-hidden rounded-2xl p-4 transition-all duration-300 select-none text-white border-0 shadow-[inset_0_1px_1.5px_rgba(255,255,255,0.45),0_3px_12px_-2px_rgba(0,0,0,0.08)] hover:-translate-y-0.5 hover:shadow-[inset_0_1px_1.5px_rgba(255,255,255,0.65),0_8px_24px_-4px_rgba(0,0,0,0.15)] cursor-default',
      semanticTheme.shadowClass
    ]"
    :style="{ background: semanticTheme.gradient }"
  >
    <!-- Soft Glass Inner Glow / Lighting Reflection -->
    <div 
      class="absolute inset-0 pointer-events-none opacity-20"
      style="background: radial-gradient(circle at 85% 15%, rgba(255, 255, 255, 0.4) 0%, transparent 60%);"
    ></div>

    <!-- Inspira UI DotPattern Texture Overlay -->
    <DotPattern 
      :width="12" 
      :height="12" 
      :cx="1" 
      :cy="1" 
      :cr="1" 
      class="text-white/20" 
    />
    
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
      <div 
        v-if="thresholdStatus"
        class="px-3.5 py-1.5 rounded-full bg-white/25 hover:bg-white/30 backdrop-blur-md text-white flex items-center gap-1.5 text-xs sm:text-sm font-bold shrink-0 border border-white/40 shadow-sm"
      >
        <component :is="thresholdStatus.icon" class="w-4 h-4 stroke-[2.5] text-white" />
        <span class="tracking-wide">{{ thresholdStatus.label }}</span>
      </div>
    </div>
  </div>
</template>

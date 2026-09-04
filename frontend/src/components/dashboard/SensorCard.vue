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
  isStale?: boolean
  readingAt?: string | null
}>(), {
  size: 'default',
  isStale: false,
})

// Status kapsul (Rendah / Ideal / Tinggi) SEMATA dari ambang operator di
// database. Kalau operator belum mengisinya, kartu tidak menampilkan status.
//
// Dulu di sini ada angka cadangan NPK (N 20-60, P 20-40, K 20-40) yang tidak
// punya sumber dan bahkan BERBEDA dari angka cadangan di NodeDashboard.vue
// (N 20-80, P 15-60, K 20-60), jadi satu pembacaan bisa disebut "Ideal" di satu
// kartu dan "Tinggi" di kartu lain. Klasifikasi terhadap standar terbit datang
// dari backend (soil_health).
const thresholdStatus = computed(() => {
  if (props.value === null || props.value === undefined) return null

  const min = props.minThreshold
  const max = props.maxThreshold

  if (min == null && max == null) return null

  const val = Number(props.value)
  if (isNaN(val)) return null

  if (min != null && val < min) {
    return {
      status: 'low',
      label: 'Rendah',
      icon: ArrowDownRight,
      min,
      max
    }
  }
  if (max != null && val > max) {
    return {
      status: 'high',
      label: 'Tinggi',
      icon: ArrowUpRight,
      min,
      max
    }
  }
  return {
    status: 'ideal',
    label: 'Ideal',
    icon: Check,
    min,
    max
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
  if (t.includes('phosphorus') || t.includes('phosphor') || t.includes('phospor') || t.includes('fosfor') || t === 'p') {
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
    
    <div class="flex items-start justify-between relative z-10 gap-2">
      <div class="min-w-0 flex-1">
        <p class="font-semibold text-sm sm:text-base text-white tracking-wide drop-shadow-[0_1px_2px_rgba(0,0,0,0.35)] line-clamp-2 leading-snug">{{ title }}</p>
        <div class="flex items-baseline gap-1.5 mt-1">
          <h3 class="font-black tracking-tight text-white text-3xl sm:text-4xl drop-shadow-[0_1.5px_3px_rgba(0,0,0,0.4)]">
            {{ value !== null && value !== undefined ? value : '--' }}
          </h3>
          <span class="text-white/95 font-bold text-sm drop-shadow-[0_1px_2px_rgba(0,0,0,0.35)]">{{ unit }}</span>
        </div>
        <!-- Angka hasil forward-fill: pembacaan lama yang disalin karena paket
             terbaru tidak membawa field ini. -->
        <p
          v-if="isStale"
          class="mt-1 text-[11px] font-semibold text-white/80 flex items-center gap-1"
          :title="readingAt ? 'Pembacaan terakhir: ' + readingAt : 'Tidak ada pembacaan baru'"
        >
          <span class="inline-block w-1.5 h-1.5 rounded-full bg-white/70"></span>
          Data terakhir, bukan pembacaan baru
        </p>
      </div>

      <!-- Structured Stacked Status & Threshold Container (Option B - Apple Health Style) -->
      <div 
        v-if="thresholdStatus"
        :class="[
          'bg-white/20 hover:bg-white/25 backdrop-blur-md text-white border border-white/35 shadow-sm shrink-0 transition-all select-none',
          (thresholdStatus.status === 'low' || thresholdStatus.status === 'high') && (thresholdStatus.min != null || thresholdStatus.max != null)
            ? 'px-3.5 sm:px-4 py-2 sm:py-2.5 rounded-2xl flex flex-col items-center gap-1.5 min-w-[125px] sm:min-w-[140px]'
            : 'px-4 py-2 rounded-full flex items-center gap-2'
        ]"
      >
        <!-- Status with Icon (Prominent & Bold) -->
        <div class="flex items-center gap-1.5 text-xs sm:text-sm font-black text-white leading-tight tracking-wide">
          <component :is="thresholdStatus.icon" class="w-4 h-4 stroke-[2.5] text-white shrink-0" />
          <span>{{ thresholdStatus.label }}</span>
        </div>

        <!-- Integrated Threshold Limit Row (Larger, High Readability Typography) -->
        <div 
          v-if="(thresholdStatus.status === 'low' || thresholdStatus.status === 'high') && (thresholdStatus.min != null || thresholdStatus.max != null)"
          class="text-xs sm:text-[13px] font-bold text-white flex items-center justify-center gap-1.5 border-t border-white/25 pt-1.5 w-full tracking-tight whitespace-nowrap"
          :title="`Ambang Batas Normal: ${thresholdStatus.min ?? 0} - ${thresholdStatus.max ?? '∞'} ${unit}`"
        >
          <span class="text-white/80 text-[11px] sm:text-xs font-medium">Batas:</span>
          <span class="font-black text-white">{{ thresholdStatus.min ?? 0 }}–{{ thresholdStatus.max ?? '∞' }}</span>
          <span class="text-[11px] sm:text-xs text-white/85 font-semibold">{{ unit }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  status?: 'surplus' | 'defisit' | 'standby' | 'offline' | string
  label?: string
}

const props = withDefaults(defineProps<Props>(), {
  status: 'offline',
  label: undefined
})

const normalizedStatus = computed(() => {
  const s = (props.status || '').toLowerCase()
  if (s === 'surplus') return 'surplus'
  if (s === 'defisit') return 'defisit'
  if (s === 'standby') return 'standby'
  return 'offline'
})

const defaultLabels: Record<string, string> = {
  surplus: 'Solar Aktif (Mengisi Aki)',
  defisit: 'Tenaga Baterai (Solar Mati)',
  standby: 'Daya Seimbang (Siaga)',
  offline: 'Sensor Offline'
}

const displayLabel = computed(() => {
  return props.label || defaultLabels[normalizedStatus.value] || 'Sensor Offline'
})

const containerClasses = computed(() => {
  switch (normalizedStatus.value) {
    case 'surplus':
      return 'bg-emerald-500/10 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30'
    case 'defisit':
      return 'bg-amber-500/10 dark:bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30'
    case 'standby':
      return 'bg-sky-500/10 dark:bg-sky-500/15 text-sky-700 dark:text-sky-300 border-sky-500/30'
    default:
      return 'bg-slate-500/10 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'
  }
})
</script>

<template>
  <div 
    :class="[
      'px-2.5 py-1 rounded-xl border flex items-center gap-2 shadow-2xs text-xs font-bold transition-all shrink-0 select-none',
      containerClasses
    ]"
  >
    <!-- STATE 1: SURPLUS (3D Sun - Float & Subtle Glow) -->
    <div v-if="normalizedStatus === 'surplus'" class="relative flex items-center justify-center w-5 h-5 shrink-0">
      <img 
        src="/sun-dynamic-color.svg" 
        alt="Solar Aktif" 
        class="w-5 h-5 object-contain animate-float-sun select-none pointer-events-none drop-shadow-sun"
      />
    </div>

    <!-- STATE 2: DEFISIT (3D Battery - Pulse Breathing) -->
    <div v-else-if="normalizedStatus === 'defisit'" class="relative flex items-center justify-center w-5 h-5 shrink-0">
      <img 
        src="/battery-dynamic-color.svg" 
        alt="Tenaga Baterai" 
        class="w-5 h-5 object-contain animate-pulse-battery select-none pointer-events-none drop-shadow-battery"
      />
    </div>

    <!-- STATE 3: STANDBY (3D Shield Check - Calm Equilibrium) -->
    <div v-else-if="normalizedStatus === 'standby'" class="relative flex items-center justify-center w-5 h-5 shrink-0">
      <img 
        src="/sheild-dynamic-color.svg" 
        alt="Daya Seimbang" 
        class="w-5 h-5 object-contain animate-breathe-shield select-none pointer-events-none drop-shadow-shield"
      />
    </div>

    <!-- STATE 4: OFFLINE (3D Wi-Fi - Muted Grayscale) -->
    <div v-else class="relative flex items-center justify-center w-5 h-5 shrink-0">
      <img 
        src="/wifi-dynamic-color.svg" 
        alt="Sensor Offline" 
        class="w-5 h-5 object-contain grayscale opacity-50 select-none pointer-events-none"
      />
    </div>

    <!-- Text Label -->
    <span class="text-[11px] sm:text-xs tracking-tight">{{ displayLabel }}</span>
  </div>
</template>

<style scoped>
@keyframes floatSun {
  0%, 100% {
    transform: translateY(0px) rotate(0deg) scale(1);
  }
  50% {
    transform: translateY(-2px) rotate(4deg) scale(1.05);
  }
}

@keyframes pulseBattery {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.08) rotate(-2deg);
  }
}

@keyframes breatheShield {
  0%, 100% {
    transform: scale(1);
    opacity: 0.95;
  }
  50% {
    transform: scale(1.05);
    opacity: 1;
  }
}

.animate-float-sun {
  animation: floatSun 3.2s ease-in-out infinite;
}

.animate-pulse-battery {
  animation: pulseBattery 2s ease-in-out infinite;
}

.animate-breathe-shield {
  animation: breatheShield 3.5s ease-in-out infinite;
}

.drop-shadow-sun {
  filter: drop-shadow(0 2px 5px rgba(245, 158, 11, 0.4));
}

.drop-shadow-battery {
  filter: drop-shadow(0 2px 5px rgba(245, 158, 11, 0.35));
}

.drop-shadow-shield {
  filter: drop-shadow(0 2px 5px rgba(14, 165, 233, 0.35));
}
</style>

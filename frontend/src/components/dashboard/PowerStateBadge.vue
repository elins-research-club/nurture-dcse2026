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
    <!-- STATE 1: SURPLUS (Solar Aktif / Mengisi Aki) -->
    <!-- Micro-animation: Sinar matahari berputar kontinu halus + inti bercahaya -->
    <div v-if="normalizedStatus === 'surplus'" class="relative flex items-center justify-center w-4 h-4 shrink-0">
      <svg viewBox="0 0 24 24" class="w-4 h-4 text-emerald-600 dark:text-emerald-400 animate-spin-slow origin-center">
        <line x1="12" y1="2" x2="12" y2="5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />
        <line x1="12" y1="19" x2="12" y2="22" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />
        <line x1="2" y1="12" x2="5" y2="12" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />
        <line x1="19" y1="12" x2="22" y2="12" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />
        <line x1="4.93" y1="4.93" x2="7.05" y2="7.05" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />
        <line x1="16.95" y1="16.95" x2="19.07" y2="19.07" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />
        <line x1="4.93" y1="19.07" x2="7.05" y2="16.95" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />
        <line x1="16.95" y1="7.05" x2="19.07" y2="4.93" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" />
      </svg>
      <div class="absolute w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse-gentle shadow-[0_0_6px_rgba(16,185,129,0.7)]"></div>
    </div>

    <!-- STATE 2: DEFISIT (Tenaga Baterai / Discharging) -->
    <!-- Micro-animation: Sel aki berdenyut + panah daya mengalir keluar -->
    <div v-else-if="normalizedStatus === 'defisit'" class="relative flex items-center justify-center w-4 h-4 shrink-0">
      <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4 text-amber-600 dark:text-amber-400">
        <!-- Battery Body & Terminal -->
        <rect x="2" y="6" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.8" />
        <path d="M14 10h1.5a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        <!-- Battery Active Energy Core (Pulsing) -->
        <rect x="4.5" y="8.5" width="7" height="7" rx="1" class="fill-amber-500 dark:fill-amber-400 animate-pulse-gentle" />
      </svg>
      <!-- Micro Arrow Discharge Outwards -->
      <div class="absolute -right-1 top-1/2 flex items-center animate-slide-arrow">
        <svg viewBox="0 0 8 10" class="w-2 h-2 text-amber-600 dark:text-amber-300 fill-current">
          <path d="M1 1l5 4-5 4z" />
        </svg>
      </div>
    </div>

    <!-- STATE 3: STANDBY (Daya Seimbang / Siaga) -->
    <!-- Micro-animation: Simbol aliran setimbang bolak-balik berdenyut tenang -->
    <div v-else-if="normalizedStatus === 'standby'" class="relative flex items-center justify-center w-4 h-4 shrink-0">
      <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4 text-sky-600 dark:text-sky-400">
        <path d="M5 9h14M15 5l4 4-4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="animate-pulse-slow" />
        <path d="M19 15H5M9 19l-4-4 4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="animate-pulse-slow" />
      </svg>
    </div>

    <!-- STATE 4: OFFLINE (Sensor Tidak Terbaca) -->
    <!-- Micro-visual: Ikon radar/kabel terputus statis abu-abu -->
    <div v-else class="relative flex items-center justify-center w-4 h-4 shrink-0">
      <svg viewBox="0 0 24 24" fill="none" class="w-4 h-4 text-slate-400 dark:text-slate-500">
        <line x1="2" y1="2" x2="22" y2="22" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        <path d="M18.36 6.64a9 9 0 0 1-.49 12.23M6.13 6.13a9 9 0 0 0-.49 12.24M15.54 9.46a5 5 0 0 1 0 5.08M8.46 8.46a5 5 0 0 0 0 7.08" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </div>

    <!-- Text Label -->
    <span class="text-[11px] sm:text-xs tracking-tight">{{ displayLabel }}</span>
  </div>
</template>

<style scoped>
@keyframes spinSlow {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulseGentle {
  0%, 100% {
    opacity: 0.95;
    transform: scale(1);
  }
  50% {
    opacity: 0.45;
    transform: scale(0.88);
  }
}

@keyframes slideArrow {
  0%, 100% {
    transform: translate(0, -50%);
    opacity: 0.35;
  }
  50% {
    transform: translate(2.5px, -50%);
    opacity: 1;
  }
}

@keyframes pulseSlow {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.animate-spin-slow {
  animation: spinSlow 12s linear infinite;
}

.animate-pulse-gentle {
  animation: pulseGentle 2.2s ease-in-out infinite;
}

.animate-slide-arrow {
  animation: slideArrow 1.6s ease-in-out infinite;
}

.animate-pulse-slow {
  animation: pulseSlow 3s ease-in-out infinite;
}
</style>

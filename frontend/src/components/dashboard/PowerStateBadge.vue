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

const defaultLabels: Record<string, { title: string; subtitle: string; colorClass: string }> = {
  surplus: {
    title: 'Solar Aktif',
    subtitle: 'Mengisi Aki',
    colorClass: 'text-emerald-600 dark:text-emerald-400'
  },
  defisit: {
    title: 'Tenaga Baterai',
    subtitle: 'Solar Mati',
    colorClass: 'text-amber-600 dark:text-amber-400'
  },
  standby: {
    title: 'Daya Seimbang',
    subtitle: 'Siaga / Float',
    colorClass: 'text-sky-600 dark:text-sky-400'
  },
  offline: {
    title: 'Sensor Offline',
    subtitle: 'Tidak Terbaca',
    colorClass: 'text-slate-400 dark:text-slate-500'
  }
}

const parsedLabel = computed(() => {
  const defaults = defaultLabels[normalizedStatus.value] || defaultLabels.offline
  if (!props.label) return defaults
  
  // Format parsing: "Judul (Keterangan)"
  const match = props.label.match(/^([^(]+)(?:\(([^)]+)\))?/)
  if (match) {
    return {
      title: match[1].trim(),
      subtitle: match[2] ? match[2].trim() : defaults.subtitle,
      colorClass: defaults.colorClass
    }
  }
  return {
    title: props.label,
    subtitle: defaults.subtitle,
    colorClass: defaults.colorClass
  }
})
</script>

<template>
  <!-- KOTAK STATUS JUMBO TRANSPARAN TANPA BG -->
  <div 
    class="flex flex-col items-center justify-center text-center gap-1.5 select-none relative p-2 min-h-[140px]"
  >
    <!-- STATE 1: SURPLUS (3D Sun - Jumbo Floating Levitation) -->
    <div v-if="normalizedStatus === 'surplus'" class="relative flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 shrink-0 z-10">
      <img 
        src="/sun-dynamic-color.svg" 
        alt="Solar Aktif" 
        class="w-full h-full object-contain animate-float-sun select-none pointer-events-none drop-shadow-sun"
      />
    </div>

    <!-- STATE 2: DEFISIT (3D Battery - Jumbo Heartbeat Pulse) -->
    <div v-else-if="normalizedStatus === 'defisit'" class="relative flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 shrink-0 z-10">
      <img 
        src="/battery-dynamic-color.svg" 
        alt="Tenaga Baterai" 
        class="w-full h-full object-contain animate-pulse-battery select-none pointer-events-none drop-shadow-battery"
      />
    </div>

    <!-- STATE 3: STANDBY (3D Shield Check - Jumbo Calm Breathing) -->
    <div v-else-if="normalizedStatus === 'standby'" class="relative flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 shrink-0 z-10">
      <img 
        src="/sheild-dynamic-color.svg" 
        alt="Daya Seimbang" 
        class="w-full h-full object-contain animate-breathe-shield select-none pointer-events-none drop-shadow-shield"
      />
    </div>

    <!-- STATE 4: OFFLINE (3D Wi-Fi - Jumbo Grayscale) -->
    <div v-else class="relative flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 shrink-0 z-10">
      <img 
        src="/wifi-dynamic-color.svg" 
        alt="Sensor Offline" 
        class="w-full h-full object-contain grayscale opacity-45 select-none pointer-events-none"
      />
    </div>

    <!-- Typography Underneath Icon -->
    <div class="relative z-10 flex flex-col items-center">
      <span class="text-xs sm:text-sm font-extrabold text-foreground tracking-tight leading-tight">
        {{ parsedLabel.title }}
      </span>
      <span :class="['text-[10px] sm:text-[11px] font-bold mt-0.5 leading-tight', parsedLabel.colorClass]">
        {{ parsedLabel.subtitle }}
      </span>
    </div>
  </div>
</template>

<style scoped>
@keyframes floatSun {
  0%, 100% {
    transform: translateY(0px) rotate(0deg) scale(1);
  }
  50% {
    transform: translateY(-4px) rotate(5deg) scale(1.05);
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
  filter: drop-shadow(0 4px 12px rgba(245, 158, 11, 0.45));
}

.drop-shadow-battery {
  filter: drop-shadow(0 4px 12px rgba(245, 158, 11, 0.4));
}

.drop-shadow-shield {
  filter: drop-shadow(0 4px 12px rgba(14, 165, 233, 0.4));
}
</style>

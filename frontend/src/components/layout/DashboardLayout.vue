<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from './Sidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { LogIn } from 'lucide-vue-next'
import { useDark, useStorage } from '@vueuse/core'

const props = withDefaults(defineProps<{
  noPadding?: boolean
  compactZoom?: boolean
}>(), {
  noPadding: false,
  compactZoom: false
})

const router = useRouter()
// Default is false (wide/expanded), and persisted in localStorage across page transitions
const isCollapsed = useStorage('gconnect_sidebar_collapsed', false)
const authStore = useAuthStore()

const isDarkMode = useDark({
  storageKey: 'theme',
  valueDark: 'dark',
  valueLight: 'light'
})

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
}

</script>

<template>
  <div class="min-h-screen relative flex flex-col font-sans">
    <!-- TOPOGRAPHIC CONTOUR ELEVATION (ISOLINES) - NEUTRAL GRAY -->
    <div class="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none bg-[#F8FAFC] dark:bg-[#0B0F17]">
      <!-- 1. Ambient Neutral Glows -->
      <div class="absolute -top-32 -left-32 w-[700px] h-[600px] rounded-full bg-slate-200/50 dark:bg-slate-800/30 blur-[140px] pointer-events-none"></div>
      <div class="absolute -bottom-32 -right-32 w-[750px] h-[650px] rounded-full bg-slate-200/40 dark:bg-slate-800/30 blur-[150px] pointer-events-none"></div>

      <!-- 2. High-Density Mathematical Topographic SVG -->
      <div 
        class="absolute inset-0 w-full h-full bg-slate-500 dark:bg-slate-400 opacity-[0.15] dark:opacity-[0.15]"
        style="
          mask-image: url('/topography.svg'); 
          mask-size: cover; 
          mask-position: center; 
          -webkit-mask-image: url('/topography.svg'); 
          -webkit-mask-size: cover; 
          -webkit-mask-position: center;
        "
      ></div>
    </div>

    <!-- Foreground UI Container with relative z-10 -->
    <div class="relative z-10 flex flex-col flex-1 min-h-screen">
      <!-- Clean Minimalist Sidebar for Authenticated Users -->
      <Sidebar 
        v-if="authStore.isAuthenticated()" 
        :collapsed="isCollapsed" 
        @update:collapsed="isCollapsed = $event" 
      />

      <!-- Guest Top Navigation Bar (Floating Island Capsule) -->
      <header 
        v-else 
        class="sticky top-3.5 z-40 w-full px-3 sm:px-6 pointer-events-none transition-all duration-300 mb-3.5"
      >
        <div class="max-w-6xl mx-auto rounded-2xl bg-card/85 dark:bg-card/75 backdrop-blur-xl border border-border/80 shadow-lg shadow-black/5 dark:shadow-black/25 px-4 sm:px-6 py-2 sm:py-2.5 flex items-center justify-between gap-3 pointer-events-auto transition-all">
          <!-- Logo & Branding -->
          <div class="flex items-center gap-2.5 shrink-0">
            <img src="/logo-icon.webp" alt="G-Connect Logo" class="w-7 h-7 sm:w-7.5 sm:h-7.5 object-contain shrink-0" />
            <h1 class="text-base sm:text-lg font-extrabold text-foreground tracking-tight">G-CONNECT</h1>
          </div>

          <!-- Center Slot for Node Switcher in Public Mode -->
          <div class="flex-1 flex items-center justify-center min-w-0">
            <slot name="header-center" />
          </div>

          <!-- Right Side: Theme Toggle & Login Button -->
          <div class="flex items-center gap-2.5 sm:gap-3.5 shrink-0">
            <!-- Custom Pill Theme Toggle with Moving Clouds & Streaming Stars -->
            <button 
              type="button"
              @click="toggleTheme" 
              class="relative inline-flex h-8 w-16 items-center rounded-full p-0.5 transition-colors duration-500 focus:outline-none cursor-pointer select-none border overflow-hidden active:scale-95 shadow-sm"
              :class="isDarkMode 
                ? 'bg-[#1e2338] border-indigo-500/30 hover:border-indigo-400/50 shadow-inner' 
                : 'bg-[#fed7aa] border-amber-300 hover:border-amber-400 shadow-inner'"
              :title="isDarkMode ? 'Beralih ke Mode Terang' : 'Beralih ke Mode Gelap'"
            >
              <!-- Night Sky: Golden Stars Streaming from Right (Moon side) to Left (Visible in Dark Mode) -->
              <div 
                class="absolute inset-0 pointer-events-none transition-all duration-500 overflow-hidden"
                :class="isDarkMode ? 'opacity-100' : 'opacity-0 pointer-events-none'"
              >
                <!-- Star 1 (Top track, moving right -> left) -->
                <span class="absolute top-1 left-0 text-amber-300 text-[8.5px] animate-star-stream-1 leading-none">✦</span>
                <!-- Star 2 (Middle track, moving right -> left) -->
                <span class="absolute top-2.5 left-0 text-yellow-200 text-[7px] animate-star-stream-2 leading-none">★</span>
                <!-- Star 3 (Bottom track, moving right -> left) -->
                <span class="absolute bottom-1.5 left-0 text-amber-200/90 text-[6px] animate-star-stream-3 leading-none">✦</span>
                <!-- Shooting Star Glide Dot -->
                <span class="absolute top-2 left-0 w-1.5 h-0.5 rounded-full bg-yellow-200 animate-shooting-star shadow-xs"></span>
              </div>

              <!-- Day Sky: White Clouds Streaming all the way to Far Right (Visible in Light Mode) -->
              <div 
                class="absolute inset-0 pointer-events-none transition-all duration-500 overflow-hidden"
                :class="!isDarkMode ? 'opacity-100' : 'opacity-0 pointer-events-none'"
              >
                <!-- Cloud 1 (Top track, gliding to far right end) -->
                <svg class="absolute top-1 left-0 w-4 h-2.5 text-white/95 animate-cloud-stream-1 drop-shadow-xs" viewBox="0 0 24 14" fill="currentColor">
                  <path d="M19.35 6.04C18.67 2.59 15.64 0 12 0 9.11 0 6.6 1.64 5.35 4.04 2.34 4.36 0 6.91 0 10c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
                </svg>
                <!-- Cloud 2 (Bottom track, gliding to far right end) -->
                <svg class="absolute bottom-1 left-0 w-3.5 h-2 text-white/85 animate-cloud-stream-2 drop-shadow-xs" viewBox="0 0 24 14" fill="currentColor">
                  <path d="M19.35 6.04C18.67 2.59 15.64 0 12 0 9.11 0 6.6 1.64 5.35 4.04 2.34 4.36 0 6.91 0 10c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
                </svg>
                <!-- Cloud 3 / Breeze puff (Middle track, gliding across) -->
                <span class="absolute top-3.5 left-0 w-2 h-0.5 rounded-full bg-white/75 animate-cloud-stream-3"></span>
              </div>

              <!-- Sliding Knob with Elastic Spring Animation -->
              <span 
                class="relative z-10 flex h-7 w-7 items-center justify-center rounded-full shadow-md transition-transform duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] transform"
                :class="isDarkMode 
                  ? 'translate-x-8 bg-slate-900 border border-slate-700 shadow-indigo-950/50' 
                  : 'translate-x-0 bg-gradient-to-tr from-amber-400 to-yellow-300 border border-amber-200'"
              >
                <!-- Sun Icon (Smooth Crossfade & Rotation) -->
                <svg 
                  class="absolute h-4.5 w-4.5 text-amber-600 transition-all duration-500 ease-in-out drop-shadow-[0_0_4px_rgba(245,158,11,0.6)]" 
                  :class="isDarkMode ? 'opacity-0 rotate-90 scale-50 pointer-events-none' : 'opacity-100 rotate-0 scale-100'"
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  stroke-width="2" 
                  stroke-linecap="round" 
                  stroke-linejoin="round" 
                >
                  <circle cx="12" cy="12" r="4" fill="#f59e0b" stroke="#ea580c" />
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" stroke="#ea580c"/>
                </svg>

                <!-- Moon Icon (Smooth Crossfade & Rotation) -->
                <svg 
                  class="absolute h-4 w-4 text-indigo-200 transition-all duration-500 ease-in-out drop-shadow-[0_0_4px_rgba(199,210,254,0.6)]" 
                  :class="isDarkMode ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-50 pointer-events-none'"
                  viewBox="0 0 24 24" 
                  fill="currentColor" 
                >
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                </svg>
              </span>
            </button>

            <!-- Login Button (Inverted: Light Background, Dark Outline, Dark Text) -->
            <Button 
              @click="router.push('/login')" 
              class="h-8 px-4 rounded-xl font-bold gap-2 bg-white dark:bg-card border border-slate-300/90 dark:border-slate-600 text-slate-800 dark:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-slate-400 shadow-xs cursor-pointer hover:scale-[1.02] active:scale-[0.98] transition-all text-xs sm:text-sm"
            >
              <LogIn class="w-3.5 h-3.5 text-slate-700 dark:text-slate-200" />
              <span>Masuk</span>
            </Button>
          </div>
        </div>
      </header>

      <!-- Main Content Container with dynamic left padding matching Sidebar state (at unzoomed 1.0x scale) -->
      <div 
        :class="[
          'flex-1 flex flex-col min-w-0 transition-all duration-300',
          authStore.isAuthenticated() ? (isCollapsed ? 'pl-[68px]' : 'pl-64') : 'pl-0'
        ]"
      >
        <main 
          :class="[
            'flex-1 transition-all duration-300 bg-transparent',
            !props.noPadding ? 'p-3 sm:p-5 overflow-y-auto' : 'overflow-hidden flex flex-col h-screen w-full'
          ]"
          :style="props.compactZoom ? 'zoom: 0.75;' : ''"
        >
          <slot />
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes starStream1 {
  0% {
    transform: translateX(28px) scale(0.3);
    opacity: 0;
  }
  25% {
    transform: translateX(20px) scale(1);
    opacity: 1;
  }
  70% {
    transform: translateX(8px) scale(0.85);
    opacity: 0.9;
  }
  100% {
    transform: translateX(-4px) scale(0.3);
    opacity: 0;
  }
}

@keyframes starStream2 {
  0% {
    transform: translateX(26px) scale(0.4);
    opacity: 0;
  }
  30% {
    transform: translateX(18px) scale(1);
    opacity: 1;
  }
  70% {
    transform: translateX(7px) scale(0.8);
    opacity: 0.9;
  }
  100% {
    transform: translateX(-6px) scale(0.3);
    opacity: 0;
  }
}

@keyframes starStream3 {
  0% {
    transform: translateX(29px) scale(0.3);
    opacity: 0;
  }
  30% {
    transform: translateX(19px) scale(0.9);
    opacity: 0.85;
  }
  70% {
    transform: translateX(8px) scale(0.7);
    opacity: 0.8;
  }
  100% {
    transform: translateX(-3px) scale(0.2);
    opacity: 0;
  }
}

@keyframes shootingStar {
  0% {
    transform: translateX(28px) scaleX(0.4);
    opacity: 0;
  }
  25% {
    transform: translateX(18px) scaleX(1.4);
    opacity: 1;
  }
  70% {
    transform: translateX(6px) scaleX(1.1);
    opacity: 0.9;
  }
  100% {
    transform: translateX(-6px) scaleX(0.2);
    opacity: 0;
  }
}

@keyframes cloudStream1 {
  0% {
    transform: translateX(14px) scale(0.65);
    opacity: 0;
  }
  20% {
    opacity: 0.95;
    transform: translateX(26px) scale(1);
  }
  75% {
    opacity: 0.9;
    transform: translateX(46px) scale(0.95);
  }
  100% {
    transform: translateX(58px) scale(0.6);
    opacity: 0;
  }
}

@keyframes cloudStream2 {
  0% {
    transform: translateX(12px) scale(0.55);
    opacity: 0;
  }
  25% {
    opacity: 0.85;
    transform: translateX(24px) scale(0.9);
  }
  70% {
    opacity: 0.85;
    transform: translateX(44px) scale(0.85);
  }
  100% {
    transform: translateX(56px) scale(0.5);
    opacity: 0;
  }
}

@keyframes cloudStream3 {
  0% {
    transform: translateX(18px);
    opacity: 0;
  }
  25% {
    opacity: 0.75;
    transform: translateX(30px);
  }
  75% {
    opacity: 0.7;
    transform: translateX(48px);
  }
  100% {
    transform: translateX(58px);
    opacity: 0;
  }
}

.animate-star-stream-1 {
  animation: starStream1 2.8s linear infinite;
}

.animate-star-stream-2 {
  animation: starStream2 3.4s linear infinite 1.2s;
}

.animate-star-stream-3 {
  animation: starStream3 2.4s linear infinite 0.6s;
}

.animate-shooting-star {
  animation: shootingStar 2.2s ease-out infinite 1.5s;
}

.animate-cloud-stream-1 {
  animation: cloudStream1 4.5s linear infinite;
}

.animate-cloud-stream-2 {
  animation: cloudStream2 5.2s linear infinite 2s;
}

.animate-cloud-stream-3 {
  animation: cloudStream3 3.8s linear infinite 0.8s;
}
</style>

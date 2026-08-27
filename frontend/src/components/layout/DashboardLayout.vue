<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from './Sidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { LogIn, Sun, Moon } from 'lucide-vue-next'

const props = defineProps<{
  noPadding?: boolean
}>()

const router = useRouter()
const isCollapsed = ref(true)
const authStore = useAuthStore()

const isDarkMode = ref(document.documentElement.classList.contains('dark'))

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}
</script>

<template>
  <div class="min-h-screen bg-background flex flex-col font-sans">
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
      <div class="max-w-6xl mx-auto rounded-2xl bg-card/85 dark:bg-card/75 backdrop-blur-xl border border-border/80 shadow-lg shadow-black/5 dark:shadow-black/25 px-4 sm:px-6 py-2 sm:py-2.5 flex items-center justify-between pointer-events-auto transition-all">
        <!-- Logo & Branding -->
        <div class="flex items-center gap-2.5">
          <img src="/logo-icon.webp" alt="G-Connect Logo" class="w-7 h-7 sm:w-7.5 sm:h-7.5 object-contain shrink-0" />
          <h1 class="text-base sm:text-lg font-extrabold text-foreground tracking-tight">G-CONNECT</h1>
        </div>

        <!-- Right Side: Theme Toggle & Login Button -->
        <div class="flex items-center gap-2.5 sm:gap-3.5">
          <!-- Custom Pill Theme Toggle with Semantic Day/Night Colors & Animations -->
          <button 
            type="button"
            @click="toggleTheme" 
            class="relative inline-flex h-8 w-15.5 items-center rounded-full p-0.5 transition-all duration-500 focus:outline-none cursor-pointer select-none border overflow-hidden"
            :class="isDarkMode 
              ? 'bg-[#1e2338] border-indigo-500/30 hover:border-indigo-400/50 shadow-inner' 
              : 'bg-[#fed7aa] border-amber-300 hover:border-amber-400 shadow-inner'"
            :title="isDarkMode ? 'Beralih ke Mode Terang' : 'Beralih ke Mode Gelap'"
          >
            <!-- Night Sky: Golden Stars Streaming Left to Right (Visible in Dark Mode) -->
            <div 
              class="absolute right-1 top-0 bottom-0 w-7.5 flex items-center pointer-events-none transition-all duration-300 overflow-hidden"
              :class="isDarkMode ? 'opacity-100' : 'opacity-0 pointer-events-none'"
            >
              <!-- Star 1 (Top track, moving left -> right) -->
              <span class="absolute top-1 left-2 text-amber-300 text-[8.5px] animate-star-stream-1 leading-none">✦</span>
              <!-- Star 2 (Middle track, moving left -> right) -->
              <span class="absolute top-2.5 left-1 text-yellow-200 text-[7px] animate-star-stream-2 leading-none">★</span>
              <!-- Star 3 (Bottom track, moving left -> right) -->
              <span class="absolute bottom-1.5 left-2 text-amber-200/90 text-[6px] animate-star-stream-3 leading-none">✦</span>
              <!-- Shooting Star Glide Dot -->
              <span class="absolute top-2 left-0 w-1.5 h-0.5 rounded-full bg-yellow-200 animate-shooting-star shadow-xs"></span>
            </div>

            <!-- Day Sky: White Clouds Streaming Left to Right (Visible in Light Mode) -->
            <div 
              class="absolute left-1 top-0 bottom-0 w-7.5 flex items-center pointer-events-none transition-all duration-300 overflow-hidden"
              :class="!isDarkMode ? 'opacity-100' : 'opacity-0 pointer-events-none'"
            >
              <!-- Cloud 1 (Top track, moving left -> right) -->
              <svg class="absolute top-1 left-1 w-3.5 h-2 text-white/90 animate-cloud-stream-1 drop-shadow-xs" viewBox="0 0 24 14" fill="currentColor">
                <path d="M19.35 6.04C18.67 2.59 15.64 0 12 0 9.11 0 6.6 1.64 5.35 4.04 2.34 4.36 0 6.91 0 10c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
              </svg>
              <!-- Cloud 2 (Bottom track, moving left -> right) -->
              <svg class="absolute bottom-1.5 left-0 w-3 h-1.5 text-white/80 animate-cloud-stream-2 drop-shadow-xs" viewBox="0 0 24 14" fill="currentColor">
                <path d="M19.35 6.04C18.67 2.59 15.64 0 12 0 9.11 0 6.6 1.64 5.35 4.04 2.34 4.36 0 6.91 0 10c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
              </svg>
              <!-- Cloud 3 / Breeze puff (Middle track) -->
              <span class="absolute top-3 left-1.5 w-1.5 h-0.5 rounded-full bg-white/70 animate-cloud-stream-3"></span>
            </div>

            <!-- Sliding Knob -->
            <span 
              class="relative z-10 pointer-events-none flex h-6 w-6 transform items-center justify-center rounded-full bg-white dark:bg-card shadow-sm border border-border/40 transition-transform duration-400 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
              :class="isDarkMode ? 'translate-x-0' : 'translate-x-7.5'"
            >
              <!-- Moon Icon for Dark Mode (Warm Golden Crescent Moon) -->
              <svg 
                v-if="isDarkMode" 
                class="h-3.5 w-3.5 text-amber-300 fill-amber-300" 
                viewBox="0 0 24 24" 
              >
                <path d="M12.3 2a10 10 0 0 0-1.9 20 10 10 0 0 0 8.7-5 1 1 0 0 0-1-1.4 8 8 0 1 1-6.8-13.6 1 1 0 0 0 1-1z"/>
              </svg>

              <!-- Sun Icon for Light Mode (Warm Orange-Gold Sun) -->
              <svg 
                v-else 
                class="h-3.5 w-3.5 text-amber-500" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                stroke-width="2.5" 
                stroke-linecap="round" 
                stroke-linejoin="round"
              >
                <circle cx="12" cy="12" r="4" fill="#f59e0b" stroke="#ea580c" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" stroke="#ea580c"/>
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
          'flex-1 transition-all duration-300 bg-background',
          !props.noPadding ? 'p-3 sm:p-5 overflow-y-auto' : 'overflow-hidden flex flex-col'
        ]"
        style="zoom: 0.75;"
      >
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
@keyframes starStream1 {
  0% {
    transform: translateX(-16px) scale(0.4);
    opacity: 0;
  }
  25% {
    opacity: 1;
    transform: translateX(-4px) scale(0.95);
  }
  75% {
    opacity: 0.9;
    transform: translateX(12px) scale(0.85);
  }
  100% {
    transform: translateX(24px) scale(0.3);
    opacity: 0;
  }
}

@keyframes starStream2 {
  0% {
    transform: translateX(-18px) scale(0.5);
    opacity: 0;
  }
  30% {
    opacity: 1;
    transform: translateX(-3px) scale(1);
  }
  70% {
    opacity: 0.9;
    transform: translateX(10px) scale(0.8);
  }
  100% {
    transform: translateX(22px) scale(0.3);
    opacity: 0;
  }
}

@keyframes starStream3 {
  0% {
    transform: translateX(-15px) scale(0.3);
    opacity: 0;
  }
  25% {
    opacity: 0.8;
    transform: translateX(-2px) scale(0.85);
  }
  75% {
    opacity: 0.8;
    transform: translateX(14px) scale(0.7);
  }
  100% {
    transform: translateX(25px) scale(0.2);
    opacity: 0;
  }
}

@keyframes shootingStar {
  0% {
    transform: translateX(-20px) scaleX(0.4);
    opacity: 0;
  }
  20% {
    opacity: 1;
    transform: translateX(0px) scaleX(1.3);
  }
  70% {
    opacity: 0.9;
    transform: translateX(18px) scaleX(1.1);
  }
  100% {
    transform: translateX(32px) scaleX(0.2);
    opacity: 0;
  }
}

@keyframes cloudStream1 {
  0% {
    transform: translateX(-16px) scale(0.6);
    opacity: 0;
  }
  25% {
    opacity: 0.85;
    transform: translateX(-3px) scale(0.95);
  }
  75% {
    opacity: 0.85;
    transform: translateX(12px) scale(0.9);
  }
  100% {
    transform: translateX(25px) scale(0.5);
    opacity: 0;
  }
}

@keyframes cloudStream2 {
  0% {
    transform: translateX(-18px) scale(0.5);
    opacity: 0;
  }
  30% {
    opacity: 0.9;
    transform: translateX(-2px) scale(1);
  }
  70% {
    opacity: 0.9;
    transform: translateX(10px) scale(0.85);
  }
  100% {
    transform: translateX(23px) scale(0.4);
    opacity: 0;
  }
}

@keyframes cloudStream3 {
  0% {
    transform: translateX(-14px);
    opacity: 0;
  }
  25% {
    opacity: 0.6;
    transform: translateX(0px);
  }
  75% {
    opacity: 0.6;
    transform: translateX(14px);
  }
  100% {
    transform: translateX(26px);
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
  animation: cloudStream1 3.2s linear infinite;
}

.animate-cloud-stream-2 {
  animation: cloudStream2 3.8s linear infinite 1.4s;
}

.animate-cloud-stream-3 {
  animation: cloudStream3 2.6s linear infinite 0.7s;
}
</style>

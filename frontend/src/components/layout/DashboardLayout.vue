<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { 
  LogIn, LogOut, LayoutDashboard, Network, MapPin, 
  ScrollText, Settings, BookmarkCheck, Trash2 
} from 'lucide-vue-next'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useDark, useColorMode, useStorage } from '@vueuse/core'

const props = withDefaults(defineProps<{
  noPadding?: boolean
  compactZoom?: boolean
}>(), {
  noPadding: false,
  compactZoom: false
})

const router = useRouter()
const route = useRoute()
// Default is false (wide/expanded), and persisted in localStorage across page transitions
const isCollapsed = useStorage('gconnect_sidebar_collapsed', false)
const authStore = useAuthStore()

const colorMode = useColorMode({
  storageKey: 'theme',
  emitAuto: true,
  modes: {
    dark: 'dark',
    light: 'light'
  }
})

const isDarkMode = useDark({
  storageKey: 'theme',
  valueDark: 'dark',
  valueLight: 'light'
})

const toggleTheme = () => {
  colorMode.value = isDarkMode.value ? 'light' : 'dark'
}

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Alat IoT', path: '/nodes', icon: Network },
  { name: 'Peta', path: '/map', icon: MapPin },
  { name: 'Logs', path: '/logs', icon: ScrollText },
  { name: 'Setelan', path: '/settings', icon: Settings },
]

const isActive = (path: string) => {
  if (path === '/nodes' && route.path.startsWith('/nodes')) return true
  if (path === '/logs' && (route.path.startsWith('/logs') || route.path.startsWith('/alerts'))) return true
  return route.path === path
}

const isLogoutModalOpen = ref(false)

const handleSoftLogout = () => {
  isLogoutModalOpen.value = false
  authStore.logout(false)
}

const handleFullLogout = () => {
  isLogoutModalOpen.value = false
  authStore.logout(true)
}
</script>

<template>
  <div class="min-h-screen relative flex flex-col font-sans">
    <!-- FARMLAND TOPOGRAPHIC ELEVATION & NIGHT ATMOSPHERE -->
    <div class="fixed inset-0 pointer-events-none z-0 overflow-hidden select-none bg-[#F8FAFC] dark:bg-[#050C10]">
      <!-- 1. Ambient Natural Farmland Mist Glows -->
      <div class="absolute -top-32 -left-32 w-[700px] h-[600px] rounded-full bg-slate-200/50 dark:bg-emerald-950/25 blur-[140px] pointer-events-none"></div>
      <div class="absolute -bottom-32 -right-32 w-[750px] h-[650px] rounded-full bg-slate-200/40 dark:bg-teal-950/25 blur-[150px] pointer-events-none"></div>
      <div class="hidden dark:block absolute top-1/4 right-1/4 w-[500px] h-[500px] rounded-full bg-emerald-900/10 blur-[160px] pointer-events-none"></div>

      <!-- 2. Farmland Elevation Contour Isolines -->
      <div 
        class="absolute inset-0 w-full h-full bg-slate-500 dark:bg-emerald-500/25 opacity-[0.12] dark:opacity-[0.14]"
        style="
          mask-image: url('/topography.svg'); 
          mask-size: cover; 
          mask-position: center; 
          -webkit-mask-image: url('/topography.svg'); 
          -webkit-mask-size: cover; 
          -webkit-mask-position: center;
        "
      ></div>

      <!-- 3. Soft Farmland Atmosphere Grain / Ambient Mist -->
      <div class="absolute inset-0 bg-gradient-to-t from-emerald-950/15 via-transparent to-transparent pointer-events-none"></div>
    </div>

    <!-- Foreground UI Container with relative z-10 -->
    <div class="relative z-10 flex flex-col flex-1 min-h-screen">
      <!-- Clean Minimalist Sidebar for Authenticated Users (Desktop Only >=md) -->
      <Sidebar 
        v-if="authStore.isAuthenticated()" 
        :collapsed="isCollapsed" 
        @update:collapsed="isCollapsed = $event" 
      />

      <!-- Mobile Top Navigation Bar for Authenticated Users (<md) -->
      <header
        v-if="authStore.isAuthenticated()"
        class="md:hidden sticky top-0 z-30 w-full px-3 py-2 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-b border-border/70 flex items-center justify-between gap-2 shadow-2xs transition-all"
      >
        <!-- Logo & Branding -->
        <router-link to="/dashboard" class="flex items-center gap-1.5 shrink-0 focus:outline-none select-none">
          <img src="/logo-icon.webp" alt="Nurture Logo" class="w-6 h-6 object-contain shrink-0" />
          <span class="text-sm font-black tracking-tight text-foreground">Nurture</span>
        </router-link>

        <!-- Center Slot for Node Switcher on Mobile -->
        <div class="flex-1 flex items-center justify-center min-w-0 px-1">
          <slot name="header-center" />
        </div>

        <!-- Right Controls: Theme Toggle & Logout -->
        <div class="flex items-center gap-1.5 shrink-0">
          <!-- Compact Theme Pill Toggle -->
          <button 
            type="button"
            @click="toggleTheme" 
            class="relative inline-flex h-7 w-12 items-center rounded-full p-0.5 transition-colors duration-300 focus:outline-none cursor-pointer border overflow-hidden active:scale-95 shadow-2xs"
            :class="isDarkMode 
              ? 'bg-[#1e2338] border-indigo-500/30' 
              : 'bg-[#fed7aa] border-amber-300'"
            :title="colorMode === 'auto' ? `Otomatis Sistem (${isDarkMode ? 'Gelap' : 'Terang'}) - Klik untuk ganti` : (isDarkMode ? 'Mode Terang' : 'Mode Gelap')"
          >
            <span 
              class="relative z-10 flex h-5.5 w-5.5 items-center justify-center rounded-full shadow-xs transition-transform duration-300 transform"
              :class="isDarkMode 
                ? 'translate-x-5 bg-slate-900 text-indigo-200' 
                : 'translate-x-0 bg-gradient-to-tr from-amber-400 to-yellow-300 text-amber-700'"
            >
              <svg v-if="!isDarkMode" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="4" fill="#f59e0b" stroke="#ea580c"/>
              </svg>
              <svg v-else class="w-3 h-3 text-indigo-200" viewBox="0 0 24 24" fill="currentColor">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            </span>
          </button>

          <!-- Logout Button Trigger -->
          <button
            @click="isLogoutModalOpen = true"
            type="button"
            class="h-7 w-7 rounded-lg flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors cursor-pointer active:scale-90"
            title="Keluar / Logout"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>
      </header>

      <!-- Guest Top Navigation Bar (Floating Island Capsule) -->
      <header 
        v-else 
        class="sticky top-2 sm:top-3.5 z-40 w-full px-2 sm:px-6 pointer-events-none transition-all duration-300 mb-2 sm:mb-3.5"
      >
        <div class="max-w-6xl mx-auto rounded-2xl bg-white/80 dark:bg-slate-900/80 backdrop-blur-2xl backdrop-saturate-150 border border-white/80 dark:border-white/10 ring-1 ring-slate-900/5 dark:ring-white/5 shadow-[inset_0_1.5px_0_0_rgba(255,255,255,1),inset_0_0_20px_0_rgba(255,255,255,0.35),0_6px_24px_-4px_rgba(15,23,42,0.07)] dark:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.12),inset_0_0_20px_0_rgba(255,255,255,0.02),0_6px_24px_-4px_rgba(0,0,0,0.35)] px-4 sm:px-6 py-3 sm:py-2.5 flex flex-wrap items-center justify-between gap-x-2 gap-y-2.5 sm:gap-3 pointer-events-auto transition-all">
          <!-- Logo & Branding -->
          <div class="flex items-center gap-2.5 shrink-0">
            <img src="/logo-icon.webp" alt="Nurture Logo" class="w-7 h-7 sm:w-7.5 sm:h-7.5 object-contain shrink-0" />
            <h1 class="text-base sm:text-lg font-extrabold text-foreground tracking-tight">Nurture</h1>
          </div>

          <!-- Center Slot for Node Switcher in Public Mode -->
          <!-- Di layar sempit pemilih stasiun turun ke barisnya sendiri.
               Sebelumnya ia flex-1 di antara dua kelompok shrink-0 yang jumlah
               lebarnya sudah melebihi layar, jadi lebarnya terhitung nyaris nol
               dan isinya menabrak tombol tema di sebelahnya.
               empty:hidden supaya tidak menyisakan baris kosong di halaman
               yang tidak mengisi slot ini. -->
          <div class="order-last w-full flex items-center justify-center min-w-0 empty:hidden sm:order-none sm:w-auto sm:flex-1">
            <slot name="header-center" />
          </div>

          <!-- Right Side: Theme Toggle & Login Button -->
          <div class="flex items-center gap-2 sm:gap-3.5 shrink-0">
            <!-- Custom Pill Theme Toggle with Moving Clouds & Streaming Stars -->
            <button 
              type="button"
              @click="toggleTheme" 
              class="relative inline-flex h-7 sm:h-8 w-13 sm:w-16 items-center rounded-full p-0.5 transition-colors duration-500 focus:outline-none cursor-pointer select-none border overflow-hidden active:scale-95 shadow-sm"
              :class="isDarkMode 
                ? 'bg-[#1e2338] border-indigo-500/30 hover:border-indigo-400/50 shadow-inner' 
                : 'bg-[#fed7aa] border-amber-300 hover:border-amber-400 shadow-inner'"
              :title="colorMode === 'auto' ? `Otomatis Sistem (${isDarkMode ? 'Gelap' : 'Terang'}) - Klik untuk ganti` : (isDarkMode ? 'Beralih ke Mode Terang' : 'Beralih ke Mode Gelap')"
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
                class="relative z-10 flex h-6 w-6 sm:h-7 sm:w-7 items-center justify-center rounded-full shadow-md transition-transform duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] transform"
                :class="isDarkMode 
                  ? 'translate-x-6 sm:translate-x-8 bg-slate-900 border border-slate-700 shadow-indigo-950/50' 
                  : 'translate-x-0 bg-gradient-to-tr from-amber-400 to-yellow-300 border border-amber-200'"
              >
                <!-- Sun Icon (Smooth Crossfade & Rotation) -->
                <svg 
                  class="absolute h-3.5 w-3.5 sm:h-4.5 sm:w-4.5 text-amber-600 transition-all duration-500 ease-in-out drop-shadow-[0_0_4px_rgba(245,158,11,0.6)]" 
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
                  class="absolute h-3 w-3 sm:h-4 sm:w-4 text-indigo-200 transition-all duration-500 ease-in-out drop-shadow-[0_0_4px_rgba(199,210,254,0.6)]" 
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
              class="h-7.5 sm:h-8 px-3 sm:px-4 rounded-xl font-bold gap-1.5 sm:gap-2 bg-white dark:bg-card border border-slate-300/90 dark:border-slate-600 text-slate-800 dark:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800 hover:border-slate-400 shadow-xs cursor-pointer hover:scale-[1.02] active:scale-[0.98] transition-all text-xs sm:text-sm"
            >
              <LogIn class="w-3.5 h-3.5 text-slate-700 dark:text-slate-200" />
              <span>Masuk</span>
            </Button>
          </div>
        </div>
      </header>

      <!-- Main Content Container with dynamic left padding matching Sidebar state on desktop, and pl-0 on mobile -->
      <div 
        :class="[
          'flex-1 flex flex-col min-w-0 transition-[padding-left] duration-300 ease-in-out pl-0',
          authStore.isAuthenticated() ? (isCollapsed ? 'md:pl-[68px]' : 'md:pl-[230px]') : ''
        ]"
      >
        <main 
          :class="[
            'flex-1 bg-transparent',
            !props.noPadding ? 'p-3 sm:p-5 pb-24 md:pb-5 overflow-y-auto' : 'overflow-hidden flex flex-col h-screen w-full pb-20 md:pb-0',
            props.compactZoom ? 'compact-zoom-desktop' : ''
          ]"
        >
          <slot />
        </main>
      </div>

      <!-- Mobile Bottom Navigation Bar for Authenticated Users (<md) -->
      <nav 
        v-if="authStore.isAuthenticated()"
        class="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur-2xl border-t border-border/80 shadow-[0_-4px_24px_rgba(0,0,0,0.08)] px-2 pt-1.5 pb-[max(0.6rem,env(safe-area-inset-bottom))] flex items-center justify-around select-none"
      >
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex flex-col items-center justify-center min-w-[56px] py-1 px-1.5 rounded-xl transition-all duration-200 active:scale-90 group',
            isActive(item.path)
              ? 'text-primary font-bold'
              : 'text-muted-foreground hover:text-foreground font-medium'
          ]"
        >
          <div 
            :class="[
              'w-8 h-7 rounded-lg flex items-center justify-center transition-all duration-200',
              isActive(item.path) ? 'bg-primary/15 scale-105' : 'group-hover:bg-slate-100 dark:group-hover:bg-slate-800'
            ]"
          >
            <component :is="item.icon" class="w-4.5 h-4.5" />
          </div>
          <span class="text-[10px] tracking-tight mt-0.5 leading-tight">
            {{ item.name }}
          </span>
        </router-link>
      </nav>

      <!-- Logout Confirmation Dialog for Mobile Header Trigger -->
      <Dialog :open="isLogoutModalOpen" @update:open="isLogoutModalOpen = $event">
        <DialogContent class="sm:max-w-[420px] p-6 rounded-2xl border border-border/80 shadow-2xl bg-white dark:bg-card">
          <div class="flex flex-col items-center pt-2">
            <!-- Large Centered Logout Icon with Soft Glow Ring -->
            <div class="w-16 h-16 sm:w-18 sm:h-18 rounded-2xl bg-rose-500/10 dark:bg-rose-500/20 border border-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400 mb-4 shadow-inner">
              <LogOut class="w-8 h-8 sm:w-9 sm:h-9" />
            </div>

            <DialogHeader class="text-center sm:text-center space-y-1.5 w-full">
              <DialogTitle class="text-lg sm:text-xl font-extrabold text-foreground tracking-tight text-center">
                {{ authStore.isRemembered ? 'Pilihan Keluar Sesi' : 'Konfirmasi Logout' }}
              </DialogTitle>
              <DialogDescription class="text-xs sm:text-sm text-muted-foreground text-center leading-relaxed font-medium">
                <template v-if="authStore.isRemembered">
                  Akun Anda saat ini tersimpan di peramban ini. Silakan tentukan metode keluar sesi:
                </template>
                <template v-else>
                  Apakah Anda yakin ingin keluar dari sesi sistem monitoring <strong class="text-foreground font-bold">NURTURE</strong>?
                </template>
              </DialogDescription>
            </DialogHeader>

            <!-- Remembered Session Action Choices -->
            <div v-if="authStore.isRemembered" class="w-full space-y-2.5 mt-6">
              <!-- Choice 1: Soft Logout (Keep Remembered) -->
              <button
                @click="handleSoftLogout"
                class="w-full p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10 dark:bg-emerald-500/10 dark:hover:bg-emerald-500/15 text-left transition-all cursor-pointer group flex items-center gap-3 active:scale-[0.99]"
              >
                <div class="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0">
                  <BookmarkCheck class="w-4 h-4" />
                </div>
                <p class="text-xs sm:text-sm font-bold text-foreground group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                  Logout Saja (Tetap Ingat Saya)
                </p>
              </button>

              <!-- Choice 2: Full Logout (Wipe All) -->
              <button
                @click="handleFullLogout"
                class="w-full p-3 rounded-xl border border-rose-500/30 bg-rose-500/5 hover:bg-rose-500/10 dark:bg-rose-500/10 dark:hover:bg-rose-500/15 text-left transition-all cursor-pointer group flex items-center gap-3 active:scale-[0.99]"
              >
                <div class="w-8 h-8 rounded-lg bg-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400 shrink-0">
                  <Trash2 class="w-4 h-4" />
                </div>
                <p class="text-xs sm:text-sm font-bold text-rose-600 dark:text-rose-400">
                  Logout & Hapus Kredensial
                </p>
              </button>

              <Button 
                variant="ghost" 
                size="sm"
                class="w-full h-8 text-xs font-semibold text-muted-foreground hover:text-foreground cursor-pointer mt-1"
                @click="isLogoutModalOpen = false"
              >
                Batal
              </Button>
            </div>

            <!-- Normal Standard Logout Actions -->
            <div v-else class="grid grid-cols-2 gap-3 w-full mt-6">
              <Button 
                variant="outline" 
                class="h-10 rounded-xl font-bold border-border/80 hover:bg-slate-100 dark:hover:bg-slate-800 text-foreground cursor-pointer text-xs sm:text-sm transition-all"
                @click="isLogoutModalOpen = false"
              >
                Batal
              </Button>
              <Button 
                variant="destructive" 
                class="h-10 rounded-xl font-bold bg-rose-600 hover:bg-rose-700 text-white shadow-sm cursor-pointer text-xs sm:text-sm gap-1.5 transition-all"
                @click="handleFullLogout"
              >
                <LogOut class="w-4 h-4" />
                <span>Logout</span>
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
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

@media (min-width: 1024px) {
  .compact-zoom-desktop {
    zoom: 0.75;
  }
}
</style>

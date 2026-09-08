<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMutation } from '@tanstack/vue-query'
import { usePreferredDark } from '@vueuse/core'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff, User, ArrowRight, Laptop, ShieldCheck, Check, AlertCircle } from 'lucide-vue-next'

// Halaman login selalu mengikuti tema sistem laptop (Dark / Light)
const preferredDark = usePreferredDark()
const isDarkMode = computed(() => preferredDark.value)

// Sinkronisasi kelas dark pada <html> secara dinamis mengikuti preferensi laptop
watch(preferredDark, (isDark) => {
  document.documentElement.classList.toggle('dark', isDark)
}, { immediate: true })

onUnmounted(() => {
  // Kembalikan ke preferensi tema dashboard saat berpindah dari halaman login
  const storedTheme = localStorage.getItem('theme')
  if (storedTheme === 'dark') {
    document.documentElement.classList.add('dark')
  } else if (storedTheme === 'light') {
    document.documentElement.classList.remove('dark')
  } else {
    document.documentElement.classList.toggle('dark', preferredDark.value)
  }
})

const username = ref('')
const password = ref('')
const rememberMe = ref(false) // Default unchecked
const usernameError = ref('')
const passwordError = ref('')
const showPassword = ref(false)
const hasRememberedAccount = ref(false)
const savedUsername = ref('')
const showManualForm = ref(false)

const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  const rememberedToken = localStorage.getItem('gconnect_remembered_token')
  const savedUser = localStorage.getItem('gconnect_saved_username')
  
  if (rememberedToken) {
    hasRememberedAccount.value = true
    savedUsername.value = savedUser || 'Administrator'
  } else if (savedUser) {
    username.value = savedUser
  }
})

const handleQuickBypass = () => {
  const success = authStore.quickLogin()
  if (!success) {
    hasRememberedAccount.value = false
    showManualForm.value = true
  }
}

const loginMutation = useMutation({
  mutationFn: async () => {
    const params = new URLSearchParams()
    params.append('username', username.value)
    params.append('password', password.value)

    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Gagal masuk')
    }
    return response.json()
  },
  onSuccess: (data) => {
    authStore.setToken(data.access_token, rememberMe.value, username.value)

    if (rememberMe.value) {
      localStorage.setItem('gconnect_remembered_token', data.access_token)
      localStorage.setItem('gconnect_saved_username', username.value)
    } else {
      localStorage.removeItem('gconnect_remembered_token')
      localStorage.removeItem('gconnect_saved_username')
    }

    router.push('/dashboard')
  },
  onError: (err: any) => {
    const msg = (err.message || '').toLowerCase()
    if (msg.includes('username tidak terdaftar') || (msg.includes('username') && !msg.includes('sandi') && !msg.includes('password'))) {
      usernameError.value = 'Username tidak terdaftar'
      passwordError.value = ''
    } else if (msg.includes('kata sandi') || msg.includes('sandi') || msg.includes('password')) {
      passwordError.value = 'Kata sandi salah'
      usernameError.value = ''
    } else if (msg.includes('nonaktif') || msg.includes('inactive')) {
      usernameError.value = 'Akun dinonaktifkan'
      passwordError.value = ''
    } else {
      usernameError.value = 'Periksa username'
      passwordError.value = 'Periksa kata sandi'
    }
  }
})

const handleLogin = () => {
  usernameError.value = ''
  passwordError.value = ''

  if (!username.value.trim()) {
    usernameError.value = 'Harap masukkan username'
    return
  }
  if (!password.value) {
    passwordError.value = 'Harap masukkan kata sandi'
    return
  }

  loginMutation.mutate()
}
</script>

<template>
  <div class="relative flex items-center justify-center min-h-screen overflow-hidden bg-[#F0FDF4] dark:bg-[#030712] text-foreground transition-colors duration-500">

    <!-- Theme Indicator Floating Pill in Top-Right (Always synced with laptop OS) -->
    <div class="absolute top-4 right-4 z-30">
      <div 
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-slate-200/80 dark:border-white/10 text-xs font-semibold text-slate-700 dark:text-slate-200 shadow-sm select-none cursor-default"
        :title="`Tema login otomatis mengikuti sistem laptop (${isDarkMode ? 'Mode Gelap' : 'Mode Terang'})`"
      >
        <Laptop class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
        <span>{{ isDarkMode ? 'Mode Gelap' : 'Mode Terang' }}</span>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- ☀️ 1. DAYTIME SCENE: WHITE SKY, FLYING BIRDS, CROPS & FIELD -->
    <!-- ======================================================== -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none select-none dark:hidden transition-opacity duration-500">
      
      <!-- Sky Gradient: Clean Airy White to Soft Meadow Horizon -->
      <div class="absolute inset-0 bg-gradient-to-b from-[#FFFFFF] via-[#F8FAFC] to-[#EDFDF5]"></div>

      <!-- Soft Sun Glow Halo -->
      <div class="absolute -top-32 right-12 w-[650px] h-[650px] rounded-full bg-amber-100/40 blur-[130px]"></div>

      <!-- Soaring Flock of Birds (Silhouette Burung Camar Melayang Asli Sesuai Referensi) -->
      <div class="birds-container absolute inset-0 overflow-hidden pointer-events-none">
        <div class="bird bird-1">
          <svg viewBox="0 0 64 28" class="bird-svg text-slate-800 dark:text-slate-200">
            <!-- Left Wing -->
            <g class="seagull-wing-l">
              <path d="M32,22 C26,14 20,4 12,4 C6,4 2,10 0,14 C4,11 9,8 14,8 C22,8 27,16 32,22 Z" fill="currentColor" />
            </g>
            <!-- Right Wing -->
            <g class="seagull-wing-r">
              <path d="M32,22 C37,16 42,7 50,7 C56,7 60,11 64,18 C60,14 55,11 49,11 C42,11 37,17 32,22 Z" fill="currentColor" />
            </g>
            <!-- Center Body -->
            <circle cx="32" cy="21.5" r="3.5" fill="currentColor" />
          </svg>
        </div>

        <div class="bird bird-2">
          <svg viewBox="0 0 64 28" class="bird-svg text-slate-700 dark:text-slate-300">
            <g class="seagull-wing-l">
              <path d="M32,22 C26,14 20,4 12,4 C6,4 2,10 0,14 C4,11 9,8 14,8 C22,8 27,16 32,22 Z" fill="currentColor" />
            </g>
            <g class="seagull-wing-r">
              <path d="M32,22 C37,16 42,7 50,7 C56,7 60,11 64,18 C60,14 55,11 49,11 C42,11 37,17 32,22 Z" fill="currentColor" />
            </g>
            <circle cx="32" cy="21.5" r="3.5" fill="currentColor" />
          </svg>
        </div>

        <div class="bird bird-3">
          <svg viewBox="0 0 64 28" class="bird-svg text-slate-800 dark:text-slate-200">
            <g class="seagull-wing-l">
              <path d="M32,22 C26,14 20,4 12,4 C6,4 2,10 0,14 C4,11 9,8 14,8 C22,8 27,16 32,22 Z" fill="currentColor" />
            </g>
            <g class="seagull-wing-r">
              <path d="M32,22 C37,16 42,7 50,7 C56,7 60,11 64,18 C60,14 55,11 49,11 C42,11 37,17 32,22 Z" fill="currentColor" />
            </g>
            <circle cx="32" cy="21.5" r="3.5" fill="currentColor" />
          </svg>
        </div>

        <div class="bird bird-4">
          <svg viewBox="0 0 64 28" class="bird-svg text-slate-700 dark:text-slate-300">
            <g class="seagull-wing-l">
              <path d="M32,22 C26,14 20,4 12,4 C6,4 2,10 0,14 C4,11 9,8 14,8 C22,8 27,16 32,22 Z" fill="currentColor" />
            </g>
            <g class="seagull-wing-r">
              <path d="M32,22 C37,16 42,7 50,7 C56,7 60,11 64,18 C60,14 55,11 49,11 C42,11 37,17 32,22 Z" fill="currentColor" />
            </g>
            <circle cx="32" cy="21.5" r="3.5" fill="currentColor" />
          </svg>
        </div>
      </div>

      <!-- Floating Wispy Morning Clouds -->
      <div class="cloud cloud-1"></div>
      <div class="cloud cloud-2"></div>
      <div class="cloud cloud-3"></div>

      <!-- Lush Clean Terraced Farmland Landscape Silhouette -->
      <div class="absolute bottom-0 inset-x-0 w-full h-[270px] sm:h-[350px] pointer-events-none">
        <svg class="w-full h-full object-cover" viewBox="0 0 1440 360" preserveAspectRatio="none" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <!-- Distant Hills Gradient -->
            <linearGradient id="dayHills" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#99f6e4" stop-opacity="0.5" />
              <stop offset="100%" stop-color="#34d399" stop-opacity="0.75" />
            </linearGradient>

            <!-- Mid Terraces Gradient -->
            <linearGradient id="dayMidFarmland" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#4ade80" stop-opacity="0.85" />
              <stop offset="100%" stop-color="#16a34a" stop-opacity="0.95" />
            </linearGradient>

            <!-- Foreground Fertile Soil & Crops Gradient -->
            <linearGradient id="dayCropsBase" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#15803d" />
              <stop offset="50%" stop-color="#14532d" />
              <stop offset="100%" stop-color="#052e16" />
            </linearGradient>
          </defs>

          <!-- 1. Distant Mountain Silhouette -->
          <path d="M0,170 Q240,110 480,160 T960,140 Q1200,105 1440,170 L1440,360 L0,360 Z" fill="url(#dayHills)"></path>

          <!-- 2. Middle Terraced Hills Ridge -->
          <path d="M0,205 C180,175 360,240 540,200 C720,165 900,235 1080,195 C1260,160 1380,220 1440,205 L1440,360 L0,360 Z" fill="url(#dayMidFarmland)"></path>
          <path d="M0,205 C180,175 360,240 540,200 C720,165 900,235 1080,195 C1260,160 1380,220 1440,205" stroke="#bbf7d0" stroke-width="1.5" stroke-opacity="0.6" fill="none"></path>

          <!-- 3. Foreground Fertile Farmland Earth Base -->
          <path d="M0,245 C200,215 400,275 600,240 C800,205 1000,270 1200,235 C1350,210 1410,250 1440,245 L1440,360 L0,360 Z" fill="url(#dayCropsBase)"></path>
        </svg>
      </div>

    </div>

    <!-- ======================================================== -->
    <!-- 🌙 2. NIGHTTIME SCENE: STARLIT LUSH TERRACES (DARK MODE)  -->
    <!-- ======================================================== -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none select-none hidden dark:block transition-opacity duration-500">
      
      <!-- Deep Midnight Sky: Cosmic Blue to Deep Nocturnal Forest -->
      <div class="absolute inset-0 bg-gradient-to-b from-[#020617] via-[#04141c] to-[#021811]"></div>

      <!-- Soft Celestial Nebula & Moonlit Mist -->
      <div class="absolute -top-24 right-1/4 w-[650px] h-[650px] rounded-full bg-teal-500/12 blur-[150px]"></div>
      <div class="absolute top-1/3 left-1/4 w-[550px] h-[550px] rounded-full bg-emerald-600/15 blur-[140px]"></div>

      <!-- Twinkling Celestial Stars -->
      <div class="stars-container absolute inset-0">
        <div class="star star-1"></div>
        <div class="star star-2"></div>
        <div class="star star-3"></div>
        <div class="star star-4"></div>
        <div class="star star-5"></div>
        <div class="star star-6"></div>
        <div class="star star-7"></div>
        <div class="star star-8"></div>
        <div class="star star-9"></div>
        <div class="star star-10"></div>
        <div class="star star-11"></div>
        <div class="star star-12"></div>
      </div>

      <!-- Farmland Fireflies (Bio-luminescent Warm Glow) -->
      <div class="firefly firefly-1"></div>
      <div class="firefly firefly-2"></div>
      <div class="firefly firefly-3"></div>
      <div class="firefly firefly-4"></div>
      <div class="firefly firefly-5"></div>
      <div class="firefly firefly-6"></div>
      <div class="firefly firefly-7"></div>

      <!-- Nocturnal Farmland Mountain & Terraces Landscape Silhouette -->
      <div class="absolute bottom-0 inset-x-0 w-full h-[260px] sm:h-[340px] pointer-events-none">
        <svg class="w-full h-full object-cover" viewBox="0 0 1440 360" preserveAspectRatio="none" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="nightMountain" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#0f2b38" stop-opacity="0.7" />
              <stop offset="100%" stop-color="#06221c" stop-opacity="0.9" />
            </linearGradient>

            <linearGradient id="nightMidTerraces" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#063228" stop-opacity="0.85" />
              <stop offset="100%" stop-color="#021f19" stop-opacity="0.95" />
            </linearGradient>

            <linearGradient id="nightForeground" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#04271f" />
              <stop offset="60%" stop-color="#021410" />
              <stop offset="100%" stop-color="#010a08" />
            </linearGradient>
          </defs>

          <!-- 1. Distant Midnight Mountain -->
          <path d="M0,160 Q240,90 480,150 T960,130 Q1200,90 1440,160 L1440,360 L0,360 Z" fill="url(#nightMountain)"></path>

          <!-- 2. Middle Nocturnal Terraced Ridge -->
          <path d="M0,195 C180,160 360,230 540,190 C720,150 900,225 1080,185 C1260,145 1380,210 1440,195 L1440,360 L0,360 Z" fill="url(#nightMidTerraces)"></path>
          <!-- Moonlit Rim Line -->
          <path d="M0,195 C180,160 360,230 540,190 C720,150 900,225 1080,185 C1260,145 1380,210 1440,195" stroke="#34d399" stroke-width="1.5" stroke-opacity="0.35" fill="none"></path>

          <!-- 3. Foreground Dark Fertile Earth Silhouette -->
          <path d="M0,240 C200,210 400,270 600,235 C800,200 1000,265 1200,230 C1350,205 1410,245 1440,240 L1440,360 L0,360 Z" fill="url(#nightForeground)"></path>
          <!-- Foreground Dewdrop Rim -->
          <path d="M0,240 C200,210 400,270 600,235 C800,200 1000,265 1200,230 C1350,205 1410,245 1440,240" stroke="#10b981" stroke-width="1.5" stroke-opacity="0.25" fill="none"></path>
        </svg>
      </div>

    </div>

    <!-- Card Container -->
    <div class="relative z-10 w-full max-w-sm px-4 animate-slide-up-in">
      <div class="relative bg-card/90 dark:bg-[#0b0f14]/85 backdrop-blur-2xl border border-border/80 dark:border-white/[0.12] rounded-3xl shadow-2xl shadow-black/10 dark:shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85)] p-8 space-y-6 overflow-hidden">
        <!-- Top Dewy Frosted Rim Line -->
        <div class="absolute inset-x-0 top-0 h-[1.5px] bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none"></div>

        <!-- Brand -->
        <div class="flex flex-col items-center gap-3 mb-2">
          <div class="flex items-center justify-center w-20 h-20 select-none">
            <img src="/logo-icon.webp" alt="Lab ELINS Logo" class="w-full h-full object-contain drop-shadow-md" />
          </div>
          <div class="text-center">
            <h1 class="text-2xl font-bold tracking-tight text-foreground">G-CONNECT</h1>
            <p class="text-sm text-muted-foreground mt-0.5">Smart Farming Platform</p>
          </div>
        </div>

        <!-- Divider -->
        <div class="border-t border-border/50 dark:border-white/[0.08]"></div>

        <!-- Quick Login / Bypass Card for Remembered User -->
        <div v-if="hasRememberedAccount && !showManualForm" class="space-y-4 animate-slide-up-in">
          <div class="p-4 rounded-2xl bg-emerald-500/10 dark:bg-emerald-950/30 border border-emerald-500/30 flex items-center gap-3.5 shadow-sm">
            <div class="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0 shadow-inner">
              <User class="w-6 h-6" />
            </div>
            <div class="min-w-0 flex-1">
              <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">Akun Tersimpan</span>
              <p class="text-sm sm:text-base font-extrabold text-foreground truncate mt-0.5">{{ savedUsername }}</p>
            </div>
          </div>

          <Button
            type="button"
            class="w-full h-11 font-bold text-sm bg-emerald-600 hover:bg-emerald-700 text-white shadow-md cursor-pointer gap-2 active:scale-[0.99] transition-all rounded-xl"
            @click="handleQuickBypass"
          >
            <span>Masuk Cepat</span>
            <ArrowRight class="w-4 h-4" />
          </Button>

          <div class="text-center pt-2">
            <button
              type="button"
              @click="showManualForm = true"
              class="text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            >
              Gunakan Akun Lain / Masuk Manual &rarr;
            </button>
          </div>
        </div>

        <!-- Form (Using semantic form so browser password manager natively prompts to save credentials) -->
        <form v-else @submit.prevent="handleLogin" class="space-y-4 animate-slide-up-in">
          <!-- Username Field -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between min-h-[20px]">
              <Label for="username" class="text-sm font-medium">Username</Label>
              <!-- Inline Header Error Badge for Username -->
              <transition name="popup-scale">
                <span 
                  v-if="usernameError" 
                  class="flex items-center gap-1 text-[11px] font-bold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 px-2 py-0.5 rounded-full border border-red-200 dark:border-red-800/50 animate-shake select-none"
                >
                  <AlertCircle class="w-3 h-3 stroke-[2.5]" />
                  {{ usernameError }}
                </span>
              </transition>
            </div>

            <Input
              id="username"
              name="username"
              v-model="username"
              type="text"
              autocomplete="username"
              placeholder="e.g. gconnect"
              class="h-10 bg-background/50 dark:bg-[#06090e]/80 dark:border-white/[0.12] dark:focus:border-emerald-500 transition-all"
              :class="usernameError ? 'border-red-500 dark:border-red-500/80 ring-1 ring-red-500/30' : ''"
              @input="usernameError = ''"
              required
            />
          </div>

          <!-- Password Field -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between min-h-[20px]">
              <Label for="password" class="text-sm font-medium">Password</Label>
              <!-- Inline Header Error Badge for Password -->
              <transition name="popup-scale">
                <span 
                  v-if="passwordError" 
                  class="flex items-center gap-1 text-[11px] font-bold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 px-2 py-0.5 rounded-full border border-red-200 dark:border-red-800/50 animate-shake select-none"
                >
                  <AlertCircle class="w-3 h-3 stroke-[2.5]" />
                  {{ passwordError }}
                </span>
              </transition>
            </div>

            <div class="relative">
              <Input
                id="password"
                name="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                class="pr-10 h-10 bg-background/50 dark:bg-[#06090e]/80 dark:border-white/[0.12] dark:focus:border-emerald-500 hide-password-eye transition-all"
                :class="passwordError ? 'border-red-500 dark:border-red-500/80 ring-1 ring-red-500/30' : ''"
                @input="passwordError = ''"
                required
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                tabindex="-1"
              >
                <component :is="showPassword ? EyeOff : Eye" class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Remember Me Checkbox (Custom Interactive Pill) -->
          <div class="flex items-center justify-between pt-0.5 pb-1 select-none">
            <button
              type="button"
              @click="rememberMe = !rememberMe"
              class="flex items-center gap-2.5 cursor-pointer group text-left focus:outline-none"
            >
              <!-- Custom Checkbox Box -->
              <div 
                class="w-4.5 h-4.5 rounded-md border flex items-center justify-center transition-all duration-200 shadow-2xs"
                :class="rememberMe 
                  ? 'bg-primary border-primary text-primary-foreground shadow-sm shadow-primary/20 scale-105' 
                  : 'bg-background border-input hover:border-primary/60 group-hover:border-foreground/50'"
              >
                <Check v-if="rememberMe" class="w-3.5 h-3.5 stroke-[3]" />
              </div>
              <span 
                class="text-xs sm:text-sm font-medium transition-colors"
                :class="rememberMe ? 'text-foreground font-semibold' : 'text-muted-foreground group-hover:text-foreground'"
              >
                Ingat saya
              </span>
            </button>

            <button
              v-if="hasRememberedAccount"
              type="button"
              @click="showManualForm = false"
              class="text-xs text-primary hover:underline font-semibold cursor-pointer"
            >
              &larr; Masuk Cepat
            </button>
          </div>

          <!-- Submit -->
          <Button
            type="submit"
            class="w-full h-10 mt-2 font-semibold cursor-pointer shadow-sm active:scale-[0.99] transition-all"
            :disabled="loginMutation.isPending.value"
          >
            <span v-if="loginMutation.isPending.value" class="flex items-center gap-2">
              <span class="w-4 h-4 rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground animate-spin"></span>
              Signing in...
            </span>
            <span v-else>Sign In</span>
          </Button>
        </form>

      </div>

        <!-- Institutional Credits / Community Service Footer (Area-wide group hover) -->
        <div class="mt-8 text-center space-y-3 select-none group cursor-pointer">
          <p class="text-xs font-extrabold uppercase tracking-wider text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.6)]">
            Community Service Program
          </p>
          <div class="flex items-center justify-center gap-6 py-1 px-4 transition-all duration-300">
            <img src="/Logo-UGM.png" alt="Universitas Gadjah Mada" class="h-9 max-w-[50px] object-contain select-none brightness-0 invert group-hover:brightness-100 group-hover:invert-0 dark:group-hover:brightness-0 dark:group-hover:invert opacity-85 group-hover:opacity-100 group-hover:scale-105 transition-all duration-300 drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)] group-hover:drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]" title="Universitas Gadjah Mada" />
            <img src="/Logo-DIKE.png" alt="Departemen Ilmu Komputer dan Elektronika" class="h-8 max-w-[70px] object-contain select-none brightness-0 invert group-hover:brightness-100 group-hover:invert-0 dark:group-hover:invert opacity-85 group-hover:opacity-100 group-hover:scale-105 transition-all duration-300 drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)] group-hover:drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]" title="Departemen Ilmu Komputer dan Elektronika UGM" />
            <img src="/logo-icon.webp" alt="Laboratorium Elektronika dan Instrumentasi" class="h-8 max-w-[38px] object-contain select-none brightness-0 invert group-hover:brightness-100 group-hover:invert-0 opacity-85 group-hover:opacity-100 group-hover:scale-105 transition-all duration-300 drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)] group-hover:drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]" title="Laboratorium Elektronika dan Instrumentasi" />
            <img src="/logo-webdev.webp" alt="Webdev ERC" class="h-8 max-w-[38px] object-contain select-none brightness-0 invert group-hover:brightness-100 group-hover:invert-0 dark:group-hover:invert opacity-85 group-hover:opacity-100 group-hover:scale-105 transition-all duration-300 drop-shadow-[0_1px_2px_rgba(0,0,0,0.5)] group-hover:drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]" title="Webdev ERC" />
          </div>
          <p class="text-[11px] font-semibold text-white/90 drop-shadow-[0_1px_3px_rgba(0,0,0,0.6)]">
            &copy; 2026 G-CONNECT &bull; Laboratorium Riset Sistem Elektronika & Instrumentasi UGM
          </p>
        </div>

    </div>
  </div>
</template>

<style scoped>
@keyframes slide-up-in {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-slide-up-in {
  animation: slide-up-in 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

/* Twinkling Farmland Night Stars */
.star {
  position: absolute;
  border-radius: 50%;
  background: #ffffff;
  animation: star-twinkle var(--duration, 3s) ease-in-out infinite alternate;
}
.star-1  { top: 8%;  left: 12%; width: 2px; height: 2px; --duration: 2.8s; opacity: 0.8; }
.star-2  { top: 18%; left: 28%; width: 1.5px; height: 1.5px; --duration: 4.2s; opacity: 0.6; }
.star-3  { top: 12%; left: 45%; width: 2.5px; height: 2.5px; --duration: 3.1s; opacity: 0.9; box-shadow: 0 0 4px #a7f3d0; }
.star-4  { top: 22%; left: 62%; width: 1.5px; height: 1.5px; --duration: 3.7s; opacity: 0.7; }
.star-5  { top: 7%;  left: 78%; width: 2px; height: 2px; --duration: 4.5s; opacity: 0.85; }
.star-6  { top: 15%; left: 88%; width: 2px; height: 2px; --duration: 2.5s; opacity: 0.9; box-shadow: 0 0 3px #a7f3d0; }
.star-7  { top: 32%; left: 8%;  width: 1.5px; height: 1.5px; --duration: 3.4s; opacity: 0.65; }
.star-8  { top: 40%; left: 82%; width: 2px; height: 2px; --duration: 4.8s; opacity: 0.75; }
.star-9  { top: 28%; left: 93%; width: 1px; height: 1px; --duration: 2.2s; opacity: 0.5; }
.star-10 { top: 48%; left: 16%; width: 1.5px; height: 1.5px; --duration: 3.9s; opacity: 0.7; }
.star-11 { top: 5%;  left: 35%; width: 1.5px; height: 1.5px; --duration: 3.3s; opacity: 0.6; }
.star-12 { top: 25%; left: 50%; width: 2px; height: 2px; --duration: 4.0s; opacity: 0.85; }

@keyframes star-twinkle {
  0%   { opacity: 0.2; transform: scale(0.7); }
  50%  { opacity: 0.95; transform: scale(1.1); }
  100% { opacity: 0.3; transform: scale(0.8); }
}

/* Floating Fireflies (Warm Gentle Amber Glow) */
.firefly {
  position: absolute;
  width: 3.5px;
  height: 3.5px;
  border-radius: 50%;
  background: #fef08a;
  box-shadow: 0 0 8px 2px rgba(250, 204, 21, 0.7), 0 0 16px 4px rgba(234, 179, 8, 0.3);
  pointer-events: none;
  animation: firefly-float var(--float-time, 14s) ease-in-out infinite alternate, firefly-glow var(--glow-time, 3.5s) ease-in-out infinite alternate;
}

.firefly-1 { top: 62%; left: 16%; --float-time: 16s; --glow-time: 3.2s; animation-delay: 0s; }
.firefly-2 { top: 70%; left: 78%; --float-time: 14s; --glow-time: 2.7s; animation-delay: -3s; }
.firefly-3 { top: 52%; left: 84%; --float-time: 18s; --glow-time: 3.8s; animation-delay: -6s; }
.firefly-4 { top: 76%; left: 28%; --float-time: 15s; --glow-time: 2.4s; animation-delay: -1.5s; }
.firefly-5 { top: 58%; left: 8%;  --float-time: 20s; --glow-time: 4.1s; animation-delay: -4.5s; }
.firefly-6 { top: 44%; left: 72%; --float-time: 17s; --glow-time: 3.5s; animation-delay: -7s; }
.firefly-7 { top: 80%; left: 52%; --float-time: 19s; --glow-time: 2.9s; animation-delay: -2s; }

@keyframes firefly-float {
  0%   { transform: translate(0, 0); }
  25%  { transform: translate(25px, -35px); }
  50%  { transform: translate(-20px, -60px); }
  75%  { transform: translate(30px, -25px); }
  100% { transform: translate(-15px, -80px); }
}

@keyframes firefly-glow {
  0%, 100% { opacity: 0.1; transform: scale(0.6); }
  50%      { opacity: 0.85; transform: scale(1.15); }
}

/* Daytime Floating Wispy Clouds */
.cloud {
  position: absolute;
  background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.75) 0%, rgba(255, 255, 255, 0.35) 50%, transparent 75%);
  filter: blur(28px);
  border-radius: 50%;
  pointer-events: none;
  animation: cloud-drift var(--drift-duration, 32s) linear infinite;
}

.cloud-1 {
  width: 450px; height: 160px;
  top: 8%; left: -10%;
  --drift-duration: 35s;
}
.cloud-2 {
  width: 550px; height: 180px;
  top: 22%; left: 35%;
  --drift-duration: 42s;
  animation-delay: -15s;
}
.cloud-3 {
  width: 380px; height: 140px;
  top: 5%; left: 68%;
  --drift-duration: 30s;
  animation-delay: -8s;
}

@keyframes cloud-drift {
  0%   { transform: translateX(-50px); }
  50%  { transform: translateX(50px); }
  100% { transform: translateX(-50px); }
}

/* Daytime Floating Sunlit Pollen / Gentle Dust Sparkles */
.sparkle {
  position: absolute;
  width: 3.5px;
  height: 3.5px;
  border-radius: 50%;
  background: #fde047;
  box-shadow: 0 0 6px 1px rgba(234, 179, 8, 0.6);
  pointer-events: none;
  animation: sparkle-float var(--float-time, 14s) ease-in-out infinite alternate;
}

.sparkle-1 { top: 60%; left: 20%; --float-time: 14s; }
.sparkle-2 { top: 75%; left: 70%; --float-time: 16s; animation-delay: -3s; }
.sparkle-3 { top: 50%; left: 80%; --float-time: 13s; animation-delay: -6s; }
.sparkle-4 { top: 80%; left: 35%; --float-time: 15s; animation-delay: -2s; }
.sparkle-5 { top: 65%; left: 10%; --float-time: 18s; animation-delay: -4s; }

@keyframes sparkle-float {
  0%   { transform: translate(0, 0) scale(0.6); opacity: 0.2; }
  50%  { transform: translate(20px, -25px) scale(1.05); opacity: 0.7; }
  100% { transform: translate(-15px, -45px) scale(0.7); opacity: 0.25; }
}

/* Soaring Flying Birds Across Daylight Sky (Classic Seagull Flight) */
.bird {
  position: absolute;
  top: var(--bird-top, 15%);
  left: -90px;
  width: var(--bird-size, 38px);
  animation: bird-flight var(--fly-time, 24s) linear infinite;
  opacity: var(--bird-opacity, 0.75);
  pointer-events: none;
  will-change: transform;
}

.bird-1 { --bird-top: 9%;  --bird-size: 44px; --fly-time: 20s; animation-delay: 0s;   --bird-opacity: 0.85; }
.bird-2 { --bird-top: 14%; --bird-size: 34px; --fly-time: 24s; animation-delay: -6s;  --bird-opacity: 0.7; }
.bird-3 { --bird-top: 6%;  --bird-size: 26px; --fly-time: 28s; animation-delay: -14s; --bird-opacity: 0.6; }
.bird-4 { --bird-top: 18%; --bird-size: 38px; --fly-time: 22s; animation-delay: -3s;  --bird-opacity: 0.75; }

.bird-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

/* Authentic Seagull Arched Wing Flapping (Continuous Smooth Aerodynamic Wave) */
.seagull-wing-l {
  transform-origin: 32px 22px;
  animation: flap-seagull-l 1.2s cubic-bezier(0.42, 0, 0.58, 1) infinite;
  will-change: transform;
}
.seagull-wing-r {
  transform-origin: 32px 22px;
  animation: flap-seagull-r 1.2s cubic-bezier(0.42, 0, 0.58, 1) infinite;
  will-change: transform;
}

.bird-1 .seagull-wing-l, .bird-1 .seagull-wing-r { animation-duration: 1.25s; }
.bird-2 .seagull-wing-l, .bird-2 .seagull-wing-r { animation-duration: 1.1s; animation-delay: -0.3s; }
.bird-3 .seagull-wing-l, .bird-3 .seagull-wing-r { animation-duration: 0.98s; animation-delay: -0.6s; }
.bird-4 .seagull-wing-l, .bird-4 .seagull-wing-r { animation-duration: 1.35s; animation-delay: -0.4s; }

@keyframes flap-seagull-l {
  0% {
    transform: rotate(-22deg) scaleY(1.05);
  }
  32% {
    transform: rotate(16deg) scaleY(0.92);
  }
  50% {
    transform: rotate(24deg) scaleY(0.86);
  }
  75% {
    transform: rotate(-8deg) scaleY(0.98);
  }
  100% {
    transform: rotate(-22deg) scaleY(1.05);
  }
}

@keyframes flap-seagull-r {
  0% {
    transform: rotate(22deg) scaleY(1.05);
  }
  32% {
    transform: rotate(-16deg) scaleY(0.92);
  }
  50% {
    transform: rotate(-24deg) scaleY(0.86);
  }
  75% {
    transform: rotate(8deg) scaleY(0.98);
  }
  100% {
    transform: rotate(22deg) scaleY(1.05);
  }
}

@keyframes bird-flight {
  0%   { transform: translateX(-90px) translateY(0); }
  50%  { transform: translateX(calc(50vw)) translateY(-15px); }
  100% { transform: translateX(calc(100vw + 120px)) translateY(10px); }
}

/* Floating Error Tooltip Shake & Transition Animations */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-4px); }
  40%, 80% { transform: translateX(4px); }
}
.animate-shake {
  animation: shake 0.35s ease-in-out both;
}

.popup-scale-enter-active,
.popup-scale-leave-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.popup-scale-enter-from,
.popup-scale-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.92);
}

/* Hide default edge password eye icon */
.hide-password-eye::-ms-reveal,
.hide-password-eye::-ms-clear {
  display: none;
}
</style>



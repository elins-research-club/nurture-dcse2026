<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMutation } from '@tanstack/vue-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff, User, ArrowRight, ShieldCheck, Check } from 'lucide-vue-next'

const username = ref('')
const password = ref('')
const rememberMe = ref(false) // Default unchecked
const errorMsg = ref('')
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
      throw new Error(errData.detail || 'Invalid credentials')
    }
    return response.json()
  },
  onSuccess: (data) => {
    authStore.setToken(data.access_token, rememberMe.value, username.value)
    router.push('/dashboard')
  },
  onError: (err: any) => {
    errorMsg.value = err.message || 'Login failed'
  }
})

const handleLogin = () => {
  errorMsg.value = ''
  loginMutation.mutate()
}
</script>

<template>
  <div class="relative flex items-center justify-center min-h-screen overflow-hidden bg-background">

    <!-- Animated gradient blobs -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
    </div>

    <!-- Subtle grid overlay -->
    <div class="absolute inset-0 bg-[linear-gradient(rgba(0,200,80,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,200,80,0.03)_1px,transparent_1px)] bg-[size:48px_48px] pointer-events-none"></div>

    <!-- Card -->
    <div class="relative z-10 w-full max-w-sm px-4 animate-slide-up-in">
      <div class="bg-card/80 backdrop-blur-xl border border-border/60 rounded-2xl shadow-2xl shadow-black/10 dark:shadow-black/40 p-8 space-y-6">

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
        <div class="border-t border-border/50"></div>

        <!-- Quick Login / Bypass Card for Remembered User -->
        <div v-if="hasRememberedAccount && !showManualForm" class="space-y-4 animate-slide-up-in">
          <div class="p-4 rounded-2xl bg-emerald-500/10 dark:bg-emerald-500/15 border border-emerald-500/30 flex items-center gap-3.5 shadow-sm">
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
          <div class="space-y-1.5">
            <Label for="username" class="text-sm font-medium">Username</Label>
            <Input
              id="username"
              name="username"
              v-model="username"
              type="text"
              autocomplete="username"
              placeholder="e.g. gconnect"
              class="h-10 bg-background/50"
              required
            />
          </div>

          <div class="space-y-1.5">
            <Label for="password" class="text-sm font-medium">Password</Label>
            <div class="relative">
              <Input
                id="password"
                name="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                class="pr-10 h-10 bg-background/50 hide-password-eye"
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

          <!-- Error -->
          <div v-if="errorMsg" class="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
            <span class="w-1.5 h-1.5 rounded-full bg-destructive shrink-0"></span>
            {{ errorMsg }}
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

        <!-- Institutional Credits / Community Service Footer -->
        <div class="mt-8 text-center space-y-4">
          <p class="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
            Community Service Program
          </p>
          <div class="flex items-center justify-center gap-6 grayscale opacity-80 hover:grayscale-0 hover:opacity-100 transition-all duration-300">
            <img src="/Logo-UGM.png" alt="Universitas Gadjah Mada" class="h-[45px] max-w-[53px] object-contain select-none dark:brightness-0 dark:invert" title="Universitas Gadjah Mada" />
            <img src="/Logo-DIKE.png" alt="Departemen Ilmu Komputer dan Elektronika" class="h-9 max-w-[75px] object-contain select-none dark:brightness-0 dark:invert" title="Departemen Ilmu Komputer dan Elektronika UGM" />
            <img src="/logo-icon.webp" alt="Laboratorium Elektronika dan Instrumentasi" class="h-9 max-w-[40px] object-contain select-none" title="Laboratorium Elektronika dan Instrumentasi" />
            <img src="/logo-webdev.webp" alt="Webdev ERC" class="h-9 max-w-[40px] object-contain select-none dark:invert" title="Webdev ERC" />
          </div>
          <p class="text-[11px] font-medium text-slate-500 dark:text-slate-400">
            &copy; 2026 G-CONNECT &bull; Laboratorium ELINS DIKE UGM
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

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
  animation: drift 12s ease-in-out infinite alternate;
}
.dark .blob { opacity: 0.2; }

.blob-1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, hsl(120, 80%, 40%) 0%, transparent 70%);
  top: -150px; left: -150px;
  animation-delay: 0s;
}
.blob-2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, hsl(140, 70%, 50%) 0%, transparent 70%);
  bottom: -100px; right: -100px;
  animation-delay: -4s;
}
.blob-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, hsl(100, 60%, 55%) 0%, transparent 70%);
  top: 40%; left: 55%;
  animation-delay: -8s;
  animation-duration: 16s;
}

@keyframes drift {
  0%   { transform: translate(0, 0) scale(1); }
  33%  { transform: translate(40px, -30px) scale(1.05); }
  66%  { transform: translate(-20px, 40px) scale(0.95); }
  100% { transform: translate(30px, 20px) scale(1.02); }
}

/* Hide default edge password eye icon */
.hide-password-eye::-ms-reveal,
.hide-password-eye::-ms-clear {
  display: none;
}
</style>



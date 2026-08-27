<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMutation } from '@tanstack/vue-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff } from 'lucide-vue-next'

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const showPassword = ref(false)

const router = useRouter()
const authStore = useAuthStore()

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
    authStore.setToken(data.access_token)
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

        <!-- Form -->
        <div class="space-y-4">
          <div class="space-y-1.5">
            <Label for="username" class="text-sm font-medium">Username</Label>
            <Input
              id="username"
              v-model="username"
              type="text"
              autocomplete="username"
              placeholder="e.g. gconnect"
              class="h-10 bg-background/50"
              @keyup.enter="handleLogin"
            />
          </div>

          <div class="space-y-1.5">
            <Label for="password" class="text-sm font-medium">Password</Label>
            <div class="relative">
              <Input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                @keyup.enter="handleLogin"
                class="pr-10 h-10 bg-background/50 hide-password-eye"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <component :is="showPassword ? EyeOff : Eye" class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Error -->
          <div v-if="errorMsg" class="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
            <span class="w-1.5 h-1.5 rounded-full bg-destructive shrink-0"></span>
            {{ errorMsg }}
          </div>

          <!-- Submit -->
          <Button
            class="w-full h-10 mt-2 font-semibold"
            @click="handleLogin"
            :disabled="loginMutation.isPending.value"
          >
            <span v-if="loginMutation.isPending.value" class="flex items-center gap-2">
              <span class="w-4 h-4 rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground animate-spin"></span>
              Signing in...
            </span>
            <span v-else>Sign In</span>
          </Button>
        </div>

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



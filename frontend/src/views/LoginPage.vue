<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMutation } from '@tanstack/vue-query'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Eye, EyeOff } from 'lucide-vue-next'

const username = ref('gconnect')
const password = ref('atminelins123')
const errorMsg = ref('')
const showPassword = ref(false)

const router = useRouter()
const authStore = useAuthStore()

const loginMutation = useMutation({
  mutationFn: async () => {
    const params = new URLSearchParams()
    params.append('username', username.value)
    params.append('password', password.value)

    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params
    })

    if (!response.ok) {
      throw new Error('Invalid credentials')
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
  <div class="flex items-center justify-center min-h-screen p-4 bg-muted/20">
    <Card class="w-full max-w-sm">
      <CardHeader>
        <CardTitle class="text-2xl font-bold">G-CONNECT</CardTitle>
        <CardDescription>Enter your credentials to access the dashboard</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <Label for="username">Username</Label>
          <Input id="username" v-model="username" type="text" placeholder="Enter username" />
        </div>
        <div class="space-y-2">
          <Label for="password">Password</Label>
          <div class="relative">
            <Input id="password" v-model="password" :type="showPassword ? 'text' : 'password'" placeholder="Enter password" @keyup.enter="handleLogin" class="pr-10" />
            <button type="button" @click="showPassword = !showPassword" class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
              <component :is="showPassword ? EyeOff : Eye" class="w-4 h-4" />
            </button>
          </div>
        </div>
        <div v-if="errorMsg" class="text-sm text-destructive font-medium">
          {{ errorMsg }}
        </div>
      </CardContent>
      <CardFooter>
        <Button class="w-full" @click="handleLogin" :disabled="loginMutation.isPending.value">
          {{ loginMutation.isPending.value ? 'Logging in...' : 'Sign In' }}
        </Button>
      </CardFooter>
    </Card>
  </div>
</template>

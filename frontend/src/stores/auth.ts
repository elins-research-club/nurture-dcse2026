import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<any>(null)
  const router = useRouter()

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    if (router) {
      router.push('/dashboard')
    }
  }

  return {
    token,
    user,
    setToken,
    logout,
    isAuthenticated: () => !!token.value
  }
})

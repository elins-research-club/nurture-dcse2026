import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

export function isTokenExpired(tokenStr: string | null): boolean {
  if (!tokenStr) return true
  try {
    const parts = tokenStr.split('.')
    if (parts.length !== 3) return true
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    if (!payload.exp) return false
    return Date.now() >= payload.exp * 1000
  } catch {
    return true
  }
}

export const useAuthStore = defineStore('auth', () => {
  const rawToken = localStorage.getItem('token') || sessionStorage.getItem('token')
  const initialToken = isTokenExpired(rawToken) ? null : rawToken
  if (rawToken && isTokenExpired(rawToken)) {
    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
    localStorage.removeItem('gconnect_remembered_token')
  }

  const token = ref<string | null>(initialToken)
  const user = ref<any>(null)
  const router = useRouter()

  const isRemembered = ref<boolean>(
    !!localStorage.getItem('token') && !!localStorage.getItem('gconnect_remembered_token')
  )
  const savedUsername = ref<string>(localStorage.getItem('gconnect_saved_username') || '')

  const setToken = (newToken: string, remember: boolean = false, usernameStr: string = '') => {
    token.value = newToken
    isRemembered.value = remember
    savedUsername.value = usernameStr
    if (remember) {
      localStorage.setItem('token', newToken)
      localStorage.setItem('gconnect_remembered_token', newToken)
      if (usernameStr) {
        localStorage.setItem('gconnect_saved_username', usernameStr)
      }
      sessionStorage.removeItem('token')
    } else {
      sessionStorage.setItem('token', newToken)
      localStorage.removeItem('token')
      localStorage.removeItem('gconnect_remembered_token')
      localStorage.removeItem('gconnect_saved_username')
    }
  }

  const quickLogin = () => {
    const remembered = localStorage.getItem('gconnect_remembered_token')
    if (remembered && !isTokenExpired(remembered)) {
      token.value = remembered
      isRemembered.value = true
      savedUsername.value = localStorage.getItem('gconnect_saved_username') || 'Administrator'
      localStorage.setItem('token', remembered)
      if (router) {
        router.push('/dashboard')
      }
      return true
    }
    if (remembered && isTokenExpired(remembered)) {
      localStorage.removeItem('gconnect_remembered_token')
    }
    return false
  }

  const logout = (clearRemembered: boolean = false) => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
    if (clearRemembered) {
      isRemembered.value = false
      savedUsername.value = ''
      localStorage.removeItem('gconnect_remembered_token')
      localStorage.removeItem('gconnect_saved_username')
    }
    if (router && router.currentRoute.value.path !== '/login') {
      router.push('/login')
    }
  }

  const login = (newToken: string, userData?: any) => {
    token.value = newToken
    if (userData) user.value = userData
    localStorage.setItem('token', newToken)
  }

  const isAuthenticated = () => {
    if (!token.value) return false
    if (isTokenExpired(token.value)) {
      logout()
      return false
    }
    return true
  }

  return {
    token,
    user,
    isRemembered,
    savedUsername,
    setToken,
    login,
    quickLogin,
    logout,
    isAuthenticated
  }
})

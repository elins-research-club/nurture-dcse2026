import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(
    localStorage.getItem('token') || sessionStorage.getItem('token')
  )
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
    if (remembered) {
      token.value = remembered
      isRemembered.value = true
      savedUsername.value = localStorage.getItem('gconnect_saved_username') || 'Administrator'
      localStorage.setItem('token', remembered)
      if (router) {
        router.push('/dashboard')
      }
      return true
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
    if (router) {
      router.push('/dashboard')
    }
  }

  return {
    token,
    user,
    isRemembered,
    savedUsername,
    setToken,
    quickLogin,
    logout,
    isAuthenticated: () => !!token.value
  }
})

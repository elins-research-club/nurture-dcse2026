<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTelemetryStore } from '@/stores/telemetry'
import Lenis from 'lenis'

const router = useRouter()
const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()

let lenis: Lenis | null = null
let rafId: number | null = null

onMounted(() => {
  // Initialize Lenis Smooth Scrolling
  lenis = new Lenis({
    duration: 1.1,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    orientation: 'vertical',
    gestureOrientation: 'vertical',
    smoothWheel: true,
    wheelMultiplier: 1,
    touchMultiplier: 1.5,
    infinite: false,
  })

  function raf(time: number) {
    lenis?.raf(time)
    rafId = requestAnimationFrame(raf)
  }

  rafId = requestAnimationFrame(raf)

  // Reset scroll to top smoothly on route change
  router.afterEach(() => {
    lenis?.scrollTo(0, { immediate: true })
  })

  if (authStore.isAuthenticated()) {
    telemetryStore.connectWebSocket()
  }
})

onUnmounted(() => {
  if (rafId !== null) {
    cancelAnimationFrame(rafId)
  }
  lenis?.destroy()
  lenis = null
})

watch(() => authStore.token, (token) => {
  if (token) {
    telemetryStore.connectWebSocket()
  } else {
    telemetryStore.disconnectWebSocket()
  }
})
</script>

<template>
  <div class="min-h-screen bg-background text-foreground flex flex-col font-sans antialiased">
    <RouterView v-slot="{ Component, route }">
      <Transition name="page" mode="out-in">
        <component :is="Component" :key="route.name || route.path" />
      </Transition>
    </RouterView>
  </div>
</template>

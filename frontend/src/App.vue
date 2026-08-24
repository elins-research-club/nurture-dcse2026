<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTelemetryStore } from '@/stores/telemetry'

const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()

onMounted(() => {
  if (authStore.isAuthenticated()) {
    telemetryStore.connectWebSocket()
  }
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
    <RouterView />
  </div>
</template>

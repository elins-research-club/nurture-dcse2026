<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useDark } from '@vueuse/core'
import { useTelemetryStore } from '@/stores/telemetry'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Sun, Moon, CheckCircle, XCircle, Loader2, ChevronDown, ChevronRight, Sprout } from 'lucide-vue-next'

const tabList = [
  { value: 'appearance', label: 'Tampilan' },
  { value: 'system', label: 'Sistem' },
  { value: 'alerts', label: 'Notifikasi' },
  { value: 'thresholds', label: 'Sensor & Batas' },
  { value: 'security', label: 'Keamanan' },
  { value: 'about', label: 'Tentang' }
]

const activeTab = ref('appearance')
const tabRefs = ref<Record<string, HTMLElement | any>>({})
const prevTabIndex = ref(0)
const bounceClass = ref('')

const setTabRef = (key: string, el: any) => {
  if (el) {
    tabRefs.value[key] = el.$el || el
  }
}

const transitionTiming = computed(() => {
  const currentIndex = tabList.findIndex(t => t.value === activeTab.value)
  if (currentIndex === 0 || currentIndex === tabList.length - 1) {
    return 'cubic-bezier(0.22, 1, 0.36, 1)'
  }
  return 'cubic-bezier(0.34, 1.25, 0.64, 1)'
})

const sliderStyle = ref({
  left: '0px',
  top: '0px',
  width: '0px',
  height: '0px',
  opacity: 0
})

const updateSlider = () => {
  nextTick(() => {
    const currentIndex = tabList.findIndex(t => t.value === activeTab.value)
    const el = tabRefs.value[activeTab.value]
    if (el) {
      sliderStyle.value = {
        left: `${el.offsetLeft}px`,
        top: `${el.offsetTop}px`,
        width: `${el.offsetWidth}px`,
        height: `${el.offsetHeight}px`,
        opacity: 1
      }
      
      // Determine wall collision squish effect
      if (currentIndex === tabList.length - 1 && prevTabIndex.value < currentIndex) {
        bounceClass.value = 'tab-squish-right'
      } else if (currentIndex === 0 && prevTabIndex.value > currentIndex) {
        bounceClass.value = 'tab-squish-left'
      } else if (prevTabIndex.value !== currentIndex) {
        bounceClass.value = 'tab-stretch-mid'
      }
      
      setTimeout(() => {
        bounceClass.value = ''
      }, 400)
      
      prevTabIndex.value = currentIndex
    }
  })
}

watch(activeTab, () => {
  updateSlider()
})

const isDarkMode = useDark({
  storageKey: 'theme',
  valueDark: 'dark',
  valueLight: 'light'
})

const showModal = ref(false)
const modalType = ref<'success' | 'error'>('success')
const modalMessage = ref('')

const toggleTheme = (dark: boolean) => {
  isDarkMode.value = dark
}

const API_BASE_URL = '/api/v1'

const systemConfig = ref({
  node_status_check_interval: 15,
  telemetry_cache_interval: 30,
  data_retention_days: 30,
  offline_threshold_mins: 15,
  telegram_bot_token: '',
  telegram_chat_id: ''
})

const isLoadingConfig = ref(true)
const isSavingConfig = ref(false)
const isTestingTelegram = ref(false)
const authStore = useAuthStore()
const telemetryStore = useTelemetryStore()

const ujiWebpush = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/push/test`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    const data = await res.json().catch(() => ({}))
    modalType.value = res.ok ? 'success' : 'error'
    modalMessage.value = res.ok
      ? `Notifikasi terkirim ke ${data.terkirim} perangkat.`
      : (data.detail || 'Gagal mengirim notifikasi.')
  } catch (e) {
    modalType.value = 'error'
    modalMessage.value = 'Gagal menghubungi server.'
  }
  showModal.value = true
}

const loadSystemConfig = async () => {
  try {
    isLoadingConfig.value = true
    const headers: Record<string, string> = {}
    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`
    }
    const res = await fetch(`${API_BASE_URL}/system/config`, { headers })
    if (res.ok) {
      const data = await res.json()
      systemConfig.value = {
        offline_threshold_mins: data.offline_threshold_mins ?? 20,
        telegram_bot_token: data.telegram_bot_token ?? '',
        telegram_chat_id: data.telegram_chat_id ?? ''
      }
    }
  } catch (error) {
    console.error('Failed to load system config:', error)
  } finally {
    isLoadingConfig.value = false
  }
}

watch(activeTab, (newTab) => {
  if (newTab === 'system') {
    loadSystemConfig()
  } else if (newTab === 'thresholds') {
    fetchSensors()
  }
})

const saveSystemConfig = async () => {
  try {
    isSavingConfig.value = true
    const res = await fetch(`${API_BASE_URL}/system/config`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify(systemConfig.value)
    })
    if (res.ok) {
      await loadSystemConfig()
      modalType.value = 'success'
      modalMessage.value = 'Pengaturan sistem berhasil disimpan'
      showModal.value = true
      setTimeout(() => {
        showModal.value = false
      }, 2000)
    } else {
      const err = await res.json()
      modalType.value = 'error'
      modalMessage.value = `Gagal menyimpan pengaturan:\n${err.detail || res.statusText}`
      showModal.value = true
    }
  } catch (error) {
    console.error('Failed to save config:', error)
    alert('Gagal menyimpan konfigurasi sistem. Periksa koneksi.')
  } finally {
    isSavingConfig.value = false
  }
}

const testTelegramConnection = async () => {
  try {
    isTestingTelegram.value = true
    const res = await fetch(`${API_BASE_URL}/system/test-telegram`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    
    if (res.ok) {
      modalType.value = 'success'
      modalMessage.value = 'Pesan uji coba berhasil dikirim ke Telegram!'
      showModal.value = true
      setTimeout(() => {
        showModal.value = false
      }, 2000)
    } else {
      const err = await res.json()
      modalType.value = 'error'
      modalMessage.value = `Gagal mengirim ke Telegram:\n${err.detail || res.statusText}`
      showModal.value = true
    }
  } catch (error) {
    alert('Gagal menguji koneksi. Pastikan pengaturan sudah disimpan terlebih dahulu.')
  } finally {
    isTestingTelegram.value = false
  }
}


const nodesWithSensors = ref<any[]>([])
const expandedNodes = ref<Record<string, boolean>>({})
const expandedChannels = ref<Record<string, boolean>>({})

const toggleNode = (nodeId: string) => {
  expandedNodes.value[nodeId] = !expandedNodes.value[nodeId]
}

const toggleChannel = (channelKey: string) => {
  expandedChannels.value[channelKey] = !expandedChannels.value[channelKey]
}

const getFieldNum = (fieldStr: string): number => {
  if (!fieldStr) return 999
  const match = fieldStr.match(/\d+/)
  return match ? parseInt(match[0], 10) : 999
}

const isSavingThresholds = ref(false)
const isLoadingSensors = ref(true)
const selectedNodeId = ref('')

const fetchSensors = async () => {
  isLoadingSensors.value = true
  try {
    const resNodes = await fetch(`${API_BASE_URL}/nodes/`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    if (!resNodes.ok) return
    const nodes = await resNodes.json()
    
    const enrichedNodes: any[] = []
    for (const node of nodes) {
      const nodeIdentifier = node.node_id || node.id
      const headers: Record<string, string> = {}
      if (authStore.token) {
        headers['Authorization'] = `Bearer ${authStore.token}`
      }

      const [resSensors, resChannels] = await Promise.all([
        fetch(`${API_BASE_URL}/nodes/${nodeIdentifier}/sensors/`, { headers }),
        fetch(`${API_BASE_URL}/nodes/${nodeIdentifier}/channels/`, { headers })
      ])
      
      let sensors: any[] = []
      let channels: any[] = []
      
      if (resSensors.ok) {
        sensors = await resSensors.json()
      }
      if (resChannels.ok) {
        channels = await resChannels.json()
      }
      
      node.sensors = sensors
      
      if (sensors.length > 0) {
        // Group sensors by channel from database
        const channelGroups: any[] = []
        const channelMap = new Map<string, any>()
        
        channels.forEach((ch: any, idx: number) => {
          const key = String(ch.id).toLowerCase()
          channelMap.set(key, {
            id: ch.id,
            channel_id: ch.channel_id,
            label: ch.label || `Channel ${idx + 1}`,
            sensors: []
          })
        })

        // Put sensors into corresponding channel groups
        const unassignedSensors: any[] = []
        sensors.forEach((s: any) => {
          const sChanKey = s.channel_id ? String(s.channel_id).toLowerCase() : ''
          if (sChanKey && channelMap.has(sChanKey)) {
            channelMap.get(sChanKey).sensors.push(s)
          } else {
            unassignedSensors.push(s)
          }
        })

        // Collect channel groups in order
        channelMap.forEach((group) => {
          group.sensors.sort((a: any, b: any) => getFieldNum(a.thingspeak_field) - getFieldNum(b.thingspeak_field))
          channelGroups.push(group)
        })

        // If there are unassigned sensors or if channels were empty, group by sensor.channel_id
        if (unassignedSensors.length > 0) {
          const fallbackGroups = new Map<string, any[]>()
          unassignedSensors.forEach((s: any) => {
            const cId = s.channel_id ? String(s.channel_id) : 'unknown'
            if (!fallbackGroups.has(cId)) fallbackGroups.set(cId, [])
            fallbackGroups.get(cId)!.push(s)
          })

          let autoIdx = channelGroups.length + 1
          fallbackGroups.forEach((sList, cId) => {
            sList.sort((a: any, b: any) => getFieldNum(a.thingspeak_field) - getFieldNum(b.thingspeak_field))
            channelGroups.push({
              id: cId,
              channel_id: cId === 'unknown' ? '-' : cId,
              label: `Channel ${autoIdx++}`,
              sensors: sList
            })
          })
        }
        
        node.channelGroups = channelGroups
        if (expandedNodes.value[node.id] === undefined) {
          expandedNodes.value[node.id] = true
        }
        enrichedNodes.push(node)
      }
    }

    nodesWithSensors.value = enrichedNodes
    if (enrichedNodes.length > 0 && !selectedNodeId.value) {
      selectedNodeId.value = enrichedNodes[0].id
    }
  } catch (err) {
    console.error(err)
  } finally {
    isLoadingSensors.value = false
  }
}

// Filter out diagnostic status & bitmask fields from threshold configuration if desired
const getThresholdableSensors = (sensors: any[]) => {
  return (sensors || []).filter(s => {
    const name = (s.name || '').toLowerCase()
    return !name.includes('status aktuator') && !name.includes('kode error')
  })
}

const saveThresholds = async (node: any, sensor: any) => {
  try {
    sensor.isSaving = true
    const payload = {
      name: sensor.name?.trim() || 'Sensor',
      unit: sensor.unit ?? '',
      min_threshold: sensor.min_threshold === '' || sensor.min_threshold === null ? null : Number(sensor.min_threshold),
      max_threshold: sensor.max_threshold === '' || sensor.max_threshold === null ? null : Number(sensor.max_threshold)
    }
    const res = await fetch(`${API_BASE_URL}/nodes/${node.node_id}/sensors/${sensor.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    if (res.ok) {
      sensor.saved = true
      telemetryStore.fetchSensors(node.node_id)
      setTimeout(() => { sensor.saved = false }, 2000)
    } else {
      const err = await res.json().catch(() => ({}))
      modalType.value = 'error'
      modalMessage.value = `Gagal menyimpan: ${err.detail || 'Terjadi kesalahan'}`
      showModal.value = true
    }
  } catch(e) {
    console.error(e)
    modalType.value = 'error'
    modalMessage.value = 'Gagal menghubungi server untuk menyimpan data sensor.'
    showModal.value = true
  } finally {
    sensor.isSaving = false
  }
}

onMounted(() => {
  fetchSensors()
  loadSystemConfig()
  telemetryStore.cekWebpush()
  updateSlider()
  window.addEventListener('resize', updateSlider)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateSlider)
})

const currentPassword = ref('')
const newPassword = ref('')
const isPasswordValid = ref<boolean | null>(null)
const isCheckingPassword = ref(false)
let passwordCheckTimeout: any = null

const verifyPassword = () => {
  if (passwordCheckTimeout) clearTimeout(passwordCheckTimeout)
  isPasswordValid.value = null
  
  if (!currentPassword.value) {
    return
  }
  
  isCheckingPassword.value = true
  passwordCheckTimeout = setTimeout(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/verify-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify({ password: currentPassword.value })
      })
      if (res.ok) {
        const data = await res.json()
        isPasswordValid.value = data.valid
      }
    } catch (e) {
      isPasswordValid.value = false
    } finally {
      isCheckingPassword.value = false
    }
  }, 500)
}

const isSavingPassword = ref(false)
const updatePassword = async () => {
  if (!currentPassword.value || !newPassword.value || newPassword.value.length < 8) {
    modalType.value = 'error'
    modalMessage.value = 'Mohon masukkan kata sandi saat ini dan kata sandi baru (minimal 8 karakter).'
    showModal.value = true
    return
  }
  
  isSavingPassword.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/auth/password`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ current_password: currentPassword.value, new_password: newPassword.value })
    })
    
    if (res.ok) {
      modalType.value = 'success'
      modalMessage.value = 'Kata sandi berhasil diperbarui!'
      showModal.value = true
      currentPassword.value = ''
      newPassword.value = ''
      isPasswordValid.value = null
      setTimeout(() => showModal.value = false, 2000)
    } else {
      const err = await res.json()
      modalType.value = 'error'
      modalMessage.value = `Gagal memperbarui kata sandi:\n${err.detail || 'Kata sandi lama tidak sesuai'}`
      showModal.value = true
    }
  } catch (e) {
    modalType.value = 'error'
    modalMessage.value = 'Gagal menghubungi server (kesalahan jaringan).'
    showModal.value = true
  } finally {
    isSavingPassword.value = false
  }
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 class="text-3xl font-bold tracking-tight">Pengaturan</h2>
      </div>
      
      <Dialog v-model:open="showModal">
        <DialogContent class="sm:max-w-sm outline-none">
          <div class="flex flex-col items-center justify-center py-8">
            <div class="h-24 w-24 flex items-center justify-center mb-6 overflow-visible">
              <template v-if="modalType === 'success'">
                <svg class="checkmark-anim" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                  <path class="checkmark__circle" fill="none" d="M 26 1 A 25 25 0 1 0 26 51 A 25 25 0 1 0 26 1" />
                  <path class="checkmark__check" fill="none" d="M10 24 l11 11 l25 -27"/>
                </svg>
              </template>
              <template v-else>
                <svg class="cross-anim" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                  <circle class="cross__circle" cx="26" cy="26" r="25" fill="none" />
                  <path class="cross__path cross__path--right" fill="none" d="M16,16 l20,20" />
                  <path class="cross__path cross__path--left" fill="none" d="M16,36 l20,-20" />
                </svg>
              </template>
            </div>
            <h3 :class="['text-2xl font-semibold tracking-tight', modalType === 'success' ? 'text-foreground' : 'text-destructive']">
              {{ modalType === 'success' ? 'Berhasil!' : 'Terjadi Kesalahan!' }}
            </h3>
            <p class="text-sm text-muted-foreground mt-2 text-center whitespace-pre-line">
              {{ modalMessage }}
            </p>
          </div>
        </DialogContent>
      </Dialog>
      
      <Tabs v-model="activeTab" class="w-full">
        <TabsList class="relative grid w-full grid-cols-3 sm:grid-cols-6 bg-white dark:bg-card border border-border/80 p-1.5 rounded-2xl shadow-sm h-auto gap-1 overflow-hidden">
          <!-- Animated Sliding Background Pill Indicator with Wall Collision Physics -->
          <div 
            class="absolute bg-primary rounded-xl shadow-md pointer-events-none z-0"
            :class="bounceClass"
            :style="{
              ...sliderStyle,
              transition: `left 0.28s ${transitionTiming}, top 0.28s ease, width 0.28s ease, height 0.28s ease, opacity 0.2s ease`
            }"
          />
          
          <TabsTrigger 
            v-for="tab in tabList"
            :key="tab.value"
            :value="tab.value"
            :ref="(el) => setTabRef(tab.value, el)"
            class="relative z-10 rounded-xl py-2.5 font-bold text-xs sm:text-sm data-[state=active]:bg-transparent data-[state=active]:text-primary-foreground data-[state=active]:shadow-none text-slate-600 dark:text-slate-400 hover:text-foreground transition-colors duration-200 cursor-pointer"
          >
            {{ tab.label }}
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="appearance">
          <Card>
            <CardHeader>
              <CardTitle>Tampilan Antarmuka</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Preferensi Tema</Label>
                  </div>
                    <div class="relative flex items-center gap-1 p-1 bg-muted/50 rounded-lg border w-fit">
                      <div 
                        class="absolute top-1 bottom-1 w-24 rounded-md bg-primary transition-transform duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] shadow-sm"
                        :class="isDarkMode ? 'translate-x-[calc(100%+0.25rem)]' : 'translate-x-0'"
                      ></div>
                      
                      <Button 
                        @click="toggleTheme(false)" 
                        variant="ghost" 
                        size="sm" 
                        class="relative z-10 w-24 shadow-none transition-colors duration-300 hover:bg-transparent"
                        :class="!isDarkMode ? 'text-primary-foreground hover:text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
                      >
                        <Sun class="w-4 h-4 mr-2" /> Terang
                      </Button>
                      <Button 
                        @click="toggleTheme(true)" 
                        variant="ghost" 
                        size="sm" 
                        class="relative z-10 w-24 shadow-none transition-colors duration-300 hover:bg-transparent"
                        :class="isDarkMode ? 'text-primary-foreground hover:text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
                      >
                        <Moon class="w-4 h-4 mr-2" /> Gelap
                      </Button>
                    </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="system">
          <Card>
            <CardHeader>
              <CardTitle>Konfigurasi Sistem</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                <!-- Offline Threshold -->
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Batas Waktu Offline</Label>
                    <p class="text-sm text-muted-foreground">Perangkat dianggap offline jika tidak mengirimkan data dalam rentang waktu ini.</p>
                  </div>
                  <div class="w-full sm:w-40 flex items-center gap-2">
                    <Input type="number" v-model="systemConfig.offline_threshold_mins" placeholder="15" min="1" />
                    <span class="text-sm font-medium text-muted-foreground">Menit</span>
                  </div>
                </div>

                <!-- Telegram Bot Integration -->
                <div class="p-4">
                  <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
                    <div>
                      <h4 class="text-base font-medium">Integrasi Bot Telegram</h4>
                    </div>
                  </div>
                  <div class="grid gap-4 sm:grid-cols-2">
                    <div class="space-y-2">
                      <Label>Token Bot</Label>
                      <Input v-model="systemConfig.telegram_bot_token" placeholder="Contoh: 7123456789:AAFlmQ9xW8ZkL0vYq..." />
                    </div>
                    <div class="space-y-2">
                      <Label>ID Obrolan (Chat ID)</Label>
                      <Input v-model="systemConfig.telegram_chat_id" placeholder="Contoh: -1001234567890 atau 1234567890" />
                    </div>
                  </div>
                  <div class="mt-4 flex justify-end">
                    <Button variant="outline" size="sm" @click="testTelegramConnection" :disabled="isTestingTelegram || !systemConfig.telegram_bot_token || !systemConfig.telegram_chat_id">
                      {{ isTestingTelegram ? 'Menguji...' : 'Uji Koneksi' }}
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button @click="saveSystemConfig" :disabled="isSavingConfig">
                {{ isSavingConfig ? 'Menyimpan...' : 'Simpan Pengaturan Sistem' }}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Pengaturan Notifikasi</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg bg-card">
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <h4 class="text-base font-medium">Notifikasi HP & PC</h4>
                    <p class="text-sm text-muted-foreground">
                      Peringatan langsung saat terdeteksi anomali sensor pada lahan.
                    </p>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <Button
                      variant="outline"
                      size="sm"
                      :disabled="telemetryStore.webpushAktif"
                      @click="telemetryStore.daftarWebpush"
                    >
                      {{ telemetryStore.webpushAktif ? 'Perangkat Terdaftar' : 'Daftarkan Perangkat' }}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      :disabled="!telemetryStore.webpushAktif"
                      @click="ujiWebpush"
                    >
                      Uji Kirim
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="thresholds">
          <Card>
            <CardHeader>
              <CardTitle>Ambang Batas & Pemetaan Sensor</CardTitle>
              <CardDescription>Sesuaikan nama sensor, satuan, serta ambang batas aman untuk setiap field ThingSpeak.</CardDescription>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg bg-card">
                <div class="p-4 space-y-6">
                  <div v-if="isLoadingSensors" class="text-sm text-muted-foreground">Memuat daftar sensor...</div>
                  <div v-else-if="nodesWithSensors.length === 0" class="text-sm text-muted-foreground">Tidak ada sensor ditemukan. Tambahkan sensor pada node terlebih dahulu.</div>
                  <div v-else v-for="node in nodesWithSensors" :key="node.id" class="space-y-2">
                    
                    <!-- Node Accordion Header -->
                    <div 
                      class="flex items-center gap-2 cursor-pointer hover:bg-accent/50 p-2.5 rounded-lg transition-colors border border-border/60 bg-slate-50/70 dark:bg-slate-900/40" 
                      @click="toggleNode(node.id)"
                    >
                      <ChevronRight class="w-4 h-4 text-muted-foreground transition-transform duration-200" :class="{'rotate-90': expandedNodes[node.id]}" />
                      <h5 class="font-bold flex items-center gap-2 text-sm text-foreground">
                        <div class="w-2.5 h-2.5 rounded-full bg-primary"></div>
                        {{ node.name }}
                      </h5>
                      <span class="ml-auto text-xs font-semibold text-muted-foreground">{{ node.sensors?.length || 0 }} total sensor</span>
                    </div>
                    
                    <!-- Node Body: Channel Groups Accordion -->
                    <Transition
                      enter-active-class="transition-all duration-300 ease-in-out overflow-hidden"
                      enter-from-class="opacity-0 max-h-0"
                      enter-to-class="opacity-100 max-h-[3000px]"
                      leave-active-class="transition-all duration-300 ease-in-out overflow-hidden"
                      leave-from-class="opacity-100 max-h-[3000px]"
                      leave-to-class="opacity-0 max-h-0"
                    >
                      <div v-show="expandedNodes[node.id]" class="space-y-3.5 pl-3 sm:pl-5 border-l-2 border-primary/30 ml-3 pb-2 mt-3">
                        
                        <!-- Loop Each Channel in Node -->
                        <div 
                          v-for="(channelGroup, idx) in node.channelGroups" 
                          :key="channelGroup.id || idx"
                          class="border border-border/80 rounded-xl overflow-hidden bg-card shadow-none transition-all"
                        >
                          <!-- Channel Dropdown Header -->
                          <div 
                            class="flex items-center justify-between p-3 cursor-pointer bg-slate-50 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition-colors"
                            @click="toggleChannel(`${node.id}_${channelGroup.id || idx}`)"
                          >
                            <div class="flex items-center gap-2.5">
                              <ChevronRight 
                                class="w-4 h-4 text-muted-foreground transition-transform duration-200" 
                                :class="{'rotate-90': expandedChannels[`${node.id}_${channelGroup.id || idx}`]}" 
                              />
                              <div class="flex flex-wrap items-center gap-2">
                                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                                <span class="font-bold text-sm text-foreground">
                                  {{ channelGroup.label }}
                                </span>
                                <span class="text-[11px] font-mono text-muted-foreground bg-white dark:bg-slate-800 px-2 py-0.5 rounded border border-border/70">
                                  ID Kanal: {{ channelGroup.channel_id }}
                                </span>
                              </div>
                            </div>
                            <span class="text-xs font-semibold text-muted-foreground bg-white dark:bg-slate-800 px-2.5 py-0.5 rounded-full border border-border/70">
                              {{ channelGroup.sensors.length }} sensor
                            </span>
                          </div>

                          <!-- Channel Sensor Fields (Field 1 to Field 8 Ascending) -->
                          <Transition
                            enter-active-class="transition-all duration-300 ease-in-out overflow-hidden"
                            enter-from-class="opacity-0 max-h-0"
                            enter-to-class="opacity-100 max-h-[3000px]"
                            leave-active-class="transition-all duration-300 ease-in-out overflow-hidden"
                            leave-from-class="opacity-100 max-h-[3000px]"
                            leave-to-class="opacity-0 max-h-0"
                          >
                            <div 
                              v-show="expandedChannels[`${node.id}_${channelGroup.id || idx}`]" 
                              class="p-3.5 divide-y divide-border/40 space-y-3 bg-white dark:bg-card"
                            >
                              <div 
                                v-for="sensor in channelGroup.sensors" 
                                :key="sensor.id" 
                                class="pt-3 first:pt-0 grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-end"
                              >
                                <!-- Field Badge & Sensor Name (col-span-4) -->
                                <div class="sm:col-span-4 space-y-1">
                                  <div class="flex items-center gap-1.5">
                                    <span class="text-[10px] font-mono font-bold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700 shrink-0">
                                      {{ sensor.thingspeak_field }}
                                    </span>
                                    <Label class="text-[10px] text-muted-foreground uppercase font-bold tracking-wider truncate">Nama Sensor / Parameter</Label>
                                  </div>
                                  <Input 
                                    type="text" 
                                    v-model="sensor.name" 
                                    placeholder="Nama Sensor" 
                                    class="h-8 text-xs font-semibold bg-slate-50/50 dark:bg-slate-900/50" 
                                  />
                                </div>

                                <!-- Satuan (col-span-2) -->
                                <div class="sm:col-span-2 space-y-1">
                                  <Label class="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Satuan</Label>
                                  <Input 
                                    type="text" 
                                    v-model="sensor.unit" 
                                    placeholder="cth: mg/kg, %" 
                                    class="h-8 text-xs font-mono bg-slate-50/50 dark:bg-slate-900/50" 
                                  />
                                </div>

                                <!-- Min Threshold (col-span-2) -->
                                <div class="sm:col-span-2 space-y-1">
                                  <Label class="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Batas Min</Label>
                                  <Input 
                                    type="number" 
                                    step="any" 
                                    v-model="sensor.min_threshold" 
                                    placeholder="Tanpa Batas" 
                                    class="h-8 text-xs bg-slate-50/50 dark:bg-slate-900/50" 
                                  />
                                </div>

                                <!-- Max Threshold (col-span-2) -->
                                <div class="sm:col-span-2 space-y-1">
                                  <Label class="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Batas Max</Label>
                                  <Input 
                                    type="number" 
                                    step="any" 
                                    v-model="sensor.max_threshold" 
                                    placeholder="Tanpa Batas" 
                                    class="h-8 text-xs bg-slate-50/50 dark:bg-slate-900/50" 
                                  />
                                </div>

                                <!-- Save Button (col-span-2) -->
                                <div class="sm:col-span-2 flex justify-end">
                                  <Button 
                                    variant="outline" 
                                    size="sm" 
                                    class="h-8 w-full font-semibold transition-all" 
                                    :class="sensor.saved ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30 font-bold' : ''"
                                    :disabled="sensor.isSaving" 
                                    @click="saveThresholds(node, sensor)"
                                  >
                                    {{ sensor.saved ? 'Tersimpan!' : (sensor.isSaving ? '...' : 'Simpan') }}
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </Transition>
                        </div>

                      </div>
                    </Transition>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>Keamanan Akun</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                  <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div class="space-y-0.5">
                      <Label class="text-base font-medium">Kata Sandi Saat Ini</Label>
                    </div>
                    <div class="w-full sm:w-72 relative">
                      <Input id="current" type="password" v-model="currentPassword" @input="verifyPassword" placeholder="Masukkan kata sandi lama" class="hide-password-eye pr-10" :class="{'border-destructive focus-visible:ring-destructive': isPasswordValid === false, 'border-emerald-500 focus-visible:ring-emerald-500': isPasswordValid === true}" />
                      <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center">
                        <Loader2 v-if="isCheckingPassword" class="w-4 h-4 animate-spin text-muted-foreground" />
                        <CheckCircle v-else-if="isPasswordValid === true" class="w-4 h-4 text-emerald-500" />
                        <XCircle v-else-if="isPasswordValid === false" class="w-4 h-4 text-destructive" />
                      </div>
                    </div>
                  </div>
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Kata Sandi Baru</Label>
                    <p class="text-sm text-muted-foreground">Minimal terdiri dari 8 karakter.</p>
                  </div>
                  <div class="w-full sm:w-72">
                    <Input id="new" type="password" v-model="newPassword" placeholder="Masukkan kata sandi baru" />
                  </div>
                </div>
              </div>
            </CardContent>
              <CardFooter>
                <Button @click="updatePassword" :disabled="isSavingPassword || isPasswordValid === false || !newPassword || newPassword.length < 8">
                  {{ isSavingPassword ? 'Menyimpan...' : 'Perbarui Kata Sandi' }}
                </Button>
              </CardFooter>
          </Card>
        </TabsContent>

        <!-- About & Community Service Tab -->
        <TabsContent value="about">
          <Card>
            <CardHeader>
              <CardTitle>Tentang & Program Pengabdian Masyarakat</CardTitle>
              <CardDescription>
                Platform IoT dan pemantauan perangkat untuk pertanian presisi (smart farming), menghubungkan sensor lapangan dan aktuator dengan dashboard web real-time untuk memantau kondisi lahan, status alat, dan peringatan dini.
              </CardDescription>
            </CardHeader>
            <CardContent class="space-y-6">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                <!-- UGM -->
                <div class="flex items-center gap-4 p-4 rounded-xl border bg-card/50 hover:bg-muted/40 transition-colors">
                  <div class="w-14 h-14 rounded-xl bg-muted/30 p-1 flex items-center justify-center shrink-0 overflow-hidden">
                    <img src="/Logo-UGM.png" alt="Universitas Gadjah Mada" class="w-full h-full object-contain scale-125 dark:brightness-0 dark:invert" />
                  </div>
                  <div>
                    <h4 class="font-semibold text-sm">Universitas Gadjah Mada</h4>
                    <p class="text-xs text-muted-foreground mt-0.5">Institusi pendidikan tinggi pengembang riset dan pengabdian kepada masyarakat</p>
                  </div>
                </div>

                <!-- DIKE -->
                <div class="flex items-center gap-4 p-4 rounded-xl border bg-card/50 hover:bg-muted/40 transition-colors">
                  <div class="w-14 h-14 rounded-xl bg-muted/30 p-2 flex items-center justify-center shrink-0">
                    <img src="/Logo-DIKE.png" alt="Departemen Ilmu Komputer dan Elektronika" class="w-full h-full object-contain dark:brightness-0 dark:invert" />
                  </div>
                  <div>
                    <h4 class="font-semibold text-sm">Departemen Ilmu Komputer dan Elektronika</h4>
                    <p class="text-xs text-muted-foreground mt-0.5">Departemen akademik di FMIPA UGM pengembang inovasi ilmu komputer dan elektronika instrumentasi</p>
                  </div>
                </div>

                <!-- Lab ELINS -->
                <div class="flex items-center gap-4 p-4 rounded-xl border bg-card/50 hover:bg-muted/40 transition-colors">
                  <div class="w-14 h-14 rounded-xl bg-muted/30 p-2 flex items-center justify-center shrink-0">
                    <img src="/logo-icon.webp" alt="Laboratorium Elektronika dan Instrumentasi" class="w-full h-full object-contain" />
                  </div>
                  <div>
                    <h4 class="font-semibold text-sm">Laboratorium Elektronika & Instrumentasi</h4>
                    <p class="text-xs text-muted-foreground mt-0.5">Laboratorium riset elektronika, sistem kendali, instrumentasi, dan jaringan sensor IoT</p>
                  </div>
                </div>

                <!-- Webdev ERC -->
                <div class="flex items-center gap-4 p-4 rounded-xl border bg-card/50 hover:bg-muted/40 transition-colors">
                  <div class="w-14 h-14 rounded-xl bg-muted/30 p-2 flex items-center justify-center shrink-0">
                    <img src="/logo-webdev.webp" alt="Webdev ERC" class="w-full h-full object-contain dark:invert" />
                  </div>
                  <div>
                    <h4 class="font-semibold text-sm">Webdev ERC</h4>
                    <p class="text-xs text-muted-foreground mt-0.5">Divisi riset dan pengembangan aplikasi web mahasiswa di Elins Research Club</p>
                  </div>
                </div>

                <!-- Gubug Milenial Margorejo -->
                <div class="flex items-center gap-4 p-4 rounded-xl border bg-card/50 hover:bg-muted/40 transition-colors md:col-span-2">
                  <div class="w-14 h-14 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0 text-emerald-600">
                    <Sprout class="w-7 h-7 text-emerald-600" />
                  </div>
                  <div>
                    <h4 class="font-semibold text-sm">Gubug Milenial Margorejo</h4>
                    <p class="text-xs text-muted-foreground mt-0.5">Mitra kelompok tani dan lokasi implementasi riset pertanian presisi berbasis IoT</p>
                  </div>
                </div>

              </div>

              <!-- Project info badge -->
              <div class="pt-4 border-t border-border/40 flex items-center justify-center text-xs text-muted-foreground text-center">
                <span>&copy; 2026 G-CONNECT &bull; Laboratorium ELINS DIKE UGM</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  </DashboardLayout>
</template>

<style scoped>
.checkmark-anim {
  width: 80px;
  height: 80px;
  display: block;
  stroke-width: 3.5;
  stroke: #22c55e;
  stroke-miterlimit: 10;
  overflow: visible;
}

.checkmark__circle {
  stroke-dasharray: 157;
  stroke-dashoffset: 157;
  stroke-width: 3.5;
  stroke: #22c55e;
  fill: none;
  /* Animates to leave a 1/4 gap (dashoffset 40) */
  animation: strokeCircle 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.checkmark__check {
  transform-origin: 50% 50%;
  stroke-dasharray: 55;
  stroke-dashoffset: 55;
  stroke: #22c55e;
  /* ease-in-expo curve to simulate starting a stroke and whipping it at the end */
  animation: stroke 0.4s cubic-bezier(0.95, 0.05, 0.795, 0.035) 0.5s forwards;
}

@keyframes strokeCircle {
  100% {
    stroke-dashoffset: 40;
  }
}

@keyframes stroke {
  100% {
    stroke-dashoffset: 0;
  }
}

.cross-anim {
  width: 80px;
  height: 80px;
  display: block;
  stroke-width: 3.5;
  stroke: #ef4444;
  stroke-linecap: round;
  stroke-miterlimit: 10;
  overflow: visible;
}

.cross__circle {
  stroke-dasharray: 157;
  stroke-dashoffset: 157;
  stroke-width: 3.5;
  stroke: #ef4444;
  fill: none;
  animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.cross__path {
  stroke-dasharray: 55;
  stroke-dashoffset: 55;
  stroke: #ef4444;
}

.cross__path--right {
  animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.4s forwards;
}

.cross__path--left {
  animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.6s forwards;
}

/* Hide default edge password eye icon */
.hide-password-eye::-ms-reveal,
.hide-password-eye::-ms-clear {
  display: none;
}

/* Wall Collision & Squish Elastic Physics for Tab Indicator */
.tab-squish-right {
  animation: hitWallRight 0.36s cubic-bezier(0.2, 0.9, 0.3, 1) forwards;
  transform-origin: right center !important;
}

.tab-squish-left {
  animation: hitWallLeft 0.36s cubic-bezier(0.2, 0.9, 0.3, 1) forwards;
  transform-origin: left center !important;
}

.tab-stretch-mid {
  animation: stretchMid 0.32s cubic-bezier(0.34, 1.25, 0.64, 1) forwards;
  transform-origin: center center;
}

@keyframes hitWallRight {
  0% {
    transform: scaleX(1) scaleY(1);
  }
  35% {
    /* Compress against the right wall while keeping right rounded edge pinned */
    transform: scaleX(0.84) scaleY(1.08);
  }
  70% {
    /* Elastic rebound */
    transform: scaleX(1.04) scaleY(0.98);
  }
  88% {
    transform: scaleX(0.99) scaleY(1.01);
  }
  100% {
    transform: scaleX(1) scaleY(1);
  }
}

@keyframes hitWallLeft {
  0% {
    transform: scaleX(1) scaleY(1);
  }
  35% {
    /* Compress against the left wall while keeping left rounded edge pinned */
    transform: scaleX(0.84) scaleY(1.08);
  }
  70% {
    /* Elastic rebound */
    transform: scaleX(1.04) scaleY(0.98);
  }
  88% {
    transform: scaleX(0.99) scaleY(1.01);
  }
  100% {
    transform: scaleX(1) scaleY(1);
  }
}

@keyframes stretchMid {
  0% {
    transform: scaleX(1) scaleY(1);
  }
  45% {
    transform: scaleX(1.06) scaleY(0.96);
  }
  75% {
    transform: scaleX(0.98) scaleY(1.01);
  }
  100% {
    transform: scaleX(1) scaleY(1);
  }
}
</style>

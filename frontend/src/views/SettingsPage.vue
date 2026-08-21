<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Sun, Moon, CheckCircle, XCircle, Loader2 } from 'lucide-vue-next'

const isDarkMode = ref(document.documentElement.classList.contains('dark'))
const showModal = ref(false)
const modalType = ref<'success' | 'error'>('success')
const modalMessage = ref('')

const toggleTheme = (dark: boolean) => {
  isDarkMode.value = dark
  if (dark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

const API_BASE_URL = 'http://localhost:8000/api/v1'

const systemConfig = ref({
  polling_interval: 15,
  data_retention_days: 30,
  offline_threshold_mins: 15,
  telegram_bot_token: '',
  telegram_chat_id: ''
})

const isLoadingConfig = ref(true)
const isSavingConfig = ref(false)
const isTestingTelegram = ref(false)
const authStore = useAuthStore()

const loadSystemConfig = async () => {
  try {
    isLoadingConfig.value = true
    const res = await fetch(`${API_BASE_URL}/system/config`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      const data = await res.json()
      systemConfig.value = {
        ...systemConfig.value,
        ...data
      }
    }
  } catch (error) {
    console.error('Failed to load system config:', error)
  } finally {
    isLoadingConfig.value = false
  }
}

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
      modalType.value = 'success'
      modalMessage.value = 'Settings saved successfully'
      showModal.value = true
      setTimeout(() => {
        showModal.value = false
      }, 2000)
    } else {
      const err = await res.json()
      modalType.value = 'error'
      modalMessage.value = `Failed to save config:\n${err.detail || res.statusText}`
      showModal.value = true
    }
  } catch (error) {
    console.error('Failed to save config:', error)
    alert('Failed to save configuration. Check console.')
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
      modalMessage.value = 'Test message sent successfully'
      showModal.value = true
      setTimeout(() => {
        showModal.value = false
      }, 2000)
    } else {
      const err = await res.json()
      modalType.value = 'error'
      modalMessage.value = `Failed to send:\n${err.detail || res.statusText}`
      showModal.value = true
    }
  } catch (error) {
    alert('Failed to test connection. Make sure to save the configuration first.')
  } finally {
    isTestingTelegram.value = false
  }
}


const nodesWithSensors = ref([])
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
    
    const enrichedNodes = []
    for (const node of nodes) {
      const resSensors = await fetch(`${API_BASE_URL}/nodes/${node.node_id}/sensors/`, {
        headers: { 'Authorization': `Bearer ${authStore.token}` }
      })
      if (resSensors.ok) {
        node.sensors = await resSensors.json()
        if (node.sensors.length > 0) {
          enrichedNodes.push(node)
        }
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

const saveThresholds = async (node, sensor) => {
  try {
    sensor.isSaving = true
    const payload = {
      min_threshold: sensor.min_threshold === '' || sensor.min_threshold === null ? null : Number(sensor.min_threshold),
      max_threshold: sensor.max_threshold === '' || sensor.max_threshold === null ? null : Number(sensor.max_threshold)
    }
    await fetch(`${API_BASE_URL}/nodes/${node.node_id}/sensors/${sensor.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    sensor.saved = true
    setTimeout(() => { sensor.saved = false }, 2000)
  } catch(e) {
    console.error(e)
  } finally {
    sensor.isSaving = false
  }
}

onMounted(() => {
  if (true) {
    fetchSensors()
  }
})

onMounted(() => {
  loadSystemConfig()
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
    modalMessage.value = 'Please provide current password and a new password (min 8 chars).'
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
      modalMessage.value = 'Password updated successfully'
      showModal.value = true
      currentPassword.value = ''
      newPassword.value = ''
      isPasswordValid.value = null
      setTimeout(() => showModal.value = false, 2000)
    } else {
      const err = await res.json()
      modalType.value = 'error'
      modalMessage.value = `Failed to update password:\n${err.detail}`
      showModal.value = true
    }
  } catch (e) {
    modalType.value = 'error'
    modalMessage.value = 'Network error'
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
        <h2 class="text-3xl font-bold tracking-tight">Settings</h2>
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
              {{ modalType === 'success' ? 'Success!' : 'Error!' }}
            </h3>
            <p class="text-sm text-muted-foreground mt-2 text-center whitespace-pre-line">
              {{ modalMessage }}
            </p>
          </div>
        </DialogContent>
      </Dialog>
      
      <Tabs defaultValue="appearance" class="w-full">
        <TabsList class="grid w-full grid-cols-5">
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="thresholds">Thresholds</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>
        
        <TabsContent value="appearance">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Theme Preference</Label>
                    <p class="text-sm text-muted-foreground">Select your preferred interface theme.</p>
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
                        <Sun class="w-4 h-4 mr-2" /> Light
                      </Button>
                      <Button 
                        @click="toggleTheme(true)" 
                        variant="ghost" 
                        size="sm" 
                        class="relative z-10 w-24 shadow-none transition-colors duration-300 hover:bg-transparent"
                        :class="isDarkMode ? 'text-primary-foreground hover:text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
                      >
                        <Moon class="w-4 h-4 mr-2" /> Dark
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
              <CardTitle>System Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Polling Interval</Label>
                    <p class="text-sm text-muted-foreground">Data fetch frequency. Example: 15 (seconds).</p>
                  </div>
                  <div class="w-full sm:w-40 flex items-center gap-2">
                    <Input type="number" v-model="systemConfig.polling_interval" placeholder="15" min="15" />
                    <span class="text-sm text-muted-foreground">Secs</span>
                  </div>
                </div>
                
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Data Retention</Label>
                    <p class="text-sm text-muted-foreground">Storage duration for telemetry. Example: 30 (days).</p>
                  </div>
                  <div class="w-full sm:w-40 flex items-center gap-2">
                    <Input type="number" v-model="systemConfig.data_retention_days" placeholder="30" />
                    <span class="text-sm text-muted-foreground">Days</span>
                  </div>
                </div>
                
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Offline Threshold</Label>
                    <p class="text-sm text-muted-foreground">Idle time before marked offline. Example: 15 (minutes).</p>
                  </div>
                  <div class="w-full sm:w-40 flex items-center gap-2">
                    <Input type="number" v-model="systemConfig.offline_threshold_mins" placeholder="15" />
                    <span class="text-sm text-muted-foreground">Mins</span>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button @click="saveSystemConfig" :disabled="isSavingConfig">
                {{ isSavingConfig ? 'Saving...' : 'Save System Config' }}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>Notification Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                <div class="p-4">
                      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
                        <div>
                          <h4 class="text-base font-medium">Telegram Bot Integration</h4>
                          <p class="text-sm text-muted-foreground">Notification destination for critical system events.</p>
                        </div>
                      </div>
                      <div class="grid gap-4 sm:grid-cols-2">
                        <div class="space-y-2">
                          <Label>Bot Token</Label>
                          <Input v-model="systemConfig.telegram_bot_token" placeholder="e.g. 123456789:ABCdef..." />
                        </div>
                        <div class="space-y-2">
                          <Label>Chat ID</Label>
                          <Input v-model="systemConfig.telegram_chat_id" placeholder="e.g. -100123456789" />
                        </div>
                      </div>
                    <div class="mt-4 flex justify-end">
                      <Button variant="outline" size="sm" @click="testTelegramConnection" :disabled="isTestingTelegram || !systemConfig.telegram_bot_token || !systemConfig.telegram_chat_id">
                        {{ isTestingTelegram ? 'Testing...' : 'Test Connection' }}
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
              <CardTitle>Sensor Thresholds</CardTitle>
              <CardDescription>Trigger Telegram alerts when sensor values go outside these safe limits.</CardDescription>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg bg-card">
                <div class="p-4 space-y-6">
                  <div v-if="isLoadingSensors" class="text-sm text-muted-foreground">Loading sensors...</div>
                  <div v-else-if="nodesWithSensors.length === 0" class="text-sm text-muted-foreground">No sensors found. Add sensors to your nodes first.</div>
                  <div v-else v-for="node in nodesWithSensors" :key="node.id" class="space-y-4">
                    <h5 class="font-medium flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-primary"></div>{{ node.name }}</h5>
                    <div class="grid gap-4 pl-4 border-l-2 border-muted">
                      <div v-for="sensor in node.sensors" :key="sensor.id" class="flex flex-col sm:flex-row gap-4 items-end">
                        <div class="w-full sm:w-1/3">
                          <Label class="text-xs text-muted-foreground">{{ sensor.name }} ({{ sensor.unit }})</Label>
                          <div class="font-medium text-sm pt-1">{{ sensor.thingspeak_field }}</div>
                        </div>
                        <div class="w-full sm:w-1/3">
                          <Label class="text-xs">Min Threshold</Label>
                          <Input type="number" step="any" v-model="sensor.min_threshold" placeholder="No Limit" class="h-8 text-sm" />
                        </div>
                        <div class="w-full sm:w-1/3">
                          <Label class="text-xs">Max Threshold</Label>
                          <Input type="number" step="any" v-model="sensor.max_threshold" placeholder="No Limit" class="h-8 text-sm" />
                        </div>
                        <Button variant="outline" size="sm" class="h-8 w-20 whitespace-nowrap" :disabled="sensor.isSaving" @click="saveThresholds(node, sensor)">
                          {{ sensor.saved ? 'Saved!' : (sensor.isSaving ? '...' : 'Save') }}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>Security</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                  <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div class="space-y-0.5">
                      <Label class="text-base font-medium">Current Password</Label>
                      <p class="text-sm text-muted-foreground">Verify your identity before making changes.</p>
                    </div>
                    <div class="w-full sm:w-72 relative">
                      <Input id="current" type="password" v-model="currentPassword" @input="verifyPassword" class="hide-password-eye pr-10" :class="{'border-destructive focus-visible:ring-destructive': isPasswordValid === false, 'border-emerald-500 focus-visible:ring-emerald-500': isPasswordValid === true}" />
                      <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center justify-center">
                        <Loader2 v-if="isCheckingPassword" class="w-4 h-4 animate-spin text-muted-foreground" />
                        <CheckCircle v-else-if="isPasswordValid === true" class="w-4 h-4 text-emerald-500" />
                        <XCircle v-else-if="isPasswordValid === false" class="w-4 h-4 text-destructive" />
                      </div>
                    </div>
                  </div>
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">New Password</Label>
                    <p class="text-sm text-muted-foreground">Must be at least 8 characters long.</p>
                  </div>
                  <div class="w-full sm:w-72">
                    <Input id="new" type="password" v-model="newPassword" />
                  </div>
                </div>
              </div>
            </CardContent>
              <CardFooter>
                <Button @click="updatePassword" :disabled="isSavingPassword || isPasswordValid === false || !newPassword || newPassword.length < 8">
                  {{ isSavingPassword ? 'Saving...' : 'Save Password' }}
                </Button>
              </CardFooter>
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
</style>

<script setup lang="ts">
import { ref } from 'vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Sun, Moon, CheckCircle } from 'lucide-vue-next'

const isDarkMode = ref(document.documentElement.classList.contains('dark'))
const showSuccessModal = ref(false)

const toggleTheme = (dark: boolean) => {
  isDarkMode.value = dark
  if (dark) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const API_BASE_URL = 'http://localhost:8000/api/v1'

const systemConfig = ref({
  polling_interval: 15,
  data_retention_days: 30,
  offline_threshold_mins: 15
})

const isLoadingConfig = ref(false)
const isSavingConfig = ref(false)
const authStore = useAuthStore()

const loadSystemConfig = async () => {
  try {
    isLoadingConfig.value = true
    const res = await fetch(`${API_BASE_URL}/system/config`, {
      headers: { 'Authorization': `Bearer ${authStore.token}` }
    })
    if (res.ok) {
      systemConfig.value = await res.json()
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
      showSuccessModal.value = true
      setTimeout(() => {
        showSuccessModal.value = false
      }, 2000)
    } else {
      alert('Failed to save config.')
    }
  } catch (error) {
    console.error('Failed to save config:', error)
    alert('Failed to save config.')
  } finally {
    isSavingConfig.value = false
  }
}

onMounted(() => {
  loadSystemConfig()
})

const currentPassword = ref('')
const newPassword = ref('')
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 class="text-3xl font-bold tracking-tight">Settings</h2>
      </div>
      
      <Dialog v-model:open="showSuccessModal">
        <DialogContent class="sm:max-w-sm [&>button]:hidden outline-none">
          <div class="flex flex-col items-center justify-center py-8">
            <div class="h-24 w-24 flex items-center justify-center mb-6 overflow-visible">
              <svg class="checkmark-anim" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                <!-- Starts at top (26,1), draws counter-clockwise to left, bottom, right -->
                <path class="checkmark__circle" fill="none" d="M 26 1 A 25 25 0 1 0 26 51 A 25 25 0 1 0 26 1" />
                <!-- Longer first stroke for better proportion -->
                <path class="checkmark__check" fill="none" d="M10 24 l11 11 l25 -27"/>
              </svg>
            </div>
            <h3 class="text-2xl font-semibold tracking-tight">Success!</h3>
            <p class="text-sm text-muted-foreground mt-2 text-center">
              System configuration has been successfully updated.
            </p>
          </div>
        </DialogContent>
      </Dialog>
      
      <Tabs defaultValue="appearance" class="w-full">
        <TabsList class="grid w-full grid-cols-4">
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>
        
        <TabsContent value="appearance">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>
                Customize how the dashboard looks. 
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Theme Preference</Label>
                    <p class="text-sm text-muted-foreground">Select your preferred interface theme.</p>
                  </div>
                  <div class="flex items-center gap-1 p-1 bg-muted/50 rounded-lg border">
                    <Button 
                      @click="toggleTheme(false)" 
                      :variant="!isDarkMode ? 'default' : 'ghost'" 
                      size="sm" 
                      class="w-24 shadow-none"
                    >
                      <Sun class="w-4 h-4 mr-2" /> Light
                    </Button>
                    <Button 
                      @click="toggleTheme(true)" 
                      :variant="isDarkMode ? 'default' : 'ghost'" 
                      size="sm" 
                      class="w-24 shadow-none"
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
              <CardDescription>Core settings for data synchronization and storage.</CardDescription>
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
              <CardDescription>
                Configure when you want to be notified about node statuses.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                <div class="p-4">
                  <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
                    <div>
                      <h4 class="text-base font-medium">Telegram Bot Integration</h4>
                      <p class="text-sm text-muted-foreground">Send critical alerts (offline node, low battery) to Telegram.</p>
                    </div>
                    <span class="text-xs bg-muted px-2 py-1 rounded text-muted-foreground font-mono"># ponytail: YAGNI</span>
                  </div>
                  <div class="grid gap-4 sm:grid-cols-2">
                    <div class="space-y-2">
                      <Label>Bot Token</Label>
                      <Input placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ" />
                    </div>
                    <div class="space-y-2">
                      <Label>Chat ID</Label>
                      <Input placeholder="-100123456789" />
                    </div>
                  </div>
                  <div class="mt-4 flex justify-end">
                    <Button variant="outline" size="sm">Test Connection</Button>
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
              <CardDescription>
                Update your password and secure your account.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div class="border border-muted-foreground/30 rounded-lg divide-y divide-muted-foreground/30 bg-card">
                <div class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div class="space-y-0.5">
                    <Label class="text-base font-medium">Current Password</Label>
                    <p class="text-sm text-muted-foreground">Verify your identity before making changes.</p>
                  </div>
                  <div class="w-full sm:w-72">
                    <Input id="current" type="password" v-model="currentPassword" />
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
              <Button>Save Password</Button>
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
</style>

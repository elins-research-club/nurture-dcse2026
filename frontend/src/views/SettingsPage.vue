<script setup lang="ts">
import { ref } from 'vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

const isDarkMode = ref(true)

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

const currentPassword = ref('')
const newPassword = ref('')
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 class="text-3xl font-bold tracking-tight">Settings</h2>
      </div>
      
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
            <CardContent class="space-y-4">
              <div class="flex items-center justify-between p-4 border rounded-lg">
                <div class="space-y-0.5">
                  <Label>Dark Mode</Label>
                  <p class="text-sm text-muted-foreground">Switch between light and dark themes.</p>
                </div>
                <Button @click="toggleTheme" :variant="isDarkMode ? 'default' : 'outline'">
                  {{ isDarkMode ? 'Dark Active' : 'Light Active' }}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="system">
          <Card>
            <CardHeader>
              <CardTitle>System Configuration</CardTitle>
              <CardDescription>Global variables for IoT polling and retention.</CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="space-y-2">
                <Label>ThingSpeak Polling Interval (Seconds)</Label>
                <Input type="number" placeholder="15" />
                <p class="text-xs text-muted-foreground">Default: 15s. Lower values may hit API rate limits.</p>
              </div>
              <div class="space-y-2">
                <Label>Data Retention (Days)</Label>
                <Input type="number" placeholder="30" />
                <p class="text-xs text-muted-foreground">Telemetry older than this will be auto-deleted.</p>
              </div>
              <div class="space-y-2">
                <Label>Offline Threshold (Minutes)</Label>
                <Input type="number" placeholder="15" />
              </div>
            </CardContent>
            <CardFooter>
              <Button>Save System Config</Button>
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
            <CardContent class="space-y-4">
              <div class="flex flex-col gap-4">
                <div class="p-4 border rounded-lg">
                  <div class="flex justify-between items-center mb-2">
                    <h4 class="font-medium">Telegram Bot Integration</h4>
                    <span class="text-xs bg-muted px-2 py-1 rounded text-muted-foreground"># ponytail: YAGNI until API exists</span>
                  </div>
                  <p class="text-sm text-muted-foreground mb-4">Send critical alerts (offline node, low battery) to Telegram.</p>
                  <div class="space-y-2">
                    <Label>Bot Token</Label>
                    <Input placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ" />
                  </div>
                  <div class="space-y-2 mt-2">
                    <Label>Chat ID</Label>
                    <Input placeholder="-100123456789" />
                  </div>
                  <Button class="mt-4" variant="outline">Test Connection</Button>
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
            <CardContent class="space-y-4">
              <div class="space-y-2">
                <Label for="current">Current Password</Label>
                <Input id="current" type="password" v-model="currentPassword" />
              </div>
              <div class="space-y-2">
                <Label for="new">New Password</Label>
                <Input id="new" type="password" v-model="newPassword" />
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

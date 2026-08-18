<script setup lang="ts">
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { useEventLogs } from '@/composables/useEventLogs'
import { Info, AlertTriangle, XCircle, Clock } from 'lucide-vue-next'

const { logsQuery } = useEventLogs()

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6">
      <div>
        <h2 class="text-3xl font-bold tracking-tight">Alerts & Event Logs</h2>
        <p class="text-muted-foreground mt-1">System events, node statuses, and threshold alerts.</p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Recent Events</CardTitle>
          <CardDescription>Chronological history of system events.</CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="logsQuery.isLoading.value" class="py-8 text-center text-muted-foreground">
            Loading logs...
          </div>
          <div v-else-if="logsQuery.isError.value" class="py-8 text-center text-destructive">
            Failed to load event logs.
          </div>
          <div v-else-if="logsQuery.data.value?.length === 0" class="py-8 text-center text-muted-foreground border border-dashed rounded-lg">
            No events found.
          </div>
          
          <div v-else class="space-y-4">
            <div 
              v-for="log in logsQuery.data.value" 
              :key="log.id"
              class="flex gap-4 p-4 rounded-xl border bg-card/50 hover:bg-muted/50 transition-colors items-start"
            >
              <!-- Icon -->
              <div class="shrink-0 mt-0.5">
                <Info v-if="log.level === 'INFO'" class="w-5 h-5 text-blue-500" />
                <AlertTriangle v-else-if="log.level === 'WARNING'" class="w-5 h-5 text-yellow-500" />
                <XCircle v-else-if="log.level === 'ERROR'" class="w-5 h-5 text-destructive" />
                <Info v-else class="w-5 h-5 text-muted-foreground" />
              </div>
              
              <!-- Content -->
              <div class="flex-1 space-y-1">
                <div class="flex items-center justify-between">
                  <p class="font-medium text-sm text-foreground">
                    {{ log.message }}
                  </p>
                  <div class="flex items-center text-xs text-muted-foreground whitespace-nowrap ml-4">
                    <Clock class="w-3 h-3 mr-1" />
                    {{ formatDate(log.created_at) }}
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span 
                    :class="[
                      'text-[10px] font-semibold px-2 py-0.5 rounded-full border uppercase tracking-wider',
                      log.level === 'INFO' ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' :
                      log.level === 'WARNING' ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' :
                      log.level === 'ERROR' ? 'bg-destructive/10 text-destructive border-destructive/20' :
                      'bg-muted text-muted-foreground border-border'
                    ]"
                  >
                    {{ log.level }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </DashboardLayout>
</template>

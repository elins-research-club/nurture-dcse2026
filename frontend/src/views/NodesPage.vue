<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import AddNodeDialog from '@/components/dashboard/AddNodeDialog.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useNodes } from '@/composables/useNodes'

const router = useRouter()
const { nodesQuery } = useNodes()

const isNodeActive = (lastSeen: string | undefined) => {
  if (!lastSeen) return false
  const diffMinutes = (new Date().getTime() - new Date(lastSeen).getTime()) / (1000 * 60)
  return diffMinutes < 15
}

const goToNodeDetail = (id: number) => {
  router.push(`/nodes/${id}`)
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-3xl font-bold tracking-tight">Nodes</h2>
        </div>
        
        <AddNodeDialog>
          <template #trigger>
            <Button>Add New Node</Button>
          </template>
        </AddNodeDialog>
      </div>

      <!-- Loading State -->
      <div v-if="nodesQuery.isLoading.value" class="py-12 text-center text-muted-foreground">
        Loading nodes...
      </div>
      
      <!-- Error State -->
      <div v-else-if="nodesQuery.isError.value" class="py-12 text-center text-destructive">
        Failed to load data. Please check connection.
      </div>
      
      <!-- Grid View -->
      <div v-else class="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        <Card v-for="node in nodesQuery.data.value" :key="node.id" class="cursor-pointer hover:border-primary/50 transition-colors" @click="goToNodeDetail(node.id)">
          <CardHeader class="pb-2">
            <div class="flex justify-between items-start">
              <div>
                <CardTitle class="text-lg">{{ node.name }}</CardTitle>
                <CardDescription class="mt-1 font-mono text-xs">{{ node.node_id }}</CardDescription>
              </div>
              <StatusBadge :is-active="isNodeActive(node.last_seen)" :last-seen="node.last_seen" />
            </div>
          </CardHeader>
          <CardContent>
            <div class="text-sm text-muted-foreground mt-4">
              <p><strong>Location:</strong> {{ node.location || 'Not specified' }}</p>
              <p><strong>Last Seen:</strong> {{ node.last_seen ? new Date(node.last_seen).toLocaleString() : 'Never' }}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </DashboardLayout>
</template>

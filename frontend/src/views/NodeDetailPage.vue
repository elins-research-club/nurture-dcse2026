<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import NodeDashboard from '@/components/dashboard/NodeDashboard.vue'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Trash2, Edit } from 'lucide-vue-next'
import { useNodes } from '@/composables/useNodes'
import { useWebSocket } from '@/composables/useWebSocket'
import type { NodeDeviceWithData } from '@/types'

import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import AddChannelDialog from '@/components/dashboard/AddChannelDialog.vue'
import { useChannels } from '@/composables/useChannels'

const route = useRoute()
const router = useRouter()
const nodeId = route.params.id as string

const nodes = ref<NodeDeviceWithData[]>([])

const activeNode = computed(() => {
  return nodes.value.find(n => n.id === nodeId)
})

const nodeStringId = computed(() => activeNode.value?.node_id || '')

const { nodesQuery, updateNodeMutation, deleteNodeMutation } = useNodes()
const { channelsQuery, deleteChannelMutation } = useChannels(nodeStringId)

watch(() => nodesQuery.data.value, (newData) => {
  if (newData) {
    nodes.value = [...newData]
  }
}, { immediate: true })

const wsUrl = 'ws://localhost:8000/ws/dashboard'
const { lastMessage } = useWebSocket(wsUrl)

watch(lastMessage, (msg) => {
  if (!msg || msg.event !== 'sensor_update') return
  
  const nodeIndex = nodes.value.findIndex(n => n.node_id === msg.node_id)
  if (nodeIndex !== -1) {
    const node = { ...nodes.value[nodeIndex] }
    node.last_seen = msg.created_at || new Date().toISOString()
    nodes.value[nodeIndex] = node
  }
})




const isNodeActive = (lastSeen: string | undefined) => {
  if (!lastSeen) return false
  const dateStr = lastSeen.endsWith('Z') ? lastSeen : lastSeen + 'Z';
    const diffMinutes = (new Date().getTime() - new Date(dateStr).getTime()) / (1000 * 60)
  return diffMinutes < 15
}

const goBack = () => {
  router.push('/nodes')
}

// Delete Node state
const isDeleteModalOpen = ref(false)
const confirmDeleteNode = async () => {
  if (!activeNode.value) return
  try {
    await deleteNodeMutation.mutateAsync(activeNode.value.node_id)
    isDeleteModalOpen.value = false
    router.push('/nodes')
  } catch (e) {
    alert('Failed to delete node.')
  }
}

// Edit state
const isEditModalOpen = ref(false)
const editName = ref('')
const editLocation = ref('')
const openEditModal = () => {
  if (!activeNode.value) return
  editName.value = activeNode.value.name
  editLocation.value = activeNode.value.location || ''
  isEditModalOpen.value = true
}

const saveEdit = async () => {
  if (!activeNode.value) return
  try {
    await updateNodeMutation.mutateAsync({
      id: activeNode.value.node_id,
      data: { name: editName.value, location: editLocation.value }
    })
    isEditModalOpen.value = false
  } catch (e) {
    alert('Failed to update node.')
  }
}

// Delete Channel state
const isDeleteChannelModalOpen = ref(false)
const channelToDelete = ref<string | null>(null)
const requestDeleteChannel = (id: string) => {
  channelToDelete.value = id
  isDeleteChannelModalOpen.value = true
}

const confirmDeleteChannel = async () => {
  if (!channelToDelete.value) return
  try {
    await deleteChannelMutation.mutateAsync(channelToDelete.value)
    isDeleteChannelModalOpen.value = false
    channelToDelete.value = null
  } catch (e) {
    alert('Failed to delete channel.')
  }
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-6">
      <div class="flex items-center gap-4">
        <Button variant="outline" size="icon" @click="goBack">
          <ArrowLeft class="w-4 h-4" />
        </Button>
        <div class="flex-1">
          <h2 class="text-3xl font-bold tracking-tight flex items-center gap-4">
            {{ activeNode?.name || 'Loading Node...' }}
            <StatusBadge 
              v-if="activeNode"
              :is-active="isNodeActive(activeNode.last_seen)" 
              :last-seen="activeNode.last_seen" 
            />
          </h2>
          <p class="text-muted-foreground font-mono text-sm mt-1">ID: {{ activeNode?.node_id }}</p>
        </div>
        
        <div class="flex gap-2">
          <Button variant="outline" @click="openEditModal"><Edit class="w-4 h-4 mr-2" /> Edit</Button>
          <Button variant="destructive" @click="isDeleteModalOpen = true"><Trash2 class="w-4 h-4 mr-2" /> Delete</Button>
        </div>
      </div>
      
      <!-- Edit Node Dialog -->
      <Dialog v-model:open="isEditModalOpen">
        <DialogContent class="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Edit Node</DialogTitle>
            <DialogDescription>Update details for {{ activeNode?.node_id }}</DialogDescription>
          </DialogHeader>
          <div class="space-y-4 py-4">
            <div class="space-y-2">
              <Label>Node Name</Label>
              <Input v-model="editName" placeholder="e.g. Greenhouse 2" />
            </div>
            <div class="space-y-2">
              <Label>Location</Label>
              <Input v-model="editLocation" placeholder="e.g. North Sector" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" @click="isEditModalOpen = false">Cancel</Button>
            <Button @click="saveEdit" :disabled="updateNodeMutation.isPending.value">
              {{ updateNodeMutation.isPending.value ? 'Saving...' : 'Save Changes' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <!-- Delete Node Dialog -->
      <Dialog v-model:open="isDeleteModalOpen">
        <DialogContent class="sm:max-w-md p-6 aspect-[4/3] flex flex-col">
          <DialogHeader class="text-center sm:text-center">
            <DialogTitle class="text-destructive w-full">Delete Node</DialogTitle>
          </DialogHeader>
          <div class="flex-1 py-6 text-sm text-muted-foreground flex flex-col items-center justify-center gap-6">
            <div class="w-24 h-24 rounded-full bg-destructive/10 flex items-center justify-center shrink-0">
              <Trash2 class="w-12 h-12 text-destructive" />
            </div>
            <div class="text-center px-4">
              Are you sure you want to delete <strong class="text-foreground font-semibold">{{ activeNode?.name }}</strong>?<br><br>
              This action cannot be undone. All data will be lost.
            </div>
          </div>
          <DialogFooter class="gap-2 sm:gap-0 mt-0 mt-auto">
            <Button variant="outline" @click="isDeleteModalOpen = false" class="w-full sm:w-auto">Cancel</Button>
            <Button variant="destructive" @click="confirmDeleteNode" :disabled="deleteNodeMutation.isPending.value" class="w-full sm:w-auto">
              {{ deleteNodeMutation.isPending.value ? 'Deleting...' : 'Delete Node' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <!-- Delete Channel Dialog -->
      <Dialog v-model:open="isDeleteChannelModalOpen">
        <DialogContent class="sm:max-w-md p-6 aspect-[4/3] flex flex-col">
          <DialogHeader class="text-center sm:text-center">
            <DialogTitle class="text-destructive w-full">Remove Channel</DialogTitle>
          </DialogHeader>
          <div class="flex-1 py-6 text-sm text-muted-foreground flex flex-col items-center justify-center gap-6">
            <div class="w-24 h-24 rounded-full bg-destructive/10 flex items-center justify-center shrink-0">
              <Trash2 class="w-12 h-12 text-destructive" />
            </div>
            <div class="text-center px-4">
              Stop fetching data from this channel?<br><br>
              You can always re-add it later.
            </div>
          </div>
          <DialogFooter class="gap-2 sm:gap-0 mt-0 mt-auto">
            <Button variant="outline" @click="isDeleteChannelModalOpen = false" class="w-full sm:w-auto">Cancel</Button>
            <Button variant="destructive" @click="confirmDeleteChannel" :disabled="deleteChannelMutation.isPending.value" class="w-full sm:w-auto">
              {{ deleteChannelMutation.isPending.value ? 'Removing...' : 'Remove Channel' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <div v-if="!activeNode && !nodesQuery.isLoading.value" class="py-12 text-center text-destructive">
        Node not found.
      </div>
      
      <Tabs defaultValue="dashboard" class="w-full" v-if="activeNode">
        <TabsList class="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
        </TabsList>
        
                <TabsContent value="dashboard" class="space-y-6">
          <NodeDashboard :node-id="nodeStringId" />
        </TabsContent>

        <TabsContent value="configuration" class="space-y-6">
          <div class="border rounded-xl bg-card p-6">
            <div class="flex justify-between items-center mb-6">
              <div>
                <h3 class="text-lg font-medium">ThingSpeak Channels</h3>
                <p class="text-sm text-muted-foreground">Manage channels for fetching data (max 8 fields per channel).</p>
              </div>
              <AddChannelDialog :nodeId="nodeStringId" />
            </div>
            
            <div v-if="channelsQuery.isLoading.value" class="py-8 text-center text-muted-foreground">
              Loading channels...
            </div>
            <div v-else-if="!channelsQuery.data.value?.length" class="py-8 text-center text-muted-foreground border border-dashed rounded-lg">
              No channels configured yet. Click "Add Channel" to connect to ThingSpeak.
            </div>
            <div v-else class="space-y-4">
              <div v-for="channel in channelsQuery.data.value" :key="channel.id" class="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h4 class="font-medium flex items-center gap-2">
                    {{ channel.label || `Channel ${channel.channel_id}` }}
                    <span class="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground font-mono">ID: {{ channel.channel_id }}</span>
                  </h4>
                  <p class="text-sm text-muted-foreground mt-1">Added on {{ new Date(channel.created_at).toLocaleDateString() }}</p>
                </div>
                <Button variant="ghost" size="icon" class="text-destructive hover:text-destructive hover:bg-destructive/10" @click="requestDeleteChannel(channel.id)">
                  <Trash2 class="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  </DashboardLayout>
</template>

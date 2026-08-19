<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useNodes } from '@/composables/useNodes'
import { useAuthStore } from '@/stores/auth'
import { Trash2 } from 'lucide-vue-next'

const isOpen = ref(false)
const step = ref(1)
const errorMsg = ref('')

// Step 1: Node
const nodeId = ref('')
const name = ref('')
const location = ref('')

// Step 2: Channels
interface TempChannel {
  label: string
  channel_id: string
  read_api_key: string
}
const channels = ref<TempChannel[]>([])
const newChannel = ref<TempChannel>({ label: '', channel_id: '', read_api_key: '' })

const { addNodeMutation, nodesQuery, queryClient } = useNodes()
const authStore = useAuthStore()
const API_BASE_URL = 'http://localhost:8000/api/v1'

watch(isOpen, (newVal) => {
  if (newVal) {
    const nodes = nodesQuery.data.value || []
    
    let maxNum = 0
    nodes.forEach(node => {
      const match = node.node_id.match(/^NODE(\d{3})$/i)
      if (match) {
        const num = parseInt(match[1], 10)
        if (num > maxNum) maxNum = num
      }
    })
    
    const nextNum = maxNum + 1
    nodeId.value = `NODE${nextNum.toString().padStart(3, '0')}`
    
    name.value = ''
    location.value = ''
    errorMsg.value = ''
    step.value = 1
    channels.value = []
    newChannel.value = { label: '', channel_id: '', read_api_key: '' }
  }
})

const nextStep = () => {
  errorMsg.value = ''
  if (!nodeId.value || !name.value) {
    errorMsg.value = 'Node ID and Name are required.'
    return
  }
  step.value = 2
}

const addTempChannel = () => {
  if (!newChannel.value.channel_id || !newChannel.value.read_api_key) {
    errorMsg.value = 'Channel ID and Read API Key are required.'
    return
  }
  channels.value.push({ ...newChannel.value })
  newChannel.value = { label: '', channel_id: '', read_api_key: '' }
  errorMsg.value = ''
}

const removeTempChannel = (index: number) => {
  channels.value.splice(index, 1)
}

const isSubmitting = ref(false)

const handleSubmit = async () => {
  errorMsg.value = ''
  isSubmitting.value = true
  
  try {
    // 1. Create Node
    const createdNode = await addNodeMutation.mutateAsync({
      node_id: nodeId.value,
      name: name.value,
      location: location.value
    })
    
    // 2. Create Channels if any
    if (channels.value.length > 0) {
      for (const ch of channels.value) {
        await fetch(`${API_BASE_URL}/nodes/${createdNode.node_id}/channels/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify({
            channel_id: ch.channel_id,
            read_api_key: ch.read_api_key,
            write_api_key: 'N/A', // dummy
            label: ch.label || undefined
          })
        })
      }
    }
    
    // Reset and close
    queryClient.invalidateQueries({ queryKey: ['nodes'] })
    isOpen.value = false
  } catch (err: any) {
    errorMsg.value = err.message || 'Failed to complete node creation'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Dialog v-model:open="isOpen">
    <DialogTrigger asChild>
      <slot name="trigger">
        <Button>Add Node</Button>
      </slot>
    </DialogTrigger>
    
    <DialogContent class="sm:max-w-xl">
      <DialogHeader>
        <DialogTitle>Add New Node</DialogTitle>
        <DialogDescription>
          Follow the steps to register and configure a new smart farming node.
        </DialogDescription>
      </DialogHeader>

      <!-- VISUAL STEPPER -->
      <div class="flex items-center py-4 px-2">
        <!-- Step 1 -->
        <div class="flex items-center text-sm" :class="step >= 1 ? 'text-primary' : 'text-muted-foreground'">
          <div class="flex h-8 w-8 items-center justify-center rounded-full border-2 font-bold transition-colors" 
               :class="step >= 1 ? 'border-primary bg-primary text-primary-foreground' : 'border-muted-foreground'">
            1
          </div>
          <span class="ml-2 font-medium">Node Details</span>
        </div>
        <!-- Connector Line -->
        <div class="mx-4 h-[2px] flex-1 transition-colors" :class="step >= 2 ? 'bg-primary' : 'bg-muted'"></div>
        <!-- Step 2 -->
        <div class="flex items-center text-sm" :class="step >= 2 ? 'text-primary' : 'text-muted-foreground'">
          <div class="flex h-8 w-8 items-center justify-center rounded-full border-2 font-bold transition-colors"
               :class="step >= 2 ? 'border-primary bg-primary text-primary-foreground' : 'border-muted'">
            2
          </div>
          <span class="ml-2 font-medium">ThingSpeak Setup</span>
        </div>
      </div>
      
      <!-- STEP 1 FORM -->
      <div v-if="step === 1" class="grid gap-4 py-2">
        <div class="space-y-2">
          <Label for="nodeId">Node ID (Auto-generated)</Label>
          <Input id="nodeId" v-model="nodeId" placeholder="e.g. NODE001" readonly tabindex="-1" class="bg-muted cursor-not-allowed text-muted-foreground font-mono focus-visible:ring-0 focus-visible:ring-offset-0" />
        </div>
        <div class="space-y-2">
          <Label for="name">Node Name</Label>
          <Input id="name" v-model="name" placeholder="e.g. Greenhouse 2" autofocus />
        </div>
        <div class="space-y-2">
          <Label for="location">Location (Optional)</Label>
          <Input id="location" v-model="location" placeholder="e.g. North Sector" />
        </div>
        
        <div v-if="errorMsg" class="text-sm text-destructive font-medium">
          {{ errorMsg }}
        </div>
      </div>
      
      <!-- STEP 2 FORM -->
      <div v-if="step === 2" class="py-2 space-y-6">
        <div class="border rounded-lg p-4 bg-muted/30 space-y-4">
          <h4 class="font-semibold text-sm">Add a ThingSpeak Channel</h4>
          <div class="grid grid-cols-12 gap-2 items-end">
            <div class="col-span-3 space-y-1">
              <Label class="text-xs text-muted-foreground">Label</Label>
              <Input v-model="newChannel.label" placeholder="e.g. Top Sensor" class="h-9 text-sm bg-background" />
            </div>
            <div class="col-span-4 space-y-1">
              <Label class="text-xs text-muted-foreground">Channel ID</Label>
              <Input v-model="newChannel.channel_id" placeholder="e.g. 123456" class="h-9 text-sm bg-background" />
            </div>
            <div class="col-span-4 space-y-1">
              <Label class="text-xs text-muted-foreground">Read API Key</Label>
              <Input v-model="newChannel.read_api_key" placeholder="API Key" class="h-9 text-sm bg-background" />
            </div>
            <div class="col-span-1">
              <Button @click="addTempChannel" size="sm" class="h-9 w-full px-0 bg-primary/20 text-primary hover:bg-primary/30 border-transparent shadow-none">+</Button>
            </div>
          </div>
        </div>

        <div class="space-y-2">
          <Label>Channels to be attached ({{ channels.length }})</Label>
          <div v-if="channels.length === 0" class="text-sm text-muted-foreground italic p-6 border border-dashed rounded-lg text-center bg-muted/10">
            No channels added yet. You can still finish and add them later.
          </div>
          <div v-else class="space-y-2 max-h-[150px] overflow-y-auto pr-2">
            <div v-for="(ch, idx) in channels" :key="idx" class="flex items-center justify-between p-3 border rounded-lg bg-card text-sm shadow-sm transition-all hover:border-primary/50">
              <div class="flex flex-col">
                <span class="font-semibold text-foreground">{{ ch.label || 'Unlabeled Channel' }}</span> 
                <span class="text-xs text-muted-foreground">ID: {{ ch.channel_id }} &bull; Key: {{ ch.read_api_key.substring(0,4) }}****</span>
              </div>
              <Button variant="ghost" size="icon" class="h-8 w-8 text-destructive hover:bg-destructive/10" @click="removeTempChannel(idx)">
                <Trash2 class="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        <div v-if="errorMsg" class="text-sm text-destructive font-medium">
          {{ errorMsg }}
        </div>
      </div>
      
      <DialogFooter class="pt-4 border-t mt-2">
        <div class="flex items-center justify-end w-full gap-2">
          <!-- Step 1 Buttons -->
          <template v-if="step === 1">
            <Button variant="outline" @click="isOpen = false">Cancel</Button>
            <Button @click="nextStep">Next Step &rarr;</Button>
          </template>

          <!-- Step 2 Buttons -->
          <template v-if="step === 2">
            <Button variant="outline" @click="step = 1" :disabled="isSubmitting">&larr; Back</Button>
            <Button @click="handleSubmit" :disabled="isSubmitting" class="min-w-[120px]">
              {{ isSubmitting ? 'Saving...' : 'Finish & Save' }}
            </Button>
          </template>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

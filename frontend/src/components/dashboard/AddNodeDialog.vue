<script setup lang="ts">
import { ref } from 'vue'
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

const isOpen = ref(false)
const nodeId = ref('')
const name = ref('')
const location = ref('')
const errorMsg = ref('')

const { addNodeMutation } = useNodes()

const handleSubmit = async () => {
  errorMsg.value = ''
  
  if (!nodeId.value || !name.value) {
    errorMsg.value = 'Node ID and Name are required.'
    return
  }

  try {
    await addNodeMutation.mutateAsync({
      node_id: nodeId.value,
      name: name.value,
      location: location.value
    })
    
    // Reset and close
    nodeId.value = ''
    name.value = ''
    location.value = ''
    isOpen.value = false
  } catch (err: any) {
    errorMsg.value = err.message || 'Failed to add node'
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
    
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Add New Node</DialogTitle>
        <DialogDescription>
          Register a new smart farming node to start receiving telemetry data.
        </DialogDescription>
      </DialogHeader>
      
      <div class="grid gap-4 py-4">
        <div class="space-y-2">
          <Label for="nodeId">Node ID</Label>
          <Input id="nodeId" v-model="nodeId" placeholder="e.g. NODE-002" />
        </div>
        <div class="space-y-2">
          <Label for="name">Node Name</Label>
          <Input id="name" v-model="name" placeholder="e.g. Greenhouse 2" />
        </div>
        <div class="space-y-2">
          <Label for="location">Location (Optional)</Label>
          <Input id="location" v-model="location" placeholder="e.g. North Sector" />
        </div>
        
        <div v-if="errorMsg" class="text-sm text-destructive font-medium">
          {{ errorMsg }}
        </div>
      </div>
      
      <DialogFooter>
        <Button variant="outline" @click="isOpen = false">Cancel</Button>
        <Button @click="handleSubmit" :disabled="addNodeMutation.isPending.value">
          {{ addNodeMutation.isPending.value ? 'Adding...' : 'Add Node' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

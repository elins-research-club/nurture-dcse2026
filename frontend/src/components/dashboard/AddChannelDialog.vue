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
import { useChannels } from '@/composables/useChannels'

const props = defineProps<{
  nodeId: string
}>()

const isOpen = ref(false)
const channelId = ref('')
const readApiKey = ref('')
const writeApiKey = ref('')
const label = ref('')
const errorMsg = ref('')

const { addChannelMutation } = useChannels(props.nodeId)

const handleSubmit = async () => {
  errorMsg.value = ''
  
  if (!channelId.value || !readApiKey.value) {
    errorMsg.value = 'Channel ID and Read API Key are required.'
    return
  }

  try {
    await addChannelMutation.mutateAsync({
      channel_id: channelId.value,
      read_api_key: readApiKey.value,
      write_api_key: writeApiKey.value || 'N/A', // Assuming write key isn't strictly necessary for read-only setups but API requires it
      label: label.value || undefined
    })
    
    // Reset and close
    channelId.value = ''
    readApiKey.value = ''
    writeApiKey.value = ''
    label.value = ''
    isOpen.value = false
  } catch (err: any) {
    errorMsg.value = err.message || 'Failed to add channel'
  }
}
</script>

<template>
  <Dialog v-model:open="isOpen">
    <DialogTrigger asChild>
      <slot name="trigger">
        <Button size="sm">Add Channel</Button>
      </slot>
    </DialogTrigger>
    
    <DialogContent class="sm:max-w-xl">
      <DialogHeader>
        <DialogTitle>Add ThingSpeak Channel</DialogTitle>
        <DialogDescription>
          Link a ThingSpeak channel to this node to receive telemetry data.
        </DialogDescription>
      </DialogHeader>
      
      <div class="grid gap-4 py-4">
        <div class="space-y-2">
          <Label for="label">Label (Optional)</Label>
          <Input id="label" v-model="label" placeholder="e.g. Sensors 1-8" />
        </div>
        <div class="space-y-2">
          <Label for="channelId">Channel ID</Label>
          <Input id="channelId" v-model="channelId" placeholder="e.g. 1234567" />
        </div>
        <div class="space-y-2">
          <Label for="readApiKey">Read API Key</Label>
          <Input id="readApiKey" v-model="readApiKey" placeholder="e.g. ABCDEFG123456XYZ" />
        </div>
        <div class="space-y-2">
          <Label for="writeApiKey">Write API Key (Optional for now)</Label>
          <Input id="writeApiKey" v-model="writeApiKey" placeholder="e.g. ZYX654321GFEDCBA" />
        </div>
        
        <div v-if="errorMsg" class="text-sm text-destructive font-medium">
          {{ errorMsg }}
        </div>
      </div>
      
      <DialogFooter>
        <Button variant="outline" @click="isOpen = false">Cancel</Button>
        <Button @click="handleSubmit" :disabled="addChannelMutation.isPending.value">
          {{ addChannelMutation.isPending.value ? 'Adding...' : 'Add Channel' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

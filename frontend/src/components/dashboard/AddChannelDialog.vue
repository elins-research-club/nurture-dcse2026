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
    
    <DialogContent class="sm:max-w-xl rounded-2xl">
      <DialogHeader>
        <DialogTitle class="text-lg font-bold text-foreground">Tambah Channel ThingSpeak</DialogTitle>
      </DialogHeader>
      
      <div class="grid gap-4 py-3">
        <div class="space-y-1.5">
          <Label for="label" class="text-xs font-bold text-foreground">Label (Opsional)</Label>
          <Input id="label" v-model="label" placeholder="Contoh: Kanal 1 - Nutrisi & Tanah" class="rounded-xl h-9 text-xs sm:text-sm" />
        </div>
        <div class="space-y-1.5">
          <Label for="channelId" class="text-xs font-bold text-foreground">Channel ID</Label>
          <Input id="channelId" v-model="channelId" placeholder="Contoh: 3461921" class="rounded-xl h-9 text-xs sm:text-sm font-mono" />
        </div>
        <div class="space-y-1.5">
          <Label for="readApiKey" class="text-xs font-bold text-foreground">Read API Key</Label>
          <Input id="readApiKey" v-model="readApiKey" placeholder="Contoh: ABCDEFG123456XYZ" class="rounded-xl h-9 text-xs sm:text-sm font-mono" />
        </div>
        <div class="space-y-1.5">
          <Label for="writeApiKey" class="text-xs font-bold text-foreground">Write API Key (Opsional)</Label>
          <Input id="writeApiKey" v-model="writeApiKey" placeholder="Contoh: ZYX654321GFEDCBA" class="rounded-xl h-9 text-xs sm:text-sm font-mono" />
        </div>
        
        <div v-if="errorMsg" class="text-xs text-destructive font-semibold bg-destructive/10 p-2.5 rounded-xl border border-destructive/20">
          {{ errorMsg }}
        </div>
      </div>
      
      <DialogFooter class="gap-2 sm:gap-0 pt-2 border-t border-border/80">
        <Button variant="outline" class="rounded-xl font-semibold text-xs cursor-pointer" @click="isOpen = false">Batal</Button>
        <Button 
          class="rounded-xl font-bold text-xs bg-primary text-primary-foreground hover:bg-primary/90 shadow-xs cursor-pointer" 
          @click="handleSubmit" 
          :disabled="addChannelMutation.isPending.value"
        >
          {{ addChannelMutation.isPending.value ? 'Menambahkan...' : 'Tambah Channel' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

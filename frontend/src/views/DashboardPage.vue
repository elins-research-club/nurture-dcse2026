<script setup lang="ts">
import { ref, watch } from 'vue'
import DashboardLayout from '@/components/layout/DashboardLayout.vue'
import NodeDashboard from '@/components/dashboard/NodeDashboard.vue'
import { useNodes } from '@/composables/useNodes'
import type { NodeDeviceWithData } from '@/types'

const { nodesQuery } = useNodes()

const nodes = ref<NodeDeviceWithData[]>([])
const selectedNodeId = ref<number | null>(null)

// When API data loads, update local state
watch(() => nodesQuery.data.value, (newData) => {
  if (newData) {
    nodes.value = [...newData]
    if (!selectedNodeId.value && nodes.value.length > 0) {
      selectedNodeId.value = nodes.value[0].id
    }
  }
}, { immediate: true })

const getActiveNodeData = () => {
  return nodes.value.find(n => n.id === selectedNodeId.value)
}
</script>

<template>
  <DashboardLayout>
    <div class="flex flex-col space-y-3">
      <!-- Loading State -->
      <div v-if="nodesQuery.isLoading.value" class="py-12 text-center text-muted-foreground">
        Loading nodes data...
      </div>
      
      <!-- Error State -->
      <div v-else-if="nodesQuery.isError.value" class="py-12 text-center text-destructive">
        Failed to load data. Please check connection.
      </div>
      
      <!-- No Data State -->
      <div v-else-if="!nodes.length" class="py-12 text-center text-muted-foreground border border-dashed rounded-xl">
        No nodes found. Add a node to get started.
      </div>
      
      <template v-else>
        <!-- Node Selector Tabs (Hanya ditampilkan jika ada lebih dari 1 node) -->
        <div v-if="nodes.length > 1" class="flex gap-2 pb-1 overflow-x-auto">
          <button
            v-for="node in nodes"
            :key="node.id"
            @click="selectedNodeId = node.id"
            :class="[
              'px-4 py-2 rounded-lg border text-sm font-semibold transition-all duration-300 whitespace-nowrap cursor-pointer',
              selectedNodeId === node.id 
                ? 'bg-primary text-primary-foreground border-primary' 
                : 'bg-white text-foreground hover:bg-slate-50 border-border/80'
            ]"
          >
            {{ node.name }}
          </button>
        </div>
        
        <div v-if="getActiveNodeData()">
          <NodeDashboard :node-id="getActiveNodeData()!.node_id" :node-name="getActiveNodeData()!.name" />
        </div>
      </template>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  TitleComponent
])

const props = defineProps<{
  data: any[]
  sensors?: any[]
  title?: string
  isLoading?: boolean
}>()

const COLOR_PALETTE = [
  '#10b981', // Emerald (N)
  '#3b82f6', // Blue (P)
  '#8b5cf6', // Purple (K)
  '#f59e0b', // Amber (pH)
  '#ef4444', // Red (Temp)
  '#06b6d4', // Cyan (Humidity)
  '#84cc16', // Lime (EC)
  '#ec4899', // Pink
  '#f97316', // Orange
  '#14b8a6', // Teal
  '#6366f1'  // Indigo
]

const formatXAxisTime = (ts: string) => {
  if (!ts) return ''
  try {
    const dateStr = ts.endsWith('Z') ? ts : ts + 'Z'
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return ts
    return `${d.toLocaleDateString([], { month: 'numeric', day: 'numeric' })} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
  } catch {
    return ts
  }
}

const option = computed(() => {
  const sensorsList = (props.sensors || []).filter(s => s.name !== 'Status aktuator')
  const feeds = props.data || []

  // Dynamic series generation from database sensor definitions
  const series = sensorsList.map((sensor, index) => {
    const fieldKey = `${sensor.channel_id}_${sensor.thingspeak_field}`
    const color = COLOR_PALETTE[index % COLOR_PALETTE.length]

    return {
      name: `${sensor.name} (${sensor.unit || ''})`.trim(),
      type: 'line',
      smooth: true,
      showSymbol: feeds.length < 30,
      symbolSize: 6,
      connectNulls: true,
      data: feeds.map(item => {
        const val = item[fieldKey]
        return val != null && val !== '' ? parseFloat(val) : null
      }),
      itemStyle: { color },
      lineStyle: { width: 2.5 }
    }
  })

  return {
    title: {
      text: props.title || 'Telemetry Trends',
      left: 'center',
      top: 0,
      textStyle: {
        color: '#475569',
        fontSize: 13,
        fontWeight: 600
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc', fontSize: 12 },
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#475569'
        }
      }
    },
    legend: {
      type: 'scroll',
      top: 24,
      textStyle: { color: '#64748b', fontSize: 11 },
      pageIconColor: '#3b82f6',
      pageTextStyle: { color: '#64748b' }
    },
    grid: {
      left: '3%',
      right: '3%',
      top: 64,
      bottom: 45,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: feeds.map(item => formatXAxisTime(item.created_at || item.timestamp)),
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#64748b', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 11 }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        show: feeds.length > 20,
        bottom: 0,
        height: 18,
        borderColor: 'transparent',
        backgroundColor: 'rgba(241,245,249,0.8)',
        fillerColor: 'rgba(59, 130, 246, 0.15)',
        handleStyle: { color: '#3b82f6' },
        textStyle: { color: '#64748b', fontSize: 10 }
      }
    ],
    series
  }
})
</script>

<template>
  <div class="relative w-full h-[350px] min-h-[350px]">
    <div v-if="isLoading" class="absolute inset-0 z-10 flex items-center justify-center bg-white/70 backdrop-blur-sm rounded-xl">
      <div class="flex items-center gap-2 text-sm text-primary font-medium animate-pulse">
        <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Memuat data historis...</span>
      </div>
    </div>
    <div v-else-if="!data || data.length === 0" class="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-30"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
      <p class="text-xs opacity-60">Belum ada data telemetri untuk rentang ini</p>
    </div>
    <v-chart class="w-full h-[350px]" style="height: 350px; width: 100%;" :option="option" autoresize />
  </div>
</template>

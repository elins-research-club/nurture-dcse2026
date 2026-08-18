<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, TitleComponent } from 'echarts/components'
import VChart, { THEME_KEY } from 'vue-echarts'

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
  title?: string
}>()

// Default theme configuration to match Tailwind UI
const option = computed(() => {
  return {
    title: {
      text: props.title || 'Sensor Trends',
      left: 'center',
      textStyle: {
        color: '#64748b',
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc' }
    },
    legend: {
      bottom: 0,
      textStyle: { color: '#64748b' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.data.map(item => new Date(item.timestamp).toLocaleTimeString()),
      axisLine: { lineStyle: { color: '#334155' } },
      axisLabel: { color: '#64748b' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLabel: { color: '#64748b' }
    },
    series: [
      {
        name: 'Temperature',
        type: 'line',
        smooth: true,
        data: props.data.map(item => item.temperature),
        itemStyle: { color: '#f97316' }, // orange-500
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: 'rgba(249, 115, 22, 0.3)' }, { offset: 1, color: 'rgba(249, 115, 22, 0)' }]
          }
        }
      },
      {
        name: 'Humidity',
        type: 'line',
        smooth: true,
        data: props.data.map(item => item.humidity),
        itemStyle: { color: '#3b82f6' }, // blue-500
      },
      {
        name: 'Soil Moisture',
        type: 'line',
        smooth: true,
        data: props.data.map(item => item.soil_moisture),
        itemStyle: { color: '#b45309' }, // amber-700
      }
    ]
  }
})
</script>

<template>
  <v-chart class="w-full h-full min-h-[350px]" :option="option" autoresize />
</template>

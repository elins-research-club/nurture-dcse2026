<script setup lang="ts">
import { computed, ref, watch, onMounted, nextTick } from 'vue'
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

const vChartRef = ref<any>(null)

// Calculate CSS zoom factor of parent container dynamically
const getParentZoom = (el: HTMLElement | null): number => {
  let curr: HTMLElement | null = el
  while (curr) {
    const style = window.getComputedStyle(curr)
    const zoom = (style as any).zoom
    if (zoom && parseFloat(zoom) && parseFloat(zoom) !== 1) {
      return parseFloat(zoom)
    }
    curr = curr.parentElement
  }
  return 0.75 // Fallback to 0.75 if zoom property is present
}

// Patch ZRender event handler to correct mouse coordinate scaling mismatch with CSS zoom
const patchChartZoom = (chartInstance: any) => {
  if (!chartInstance) return
  const zr = chartInstance.getZr ? chartInstance.getZr() : null
  if (!zr || !zr.handler || (zr.handler as any)._zoomPatched) return

  const originalTrigger = zr.handler.trigger.bind(zr.handler)
  zr.handler.trigger = function (name: string, event: any) {
    if (event) {
      const zoom = getParentZoom(zr.dom) || 0.75
      if (zoom !== 1) {
        if (event.zrX != null && !event._zoomCorrected) {
          event.zrX = event.zrX / zoom
          event._zoomCorrected = true
        }
        if (event.zrY != null && !event._zoomYCorrected) {
          event.zrY = event.zrY / zoom
          event._zoomYCorrected = true
        }
        if (event.offsetX != null && !event._offsetCorrected) {
          event.offsetX = event.offsetX / zoom
          event._offsetCorrected = true
        }
        if (event.offsetY != null && !event._offsetYCorrected) {
          event.offsetY = event.offsetY / zoom
          event._offsetYCorrected = true
        }
      }
    }
    return originalTrigger(name, event)
  }
  ;(zr.handler as any)._zoomPatched = true
}

watch(
  () => vChartRef.value,
  (inst) => {
    if (!inst) return
    nextTick(() => {
      const chart = inst.chart || (inst.getZr ? inst : null)
      if (chart) patchChartZoom(chart)
    })
  },
  { immediate: true, flush: 'post' }
)

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
    textStyle: {
      fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    },
    title: {
      show: false
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: '#334155',
      textStyle: { 
        color: '#f8fafc', 
        fontSize: 13, 
        fontWeight: 500,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      },
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#475569',
          fontSize: 12,
          fontFamily: "'Plus Jakarta Sans', sans-serif"
        }
      }
    },
    legend: {
      type: 'scroll',
      top: 0,
      textStyle: { 
        color: '#475569', 
        fontSize: 13, 
        fontWeight: 600,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      },
      pageIconColor: '#3b82f6',
      pageTextStyle: { 
        color: '#475569', 
        fontSize: 12,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      }
    },
    grid: {
      left: '1%',
      right: '2%',
      top: 36,
      bottom: 32,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: feeds.map(item => formatXAxisTime(item.created_at || item.timestamp)),
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { 
        color: '#475569', 
        fontSize: 12, 
        fontWeight: 600,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
      axisLabel: { 
        color: '#475569', 
        fontSize: 12, 
        fontWeight: 600,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      }
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
        textStyle: { 
          color: '#64748b', 
          fontSize: 10,
          fontFamily: "'Plus Jakarta Sans', sans-serif" 
        }
      }
    ],
    series
  }
})
</script>

<template>
  <div class="relative w-full h-full min-h-[320px] flex-1 flex flex-col">
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- BEAUTIFUL ANIMATED CHART SKELETON LOADER -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div 
      v-if="isLoading" 
      class="absolute inset-0 z-20 flex flex-col justify-between p-4 bg-white/95 dark:bg-card/95 backdrop-blur-md rounded-2xl animate-pulse select-none"
    >
      <!-- 1. Top Legend Skeleton Pills -->
      <div class="flex flex-wrap items-center justify-center gap-4 sm:gap-6 pt-1">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full bg-emerald-500/40 animate-ping duration-1000"></div>
          <div class="h-3.5 w-24 sm:w-28 rounded-md bg-slate-200 dark:bg-slate-800"></div>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full bg-blue-500/40"></div>
          <div class="h-3.5 w-28 sm:w-32 rounded-md bg-slate-200 dark:bg-slate-800"></div>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full bg-purple-500/40"></div>
          <div class="h-3.5 w-24 sm:w-28 rounded-md bg-slate-200 dark:bg-slate-800"></div>
        </div>
      </div>

      <!-- 2. Chart Grid & Wave Silhouette Skeleton -->
      <div class="relative flex-1 my-3 flex flex-col justify-between border-l border-b border-slate-200 dark:border-slate-800 pl-2 pb-1 overflow-hidden min-h-[190px]">
        <!-- Horizontal Guide Lines with Y-Axis Tick Skeletons -->
        <div class="w-full flex items-center gap-2">
          <span class="text-[10px] text-slate-300 dark:text-slate-700 font-mono -ml-6 w-5 text-right">80</span>
          <div class="flex-1 border-b border-dashed border-slate-200 dark:border-slate-800"></div>
        </div>
        <div class="w-full flex items-center gap-2">
          <span class="text-[10px] text-slate-300 dark:text-slate-700 font-mono -ml-6 w-5 text-right">60</span>
          <div class="flex-1 border-b border-dashed border-slate-200 dark:border-slate-800"></div>
        </div>
        <div class="w-full flex items-center gap-2">
          <span class="text-[10px] text-slate-300 dark:text-slate-700 font-mono -ml-6 w-5 text-right">40</span>
          <div class="flex-1 border-b border-dashed border-slate-200 dark:border-slate-800"></div>
        </div>
        <div class="w-full flex items-center gap-2">
          <span class="text-[10px] text-slate-300 dark:text-slate-700 font-mono -ml-6 w-5 text-right">20</span>
          <div class="flex-1 border-b border-dashed border-slate-200 dark:border-slate-800"></div>
        </div>
        <div class="w-full flex items-center gap-2">
          <span class="text-[10px] text-slate-300 dark:text-slate-700 font-mono -ml-6 w-5 text-right">0</span>
          <div class="flex-1 border-b border-slate-200 dark:border-slate-800"></div>
        </div>

        <!-- Animated Shimmer Wave Curves (SVG) -->
        <svg class="absolute inset-0 w-full h-full pointer-events-none opacity-30 dark:opacity-20 pl-2" viewBox="0 0 600 200" preserveAspectRatio="none">
          <!-- Wave 1 (Emerald Wave) -->
          <path 
            d="M 0,140 Q 90,50 180,100 T 360,70 T 500,120 T 600,60" 
            fill="none" 
            stroke="#10b981" 
            stroke-width="3.5" 
            stroke-linecap="round"
            stroke-dasharray="8 4"
          />
          <!-- Wave 2 (Blue Wave) -->
          <path 
            d="M 0,100 Q 120,160 240,80 T 420,130 T 600,90" 
            fill="none" 
            stroke="#3b82f6" 
            stroke-width="3" 
            stroke-linecap="round"
          />
          <!-- Wave 3 (Purple Wave) -->
          <path 
            d="M 0,160 Q 150,110 300,140 T 480,90 T 600,120" 
            fill="none" 
            stroke="#8b5cf6" 
            stroke-width="2.5" 
            stroke-linecap="round"
            stroke-dasharray="4 4"
          />
        </svg>

        <!-- Centered Floating Frosted Loader Pill -->
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="px-4 py-2 rounded-xl bg-white/95 dark:bg-slate-900/95 border border-slate-200 dark:border-slate-700 shadow-lg flex items-center gap-2.5 text-xs sm:text-sm font-bold text-foreground">
            <svg class="animate-spin h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Menghubungkan data telemetri...</span>
          </div>
        </div>
      </div>

      <!-- 3. Bottom X-Axis Time Pill Skeletons & DataZoom Bar -->
      <div class="space-y-2 pt-0.5">
        <div class="flex justify-between items-center px-2">
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-800"></div>
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-800"></div>
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-800"></div>
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-800"></div>
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-800"></div>
        </div>
        <!-- DataZoom Slider Bar Skeleton -->
        <div class="h-3 w-full rounded-md bg-slate-100 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-700/60"></div>
      </div>
    </div>

    <!-- Empty State (No Telemetry Data) -->
    <div v-else-if="!data || data.length === 0" class="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-30"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
      <p class="text-xs opacity-60">Belum ada data telemetri untuk rentang ini</p>
    </div>

    <!-- Live ECharts Canvas -->
    <v-chart 
      ref="vChartRef" 
      class="w-full h-full flex-1" 
      style="height: 100%; width: 100%; min-height: 280px;" 
      :option="option" 
      autoresize 
      @ready="patchChartZoom"
    />
  </div>
</template>

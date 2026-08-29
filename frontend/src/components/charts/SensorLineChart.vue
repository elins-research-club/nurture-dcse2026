<script setup lang="ts">
import { computed, ref, watch, onMounted, nextTick } from 'vue'
import { use, graphic } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, TitleComponent } from 'echarts/components'
import { useDark } from '@vueuse/core'
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

const isDarkMode = useDark({
  storageKey: 'theme',
  valueDark: 'dark',
  valueLight: 'light'
})

const vChartRef = ref<any>(null)

// Precision calibrated coordinate patch for CSS zoom / high-DPI scaling
const patchChartZoom = (chartInstance: any) => {
  const chart = chartInstance?.chart || (chartInstance?.getZr ? chartInstance : null) || vChartRef.value?.chart
  if (!chart) return
  const zr = chart.getZr ? chart.getZr() : null
  if (!zr || !zr.handler) return

  const handler = zr.handler

  const fixEventCoords = (event: any) => {
    if (!event || !zr.dom) return
    const dom = zr.dom
    const rect = dom.getBoundingClientRect()
    // Calculate real pixel ratio between canvas client layout and viewport bounding box
    const scaleX = rect.width > 0 ? dom.clientWidth / rect.width : 1
    const scaleY = rect.height > 0 ? dom.clientHeight / rect.height : 1

    // If there is any scale mismatch (e.g. CSS zoom: 0.75 where scaleX = 1.33333)
    if (Math.abs(scaleX - 1) > 0.01 || Math.abs(scaleY - 1) > 0.01) {
      if (event.clientX != null && rect.left != null) {
        event.zrX = (event.clientX - rect.left) * scaleX
        event.zrY = (event.clientY - rect.top) * scaleY
      } else if (event.zrX != null) {
        event.zrX = event.zrX * scaleX
        event.zrY = event.zrY * scaleY
      }
    }
  }

  const patchProxy = (proxy: any) => {
    if (!proxy || proxy._zoomFixed) return
    proxy._zoomFixed = true
    const origTrigger = proxy.trigger.bind(proxy)
    proxy.trigger = function (name: string, event: any) {
      try {
        fixEventCoords(event)
      } catch (err) {
        // Safe fallback
      }
      return origTrigger(name, event)
    }
  }

  if (handler.proxy) {
    patchProxy(handler.proxy)
  }

  if (!(handler as any)._zoomFixed) {
    ;(handler as any)._zoomFixed = true

    const origSetProxy = handler.setHandlerProxy ? handler.setHandlerProxy.bind(handler) : null
    if (origSetProxy) {
      handler.setHandlerProxy = function (proxy: any) {
        origSetProxy(proxy)
        patchProxy(proxy)
      }
    }
  }
}

watch(
  () => vChartRef.value,
  (inst) => {
    if (!inst) return
    nextTick(() => {
      patchChartZoom(inst)
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

const hexToRgba = (hex: string, alpha: number): string => {
  let c = hex.replace('#', '')
  if (c.length === 3) {
    c = c.split('').map(x => x + x).join('')
  }
  const num = parseInt(c, 16)
  const r = (num >> 16) & 255
  const g = (num >> 8) & 255
  const b = num & 255
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

const getSensorDeterministicColor = (sensorName: string, index: number): string => {
  const name = (sensorName || '').toLowerCase()
  if (name.includes('nitrogen') || name === 'n') return '#10b981' // Green
  if (name.includes('phosphor') || name.includes('fosfor') || name === 'p') return '#3b82f6' // Blue
  if (name.includes('potassium') || name.includes('kalium') || name === 'k') return '#8b5cf6' // Purple
  if (name.includes('ph')) return '#f59e0b' // Amber
  if (name.includes('ec') || name.includes('daya hantar')) return '#84cc16' // Lime
  if (name.includes('suhu dalam') || name.includes('box') || name.includes('panel') || name.includes('enclosure')) return '#f43f5e' // Rose
  if (name.includes('suhu') || name.includes('temp')) return '#ef4444' // Red
  if (name.includes('probe 1')) return '#0ea5e9' // Sky Blue
  if (name.includes('probe 2')) return '#06b6d4' // Cyan
  if (name.includes('probe 3')) return '#14b8a6' // Teal
  if (name.includes('kelembaban') || name.includes('moisture') || name.includes('lembab')) return '#06b6d4' // Cyan
  
  return COLOR_PALETTE[index % COLOR_PALETTE.length]
}

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
  const dark = isDarkMode.value

  // Dynamic series generation from database sensor definitions with aesthetic gradient aura
  const series = sensorsList.map((sensor, index) => {
    const fieldKey = `${sensor.channel_id}_${sensor.thingspeak_field}`
    const color = getSensorDeterministicColor(sensor.name, index)

    return {
      name: `${sensor.name} (${sensor.unit || ''})`.trim(),
      type: 'line',
      smooth: 0.28,
      showSymbol: feeds.length < 35,
      symbol: 'circle',
      symbolSize: 6,
      connectNulls: true,
      data: feeds.map(item => {
        const val = item[fieldKey]
        return val != null && val !== '' ? parseFloat(val) : null
      }),
      itemStyle: { 
        color,
        borderColor: dark ? '#0f172a' : '#ffffff',
        borderWidth: 1.5
      },
      lineStyle: { 
        width: 2.8,
        shadowColor: hexToRgba(color, 0.25),
        shadowBlur: 6,
        shadowOffsetY: 2
      },
      areaStyle: {
        color: new graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: hexToRgba(color, 0.22) },
          { offset: 0.75, color: hexToRgba(color, 0.03) },
          { offset: 1, color: hexToRgba(color, 0.0) }
        ])
      },
      emphasis: {
        focus: 'series',
        lineStyle: { width: 3.6 },
        itemStyle: {
          borderWidth: 3,
          borderColor: '#ffffff',
          shadowBlur: 10,
          shadowColor: hexToRgba(color, 0.5)
        }
      }
    }
  })

  const colorList = series.map(s => s.itemStyle.color)

  return {
    color: colorList,
    textStyle: {
      fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    },
    title: {
      show: false
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: dark ? 'rgba(15, 23, 42, 0.95)' : 'rgba(30, 41, 59, 0.95)',
      borderColor: dark ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.15)',
      borderWidth: 1,
      padding: [10, 14],
      textStyle: { 
        color: '#f8fafc', 
        fontSize: 16, 
        fontWeight: 500,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      },
      axisPointer: {
        type: 'cross',
        crossStyle: {
          color: dark ? '#475569' : '#94a3b8',
          width: 1,
          type: 'dashed'
        },
        label: {
          backgroundColor: dark ? '#334155' : '#475569',
          fontSize: 15,
          fontWeight: 600,
          fontFamily: "'Plus Jakarta Sans', sans-serif",
          borderRadius: 6
        }
      }
    },
    legend: {
      type: 'scroll',
      top: 0,
      data: series.map(s => s.name),
      textStyle: { 
        color: dark ? '#94a3b8' : '#475569', 
        fontSize: 16, 
        fontWeight: 600,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      },
      pageIconColor: '#10b981',
      pageTextStyle: { 
        color: dark ? '#94a3b8' : '#475569', 
        fontSize: 15,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      }
    },
    grid: {
      left: '1%',
      right: '2%',
      top: 42,
      bottom: 34,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: feeds.map(item => formatXAxisTime(item.created_at || item.timestamp)),
      axisLine: { 
        lineStyle: { 
          color: dark ? 'rgba(51, 65, 85, 0.6)' : 'rgba(203, 213, 225, 0.8)' 
        } 
      },
      axisLabel: { 
        color: dark ? '#94a3b8' : '#64748b', 
        fontSize: 15, 
        fontWeight: 600,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { 
        lineStyle: { 
          color: dark ? 'rgba(30, 41, 59, 0.7)' : 'rgba(241, 245, 249, 0.95)', 
          type: 'dashed' 
        } 
      },
      axisLabel: { 
        color: dark ? '#94a3b8' : '#64748b', 
        fontSize: 15, 
        fontWeight: 600,
        fontFamily: "'Plus Jakarta Sans', sans-serif" 
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true,
        moveOnMouseWheel: false,
        preventDefaultMouseMove: true
      },
      {
        type: 'slider',
        show: feeds.length > 15,
        bottom: 2,
        height: 22,
        borderRadius: 11,
        borderColor: dark ? 'rgba(51, 65, 85, 0.4)' : 'rgba(226, 232, 240, 0.8)',
        borderWidth: 1,
        backgroundColor: dark ? 'rgba(15, 23, 42, 0.75)' : 'rgba(241, 245, 249, 0.85)',
        fillerColor: dark ? 'rgba(16, 185, 129, 0.22)' : 'rgba(16, 185, 129, 0.16)',
        dataBackground: {
          lineStyle: {
            color: dark ? '#34d399' : '#10b981',
            width: 1.2,
            opacity: 0.35
          },
          areaStyle: {
            color: dark ? 'rgba(52, 211, 153, 0.08)' : 'rgba(16, 185, 129, 0.08)'
          }
        },
        selectedDataBackground: {
          lineStyle: {
            color: dark ? '#10b981' : '#059669',
            width: 1.8
          },
          areaStyle: {
            color: dark ? 'rgba(16, 185, 129, 0.3)' : 'rgba(5, 150, 105, 0.22)'
          }
        },
        // Modern Pill Handle Icon
        handleIcon: 'path://M-3,-10 h6 a3,3 0 0,1 3,3 v14 a3,3 0 0,1 -3,3 h-6 a3,3 0 0,1 -3,-3 v-14 a3,3 0 0,1 3,-3 z',
        handleSize: '110%',
        handleStyle: {
          color: '#10b981',
          borderColor: dark ? '#0f172a' : '#ffffff',
          borderWidth: 2,
          shadowBlur: 5,
          shadowColor: 'rgba(0, 0, 0, 0.2)',
          shadowOffsetY: 1
        },
        moveHandleSize: 4,
        moveHandleStyle: {
          color: dark ? 'rgba(52, 211, 153, 0.6)' : 'rgba(16, 185, 129, 0.6)'
        },
        textStyle: {
          color: dark ? '#94a3b8' : '#64748b',
          fontSize: 10,
          fontWeight: 600,
          fontFamily: "'Plus Jakarta Sans', sans-serif"
        }
      }
    ],
    series
  }
})
</script>

<template>
  <div data-lenis-prevent class="relative w-full h-full min-h-[320px] flex-1 flex flex-col">
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <!-- CLEAN MINIMAL SKELETON LOADER -->
    <!-- ═══════════════════════════════════════════════════════════════ -->
    <div 
      v-if="isLoading" 
      class="absolute inset-0 z-20 flex flex-col justify-between p-4 bg-white/95 dark:bg-card/95 backdrop-blur-md rounded-2xl select-none"
    >
      <!-- 1. Top Legend Skeleton Pills (Neutral) -->
      <div class="flex flex-wrap items-center justify-center gap-4 sm:gap-6 pt-1">
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-700"></div>
          <div class="h-3.5 w-24 sm:w-28 rounded-md bg-slate-200 dark:bg-slate-700 animate-pulse"></div>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-700"></div>
          <div class="h-3.5 w-28 sm:w-32 rounded-md bg-slate-200 dark:bg-slate-700 animate-pulse"></div>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-700"></div>
          <div class="h-3.5 w-24 sm:w-28 rounded-md bg-slate-200 dark:bg-slate-700 animate-pulse"></div>
        </div>
      </div>

      <!-- 2. Chart Grid Skeleton (Clean Horizontal Dashed Lines) -->
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

        <!-- Centered Floating Frosted Loader Pill -->
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="px-4 py-2 rounded-xl bg-white/95 dark:bg-slate-900/95 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center gap-2.5 text-xs sm:text-sm font-semibold text-foreground">
            <svg class="animate-spin h-4 w-4 text-primary shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-700 animate-pulse"></div>
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-700 animate-pulse"></div>
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-700 animate-pulse"></div>
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-700 animate-pulse"></div>
          <div class="h-2.5 w-14 sm:w-16 rounded bg-slate-200 dark:bg-slate-700 animate-pulse"></div>
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
      :update-options="{ notMerge: true }"
      autoresize 
      @ready="patchChartZoom"
    />
  </div>
</template>

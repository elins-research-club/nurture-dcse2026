/**
 * G-CONNECT Telemetry CSV Exporter Utility
 * Formats time-series sensor telemetry data into structured CSV files with UTF-8 BOM for Microsoft Excel compatibility.
 */

export interface TelemetryExportOptions {
  nodeName: string
  nodeCode: string
  feeds: Record<string, any>[]
  sensors: Array<{
    id?: string | number
    name: string
    unit?: string | null
    field_key?: string
    channel_field?: string
  }>
  timeRangeLabel?: string
  filenamePrefix?: string
}

export function formatWIBTime(dateString: string): string {
  if (!dateString) return '-'
  let s = dateString
  if (!s.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(s)) {
    s += 'Z'
  }
  try {
    const date = new Date(s)
    if (isNaN(date.getTime())) return dateString
    return new Intl.DateTimeFormat('id-ID', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(date).replace(/\./g, ':') + ' WIB'
  } catch {
    return dateString
  }
}

export function exportTelemetryToCSV(options: TelemetryExportOptions): { success: boolean; count: number } {
  const { nodeName, nodeCode, feeds, sensors, timeRangeLabel = 'Custom', filenamePrefix = 'telemetry' } = options

  if (!feeds || feeds.length === 0) {
    throw new Error('Tidak ada data telemetri untuk diekspor.')
  }

  // 1. Build Header Row
  const headers: string[] = [
    'No',
    'Timestamp (WIB)',
    'ID Stasiun',
    'Nama Stasiun'
  ]

  // Map sensor keys
  const activeSensors = sensors.filter(s => s && s.name)
  activeSensors.forEach(sensor => {
    const unitStr = sensor.unit ? ` (${sensor.unit})` : ''
    headers.push(`"${sensor.name.replace(/"/g, '""')}${unitStr}"`)
  })

  // 2. Build Data Rows
  const rows: string[] = []

  feeds.forEach((feed, index) => {
    const rowValues: (string | number)[] = [
      index + 1,
      `"${formatWIBTime(feed.created_at || feed.timestamp || '')}"`,
      `"${nodeCode || '-'}"`,
      `"${nodeName.replace(/"/g, '""')}"`
    ]

    activeSensors.forEach(sensor => {
      let val: any = undefined
      
      const channelId = sensor.channel_id ? String(sensor.channel_id).toLowerCase() : ''
      const tsField = (sensor.thingspeak_field || sensor.field_key || sensor.channel_field || '').toLowerCase()
      const compositeKey = channelId && tsField ? `${channelId}_${tsField}` : ''

      // 1. Direct composite key (UUID_fieldX)
      if (compositeKey && feed[compositeKey] !== undefined) {
        val = feed[compositeKey]
      }
      // 2. Direct sensor name or field_key / channel_field / thingspeak_field / type
      else if (sensor.field_key && feed[sensor.field_key] !== undefined) {
        val = feed[sensor.field_key]
      } else if (sensor.channel_field && feed[sensor.channel_field] !== undefined) {
        val = feed[sensor.channel_field]
      } else if (sensor.thingspeak_field && feed[sensor.thingspeak_field] !== undefined) {
        val = feed[sensor.thingspeak_field]
      } else if (sensor.name && feed[sensor.name] !== undefined) {
        val = feed[sensor.name]
      } else if (sensor.type && feed[sensor.type] !== undefined) {
        val = feed[sensor.type]
      } else {
        // 3. Robust key scanning across all feed entries
        const feedEntries = Object.entries(feed)
        
        // Match by composite key case-insensitively
        const compEntry = compositeKey ? feedEntries.find(([k]) => k.toLowerCase() === compositeKey) : undefined
        if (compEntry !== undefined) {
          val = compEntry[1]
        } else {
          // Match by suffix _fieldX (if single channel or field matching)
          const fieldEntry = tsField ? feedEntries.find(([k]) => k.toLowerCase() === tsField || k.toLowerCase().endsWith(`_${tsField}`)) : undefined
          if (fieldEntry !== undefined) {
            val = fieldEntry[1]
          } else {
            // Match by sensor name or sensor type
            const nameEntry = sensor.name ? feedEntries.find(([k]) => k.toLowerCase() === sensor.name.toLowerCase()) : undefined
            if (nameEntry !== undefined) {
              val = nameEntry[1]
            } else {
              const typeEntry = (sensor as any).type ? feedEntries.find(([k]) => k.toLowerCase() === (sensor as any).type.toLowerCase()) : undefined
              if (typeEntry !== undefined) {
                val = typeEntry[1]
              }
            }
          }
        }
      }

      if (val === null || val === undefined || val === '') {
        rowValues.push('""')
      } else if (typeof val === 'number') {
        rowValues.push(Number.isInteger(val) ? val : Number(val.toFixed(2)))
      } else if (!isNaN(Number(val)) && typeof val === 'string' && val.trim() !== '') {
        const num = Number(val)
        rowValues.push(Number.isInteger(num) ? num : Number(num.toFixed(2)))
      } else {
        rowValues.push(`"${String(val).replace(/"/g, '""')}"`)
      }
    })

    rows.push(rowValues.join(','))
  })

  // 3. Assemble Full CSV with UTF-8 BOM
  const csvContent = '\uFEFF' + [headers.join(','), ...rows].join('\r\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  // 4. Trigger Download
  const link = document.createElement('a')
  const now = new Date()
  const dateStamp = now.toISOString().slice(0, 10) + '_' + String(now.getHours()).padStart(2, '0') + '-' + String(now.getMinutes()).padStart(2, '0')
  const cleanNodeCode = (nodeCode || 'node').toLowerCase().replace(/[^a-z0-9_-]/g, '_')
  const cleanRange = timeRangeLabel.toLowerCase().replace(/[^a-z0-9_-]/g, '_')
  
  link.setAttribute('href', url)
  link.setAttribute('download', `gconnect_${filenamePrefix}_${cleanNodeCode}_${cleanRange}_${dateStamp}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  return { success: true, count: feeds.length }
}

/**
 * Single source of truth for how a sensor is categorised and ordered.
 *
 * The dashboard, the PDF report and the CSV export each used to carry their own
 * `name.includes(...)` filter. They disagreed: "Kelembapan Probe Tanah" landed in
 * the dashboard's soil category but not the report's, so the two showed different
 * parameters for the same station and period. Everything now routes through here.
 */

export type SensorCategory = 'npk' | 'soil' | 'environment' | 'other'

/** Categories a user can pick in the dashboard and the export dialogs. */
export type CategorySelection = 'all' | SensorCategory | 'iot'

export function getSensorCategory(sensor: any): SensorCategory {
  const name = (sensor?.name || '').toLowerCase()
  const type = (sensor?.type || '').toLowerCase()

  // 1. Prioritas tipe semantik NPK
  if (['npk_n', 'npk_p', 'npk_k', 'nitrogen', 'phosphorus', 'potassium'].includes(type) ||
      name.includes('nitrogen') || name.includes('phosphorus') || name.includes('phosphor') ||
      name.includes('phospor') || name.includes('potassium') || name.includes('kalium') ||
      name.includes('fosfor') || type.includes('npk')) {
    return 'npk'
  }

  // 2. Prioritas tipe semantik Tanah
  if (['soil_ph', 'soil_ec', 'soil_temp', 'soil_moisture', 'avg_soil_moisture', 'probe_moist', 'soil_probe'].includes(type) ||
      name.includes('soil') || name.includes('tanah') || name.includes('ph') ||
      name.includes('ec') || name.includes('analog') || name.includes('probe') || type.includes('soil')) {
    return 'soil'
  }

  // 3. Prioritas tipe semantik Lingkungan & Daya
  if (['air_temp', 'air_humidity', 'box_temp', 'batt_volt', 'load_volt', 'batt_current', 'load_current', 'load_power', 'power'].includes(type) ||
      name.includes('suhu') || name.includes('temp') || name.includes('kelembaban') ||
      name.includes('kelembapan') || name.includes('humidity') || name.includes('enclosure') ||
      name.includes('udara') || name.includes('cahaya') || name.includes('baterai') ||
      name.includes('daya') || name.includes('load') || type.includes('env') || type.includes('temp')) {
    return 'environment'
  }

  return 'other'
}

export type TargetWidgetInfo = {
  widgetName: string
  badgeVariant: 'default' | 'secondary' | 'outline' | 'destructive'
  icon: string
  description: string
}

/**
 * Menghasilkan informasi target widget visual di Dashboard berdasarkan type/name sensor.
 * Berguna untuk visual hint di menu Settings agar developer/operator langsung paham
 * di mana metrik ini akan ditampilkan.
 */
export function getTargetWidget(sensor: any): TargetWidgetInfo {
  const name = (sensor?.name || '').toLowerCase()
  const type = (sensor?.type || '').toLowerCase()

  if (type === 'actuator' || name.includes('aktuator')) {
    return {
      widgetName: 'Status Aktuator',
      badgeVariant: 'outline',
      icon: '🎮',
      description: 'Panel status saklar (Kipas, Lampu, Valve) di sidebar kiri.'
    }
  }
  if (['npk_n', 'npk_p', 'npk_k', 'nitrogen', 'phosphorus', 'potassium'].includes(type) ||
      name.includes('nitrogen') || name.includes('fosfor') || name.includes('phosphor') ||
      name.includes('kalium') || name.includes('potassium')) {
    return {
      widgetName: 'Highlight NPK',
      badgeVariant: 'default',
      icon: '🌿',
      description: 'Kartu metrik utama Nitrogen, Fosfor, dan Kalium di baris atas.'
    }
  }
  if (['soil_ph', 'soil_ec', 'soil_temp', 'soil_moisture', 'avg_soil_moisture', 'probe_moist', 'soil_probe'].includes(type) ||
      name.includes('tanah') || name.includes('keasaman') || name.includes('conductivity') ||
      name.includes('kelembapan tanah') || name.includes('kelembaban tanah') || name.includes('ph tanah') || name.includes('ec tanah')) {
    return {
      widgetName: 'Kondisi Tanah',
      badgeVariant: 'secondary',
      icon: '💧',
      description: 'Wrapper kartu kondisi tanah (Kelembapan, pH, Suhu, EC).'
    }
  }
  if (['batt_volt', 'load_volt', 'batt_current', 'load_current', 'load_power', 'power'].includes(type) ||
      name.includes('baterai') || name.includes('daya') ||
      (name.includes('load') && (name.includes('tegangan') || name.includes('arus')))) {
    return {
      widgetName: 'Daya & Baterai',
      badgeVariant: 'outline',
      icon: '⚡',
      description: 'Portlet sistem solar panel (Tegangan, Arus, Daya Beban).'
    }
  }
  if (['box_temp', 'air_temp', 'air_humidity', 'humidity', 'temperature'].includes(type) ||
      name.includes('box') || name.includes('panel') || name.includes('enclosure') ||
      name.includes('luar') || name.includes('udara') || name.includes('suhu') || name.includes('lembab')) {
    return {
      widgetName: 'Kondisi IoT',
      badgeVariant: 'secondary',
      icon: '🌡️',
      description: 'Wrapper kartu kondisi IoT & Lingkungan (Suhu Box, Udara, Kelembaban).'
    }
  }
  return {
    widgetName: 'Metrik Tambahan',
    badgeVariant: 'outline',
    icon: '📌',
    description: 'Grid metrik tambahan/dinamis di bawah dashboard.'
  }
}

/**
 * Canonical display order: nutrients in N-P-K sequence, then probes by index,
 * then alphabetically. Keeps the dashboard summary, the report table and the CSV
 * columns in one predictable sequence.
 */
export function sortSensorsCanonically<T extends { name?: string }>(list: T[]): T[] {
  const npkOrder = (n: string) => {
    if (n.includes('nitrogen') || n === 'n') return 1
    if (n.includes('phosphor') || n.includes('phospor') || n.includes('fosfor') || n === 'p') return 2
    if (n.includes('potassium') || n.includes('kalium') || n === 'k') return 3
    return 99
  }
  const probeOrder = (n: string) => {
    if (n.includes('probe 1')) return 1
    if (n.includes('probe 2')) return 2
    if (n.includes('probe 3')) return 3
    return 99
  }

  return [...list].sort((a, b) => {
    const nameA = (a.name || '').toLowerCase()
    const nameB = (b.name || '').toLowerCase()

    const npkA = npkOrder(nameA)
    const npkB = npkOrder(nameB)
    if (npkA !== 99 || npkB !== 99) return npkA - npkB

    const probeA = probeOrder(nameA)
    const probeB = probeOrder(nameB)
    if (probeA !== 99 || probeB !== 99) return probeA - probeB

    return nameA.localeCompare(nameB)
  })
}

/**
 * Sensors belonging to a selection, actuators removed and canonically ordered.
 * A selection that matches nothing falls back to every sensor, so a view is never
 * left blank — the same behaviour the dashboard has always had.
 */
export function filterSensorsByCategory<T extends { name?: string }>(
  sensors: T[],
  selection: CategorySelection
): T[] {
  const nonActuators = (sensors || []).filter(s => s && s.name !== 'Status aktuator')
  if (selection === 'all') return sortSensorsCanonically(nonActuators)

  // The CSV dialog labels the enclosure/climate group "iot"; it is the same set.
  const wanted: SensorCategory = selection === 'iot' ? 'environment' : selection

  const list = nonActuators.filter(s => getSensorCategory(s) === wanted)
  return sortSensorsCanonically(list.length ? list : nonActuators)
}

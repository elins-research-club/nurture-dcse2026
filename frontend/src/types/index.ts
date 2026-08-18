export interface SensorData {
  id: number
  temperature: number
  humidity: number
  soil_moisture: number
  npk_n: number
  npk_p: number
  npk_k: number
  ph: number
  light_lux: number
  battery_level: number
  is_active: boolean
  timestamp: string
}

export interface NodeDevice {
  id: number
  device_id: string
  name: string
  description?: string
  location_lat?: number
  location_lng?: number
  is_active: boolean
  created_at: string
  last_seen?: string
  thingspeak_channel_id?: string
  thingspeak_read_key?: string
  [key: string]: any
}

export interface NodeDeviceWithData extends NodeDevice {
  latest_data: SensorData | null
}

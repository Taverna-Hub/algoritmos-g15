export interface Detection {
  id?: number
  device_mac: string
  timestamp?: string
  rssi: number
  frequency?: number
  channel?: number
  frame_type?: string
  seen_count?: number
  location?: string
}

export interface Analysis {
  so_identified?: string
  distance_estimated?: number
  confidence?: number
  last_updated?: string
}

export interface Device {
  id?: number
  mac_address: string
  first_seen?: string
  last_seen?: string
  rssi?: number
  frequency?: number
  channel?: number
  frame_type?: string
  seen_count?: number
  ssid?: string
  so_identified?: string
  distance_estimated?: number
  detections?: Detection[]
  analysis?: Analysis | null
}

export interface Statistics {
  total_devices: number
  total_detections: number
  unique_os: number
  devices_inside: number
  devices_outside: number
  os_distribution: Record<string, number>
}

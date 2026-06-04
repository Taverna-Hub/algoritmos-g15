import type { Detection, Device, SensorCounter, Statistics } from './types'

const now = Date.now()

export const mockDevices: Device[] = [
  {
    id: 1,
    mac_address: 'A4:C1:38:7B:9D:21',
    first_seen: new Date(now - 1000 * 60 * 42).toISOString(),
    last_seen: new Date(now - 1000 * 12).toISOString(),
    rssi: -47,
    frequency: 2412000000,
    channel: 1,
    frame_type: 'probe_req',
    seen_count: 28,
    ssid: 'mock-capture',
    is_current_batch: true,
    last_batch_id: new Date(now).toISOString(),
    so_identified: 'Telink Semiconductor',
    distance_estimated: 1.42,
  },
  {
    id: 2,
    mac_address: 'F8:FF:C2:13:4A:0E',
    first_seen: new Date(now - 1000 * 60 * 28).toISOString(),
    last_seen: new Date(now - 1000 * 33).toISOString(),
    rssi: -63,
    frequency: 2437000000,
    channel: 6,
    frame_type: 'beacon',
    seen_count: 17,
    ssid: 'mock-capture',
    is_current_batch: true,
    last_batch_id: new Date(now).toISOString(),
    so_identified: 'Apple Inc.',
    distance_estimated: 4.87,
  },
  {
    id: 3,
    mac_address: 'D0:22:BE:88:F1:43',
    first_seen: new Date(now - 1000 * 60 * 18).toISOString(),
    last_seen: new Date(now - 1000 * 51).toISOString(),
    rssi: -76,
    frequency: 2462000000,
    channel: 11,
    frame_type: 'management',
    seen_count: 9,
    ssid: 'mock-capture',
    is_current_batch: false,
    last_batch_id: new Date(now - 1000 * 60 * 18).toISOString(),
    so_identified: 'Samsung Electronics',
    distance_estimated: 12.35,
  },
  {
    id: 4,
    mac_address: '3C:5A:B4:02:7E:B9',
    first_seen: new Date(now - 1000 * 60 * 9).toISOString(),
    last_seen: new Date(now - 1000 * 7).toISOString(),
    rssi: -58,
    frequency: 5180000000,
    channel: 36,
    frame_type: 'probe_resp',
    seen_count: 21,
    ssid: 'mock-capture',
    is_current_batch: true,
    last_batch_id: new Date(now).toISOString(),
    so_identified: 'Google LLC',
    distance_estimated: 2.96,
  },
]

export const mockDetections: Detection[] = mockDevices.flatMap((device, deviceIndex) =>
  Array.from({ length: Math.min(device.seen_count ?? 1, 6) }, (_, detectionIndex) => ({
    id: deviceIndex * 10 + detectionIndex + 1,
    device_mac: device.mac_address,
    timestamp: new Date(now - 1000 * 30 * (detectionIndex + deviceIndex)).toISOString(),
    rssi: (device.rssi ?? -70) - detectionIndex,
    frequency: device.frequency,
    channel: device.channel,
    frame_type: device.frame_type,
    seen_count: detectionIndex + 1,
    location: (device.rssi ?? -100) > -70 ? 'inside' : 'outside',
  }))
)

export const mockStatistics: Statistics = {
  total_devices: mockDevices.length,
  total_detections: mockDevices.reduce((total, device) => total + (device.seen_count ?? 1), 0),
  unique_os: new Set(mockDevices.map(device => device.so_identified).filter(Boolean)).size,
  devices_inside: mockDevices.filter(device => device.is_current_batch && (device.rssi ?? -100) > -70).length,
  devices_outside: mockDevices.filter(device => device.is_current_batch && (device.rssi ?? -100) <= -70).length,
  os_distribution: mockDevices.reduce<Record<string, number>>((distribution, device) => {
    const os = device.so_identified || 'Desconhecido'
    distribution[os] = (distribution[os] ?? 0) + 1
    return distribution
  }, {}),
}

export const mockTimeline: Record<string, number> = {
  [new Date(now - 1000 * 60 * 45).toISOString()]: 8,
  [new Date(now - 1000 * 60 * 30).toISOString()]: 14,
  [new Date(now - 1000 * 60 * 15).toISOString()]: 21,
  [new Date(now).toISOString()]: 32,
}

export const mockOpticSensorCounter: SensorCounter = {
  sensor_id: 'sensor-2',
  people_count: 0,
  updated_at: new Date(now).toISOString(),
}

export const getMockDevice = (mac: string) =>
  mockDevices.find(device => device.mac_address.toLowerCase() === mac.toLowerCase()) ?? null

export const getMockDetections = (mac: string) =>
  mockDetections.filter(detection => detection.device_mac.toLowerCase() === mac.toLowerCase())

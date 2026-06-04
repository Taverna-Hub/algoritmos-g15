import axios from 'axios'
import type { Device, Detection, SensorCounter, Statistics } from '../types'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const deviceService = {
  getDevices: () => api.get<Device[]>('/devices'),
  getDevice: (mac: string) => api.get<Device>(`/devices/${mac}`),
  getDeviceDetections: (mac: string, limit = 100) => api.get<Detection[]>(`/devices/${mac}/detections`, { params: { limit } }),
  createDevice: (data: Partial<Device>) => api.post<Device>('/devices', data),
}

export const historyService = {
  getDetections: (startDate?: string, endDate?: string, limit = 500) =>
    api.get<Detection[]>('/history/detections', { params: { start_date: startDate, end_date: endDate, limit } }),
  getStatistics: (startDate?: string, endDate?: string) =>
    api.get<Statistics>('/history/stats', { params: { start_date: startDate, end_date: endDate } }),
  getTimeline: (startDate?: string, endDate?: string, interval = 'hour') =>
    api.get<Record<string, number>>('/history/timeline', { params: { start_date: startDate, end_date: endDate, interval } }),
}

export const sensorService = {
  getOpticSensorCounter: () => api.get<SensorCounter>('/sensors/optic/sensor-2'),
}

export const systemService = {
  healthCheck: () => api.get('/health'),
  getInfo: () => api.get('/'),
}

export default api

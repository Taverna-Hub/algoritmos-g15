import { useState, useEffect } from 'react'
import { deviceService, historyService } from '../services/api'
import { getMockDetections, getMockDevice, mockDevices, mockStatistics, mockTimeline } from '../mockData'
import type { Device, Detection, Statistics } from '../types'

export const useDevices = (refreshInterval = 5000) => {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDevices = async () => {
    try {
      setLoading(true)
      const response = await deviceService.getDevices()
      setDevices(response.data)
      setError(null)
    } catch (err: any) {
      console.error('Error fetching devices:', err)
      setDevices(mockDevices)
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDevices()
    const interval = setInterval(fetchDevices, refreshInterval)
    return () => clearInterval(interval)
  }, [refreshInterval])

  return { devices, loading, error, refetch: fetchDevices }
}

export const useDeviceDetail = (mac?: string) => {
  const [device, setDevice] = useState<Device | null>(null)
  const [detections, setDetections] = useState<Detection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDevice = async () => {
    if (!mac) return

    try {
      setLoading(true)
      const [deviceRes, detectionsRes] = await Promise.all([
        deviceService.getDevice(mac),
        deviceService.getDeviceDetections(mac),
      ])
      setDevice(deviceRes.data)
      setDetections(detectionsRes.data)
      setError(null)
    } catch (err: any) {
      console.error('Error fetching device:', err)
      setDevice(getMockDevice(mac))
      setDetections(getMockDetections(mac))
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDevice()
  }, [mac])

  return { device, detections, loading, error, refetch: fetchDevice }
}

export const useStatistics = (startDate?: string, endDate?: string) => {
  const [stats, setStats] = useState<Statistics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      const response = await historyService.getStatistics(startDate, endDate)
      setStats(response.data)
      setError(null)
    } catch (err: any) {
      console.error('Error fetching statistics:', err)
      setStats(mockStatistics)
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [startDate, endDate])

  return { stats, loading, error, refetch: fetchStats }
}

export const useTimeline = (startDate?: string, endDate?: string, interval = 'hour') => {
  const [timeline, setTimeline] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTimeline = async () => {
    try {
      setLoading(true)
      const response = await historyService.getTimeline(startDate, endDate, interval)
      setTimeline(response.data)
      setError(null)
    } catch (err: any) {
      console.error('Error fetching timeline:', err)
      setTimeline(mockTimeline)
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTimeline()
  }, [startDate, endDate, interval])

  return { timeline, loading, error, refetch: fetchTimeline }
}

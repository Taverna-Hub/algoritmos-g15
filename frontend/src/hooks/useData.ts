import { useState, useEffect } from 'react'
import { deviceService, historyService, sensorService } from '../services/api'
import {
  getMockDetections,
  getMockDevice,
  mockDevices,
  mockOpticSensorCounter,
  mockStatistics,
  mockTimeline,
} from '../mockData'
import type { Device, Detection, SensorCounter, Statistics } from '../types'

export const useDevices = (refreshInterval = 60000) => {
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDevices = async (showLoading = false) => {
    try {
      if (showLoading) {
        setLoading(true)
      }
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
    fetchDevices(true)
    const interval = setInterval(() => fetchDevices(false), refreshInterval)
    return () => clearInterval(interval)
  }, [refreshInterval])

  return { devices, loading, error, refetch: () => fetchDevices(true) }
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

export const useOpticSensorCounter = (refreshInterval = 5000) => {
  const [counter, setCounter] = useState<SensorCounter>(mockOpticSensorCounter)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCounter = async (showLoading = false) => {
    try {
      if (showLoading) {
        setLoading(true)
      }
      const response = await sensorService.getOpticSensorCounter()
      setCounter(response.data)
      setError(null)
    } catch (err: any) {
      console.error('Error fetching optic sensor counter:', err)
      setCounter(mockOpticSensorCounter)
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCounter(true)
    const interval = setInterval(() => fetchCounter(false), refreshInterval)
    return () => clearInterval(interval)
  }, [refreshInterval])

  return { counter, loading, error, refetch: () => fetchCounter(true) }
}

import React, { useState, useMemo } from 'react'
import { useDevices, useStatistics } from '../hooks/useData'
import StatCard from '../components/StatCard'
import DeviceList from '../components/DeviceList'
import DeviceDetail from '../components/DeviceDetail'
import Filters from '../components/Filters'
import { Wifi, MapPin, Smartphone } from 'lucide-react'
import type { Device } from '../types'

function Dashboard(): JSX.Element {
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null)
  const [filters, setFilters] = useState({
    search: '',
    os: '',
    location: '',
    minRssi: -100,
    maxRssi: -30,
  })

  const { devices, loading, error } = useDevices(5000)
  const { stats } = useStatistics(undefined, undefined)

  const filteredDevices = useMemo(() => {
    return devices.filter(device => {
      if (filters.search && !device.mac_address.toLowerCase().includes(filters.search.toLowerCase())) {
        return false
      }
      if (filters.os && device.so_identified !== filters.os) {
        return false
      }
      if (filters.location) {
        const isInside = (device.rssi ?? -100) > -70
        if (filters.location === 'inside' && !isInside) return false
        if (filters.location === 'outside' && isInside) return false
      }
      if ((device.rssi ?? -100) < filters.minRssi || (device.rssi ?? -100) > filters.maxRssi) {
        return false
      }
      return true
    })
  }, [devices, filters])

  const osOptions = [...new Set(devices.map(d => d.so_identified).filter(Boolean))] as string[]

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">Error loading data: {error}</div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Devices" value={stats?.total_devices ?? 0} icon={<Smartphone className="w-6 h-6" />} color="blue" />
        <StatCard title="Detections" value={stats?.total_detections ?? 0} icon={<Wifi className="w-6 h-6" />} color="green" />
        <StatCard title="Inside" value={stats?.devices_inside ?? 0} icon={<MapPin className="w-6 h-6" />} color="purple" />
        <StatCard title="Outside" value={stats?.devices_outside ?? 0} icon={<MapPin className="w-6 h-6" />} color="orange" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Filters filters={filters} setFilters={setFilters} osOptions={osOptions} />

          <DeviceList devices={filteredDevices} loading={loading} onSelectDevice={setSelectedDevice} selectedDeviceMac={selectedDevice?.mac_address} />
        </div>

        <div>
          {selectedDevice ? (
            <DeviceDetail device={selectedDevice} onClose={() => setSelectedDevice(null)} />
          ) : (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500"><p>Select a device to view details</p></div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard

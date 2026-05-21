import React from 'react'
import { Activity } from 'lucide-react'
import clsx from 'clsx'
import type { Device } from '../types'

interface Props {
  devices: Device[]
  loading: boolean
  onSelectDevice: (d: Device) => void
  selectedDeviceMac?: string | undefined
}

function DeviceList({ devices, loading, onSelectDevice, selectedDeviceMac }: Props) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <div className="animate-spin">
          <Activity className="w-8 h-8 text-primary-600 mx-auto" />
        </div>
        <p className="mt-2 text-gray-600">Loading devices...</p>
      </div>
    )
  }

  if (devices.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
        <p>No devices found. Make sure the WiFi scanner is running.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">MAC Address</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">OS</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">RSSI (dBm)</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Distance</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Location</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Last Seen</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {devices.map(device => (
              <tr
                key={device.mac_address}
                onClick={() => onSelectDevice(device)}
                className={clsx(
                  'cursor-pointer transition-colors',
                  selectedDeviceMac === device.mac_address ? 'bg-primary-50' : 'hover:bg-gray-50'
                )}
              >
                <td className="px-6 py-4 text-sm font-mono font-medium">{device.mac_address}</td>
                <td className="px-6 py-4 text-sm">
                  <span className="inline-block px-2 py-1 rounded bg-gray-100 text-gray-800">{device.so_identified || 'Unknown'}</span>
                </td>
                <td className="px-6 py-4 text-sm">
                  <span className={clsx('font-semibold', (device.rssi ?? -100) > -70 ? 'text-green-600' : 'text-orange-600')}>
                    {device.rssi} dBm
                  </span>
                </td>
                <td className="px-6 py-4 text-sm">{device.distance_estimated ? `${device.distance_estimated.toFixed(2)}m` : '-'}</td>
                <td className="px-6 py-4 text-sm">
                  <span className={clsx('inline-block px-2 py-1 rounded text-xs font-medium', (device.rssi ?? -100) > -70 ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800')}>
                    {(device.rssi ?? -100) > -70 ? 'Inside' : 'Outside'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{device.last_seen ? new Date(device.last_seen).toLocaleTimeString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default DeviceList

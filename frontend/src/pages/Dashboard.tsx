import React, { useState, useMemo } from 'react'
import { useDevices, useOpticSensorCounter } from '../hooks/useData'
import DashboardKpiCard from '../components/DashboardKpiCard'
import DeviceList from '../components/DeviceList'
import DeviceDetail from '../components/DeviceDetail'
import Filters from '../components/Filters'
import DistanceHeatmap from '../components/DistanceHeatmap'
import ManufacturerDonutChart from '../components/ManufacturerDonutChart'
import { MapPin, Smartphone, Tags, Users } from 'lucide-react'
import type { Device } from '../types'

function Dashboard(): JSX.Element {
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null)
  const [filters, setFilters] = useState({
    search: '',
    os: '',
    location: '',
    minRssi: -100,
    maxRssi: -30,
    showStored: false,
  })

  const { devices, loading, error } = useDevices()
  const { counter: opticSensorCounter } = useOpticSensorCounter()

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

  const osOptions = useMemo(() => {
    return [...new Set(devices.map(d => d.so_identified).filter(Boolean))] as string[]
  }, [devices])

  const currentBatchDevices = useMemo(() => {
    return filteredDevices.filter(device => device.is_current_batch)
  }, [filteredDevices])

  const manufacturerChartData = useMemo(() => {
    const counts = currentBatchDevices.reduce<Record<string, number>>((acc, device) => {
      const manufacturer = device.so_identified || 'Desconhecido'
      acc[manufacturer] = (acc[manufacturer] ?? 0) + 1
      return acc
    }, {})

    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((left, right) => right.value - left.value)
  }, [currentBatchDevices])

  const currentStrongDevices = useMemo(() => {
    return currentBatchDevices.filter(device => (device.rssi ?? -100) > -70)
  }, [currentBatchDevices])

  const peopleInRoom = useMemo(() => {
    return currentStrongDevices.length
  }, [currentStrongDevices])

  const mostCommonManufacturer = useMemo(() => {
    const counts = currentStrongDevices.reduce<Record<string, number>>((acc, device) => {
      const manufacturer = device.so_identified || 'Desconhecido'
      acc[manufacturer] = (acc[manufacturer] ?? 0) + 1
      return acc
    }, {})

    const knownManufacturers = Object.entries(counts)
      .filter(([name]) => name !== 'Desconhecido')
      .sort((left, right) => right[1] - left[1])

    return knownManufacturers[0]?.[0] ?? 'Desconhecida'
  }, [currentStrongDevices])

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-800">
          Não foi possível carregar os dados reais. Exibindo dados simulados com MAC, RSSI, canal, frequência em Hz, frame e quantidade de detecções.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <DashboardKpiCard
          title="Pessoas por WiFi"
          value={peopleInRoom}
          description="Sinal forte no ultimo batch"
          icon={<MapPin className="w-6 h-6" />}
          tone="green"
        />
        <DashboardKpiCard
          title="Sensor optico 2"
          value={opticSensorCounter.people_count}
          description="Contagem fisica via MQTT"
          icon={<Users className="w-6 h-6" />}
          tone="blue"
        />
        <DashboardKpiCard
          title="Marca mais comum"
          value={mostCommonManufacturer}
          description="Sinal forte no ultimo batch"
          icon={<Tags className="w-6 h-6" />}
          tone="orange"
        />
        <DashboardKpiCard
          title="Detectados agora"
          value={currentBatchDevices.length}
          description="MACs do ultimo batch apos filtros"
          icon={<Smartphone className="w-6 h-6" />}
          tone="blue"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <DistanceHeatmap devices={currentBatchDevices} />
        </div>
        <ManufacturerDonutChart data={manufacturerChartData} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Filters filters={filters} setFilters={setFilters} osOptions={osOptions} showStoredToggle={false} />

          <DeviceList
            devices={currentBatchDevices}
            loading={loading}
            onSelectDevice={setSelectedDevice}
            selectedDeviceMac={selectedDevice?.mac_address}
            emptyMessage="Nenhum MAC identificado no ultimo batch."
          />
        </div>

        <div className="self-start">
          {selectedDevice ? (
            <DeviceDetail device={selectedDevice} onClose={() => setSelectedDevice(null)} />
          ) : (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500"><p>Selecione um MAC para ver os detalhes</p></div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard

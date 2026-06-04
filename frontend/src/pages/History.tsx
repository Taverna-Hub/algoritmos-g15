import React, { useMemo, useState } from 'react'
import { useDevices } from '../hooks/useData'
import DeviceList from '../components/DeviceList'
import Filters from '../components/Filters'

function History(): JSX.Element {
  const [filters, setFilters] = useState({
    search: '',
    os: '',
    location: '',
    minRssi: -100,
    maxRssi: -30,
    showStored: true,
  })

  const { devices, loading, error } = useDevices()

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
    return [...new Set(devices.map(device => device.so_identified).filter(Boolean))] as string[]
  }, [devices])

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-800">
          Nao foi possivel carregar os dados reais. Exibindo dados simulados.
        </div>
      )}

      <Filters filters={filters} setFilters={setFilters} osOptions={osOptions} showStoredToggle={false} />

      <DeviceList
        devices={filteredDevices}
        loading={loading}
        emptyMessage="Nenhum endereco armazenado encontrado com os filtros atuais."
        compact
      />
    </div>
  )
}

export default History

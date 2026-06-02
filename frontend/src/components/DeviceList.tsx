import React, { useEffect, useMemo, useState } from 'react'
import { Activity, ChevronLeft, ChevronRight } from 'lucide-react'
import clsx from 'clsx'
import type { Device } from '../types'
import { formatFrequencyHz } from '../utils/formatters'

interface Props {
  devices: Device[]
  loading: boolean
  onSelectDevice: (d: Device) => void
  selectedDeviceMac?: string | undefined
}

const frameLabels: Record<string, string> = {
  probe_req: 'Solicitação probe',
  probe_resp: 'Resposta probe',
  beacon: 'Beacon',
  management: 'Gerenciamento',
}

const formatFrameType = (frameType?: string) => frameLabels[frameType ?? ''] ?? (frameType || '-')

function DeviceList({ devices, loading, onSelectDevice, selectedDeviceMac }: Props) {
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  const totalPages = Math.max(1, Math.ceil(devices.length / pageSize))
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = Math.min(startIndex + pageSize, devices.length)
  const deviceSetKey = useMemo(() => {
    return devices.map(device => device.mac_address).sort().join('|')
  }, [devices])

  const paginatedDevices = useMemo(() => {
    return devices.slice(startIndex, endIndex)
  }, [devices, startIndex, endIndex])

  useEffect(() => {
    setCurrentPage(1)
  }, [deviceSetKey, pageSize])

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages)
    }
  }, [currentPage, totalPages])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <div className="animate-spin">
          <Activity className="w-8 h-8 text-primary-600 mx-auto" />
        </div>
        <p className="mt-2 text-gray-600">Carregando dispositivos...</p>
      </div>
    )
  }

  if (devices.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
        <p>Nenhum MAC capturado. Verifique se o firmware de captura do ESP32 está em execução.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Endereço MAC</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Frame</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">RSSI (dBm)</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Canal</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Frequência (Hz)</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Visto</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Distância est.</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Visto por último</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {paginatedDevices.map(device => (
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
                  <span className="inline-block px-2 py-1 rounded bg-gray-100 text-gray-800">{formatFrameType(device.frame_type)}</span>
                </td>
                <td className="px-6 py-4 text-sm">
                  <span className={clsx('font-semibold', (device.rssi ?? -100) > -70 ? 'text-green-600' : 'text-orange-600')}>
                    {device.rssi} dBm
                  </span>
                </td>
                <td className="px-6 py-4 text-sm">{device.channel ?? '-'}</td>
                <td className="px-6 py-4 text-sm">{formatFrequencyHz(device.frequency)}</td>
                <td className="px-6 py-4 text-sm">{device.seen_count ?? 1}</td>
                <td className="px-6 py-4 text-sm">{device.distance_estimated != null ? `${device.distance_estimated.toFixed(2)}m` : '-'}</td>
                <td className="px-6 py-4 text-sm text-gray-600">{device.last_seen ? new Date(device.last_seen).toLocaleTimeString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-3 border-t bg-gray-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Mostrar</span>
          <select
            value={pageSize}
            onChange={(event) => setPageSize(Number(event.target.value))}
            className="h-9 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
          <span>por pagina</span>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <p className="text-sm text-gray-600">
            {startIndex + 1}-{endIndex} de {devices.length}
          </p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setCurrentPage(page => Math.max(1, page - 1))}
              disabled={currentPage === 1}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-gray-300 bg-white text-gray-700 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Pagina anterior"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>

            <span className="min-w-[5rem] text-center text-sm font-medium text-gray-700">
              {currentPage} / {totalPages}
            </span>

            <button
              type="button"
              onClick={() => setCurrentPage(page => Math.min(totalPages, page + 1))}
              disabled={currentPage === totalPages}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-gray-300 bg-white text-gray-700 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Proxima pagina"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DeviceList

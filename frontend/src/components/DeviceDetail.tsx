import React from 'react'
import { X, Signal, MapPin, Smartphone, Radio, Hash } from 'lucide-react'
import { useDeviceDetail } from '../hooks/useData'
import type { Device } from '../types'
import { formatFrequencyHz } from '../utils/formatters'

interface Props {
  device: Device
  onClose: () => void
}

const frameLabels: Record<string, string> = {
  probe_req: 'Solicitação probe',
  probe_resp: 'Resposta probe',
  beacon: 'Beacon',
  management: 'Gerenciamento',
}

const formatFrameType = (frameType?: string) => frameLabels[frameType ?? ''] ?? (frameType || '-')

function DeviceDetail({ device, onClose }: Props) {
  const { detections, loading } = useDeviceDetail(device?.mac_address)

  if (!device) return null

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden flex flex-col h-full">
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-6 py-4 flex items-center justify-between">
        <h3 className="text-white font-bold">Detalhes do MAC</h3>
        <button onClick={onClose} className="text-white hover:bg-white hover:bg-opacity-20 p-1 rounded"><X className="w-5 h-5" /></button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Endereço MAC</p>
          <p className="text-sm font-mono mt-1 bg-gray-100 px-3 py-2 rounded">{device.mac_address}</p>
        </div>

        <div>
          <div className="flex items-center space-x-2">
            <Smartphone className="w-4 h-4 text-primary-600" />
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Marca/empresa</p>
          </div>
          <p className="text-sm mt-1">{device.so_identified || 'Desconhecido'}</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="flex items-center space-x-2">
              <Hash className="w-4 h-4 text-primary-600" />
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Canal</p>
            </div>
            <p className="text-sm mt-1">{device.channel ?? '-'}</p>
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <Radio className="w-4 h-4 text-primary-600" />
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Frequência (Hz)</p>
            </div>
            <p className="text-sm mt-1">{formatFrequencyHz(device.frequency)}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Frame</p>
            <p className="text-sm mt-1">{formatFrameType(device.frame_type)}</p>
          </div>

          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Quantidade vista</p>
            <p className="text-sm mt-1">{device.seen_count ?? 1}</p>
          </div>
        </div>

        <div>
          <div className="flex items-center space-x-2">
            <Signal className="w-4 h-4 text-primary-600" />
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Intensidade do sinal</p>
          </div>
          <div className="mt-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold">{device.rssi} dBm</span>
              <span className={(device.rssi ?? -100) > -70 ? 'text-green-600 text-xs font-medium px-2 py-1 rounded bg-green-100' : 'text-orange-600 text-xs font-medium px-2 py-1 rounded bg-orange-100'}>
                {(device.rssi ?? -100) > -70 ? 'Forte' : 'Fraco'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className={(device.rssi ?? -100) > -70 ? 'h-2 rounded-full transition-all bg-green-500' : 'h-2 rounded-full transition-all bg-orange-500'} style={{ width: `${Math.max(0, Math.min(100, ((device.rssi ?? -100) + 100) * 2))}%` }} />
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-primary-600" />
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Distância estimada (RSSI)</p>
          </div>
          <p className="text-sm mt-1">{device.distance_estimated != null ? `${device.distance_estimated.toFixed(2)} metros` : 'Calculando...'}</p>
        </div>

        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Localização</p>
          <p className={(device.rssi ?? -100) > -70 ? 'text-sm mt-1 font-medium px-3 py-2 rounded inline-block bg-blue-100 text-blue-800' : 'text-sm mt-1 font-medium px-3 py-2 rounded inline-block bg-gray-100 text-gray-800'}>
            {(device.rssi ?? -100) > -70 ? 'Dentro da loja' : 'Fora da loja'}
          </p>
        </div>

        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Visto pela primeira vez</p>
          <p className="text-sm text-gray-600 mt-1">{device.first_seen ? new Date(device.first_seen).toLocaleString() : '-'}</p>
        </div>

        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Visto por último</p>
          <p className="text-sm text-gray-600 mt-1">{device.last_seen ? new Date(device.last_seen).toLocaleString() : '-'}</p>
        </div>

        {!loading && detections.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Detecções recentes ({detections.length})</p>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {detections.slice(0, 5).map((detection, idx) => (
                <div key={idx} className="text-xs bg-gray-50 p-2 rounded">
                  <p className="text-gray-600">{new Date(detection.timestamp ?? '').toLocaleTimeString()}</p>
                  <p className="text-gray-500">
                    RSSI: {detection.rssi} dBm
                    {detection.frequency != null ? ` | ${formatFrequencyHz(detection.frequency)}` : ''}
                    {detection.channel != null ? ` | canal ${detection.channel}` : ''}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DeviceDetail

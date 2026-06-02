import React from 'react'
import { Cell, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import type { Device } from '../types'

interface HeatmapDatum {
  mac: string
  shortMac: string
  rssiDistance: number
  rssi: number
  channel?: number
  manufacturer: string
  seenCount: number
}

interface Props {
  devices: Device[]
}

const rssiToDistanceScore = (rssi: number) => {
  return Math.max(0, Math.min(100, ((Math.abs(rssi) - 30) / 70) * 100))
}

const pointColor = (rssiDistance: number) => {
  if (rssiDistance <= 35) return '#16a34a'
  if (rssiDistance <= 65) return '#f97316'
  return '#64748b'
}

function HeatmapTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null

  const data = payload[0].payload as HeatmapDatum

  return (
      <div className="rounded-lg border border-gray-200 bg-white p-3 shadow text-sm">
      <p className="font-mono font-semibold text-gray-900">{data.mac}</p>
      <p className="text-gray-600">Marca: {data.manufacturer}</p>
      <p className="text-gray-600">Distancia por RSSI: {data.rssiDistance.toFixed(1)}%</p>
      <p className="text-gray-600">RSSI: {data.rssi} dBm</p>
      <p className="text-gray-600">Canal: {data.channel ?? '-'}</p>
      <p className="text-gray-600">Visto: {data.seenCount}</p>
    </div>
  )
}

function DistanceHeatmap({ devices }: Props) {
  const data = devices
    .filter(device => device.rssi != null)
    .map(device => ({
      mac: device.mac_address,
      shortMac: device.mac_address.slice(-8),
      rssiDistance: rssiToDistanceScore(Number(device.rssi)),
      rssi: Number(device.rssi),
      channel: device.channel,
      manufacturer: device.so_identified || 'Desconhecido',
      seenCount: device.seen_count ?? 1,
    }))

  return (
    <div className="bg-white rounded-lg shadow p-6 min-h-[360px]">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-gray-900">Scatterplot de distancia por RSSI</h3>
        <p className="text-sm text-gray-500">Cada ponto representa um MAC; quanto mais longe da reta, mais fraco o sinal</p>
      </div>

      {data.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-sm text-gray-500">
          Nenhum dispositivo com RSSI para exibir
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <ScatterChart margin={{ top: 12, right: 20, bottom: 18, left: 0 }}>
            <XAxis
              type="category"
              dataKey="shortMac"
              name="Endereco"
              interval="preserveStartEnd"
              tick={{ fontSize: 12 }}
              label={{ value: 'Enderecos MAC', position: 'insideBottom', offset: -10, fontSize: 12 }}
            />
            <YAxis
              type="number"
              dataKey="rssiDistance"
              name="Distancia por RSSI"
              unit="%"
              domain={[0, 100]}
              tick={{ fontSize: 12 }}
              label={{ value: 'Distancia por RSSI', angle: -90, position: 'insideLeft', fontSize: 12 }}
            />
            <ZAxis range={[64, 164]} />
            <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={2} />
            <Tooltip content={<HeatmapTooltip />} cursor={{ strokeDasharray: '3 3' }} />
            <Scatter data={data} name="MACs">
              {data.map(point => (
                <Cell key={point.mac} fill={pointColor(point.rssiDistance)} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

export default DistanceHeatmap

import React from 'react'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

interface ManufacturerDatum {
  name: string
  value: number
}

interface Props {
  data: ManufacturerDatum[]
}

const COLORS = ['#2563eb', '#16a34a', '#f97316', '#7c3aed', '#0891b2', '#db2777', '#64748b']

function ManufacturerDonutChart({ data }: Props) {
  const hasData = data.length > 0

  return (
    <div className="bg-white rounded-lg shadow p-6 h-full min-h-[320px]">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-gray-900">Fabricantes detectados</h3>
        <p className="text-sm text-gray-500">Distribuicao dos MACs filtrados por marca</p>
      </div>

      {!hasData ? (
        <div className="flex h-56 items-center justify-center text-sm text-gray-500">
          Nenhum fabricante para exibir
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={58}
              outerRadius={88}
              paddingAngle={2}
              stroke="#ffffff"
              strokeWidth={2}
            >
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [`${value} dispositivos`, name]}
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

export default ManufacturerDonutChart

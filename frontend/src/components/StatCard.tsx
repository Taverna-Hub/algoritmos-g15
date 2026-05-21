import React from 'react'
import clsx from 'clsx'

interface Props {
  title: string
  value: number | string
  icon?: React.ReactNode
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red'
  subtext?: string
}

function StatCard({ title, value, icon, color = 'blue', subtext = '' }: Props) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    red: 'bg-red-50 text-red-600 border-red-200',
  }

  return (
    <div className={clsx('rounded-lg border p-6', colorClasses[color])}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium opacity-75">{title}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
          {subtext && <p className="text-xs mt-1 opacity-60">{subtext}</p>}
        </div>
        <div className="text-3xl opacity-30">{icon}</div>
      </div>
    </div>
  )
}

export default StatCard

import React from 'react'
import clsx from 'clsx'

interface Props {
  title: string
  value: string | number
  description: string
  icon: React.ReactNode
  tone: 'blue' | 'green' | 'orange'
}

const toneClasses = {
  blue: {
    icon: 'bg-blue-100 text-blue-700',
    accent: 'border-blue-200',
  },
  green: {
    icon: 'bg-green-100 text-green-700',
    accent: 'border-green-200',
  },
  orange: {
    icon: 'bg-orange-100 text-orange-700',
    accent: 'border-orange-200',
  },
}

function DashboardKpiCard({ title, value, description, icon, tone }: Props) {
  const classes = toneClasses[tone]

  return (
    <div className={clsx('bg-white rounded-lg shadow border-l-4 p-5', classes.accent)}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-2xl font-bold text-gray-900 break-words">{value}</p>
          <p className="mt-1 text-xs text-gray-500">{description}</p>
        </div>
        <div className={clsx('shrink-0 rounded-lg p-3', classes.icon)}>{icon}</div>
      </div>
    </div>
  )
}

export default DashboardKpiCard

import React from 'react'
import { Search, Filter } from 'lucide-react'

interface FiltersProps {
  filters: {
    search: string
    os: string
    location: string
    minRssi: number
    maxRssi: number
    showStored: boolean
  }
  setFilters: (f: any) => void
  osOptions: string[]
  showStoredToggle?: boolean
}

function Filters({ filters, setFilters, osOptions, showStoredToggle = true }: FiltersProps) {
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => setFilters((prev: any) => ({ ...prev, search: e.target.value }))
  const handleOsChange = (e: React.ChangeEvent<HTMLSelectElement>) => setFilters((prev: any) => ({ ...prev, os: e.target.value }))
  const handleLocationChange = (location: string) => setFilters((prev: any) => ({ ...prev, location: prev.location === location ? '' : location }))
  const handleRssiChange = (type: 'minRssi' | 'maxRssi', value: number) => setFilters((prev: any) => ({ ...prev, [type]: value }))
  const handleShowStoredChange = (e: React.ChangeEvent<HTMLInputElement>) => setFilters((prev: any) => ({ ...prev, showStored: e.target.checked }))
  const handleReset = () => setFilters({ search: '', os: '', location: '', minRssi: -100, maxRssi: -30, showStored: false })

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center mb-4">
        <Filter className="w-5 h-5 text-primary-600 mr-2" />
        <h3 className="font-semibold text-gray-900">Filtros</h3>
        <button onClick={handleReset} className="ml-auto text-sm text-primary-600 hover:text-primary-700 font-medium">Limpar</button>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Buscar endereço MAC</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" value={filters.search} onChange={handleSearchChange} placeholder="ex.: AA:BB:CC:DD:EE:FF" className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
        </div>

        {showStoredToggle && (
          <label className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-700">
            <input
              type="checkbox"
              checked={filters.showStored}
              onChange={handleShowStoredChange}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span>Mostrar todos os enderecos armazenados</span>
          </label>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Marca/empresa</label>
          <select value={filters.os} onChange={handleOsChange} className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
            <option value="">Todas as marcas</option>
            {osOptions.map(os => <option key={os} value={os}>{os}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Localização</label>
          <div className="flex space-x-2">
            <button onClick={() => handleLocationChange('inside')} className={filters.location === 'inside' ? 'flex-1 px-4 py-2 rounded-lg font-medium transition-colors bg-blue-500 text-white' : 'flex-1 px-4 py-2 rounded-lg font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200'}>Dentro</button>
            <button onClick={() => handleLocationChange('outside')} className={filters.location === 'outside' ? 'flex-1 px-4 py-2 rounded-lg font-medium transition-colors bg-orange-500 text-white' : 'flex-1 px-4 py-2 rounded-lg font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200'}>Fora</button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Intensidade do sinal (RSSI)</label>
          <div className="space-y-2">
            <div>
              <label className="text-xs text-gray-600">Mín: {filters.minRssi} dBm</label>
              <input type="range" min={-100} max={0} value={filters.minRssi} onChange={(e) => handleRssiChange('minRssi', Number(e.target.value))} className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer" />
            </div>
            <div>
              <label className="text-xs text-gray-600">Máx: {filters.maxRssi} dBm</label>
              <input type="range" min={-100} max={0} value={filters.maxRssi} onChange={(e) => handleRssiChange('maxRssi', Number(e.target.value))} className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Filters

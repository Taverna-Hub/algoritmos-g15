import React, { useState } from 'react'
import Dashboard from './pages/Dashboard'
import './App.css'

function App(): JSX.Element {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'history'>('dashboard')

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-primary-800">WiFi MAC Capture</h1>
              <p className="ml-4 text-gray-600">Nearby device monitoring</p>
            </div>
            <div className="text-sm text-gray-500">
              Status: <span className="text-green-600 font-semibold">Online</span>
            </div>
          </div>
        </div>
      </header>

      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setCurrentPage('dashboard')}
              className={`px-3 py-4 text-sm font-medium border-b-2 transition-colors ${
                currentPage === 'dashboard'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setCurrentPage('history')}
              className={`px-3 py-4 text-sm font-medium border-b-2 transition-colors ${
                currentPage === 'history'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              History
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'history' && (
          <div className="text-center py-12">
            <p className="text-gray-600">History page coming soon...</p>
          </div>
        )}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-600 text-sm">
          <p>WiFi MAC Capture System v1.0.0</p>
        </div>
      </footer>
    </div>
  )
}

export default App

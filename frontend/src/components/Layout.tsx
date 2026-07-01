import React from 'react'
import { Activity, BarChart3, Database, Search, UserCheck } from 'lucide-react'

interface LayoutProps {
  children: React.ReactNode
  currentTab: string
  setCurrentTab: (tab: string) => void
}

export const Layout: React.FC<LayoutProps> = ({ children, currentTab, setCurrentTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'track', label: 'Track Event', icon: Database },
    { id: 'search', label: 'Semantic Search', icon: Search },
    { id: 'similarity', label: 'Similar Users', icon: UserCheck },
  ]

  return (
    <div className="flex h-screen bg-brand-darkest text-gray-100 overflow-hidden font-sans">
      {/* Sidebar navigation */}
      <aside className="w-64 bg-brand-dark border-r border-gray-800 flex flex-col justify-between hidden md:flex">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-indigo-600 p-2.5 rounded-xl shadow-lg shadow-indigo-500/20">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-wide bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                UASS System
              </h1>
              <p className="text-[10px] text-gray-400 font-semibold tracking-wider uppercase">
                User Behavior Analytics + Semantic Search
              </p>
            </div>
          </div>

          <nav className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = currentTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                    isActive
                      ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/25 shadow-inner'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/40 border border-transparent'
                  }`}
                >
                  <Icon className={`h-5 w-5 ${isActive ? 'text-indigo-400' : 'text-gray-400'}`} />
                  {item.label}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="p-6 border-t border-gray-800/50">
          <div className="bg-gray-800/20 border border-gray-800 rounded-xl p-3.5 flex items-center gap-3">
            <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <div className="text-xs">
              <p className="font-medium text-gray-300">Server Status</p>
              <p className="text-gray-500">Connected to Postgres</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content body */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header navigation */}
        <header className="md:hidden bg-brand-dark border-b border-gray-800 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-indigo-500" />
            <span className="font-bold text-sm tracking-wide">UASS System</span>
          </div>
          <div className="flex gap-2">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = currentTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`p-2 rounded-lg ${
                    isActive ? 'bg-indigo-600 text-white' : 'text-gray-400'
                  }`}
                  title={item.label}
                >
                  <Icon className="h-4 w-4" />
                </button>
              )
            })}
          </div>
        </header>

        {/* Dynamic page contents wrapper */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-gradient-to-b from-brand-darkest via-brand-darkest to-brand-dark/40">
          <div className="max-w-6xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

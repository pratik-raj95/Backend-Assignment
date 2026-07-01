import React, { useEffect, useState } from 'react'
import { api, AnalyticsData } from '../utils/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Users, Zap, Layers, RefreshCw, AlertTriangle } from 'lucide-react'

export const DashboardOverview: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const analyticsData = await api.getAnalytics()
      setAnalytics(analyticsData)
    } catch (err: any) {
      console.error(err)
      setError(err.response?.data?.error?.message || 'Failed to sync dashboard data.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <div className="h-10 w-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-gray-400 text-sm font-medium">Syncing telemetry data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 text-center max-w-lg mx-auto space-y-3">
        <AlertTriangle className="h-10 w-10 text-red-500 mx-auto" />
        <h3 className="text-lg font-bold text-white">Analytics Sync Timeout</h3>
        <p className="text-sm text-gray-400">{error}</p>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-red-500/25 hover:bg-red-500/40 text-red-300 rounded-xl text-xs font-semibold transition"
        >
          Retry Connection
        </button>
      </div>
    )
  }

  // Prep data for Recharts Bar Chart
  const chartData = analytics
    ? Object.entries(analytics.eventsPerUser).map(([userId, count]) => ({
        user: userId.substring(0, 8) + (userId.length > 8 ? '..' : ''),
        count
      }))
    : []

  const stats = [
    {
      label: 'Total Ingested Events',
      value: analytics?.totalEvents || 0,
      icon: Zap,
      color: 'text-indigo-500',
      bgColor: 'bg-indigo-500/10',
      borderColor: 'border-indigo-500/15'
    },
    {
      label: 'Active System Users',
      value: analytics ? Object.keys(analytics.eventsPerUser).length : 0,
      icon: Users,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/15'
    },
    {
      label: 'Top Active Event Group',
      value: analytics?.mostActiveUsers[0]?.userId || 'N/A',
      icon: Layers,
      color: 'text-violet-500',
      bgColor: 'bg-violet-500/10',
      borderColor: 'border-violet-500/15'
    }
  ]

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">System Telemetry</h2>
          <p className="text-sm text-gray-400">Real-time usage aggregation and logs pipeline.</p>
        </div>
        <button
          onClick={fetchData}
          className="p-2.5 bg-gray-800/80 hover:bg-gray-800 border border-gray-700/60 rounded-xl transition text-gray-300"
          title="Refresh Data"
        >
          <RefreshCw className="h-4.5 w-4.5" />
        </button>
      </div>

      {/* Grid statistics metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, i) => {
          const Icon = stat.icon
          return (
            <div
              key={i}
              className={`bg-brand-dark border ${stat.borderColor} rounded-2xl p-6 flex items-center justify-between hover:scale-[1.01] transition-transform duration-300`}
            >
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  {stat.label}
                </p>
                <p className="text-3xl font-extrabold text-white tracking-tight">
                  {stat.value}
                </p>
              </div>
              <div className={`p-4 rounded-2xl ${stat.bgColor} ${stat.color}`}>
                <Icon className="h-6 w-6" />
              </div>
            </div>
          )
        })}
      </div>

      {/* Main Charts & Timeline Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual Chart Card */}
        <div className="bg-brand-dark border border-gray-800/70 rounded-2xl p-6 lg:col-span-2 space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">User Event Breakdown</h3>
            <p className="text-xs text-gray-400">Distribution mapping of events triggered per client ID.</p>
          </div>
          <div className="h-64">
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="user" stroke="#9ca3af" fontSize={11} tickLine={false} />
                  <YAxis stroke="#9ca3af" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#11131c',
                      borderColor: '#1f2937',
                      borderRadius: '12px',
                      color: '#f3f4f6',
                      fontSize: '12px'
                    }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full border border-dashed border-gray-800 rounded-xl">
                <p className="text-xs text-gray-500">No event counts to chart.</p>
              </div>
            )}
          </div>
        </div>

        {/* Top Active Users list */}
        <div className="bg-brand-dark border border-gray-800/70 rounded-2xl p-6 space-y-6">
          <div>
            <h3 className="text-base font-bold text-white">Most Active Clients</h3>
            <p className="text-xs text-gray-400">Highest volume user analytics tracked.</p>
          </div>
          <div className="space-y-4 max-h-64 overflow-y-auto pr-1">
            {analytics && analytics.mostActiveUsers.length > 0 ? (
              analytics.mostActiveUsers.map((user, i) => (
                <div key={user.userId} className="flex items-center justify-between p-3.5 bg-gray-900/40 border border-gray-800/50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-gray-500 bg-gray-800 h-6 w-6 rounded-lg flex items-center justify-center">
                      {i + 1}
                    </span>
                    <span className="text-xs font-medium text-gray-300 font-mono truncate max-w-[120px]">
                      {user.userId}
                    </span>
                  </div>
                  <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/20">
                    {user.count} events
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-500 text-center py-8">No clients tracked yet.</p>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}

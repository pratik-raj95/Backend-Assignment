import React, { useState } from 'react'
import { api, SimilarUserItem } from '../utils/api'
import { UserCheck, AlertCircle, HelpCircle } from 'lucide-react'

export const SimilarUsers: React.FC = () => {
  const [targetUserId, setTargetUserId] = useState('')
  const [limit, setLimit] = useState(5)
  const [results, setResults] = useState<SimilarUserItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!targetUserId.trim()) return

    setLoading(true)
    setError(null)
    setSearched(true)
    try {
      const response = await api.getSimilarUsers(targetUserId.trim(), limit)
      setResults(response)
    } catch (err: any) {
      console.error(err)
      setError(err.response?.data?.error?.message || 'Failed to fetch similar users.')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const loadHelperUser = (id: string) => {
    setTargetUserId(id)
    setSuccessStatesClean()
  }

  const setSuccessStatesClean = () => {
    setError(null)
    setResults([])
    setSearched(false)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Client Behavioral Overlaps</h2>
        <p className="text-sm text-gray-400">Identify clients exhibiting behavioral similarities by comparing behavioral centroids.</p>
      </div>

      {/* Query form card */}
      <div className="bg-brand-dark border border-gray-800/70 rounded-2xl p-6 md:p-8 space-y-6">
        <form onSubmit={handleQuery} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div className="md:col-span-2 space-y-2">
              <label className="text-xs font-bold text-gray-300 uppercase tracking-wide">Target Client ID</label>
              <input
                type="text"
                placeholder="e.g. user_developer_1"
                value={targetUserId}
                onChange={(e) => setTargetUserId(e.target.value)}
                className="w-full bg-gray-900 border border-gray-800 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-white focus:outline-none transition-colors"
                required
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-300 uppercase tracking-wide">Limit Matches</label>
              <select
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="bg-gray-900 border border-gray-800 text-xs text-gray-300 rounded-xl px-3 py-3 w-full focus:outline-none focus:border-indigo-500"
              >
                <option value={3}>Top 3 profiles</option>
                <option value={5}>Top 5 profiles</option>
                <option value={10}>Top 10 profiles</option>
              </select>
            </div>
          </div>

          {/* Quick helpers */}
          <div className="text-xs text-gray-500 flex items-center gap-1.5">
            <HelpCircle className="h-4.5 w-4.5 text-gray-600" />
            Try tracking events first, then search:
            <button
              type="button"
              onClick={() => loadHelperUser('user_developer_1')}
              className="text-indigo-400 hover:text-indigo-300 font-mono underline"
            >
              user_developer_1
            </button>
            or
            <button
              type="button"
              onClick={() => loadHelperUser('user_developer_2')}
              className="text-indigo-400 hover:text-indigo-300 font-mono underline"
            >
              user_developer_2
            </button>
          </div>

          <button
            type="submit"
            disabled={loading || !targetUserId.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 text-white font-semibold py-3 px-4 rounded-xl text-sm transition shadow-lg shadow-indigo-600/15 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Evaluating user coordinates...
              </>
            ) : (
              <>
                <UserCheck className="h-4.5 w-4.5" />
                Find Similar Users
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error block */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex gap-3 items-start animate-fadeIn">
          <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
          <p className="text-xs text-red-400 font-medium leading-relaxed">{error}</p>
        </div>
      )}

      {/* Similarity results representation */}
      <div className="space-y-4">
        {loading ? (
          <div className="space-y-3">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="bg-brand-dark border border-gray-800/40 rounded-xl p-5 animate-pulse h-24"></div>
            ))}
          </div>
        ) : results.length > 0 ? (
          results.map((user) => {
            const similarityPercent = Math.round(user.similarity_score * 100)
            return (
              <div
                key={user.userId}
                className="bg-brand-dark border border-gray-800/70 rounded-xl p-5 space-y-4 hover:scale-[1.01] transition-transform duration-350"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-mono font-bold text-white">{user.userId}</h4>
                    <p className="text-xs text-gray-500 mt-1">
                      Volume: {user.total_events} events &bull; Last Active:{' '}
                      {user.last_active ? new Date(user.last_active).toLocaleString() : 'N/A'}
                    </p>
                  </div>
                  <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-xl">
                    {similarityPercent}% similarity
                  </span>
                </div>
                
                {/* Horizontal Progress bar for visual aesthetics */}
                <div className="w-full bg-gray-900 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(5, similarityPercent)}%` }}
                  ></div>
                </div>
              </div>
            )
          })
        ) : (
          searched && !loading && !error && (
            <div className="text-center py-12 bg-brand-dark border border-gray-800/40 border-dashed rounded-2xl">
              <UserCheck className="h-8 w-8 text-gray-600 mx-auto mb-3" />
              <p className="text-sm text-gray-400">No active behavioral overlaps computed for this user.</p>
            </div>
          )
        )}
      </div>
    </div>
  )
}

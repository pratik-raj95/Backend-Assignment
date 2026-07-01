import React, { useState } from 'react'
import { api, SearchResultItem } from '../utils/api'
import { Search, SlidersHorizontal, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'

export const SemanticSearch: React.FC = () => {
  const [query, setQuery] = useState('')
  const [threshold, setThreshold] = useState(0.0)
  const [limit, setLimit] = useState(10)
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedCard, setExpandedCard] = useState<string | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    try {
      const response = await api.semanticSearch(query.trim(), limit, threshold)
      setResults(response.results)
    } catch (err: any) {
      console.error(err)
      setError(err.response?.data?.error?.message || 'Vector search query failed.')
    } finally {
      setLoading(false)
    }
  }

  const toggleMetadata = (id: string) => {
    if (expandedCard === id) {
      setExpandedCard(null)
    } else {
      setExpandedCard(id)
    }
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Semantic Similarity Search</h2>
        <p className="text-sm text-gray-400">Search tracked behaviors using natural language queries powered by FAISS vectors.</p>
      </div>

      {/* Query Search Panel */}
      <div className="bg-brand-dark border border-gray-800/70 rounded-2xl p-6 space-y-6">
        <form onSubmit={handleSearch} className="space-y-5">
          <div className="relative">
            <Search className="absolute left-4 top-3.5 h-5 w-5 text-gray-500" />
            <input
              type="text"
              placeholder="e.g. user exploring pricing plans..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800 focus:border-indigo-500 rounded-xl pl-12 pr-28 py-3.5 text-sm text-white focus:outline-none transition-colors"
              required
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-2 top-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 text-white font-semibold px-4 py-2 rounded-lg text-xs transition"
            >
              {loading ? 'Searching...' : 'Search Vectors'}
            </button>
          </div>

          {/* Filtering parameters collapsible */}
          <div className="p-4 bg-gray-900/40 border border-gray-800/60 rounded-xl space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-gray-300 uppercase tracking-wider">
              <SlidersHorizontal className="h-4 w-4 text-indigo-400" /> Filter Criteria
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Threshold Slider */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-gray-400">Minimum Cosine Similarity Score</span>
                  <span className="font-mono text-indigo-400 font-bold">{threshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="w-full h-1 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              {/* Limit selector */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-gray-400 block">Match Limit Count</label>
                <select
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value))}
                  className="bg-gray-900 border border-gray-800 text-xs text-gray-300 rounded-xl px-3 py-2 w-full focus:outline-none focus:border-indigo-500"
                >
                  <option value={5}>Top 5 matches</option>
                  <option value={10}>Top 10 matches</option>
                  <option value={20}>Top 20 matches</option>
                </select>
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Error block */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex gap-3 items-start animate-fadeIn">
          <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
          <p className="text-xs text-red-400 font-medium">{error}</p>
        </div>
      )}

      {/* Results Section */}
      <div className="space-y-4">
        {loading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-brand-dark border border-gray-800/40 rounded-xl p-5 animate-pulse h-20"></div>
            ))}
          </div>
        ) : results.length > 0 ? (
          results.map((item) => {
            const similarityPercent = Math.round(item.similarity_score * 100)
            const isExpanded = expandedCard === item.id

            return (
              <div
                key={item.id}
                className="bg-brand-dark border border-gray-800/70 hover:border-gray-850 rounded-xl p-5 transition duration-300 space-y-3.5"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2.5">
                      <h4 className="text-sm font-bold text-white leading-none">{item.event}</h4>
                      <button
                        onClick={() => toggleMetadata(item.id)}
                        className="text-gray-500 hover:text-gray-300"
                      >
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </button>
                    </div>
                    <p className="text-xs text-gray-400 font-medium">
                      Client ID: <span className="font-mono text-gray-500">{item.userId}</span> &bull; Logged: {new Date(item.timestamp).toLocaleString()}
                    </p>
                  </div>
                  
                  {/* Glowing match indicator percentage */}
                  <div className="text-right">
                    <span className="inline-flex items-center gap-1.5 text-xs font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-3 py-1.5 rounded-xl">
                      {similarityPercent}% Match
                    </span>
                  </div>
                </div>

                {/* Collapsible Metadata Editor block */}
                {isExpanded && (
                  <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800/50 font-mono text-xs text-gray-400 overflow-x-auto animate-slideDown">
                    <pre>{JSON.stringify(item.metadata, null, 2)}</pre>
                  </div>
                )}
              </div>
            )
          })
        ) : (
          !loading && query && (
            <div className="text-center py-12 bg-brand-dark border border-gray-800/40 border-dashed rounded-2xl">
              <Search className="h-8 w-8 text-gray-600 mx-auto mb-3" />
              <p className="text-sm text-gray-400">No semantic matches found above threshold.</p>
            </div>
          )
        )}
      </div>
    </div>
  )
}

import React, { useState } from 'react'
import { api } from '../utils/api'
import { Database, AlertCircle, CheckCircle2, Terminal } from 'lucide-react'

export const EventForm: React.FC = () => {
  const [userId, setUserId] = useState('')
  const [event, setEvent] = useState('')
  const [metadataStr, setMetadataStr] = useState('{\n  "page": "/pricing",\n  "plan": "premium"\n}')
  
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [jsonValid, setJsonValid] = useState(true)

  // Real-time JSON validation
  const handleJsonChange = (val: string) => {
    setMetadataStr(val)
    if (!val.trim()) {
      setJsonValid(true)
      return
    }
    try {
      JSON.parse(val)
      setJsonValid(true)
    } catch {
      setJsonValid(false)
    }
  }

  const loadMockTemplate = (type: string) => {
    let mockData = {}
    if (type === 'view') {
      setUserId('user_developer_1')
      setEvent('user viewed pricing page')
      mockData = { page: '/pricing', source: 'google_ads', device: 'desktop' }
    } else if (type === 'checkout') {
      setUserId('user_developer_2')
      setEvent('onboarding completion')
      mockData = { step: 3, timeSpentSeconds: 145, newsletterSubscribed: true }
    } else {
      setUserId('user_developer_3')
      setEvent('clicked payment button')
      mockData = { target: 'standard-tier-btn', method: 'stripe' }
    }
    setMetadataStr(JSON.stringify(mockData, null, 2))
    setJsonValid(true)
    setSuccess(null)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSuccess(null)
    setError(null)

    if (!userId.trim() || !event.trim()) {
      setError('Client ID and Event name are required inputs.')
      return
    }

    let parsedMetadata = {}
    if (metadataStr.trim()) {
      try {
        parsedMetadata = JSON.parse(metadataStr)
      } catch {
        setError('Invalid metadata formatting. Must be syntactically correct JSON.')
        return
      }
    }

    setLoading(true)
    try {
      const response = await api.trackEvent({
        userId: userId.trim(),
        event: event.trim(),
        metadata: parsedMetadata
      })
      setSuccess(response.message + ` Event UUID: ${response.eventId}`)
      // Clear inputs except user id to ease multiple tracks
      setEvent('')
    } catch (err: any) {
      console.error(err)
      setError(err.response?.data?.error?.message || 'Server ingestion failure.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Event Telemetry Playground</h2>
        <p className="text-sm text-gray-400">Manually trigger events to track user behaviors in PostgreSQL and FAISS.</p>
      </div>

      <div className="bg-brand-dark border border-gray-800/70 rounded-2xl p-6 md:p-8 space-y-6">
        {/* Quick autofill helpers */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Mock Templates Ingestion</p>
          <div className="flex gap-2.5">
            <button
              onClick={() => loadMockTemplate('view')}
              className="px-3.5 py-2 bg-gray-800/50 hover:bg-gray-850 border border-gray-700/60 rounded-xl text-xs font-medium transition text-gray-300"
            >
              Pricing View
            </button>
            <button
              onClick={() => loadMockTemplate('checkout')}
              className="px-3.5 py-2 bg-gray-800/50 hover:bg-gray-850 border border-gray-700/60 rounded-xl text-xs font-medium transition text-gray-300"
            >
              Onboarding Complete
            </button>
            <button
              onClick={() => loadMockTemplate('click')}
              className="px-3.5 py-2 bg-gray-800/50 hover:bg-gray-850 border border-gray-700/60 rounded-xl text-xs font-medium transition text-gray-300"
            >
              Payment Button Click
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* User ID Field */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-300 uppercase tracking-wide">Client ID (userId)</label>
            <input
              type="text"
              placeholder="e.g. user_9823"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-white focus:outline-none transition-colors"
              required
            />
          </div>

          {/* Event Field */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-300 uppercase tracking-wide">Tracked Action (event)</label>
            <input
              type="text"
              placeholder="e.g. user viewed pricing page"
              value={event}
              onChange={(e) => setEvent(e.target.value)}
              className="w-full bg-gray-900 border border-gray-800 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-white focus:outline-none transition-colors"
              required
            />
          </div>

          {/* Metadata JSON Field */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-gray-300 uppercase tracking-wide flex items-center gap-1.5">
                <Terminal className="h-4 w-4 text-indigo-400" /> Event Metadata (JSON)
              </label>
              {!jsonValid && (
                <span className="text-[10px] bg-red-500/10 text-red-400 px-2 py-0.5 border border-red-500/20 rounded font-semibold uppercase">
                  Invalid Syntax
                </span>
              )}
            </div>
            <textarea
              rows={5}
             placeholder={`{
  "key": "value"
}`}
              value={metadataStr}
              onChange={(e) => handleJsonChange(e.target.value)}
              className={`w-full bg-gray-900 border ${
                jsonValid ? 'border-gray-800 focus:border-indigo-500' : 'border-red-500 focus:border-red-500'
              } rounded-xl px-4 py-3 text-sm font-mono text-gray-300 focus:outline-none transition-colors`}
            />
          </div>

          {/* Error and Success notifications */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex gap-3 items-start animate-fadeIn">
              <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
              <p className="text-xs text-red-400 font-medium leading-relaxed">{error}</p>
            </div>
          )}

          {success && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 flex gap-3 items-start animate-fadeIn">
              <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
              <p className="text-xs text-emerald-400 font-medium leading-relaxed">{success}</p>
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading || !jsonValid}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-xl text-sm transition shadow-lg shadow-indigo-600/15 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Ingesting telemetries...
              </>
            ) : (
              <>
                <Database className="h-4 w-4" />
                Track Operations Event
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

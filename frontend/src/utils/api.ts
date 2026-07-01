import axios from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  'https://backend-assignment-6t4n.onrender.com'

const API_PREFIX = '/api/v1'
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10s timeout
})

// Intercept requests to inject logs or request tracing IDs in the client console
apiClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

export interface TrackPayload {
  userId: string
  event: string
  metadata: Record<string, any>
  timestamp?: string
}

export interface SearchResultItem {
  id: string
  userId: string
  event: string
  metadata: Record<string, any>
  timestamp: string
  similarity_score: number
}

export interface SimilarUserItem {
  userId: string
  similarity_score: number
  total_events: number
  last_active: string | null
}

export interface AnalyticsData {
  totalEvents: number
  eventsPerUser: Record<string, number>
  mostActiveUsers: Array<{ userId: string; count: number }>
}

export const api = {
  /**
   * Tracks an event
   */
  async trackEvent(payload: TrackPayload) {
    const response = await apiClient.post<{ success: boolean; eventId: string; message: string }>('/track', payload)
    return response.data
  },

  /**
   * Fetches analytics aggregation metrics
   */
  async getAnalytics(params: { event?: string; from?: string; to?: string } = {}) {
    const response = await apiClient.get<AnalyticsData>('/analytics', { params })
    return response.data
  },

  /**
   * Executes semantic search query
   */
  async semanticSearch(query: string, limit = 10, threshold = 0.0) {
    const response = await apiClient.get<{ results: SearchResultItem[] }>('/search', {
      params: { query, limit, threshold },
    })
    return response.data
  },

  /**
   * Computes similar user profiles
   */
  async getSimilarUsers(userId: string, limit = 5) {
    const response = await apiClient.get<SimilarUserItem[]>('/similar-users', {
      params: { userId, limit },
    })
    return response.data
  },

  /**
   * Fetches server health
   */
  async getHealth() {
    const response = await apiClient.get('/health')
    return response.data
  }
}


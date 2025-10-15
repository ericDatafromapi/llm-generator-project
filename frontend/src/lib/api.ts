import axios, { AxiosError } from 'axios'
import type { ApiError } from '@/types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Track if we're currently refreshing to avoid race conditions
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: any) => void
  reject: (error?: any) => void
}> = []

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })

  failedQueue = []
}

// Request interceptor - add JWT token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle token refresh with race condition protection
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config

    // If error is 401 and we haven't tried to refresh yet
    if (error.response?.status === 401 && originalRequest && !originalRequest.headers['X-Retry']) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => {
            return Promise.reject(err)
          })
      }

      const refreshToken = localStorage.getItem('refresh_token')
      
      if (!refreshToken) {
        // No refresh token - redirect to login only if not already on login page
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }

      isRefreshing = true
      originalRequest.headers['X-Retry'] = 'true'

      try {
        // Try to refresh the token
        const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token, refresh_token: newRefreshToken } = response.data

        // Update tokens
        localStorage.setItem('access_token', access_token)
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken)
        }

        // Process queued requests
        processQueue(null, access_token)

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed - process queue with error
        processQueue(refreshError, null)
        
        // Clear tokens and redirect only if not already on login page
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
        
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// Helper function to handle API errors
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>
    return axiosError.response?.data?.detail || error.message || 'An error occurred'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}
import { create } from 'zustand'
import { api } from '@/lib/api'
import type { User, LoginRequest, RegisterRequest, AuthResponse } from '@/types'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  isInitialized: boolean
  error: string | null
  
  // Actions
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  isInitialized: false,
  error: null,

  login: async (credentials) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post<AuthResponse>('/api/v1/auth/login', {
        email: credentials.email,
        password: credentials.password,
      })

      const { access_token, refresh_token, user } = response.data

      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)

      set({ user, isAuthenticated: true, isInitialized: true, isLoading: false })
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post<AuthResponse>('/api/v1/auth/register', data)
      const { access_token, refresh_token, user } = response.data

      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)

      set({ user, isAuthenticated: true, isInitialized: true, isLoading: false })
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Registration failed'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false, isInitialized: true })
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isAuthenticated: false, user: null, isInitialized: true })
      return
    }

    try {
      const response = await api.get<User>('/api/v1/auth/me')
      set({ user: response.data, isAuthenticated: true, isInitialized: true })
    } catch (error) {
      // Only clear tokens and logout if it's not a network error
      const isNetworkError = !error || !(error as any).response
      if (!isNetworkError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
      set({ user: null, isAuthenticated: false, isInitialized: true })
    }
  },

  clearError: () => set({ error: null }),
}))
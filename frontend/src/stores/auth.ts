/**
 * Authentication Store - Phase 7
 * Manages user authentication state, JWT tokens, and login/logout flow
 */
import { defineStore } from 'pinia'
import { authApi, type User } from '../api/authApi'
import axios from 'axios'

const TOKEN_STORAGE_KEY = 'tenderlenzz_auth_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: localStorage.getItem(TOKEN_STORAGE_KEY) || null as string | null,
    isAuthenticating: false,
    authError: null as string | null
  }),

  getters: {
    isAuthenticated: (state): boolean => state.token !== null && state.user !== null,
    isOfficer: (state): boolean => state.user?.role === 'OFFICER',
    isBidder: (state): boolean => state.user?.role === 'BIDDER',
    currentUsername: (state): string => state.user?.username || 'Guest'
  },

  actions: {
    /**
     * Login with username and password
     */
    async login(username: string, password: string): Promise<boolean> {
      this.isAuthenticating = true
      this.authError = null

      try {
        const response = await authApi.login({ username, password })

        // Store token
        this.token = response.access_token
        localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token)

        // Store user info
        this.user = response.user

        // Configure axios to include token in all requests
        this.setupAxiosInterceptor()

        console.log(`✅ Logged in as ${response.user.username} (${response.user.role})`)
        return true
      } catch (error: any) {
        console.error('Login failed:', error)
        this.authError = error.response?.data?.detail || 'Login failed. Please check your credentials.'
        this.clearAuth()
        return false
      } finally {
        this.isAuthenticating = false
      }
    },

    /**
     * Logout and clear authentication state
     */
    logout() {
      this.clearAuth()
      console.log('✅ Logged out')
    },

    /**
     * Fetch current user info from token
     */
    async fetchMe(): Promise<boolean> {
      if (!this.token) {
        return false
      }

      try {
        this.user = await authApi.getMe()
        return true
      } catch (error) {
        console.error('Failed to fetch user info:', error)
        this.clearAuth()
        return false
      }
    },

    /**
     * Initialize auth state on app startup
     */
    async initializeAuth(): Promise<boolean> {
      if (!this.token) {
        return false
      }

      // Setup axios interceptor first
      this.setupAxiosInterceptor()

      // Verify token is still valid by fetching user info
      return await this.fetchMe()
    },

    /**
     * Clear authentication state
     */
    clearAuth() {
      this.user = null
      this.token = null
      this.authError = null
      localStorage.removeItem(TOKEN_STORAGE_KEY)

      // Remove axios Authorization header
      delete axios.defaults.headers.common['Authorization']
    },

    /**
     * Setup axios interceptor to inject JWT token
     */
    setupAxiosInterceptor() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      }

      // Add response interceptor to handle 401 errors
      axios.interceptors.response.use(
        (response) => response,
        (error) => {
          if (error.response?.status === 401) {
            console.warn('401 Unauthorized - clearing auth state')
            this.clearAuth()
            // Redirect to login will be handled by router guard
          }
          return Promise.reject(error)
        }
      )
    }
  }
})

/**
 * Authentication API Client
 * Handles login, registration, and user info endpoints
 */
import axios from 'axios'

const API_BASE = '/api/auth'

export interface UserRole {
  OFFICER: 'OFFICER'
  BIDDER: 'BIDDER'
}

export interface User {
  id: number
  username: string
  role: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  role: 'OFFICER' | 'BIDDER'
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export const authApi = {
  /**
   * Login with username and password
   */
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await axios.post<TokenResponse>(`${API_BASE}/login`, credentials)
    return response.data
  },

  /**
   * Register a new user
   */
  async register(userData: RegisterRequest): Promise<User> {
    const response = await axios.post<User>(`${API_BASE}/register`, userData)
    return response.data
  },

  /**
   * Get current authenticated user info
   * Requires Authorization header with JWT token
   */
  async getMe(): Promise<User> {
    const response = await axios.get<User>(`${API_BASE}/me`)
    return response.data
  }
}

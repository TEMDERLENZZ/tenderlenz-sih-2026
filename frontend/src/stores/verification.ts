import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = '/api/verification'

export const useVerificationStore = defineStore('verification', {
  state: () => ({
    currentSession: null,
    verificationResults: [],
    providersStatus: null,
    loading: false,
    error: null
  }),

  actions: {
    async runVerification(bidderId: string) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post(`${API_BASE}/run/${bidderId}`)
        this.currentSession = response.data.summary

        // Fetch detailed results
        await this.fetchSessionResults(response.data.session_id)

        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Verification failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchSessionResults(sessionId: number) {
      try {
        const response = await axios.get(`${API_BASE}/session/${sessionId}/results`)
        this.verificationResults = response.data.results
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch results'
        throw err
      }
    },

    async fetchLatestSession(bidderId: string) {
      try {
        const response = await axios.get(`${API_BASE}/bidder/${bidderId}/latest`)
        this.currentSession = response.data

        // Fetch detailed results
        await this.fetchSessionResults(response.data.id)

        return response.data
      } catch (err: any) {
        if (err.response?.status === 404) {
          this.currentSession = null
          this.verificationResults = []
          return null
        }
        this.error = err.response?.data?.detail || 'Failed to fetch session'
        throw err
      }
    },

    async fetchProvidersStatus() {
      try {
        const response = await axios.get(`${API_BASE}/providers/status`)
        this.providersStatus = response.data
        return response.data
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to fetch providers status'
        throw err
      }
    },

    getResultsByCategory(category: string) {
      return this.verificationResults.filter(r => r.category === category)
    },

    getResultsByStatus(status: string) {
      return this.verificationResults.filter(r => r.status === status)
    },

    clearVerificationData() {
      this.currentSession = null
      this.verificationResults = []
      this.error = null
    }
  },

  getters: {
    hasVerificationData: (state) => state.currentSession !== null,

    verificationSummary: (state) => {
      if (!state.currentSession) return null

      return {
        total: state.currentSession.total_checks,
        verified: state.currentSession.verified_count,
        mismatch: state.currentSession.mismatch_count,
        missing: state.currentSession.missing_count,
        notApplicable: state.currentSession.not_applicable_count,
        sourceUnavailable: state.currentSession.source_unavailable_count
      }
    },

    isSandboxMode: (state) => {
      return state.providersStatus?.sandbox_mode_active || false
    },

    sandboxWarning: (state) => {
      return state.providersStatus?.warning || ''
    }
  }
})

import axios from 'axios'

const SANDBOX_BASE_URL = 'http://localhost:8001'

const sandboxClient = axios.create({
  baseURL: SANDBOX_BASE_URL,
  timeout: 4000
})

export interface SandboxProviderInfo {
  provider_name: string
  environment: string
  disclaimer: string
  supported_verifications: string[]
}

export const sandboxApi = {
  async checkConnection(): Promise<{ connected: boolean; message: string }> {
    try {
      const res = await sandboxClient.get('/api/health')
      if (res.data && res.data.status === 'healthy') {
        return { connected: true, message: 'TenderVerify Sandbox Online' }
      }
      return { connected: false, message: 'Sandbox Health Check Failed' }
    } catch (e: any) {
      return { connected: false, message: 'TenderVerify Sandbox Unreachable (Offline)' }
    }
  },

  async getProviderInfo(): Promise<SandboxProviderInfo | null> {
    try {
      const res = await sandboxClient.get('/api/provider-info')
      return res.data
    } catch (e) {
      return null
    }
  },

  async fetchGstDetails(gstin: string) {
    try {
      const res = await sandboxClient.get(`/api/gst/${gstin}`)
      return { success: true, data: res.data }
    } catch (e: any) {
      return { success: false, error: e.message || 'GST Sandbox lookup failed' }
    }
  },

  async fetchPanDetails(pan: string) {
    try {
      const res = await sandboxClient.get(`/api/pan/${pan}`)
      return { success: true, data: res.data }
    } catch (e: any) {
      return { success: false, error: e.message || 'PAN Sandbox lookup failed' }
    }
  },

  async fetchUdyamDetails(udyam: string) {
    try {
      const res = await sandboxClient.get(`/api/udyam/${udyam}`)
      return { success: true, data: res.data }
    } catch (e: any) {
      return { success: false, error: e.message || 'Udyam Sandbox lookup failed' }
    }
  },

  async fetchMcaDetails(cin: string) {
    try {
      const res = await sandboxClient.get(`/api/mca/${cin}`)
      return { success: true, data: res.data }
    } catch (e: any) {
      return { success: false, error: e.message || 'MCA Sandbox lookup failed' }
    }
  }
}

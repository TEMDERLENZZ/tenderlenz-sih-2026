import axios from 'axios'

const API_BASE = '/api/verification'

export interface VerificationResultItem {
  id: number
  session_id: number
  bidder_id: string
  check_id: string
  category: 'IDENTITY' | 'REGISTRATION' | 'FINANCIAL' | 'COMPLIANCE' | 'CROSS_CHECK' | 'EXTERNAL'
  requirement: string
  document_source_a?: string
  document_source_b?: string
  extracted_value_a?: any
  extracted_value_b?: any
  verified_value?: any
  verification_source: string
  source_mode: 'LIVE' | 'SANDBOX' | 'DEMO' | 'UNAVAILABLE'
  status: 'VERIFIED' | 'MISMATCH' | 'NOT_VERIFIED' | 'MISSING' | 'NOT_APPLICABLE' | 'SOURCE_UNAVAILABLE'
  confidence?: number
  explanation: string
  evidence?: Record<string, any>
  timestamp?: string
}

export interface VerificationSessionSummary {
  id: number
  bidder_id: string
  session_type: string
  status: string
  total_checks: number
  verified_count: number
  mismatch_count: number
  missing_count: number
  not_applicable_count: number
  source_unavailable_count: number
  started_at: string
  completed_at?: string
}

export interface ProviderStatus {
  name: string
  code: string
  mode: string
  is_active: boolean
  description: string
}

export interface ProvidersStatusResponse {
  providers: ProviderStatus[]
  sandbox_mode_active: boolean
  warning: string
}

export const verificationApi = {
  async runVerification(bidderId: string, sessionType = 'FULL_VERIFICATION') {
    const res = await axios.post(`${API_BASE}/run/${bidderId}?session_type=${sessionType}`)
    return res.data
  },

  async getSessionSummary(sessionId: number): Promise<VerificationSessionSummary> {
    const res = await axios.get(`${API_BASE}/session/${sessionId}`)
    return res.data
  },

  async getSessionResults(sessionId: number) {
    const res = await axios.get(`${API_BASE}/session/${sessionId}/results`)
    return res.data
  },

  async getLatestSession(bidderId: string): Promise<VerificationSessionSummary | null> {
    try {
      const res = await axios.get(`${API_BASE}/bidder/${bidderId}/latest`)
      return res.data
    } catch (e: any) {
      if (e.response?.status === 404) return null
      throw e
    }
  },

  async getProvidersStatus(): Promise<ProvidersStatusResponse> {
    const res = await axios.get(`${API_BASE}/providers/status`)
    return res.data
  }
}

import axios from 'axios'

const API_BASE = '/api/tenders'

export interface OfficerDecisionCreate {
  decision: 'PENDING' | 'APPROVED' | 'REJECTED' | 'REQUIRES_REVIEW'
  officer_id: string
  officer_name?: string
  remarks?: string
}

export interface OfficerDecisionResponse {
  id: number
  tender_id: string
  bidder_id: string
  decision: string
  officer_id: string
  officer_name?: string
  remarks?: string
  decided_at: string
}

export interface AuditLogEntry {
  id: number
  event_type: string
  tender_id?: string
  bidder_id?: string
  user_id?: string
  user_name?: string
  action_description: string
  metadata?: string
  timestamp: string
}

export const decisionApi = {
  async recordDecision(
    tenderId: string,
    bidderId: string,
    decisionData: OfficerDecisionCreate
  ): Promise<OfficerDecisionResponse> {
    const res = await axios.post(
      `${API_BASE}/${tenderId}/bidders/${bidderId}/decision`,
      decisionData
    )
    return res.data
  },

  async getDecision(
    tenderId: string,
    bidderId: string
  ): Promise<OfficerDecisionResponse | null> {
    try {
      const res = await axios.get(
        `${API_BASE}/${tenderId}/bidders/${bidderId}/decision`
      )
      return res.data
    } catch (e: any) {
      if (e.response?.status === 404) {
        return null
      }
      throw e
    }
  },

  async getAuditLogs(
    tenderId?: string,
    bidderId?: string,
    eventType?: string,
    limit: number = 100
  ): Promise<AuditLogEntry[]> {
    const params = new URLSearchParams()
    if (tenderId) params.append('tender_id', tenderId)
    if (bidderId) params.append('bidder_id', bidderId)
    if (eventType) params.append('event_type', eventType)
    params.append('limit', limit.toString())

    const res = await axios.get(`${API_BASE}/audit-logs?${params.toString()}`)
    return res.data
  }
}

import axios from 'axios'

const API_BASE = '/api/tenders'

export interface RiskFactor {
  type: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH'
  requirement?: string
  check?: string
  category?: string
  description: string
  source: string
  points: number
}

export interface BidderRiskAssessment {
  id: number
  tender_id: string
  bidder_id: string
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  risk_score: number
  factors: RiskFactor[]
  summary: string
  calculated_at: string
}

export const riskApi = {
  async assessRisk(tenderId: string, bidderId: string): Promise<BidderRiskAssessment> {
    const res = await axios.post(`${API_BASE}/${tenderId}/bidders/${bidderId}/assess-risk`)
    return res.data
  },

  async getRisk(tenderId: string, bidderId: string): Promise<BidderRiskAssessment> {
    const res = await axios.get(`${API_BASE}/${tenderId}/bidders/${bidderId}/risk`)
    return res.data
  }
}

import axios from 'axios'

const API_BASE = '/api/tenders'

export interface TenderRequirement {
  id: number
  tender_id: str
  requirement_code: string
  category: string
  title: string
  description?: string
  requirement_type: string
  mandatory: boolean
  operator?: string
  required_value?: any
  unit?: string
  source_document?: string
  source_page?: number
  evidence_text?: string
  extraction_confidence?: number
  created_at?: string
}

export interface TenderComplianceResult {
  id: number
  tender_id: string
  bidder_id: string
  requirement_id?: number
  requirement_code: string
  result: 'SATISFIED' | 'NOT_SATISFIED' | 'MISSING' | 'REVIEW_REQUIRED' | 'NOT_APPLICABLE' | 'UNABLE_TO_VERIFY'
  required_value?: any
  actual_value?: any
  confidence?: number
  explanation: string
  evidence?: Record<string, any>
  created_at?: string
}

export interface TenderComplianceSummary {
  tender_id: string
  bidder_id: string
  total_requirements: number
  satisfied: number
  not_satisfied: number
  missing: number
  review_required: number
  unable_to_verify: number
  not_applicable: number
  compliance_percentage: number
  disclaimer: string
  results: TenderComplianceResult[]
}

export const tenderApi = {
  async listTenders() {
    const res = await axios.get(`${API_BASE}/list`)
    return res.data
  },

  async seedDemoTender() {
    const res = await axios.post(`${API_BASE}/seed-demo`)
    return res.data
  },

  async uploadTender(file: File, title?: string) {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)

    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data
  },

  async extractRequirements(tenderId: string) {
    const res = await axios.post(`${API_BASE}/${tenderId}/extract-requirements`)
    return res.data
  },

  async getRequirements(tenderId: string): Promise<TenderRequirement[]> {
    const res = await axios.get(`${API_BASE}/${tenderId}/requirements`)
    return res.data
  },

  async updateRequirement(requirementId: number, data: Partial<TenderRequirement>) {
    const res = await axios.put(`${API_BASE}/requirements/${requirementId}`, data)
    return res.data
  },

  async addCustomRequirement(tenderId: string, data: Partial<TenderRequirement>) {
    const res = await axios.post(`${API_BASE}/${tenderId}/requirements`, data)
    return res.data
  },

  async deleteRequirement(requirementId: number) {
    const res = await axios.delete(`${API_BASE}/requirements/${requirementId}`)
    return res.data
  },

  async evaluateBidder(tenderId: string, bidderId: string): Promise<TenderComplianceSummary> {
    const res = await axios.post(`${API_BASE}/${tenderId}/bidders/${bidderId}/evaluate`)
    return res.data
  },

  async getComplianceSummary(tenderId: string, bidderId: string): Promise<TenderComplianceSummary> {
    const res = await axios.get(`${API_BASE}/${tenderId}/bidders/${bidderId}/compliance`)
    return res.data
  }
}

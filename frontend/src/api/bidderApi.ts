import axios from 'axios'

const API_BASE = '/api/documents'

export interface BidderDocument {
  id: number
  bidder_id: string
  document_type: string
  file_name: string
  file_path: string
  file_size?: number
  mime_type?: string
  status: 'UPLOADED' | 'PROCESSING' | 'EXTRACTED' | 'PARTIALLY_EXTRACTED' | 'EXTRACTION_FAILED' | 'FAILED'
  extracted_data?: Record<string, any>
  extraction_confidence?: number
  raw_text?: string
  extraction_trace?: any[]
  uploaded_at?: string
  error_message?: string
}

export interface BidderSummary {
  bidder_id: string
  total_documents: number
  uploaded_document_types: string[]
  missing_document_types: string[]
  document_counts: Record<string, number>
  completion_percentage: number
}

export const bidderApi = {
  async getBidderDocuments(bidderId: string): Promise<BidderDocument[]> {
    const res = await axios.get(`${API_BASE}/bidder/${bidderId}`)
    return res.data
  },

  async getBidderSummary(bidderId: string): Promise<BidderSummary> {
    const res = await axios.get(`${API_BASE}/bidder/${bidderId}/summary`)
    return res.data
  },

  async uploadSingleDocument(bidderId: string, documentType: string, file: File) {
    const formData = new FormData()
    formData.append('bidder_id', bidderId)
    formData.append('document_type', documentType)
    formData.append('file', file)

    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data
  },

  async uploadBatchDocuments(bidderId: string, files: File[]) {
    const formData = new FormData()
    formData.append('bidder_id', bidderId)
    files.forEach((file) => formData.append('files', file))

    const res = await axios.post(`${API_BASE}/upload-batch`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return res.data
  },

  async reprocessDocument(documentId: number) {
    const res = await axios.post(`${API_BASE}/reprocess/${documentId}`)
    return res.data
  },

  async clearBidderDocuments(bidderId: string) {
    const res = await axios.delete(`${API_BASE}/bidder/${bidderId}/clear`)
    return res.data
  },

  async clearAllDocuments() {
    const res = await axios.delete(`${API_BASE}/clear-all`)
    return res.data
  }
}

<template>
  <div class="dashboard">
    <!-- Bidder ID Input & Action Buttons -->
    <div class="bidder-section">
      <div class="bidder-input-group">
        <label for="bidder-id">Bidder ID:</label>
        <input
          id="bidder-id"
          v-model="bidderId"
          type="text"
          placeholder="Enter Bidder ID (e.g., BIDDER_001)"
          @change="loadBidderDocuments"
        />
        <button @click="loadBidderDocuments" class="btn-primary">Load Documents</button>
      </div>

      <div class="action-buttons-group">
        <button @click="clearBidderData" :disabled="clearing" class="btn-warning">
          🧹 Clear Current Bidder Data
        </button>
        <button @click="clearAllData" :disabled="clearing" class="btn-danger">
          🗑️ Clear All Old Data
        </button>
      </div>
    </div>

    <!-- Overall Summary Card -->
    <div v-if="summary" class="summary-card">
      <h2>📊 Document Completion Status</h2>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: summary.completion_percentage + '%' }"></div>
        <span class="progress-text">{{ Math.round(summary.completion_percentage) }}%</span>
      </div>
      <p>{{ summary.uploaded_document_types.length }} of 14 documents uploaded</p>

      <!-- Phase 2: Run Verification Button -->
      <div v-if="summary.uploaded_document_types.length > 0" class="verification-section">
        <button @click="runVerification" class="btn-verification" :disabled="runningVerification">
          {{ runningVerification ? '⏳ Running Verification...' : '🔍 Run Phase 2 Verification' }}
        </button>
        <p class="verification-hint">Sandbox Demonstration — External verification uses demonstration data, not live government sources.</p>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- NEW: ONE-CLICK 14-DOCUMENT BATCH UPLOAD HERO SECTION -->
    <!-- ============================================================ -->
    <div class="batch-hero-card">
      <div class="batch-hero-header">
        <div class="batch-hero-title">
          <div class="hero-badge">PHASE 1 FAST-TRACK</div>
          <h2>📁 One-Click 14-Document Batch Upload</h2>
          <p class="batch-hero-subtitle">
            Upload all 14 bidder documents in ONE action. Automatic content classification, duplicate detection, and structured field extraction.
          </p>
        </div>
        <div class="batch-hero-action">
          <input
            type="file"
            ref="batchFileInput"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            @change="handleBatchFileSelect"
            class="hidden-file-input"
          />
          <button @click="triggerBatchSelect" :disabled="batchUploading" class="btn-hero-batch">
            <span class="btn-icon">📁</span>
            <span>{{ batchUploading ? 'Processing Batch...' : 'Upload All 14 Documents' }}</span>
          </button>
        </div>
      </div>

      <!-- Error / Alert Banner -->
      <div v-if="batchErrorMessage" class="batch-error-banner">
        ⚠️ {{ batchErrorMessage }}
      </div>

      <!-- Batch Progress & Live Queue Panel -->
      <div v-if="batchUploading || batchSummary || batchQueue.length > 0" class="batch-results-panel">
        <div class="batch-progress-bar-container">
          <div class="progress-info-row">
            <span class="progress-title">Upload Progress</span>
            <span class="progress-count-text">
              <strong>{{ batchSummary ? batchSummary.processed : batchQueue.length }}/14</strong> documents received
            </span>
          </div>
          <div class="batch-progress-track">
            <div
              class="batch-progress-bar-fill"
              :style="{ width: Math.min(((batchSummary ? batchSummary.processed : batchQueue.length) / 14) * 100, 100) + '%' }"
            ></div>
          </div>
        </div>

        <!-- Summary Statistics Chips -->
        <div v-if="batchSummary" class="batch-stats-grid">
          <div class="stat-card stat-total">
            <div class="stat-num">{{ batchSummary.total_files }}</div>
            <div class="stat-label">Received</div>
          </div>
          <div class="stat-card stat-success">
            <div class="stat-num">{{ batchSummary.successful }}</div>
            <div class="stat-label">Extracted</div>
          </div>
          <div class="stat-card stat-partial" v-if="batchSummary.partially_extracted">
            <div class="stat-num">{{ batchSummary.partially_extracted }}</div>
            <div class="stat-label">Partially Extracted</div>
          </div>
          <div class="stat-card stat-review" v-if="batchSummary.needs_review">
            <div class="stat-num">{{ batchSummary.needs_review }}</div>
            <div class="stat-label">Needs Review</div>
          </div>
          <div class="stat-card stat-duplicate" v-if="batchSummary.duplicates">
            <div class="stat-num">{{ batchSummary.duplicates }}</div>
            <div class="stat-label">Duplicates</div>
          </div>
          <div class="stat-card stat-failed" v-if="batchSummary.failed">
            <div class="stat-num">{{ batchSummary.failed }}</div>
            <div class="stat-label">Failed</div>
          </div>
        </div>

        <!-- 14-Document Queue Table -->
        <div v-if="batchQueue.length > 0" class="queue-table-wrapper">
          <h3 class="queue-title">📋 Document Upload Queue ({{ batchQueue.length }} files)</h3>
          <table class="queue-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Expected Document</th>
                <th>Filename</th>
                <th>Detected Type</th>
                <th>Status</th>
                <th>Confidence & Diagnostic Message</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, idx) in batchQueue"
                :key="idx"
                :class="getRowClass(item)"
              >
                <td class="idx-col">{{ idx + 1 }}</td>
                <td class="expected-col">
                  <strong>{{ getExpectedLabel(item) }}</strong>
                </td>
                <td class="filename-col">
                  <span class="file-icon">📄</span> {{ item.file_name }}
                </td>
                <td class="detected-col">
                  <span v-if="item.detected_type" class="type-badge">
                    {{ formatDocumentType(item.detected_type) }}
                  </span>
                  <span v-else class="text-muted">Analyzing content...</span>
                </td>
                <td class="status-col">
                  <span :class="'pill pill-' + getStatusPillClass(item.status)">
                    {{ formatStatusLabel(item.status) }}
                  </span>
                </td>
                <td class="message-col">
                  <div v-if="item.classification_mismatch" class="mismatch-box">
                    <strong>⚠️ Classification Mismatch</strong>
                    <div>Expected: {{ formatDocumentType(item.expected_type) }}</div>
                    <div>Detected: {{ formatDocumentType(item.detected_type) }}</div>
                    <div>Confidence: {{ Math.round((item.classification_confidence || 0) * 100) }}%</div>
                  </div>
                  <div v-else-if="item.message" class="message-text">
                    {{ item.message }}
                  </div>
                  <div v-else-if="item.extraction_confidence !== null && item.extraction_confidence !== undefined">
                    Confidence: {{ Math.round(item.extraction_confidence * 100) }}%
                  </div>
                  <div v-else class="text-muted">Extracted successfully</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Post Batch Verification Button -->
        <div v-if="batchSummary" class="batch-verification-cta">
          <button @click="runVerification" class="btn-verification-lg">
            🔍 Run Phase 2 Verification
          </button>
          <p class="cta-hint">All selected Phase 1 documents processed! Click above to execute Phase 2 cross-checks & sandbox verification.</p>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- EXISTING SINGLE DOCUMENT UPLOAD SECTION (PRESERVED) -->
    <!-- ============================================================ -->
    <div class="upload-section">
      <h2>📤 Individual Document Upload</h2>
      <p class="section-hint">Need to upload or re-upload a single document? Select document type and file below.</p>

      <div class="upload-form">
        <select v-model="selectedDocumentType" class="document-select">
          <option value="">Select Document Type</option>
          <option v-for="docType in documentTypes" :key="docType.value" :value="docType.value">
            {{ docType.label }}
          </option>
        </select>

        <input
          type="file"
          ref="fileInput"
          accept=".pdf,.jpg,.jpeg,.png"
          @change="handleFileSelect"
          class="file-input"
        />

        <button
          @click="uploadDocument"
          :disabled="!selectedDocumentType || !selectedFile || uploading"
          class="btn-upload"
        >
          {{ uploading ? 'Uploading...' : 'Upload & Extract' }}
        </button>
      </div>

      <!-- Duplicate Detection Warning Banner -->
      <div v-if="duplicateInfo" class="duplicate-banner">
        <h3>⚠️ Duplicate Document Detected</h3>
        <p>{{ duplicateInfo.message }}</p>
        <p class="duplicate-details">
          <strong>Existing File:</strong> {{ duplicateInfo.existing_file_name }} (Type: {{ duplicateInfo.existing_document_type }}, Status: {{ duplicateInfo.existing_status }})
        </p>
        <div class="duplicate-actions">
          <button @click="reprocessDocument(duplicateInfo.existing_document_id)" :disabled="reprocessing" class="btn-reprocess">
            🔄 {{ reprocessing ? 'Reprocessing...' : 'Force Re-extract Existing File' }}
          </button>
          <button @click="duplicateInfo = null" class="btn-dismiss">Dismiss</button>
        </div>
      </div>

      <p v-if="uploadMessage" :class="uploadMessageClass">{{ uploadMessage }}</p>
    </div>

    <!-- Documents Grid -->
    <div v-if="documents.length > 0" class="documents-grid">
      <h2>📄 Extracted Documents</h2>

      <div v-for="doc in documents" :key="doc.id" class="document-card">
        <div class="document-header">
          <div class="doc-header-left">
            <h3>{{ formatDocumentType(doc.document_type) }}</h3>
            <span class="file-name-label">📁 {{ doc.file_name }}</span>
          </div>
          <div class="doc-header-right">
            <button @click="reprocessDocument(doc.id)" class="btn-reprocess-sm" title="Re-extract data">
              🔄 Re-extract
            </button>
            <span :class="'status-badge status-' + doc.status.toLowerCase()">
              {{ doc.status }}
            </span>
          </div>
        </div>

        <div class="document-content">
          <DocumentDisplay :document="doc" />
        </div>
      </div>
    </div>

    <!-- Missing Documents -->
    <div v-if="summary && summary.missing_document_types.length > 0" class="missing-section">
      <h3>⚠️ Missing Documents</h3>
      <ul>
        <li v-for="docType in summary.missing_document_types" :key="docType">
          {{ formatDocumentType(docType) }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import DocumentDisplay from '../components/DocumentDisplay.vue'
import { useBidderStore } from '../stores/bidder'

const router = useRouter()
const bidderStore = useBidderStore()

// Keep a local ref that mirrors the store — users can still type a one-off ID in the input
const bidderId = ref(bidderStore.currentBidderId)
const selectedDocumentType = ref('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

// Single upload states
const uploading = ref(false)
const clearing = ref(false)
const reprocessing = ref(false)
const runningVerification = ref(false)
const uploadMessage = ref('')
const uploadMessageClass = ref('')
const duplicateInfo = ref<any>(null)

// Batch upload states
const batchFileInput = ref<HTMLInputElement | null>(null)
const batchUploading = ref(false)
const batchProgressCount = ref(0)
const batchQueue = ref<any[]>([])
const batchSummary = ref<any>(null)
const batchErrorMessage = ref('')

const documents = ref<any[]>([])
const summary = ref<any>(null)

const documentTypes = [
  { value: 'GST_CERTIFICATE', label: '1. GST Certificate' },
  { value: 'FINANCIAL_TURNOVER_CERTIFICATE', label: '2. Financial Turnover Certificate' },
  { value: 'OEM_AUTHORIZATION', label: '3. OEM Authorization' },
  { value: 'PAN_CARD', label: '4. PAN Card' },
  { value: 'UDYAM_CERTIFICATE', label: '5. Udyam / MSME Certificate' },
  { value: 'COMPANY_INCORPORATION', label: '6. Company Incorporation / MCA' },
  { value: 'LOCAL_CONTENT_DECLARATION', label: '7. Local Content Declaration' },
  { value: 'EPFO_REGISTRATION', label: '8. EPFO Registration' },
  { value: 'ESIC_REGISTRATION', label: '9. ESIC Registration' },
  { value: 'BIS_CERTIFICATE', label: '10. BIS Certificate' },
  { value: 'STARTUP_CERTIFICATE', label: '11. Startup Certificate' },
  { value: 'NSIC_CERTIFICATE', label: '12. NSIC Certificate' },
  { value: 'NON_BLACKLISTING_DECLARATION', label: '13. Non-Blacklisting Declaration' },
  { value: 'INCOME_TAX_RETURN', label: '14. Income Tax Return' }
]

// Single file select handler
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

// Single file upload handler
const uploadDocument = async () => {
  if (!selectedFile.value || !selectedDocumentType.value) return

  uploading.value = true
  uploadMessage.value = ''
  duplicateInfo.value = null

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('bidder_id', bidderId.value)
  formData.append('document_type', selectedDocumentType.value)

  try {
    await axios.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    uploadMessage.value = '✓ Document uploaded and extracted successfully!'
    uploadMessageClass.value = 'success-message'

    // Reset form
    selectedFile.value = null
    selectedDocumentType.value = ''
    if (fileInput.value) fileInput.value.value = ''

    // Reload documents
    await loadBidderDocuments()
  } catch (error: any) {
    if (error.response?.status === 409) {
      // Duplicate file detected
      duplicateInfo.value = error.response.data.detail
      uploadMessage.value = '⚠️ Duplicate upload blocked. Same file hash already exists.'
      uploadMessageClass.value = 'warning-message'
    } else {
      uploadMessage.value = '✗ Upload failed: ' + (error.response?.data?.detail || error.message)
      uploadMessageClass.value = 'error-message'
    }
  } finally {
    uploading.value = false
  }
}

// One-Click 14-Document Batch Upload Handlers
const triggerBatchSelect = () => {
  if (batchFileInput.value) {
    batchFileInput.value.click()
  }
}

const handleBatchFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const selectedFiles = Array.from(target.files)
  batchErrorMessage.value = ''
  batchSummary.value = null
  batchQueue.value = []

  if (selectedFiles.length > 14) {
    batchErrorMessage.value = `Maximum 14 files allowed per upload action. You selected ${selectedFiles.length} files. Please select up to 14 files.`
    if (batchFileInput.value) batchFileInput.value.value = ''
    return
  }

  batchUploading.value = true

  // Initial queue state
  batchQueue.value = selectedFiles.map(file => ({
    file_name: file.name,
    expected_type: detectExpectedTypeFromFilename(file.name),
    detected_type: null,
    status: 'PROCESSING',
    extraction_confidence: null,
    message: 'Uploading and extracting...'
  }))

  const formData = new FormData()
  formData.append('bidder_id', bidderId.value)
  selectedFiles.forEach(file => {
    formData.append('files', file)
  })

  try {
    const res = await axios.post('/api/documents/upload-batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    batchSummary.value = res.data
    batchQueue.value = res.data.documents

    await loadBidderDocuments()
  } catch (error: any) {
    if (error.response?.data?.detail) {
      batchErrorMessage.value = typeof error.response.data.detail === 'string'
        ? error.response.data.detail
        : JSON.stringify(error.response.data.detail)
    } else {
      batchErrorMessage.value = 'Batch upload failed: ' + error.message
    }
  } finally {
    batchUploading.value = false
    if (batchFileInput.value) batchFileInput.value.value = ''
  }
}

const detectExpectedTypeFromFilename = (filename: string) => {
  const fn = filename.toLowerCase()
  if (fn.includes('gst')) return 'GST_CERTIFICATE'
  if (fn.includes('turnover') || fn.includes('financial')) return 'FINANCIAL_TURNOVER_CERTIFICATE'
  if (fn.includes('oem')) return 'OEM_AUTHORIZATION'
  if (fn.includes('pan')) return 'PAN_CARD'
  if (fn.includes('udyam') || fn.includes('msme')) return 'UDYAM_CERTIFICATE'
  if (fn.includes('incorporation') || fn.includes('mca')) return 'COMPANY_INCORPORATION'
  if (fn.includes('local')) return 'LOCAL_CONTENT_DECLARATION'
  if (fn.includes('epfo')) return 'EPFO_REGISTRATION'
  if (fn.includes('esic')) return 'ESIC_REGISTRATION'
  if (fn.includes('bis')) return 'BIS_CERTIFICATE'
  if (fn.includes('startup')) return 'STARTUP_CERTIFICATE'
  if (fn.includes('nsic')) return 'NSIC_CERTIFICATE'
  if (fn.includes('blacklisting')) return 'NON_BLACKLISTING_DECLARATION'
  if (fn.includes('itr') || fn.includes('income_tax')) return 'INCOME_TAX_RETURN'
  return null
}

const getExpectedLabel = (item: any) => {
  if (item.expected_type) {
    return formatDocumentType(item.expected_type)
  }
  if (item.document_type) {
    return formatDocumentType(item.document_type)
  }
  return 'Document'
}

const formatStatusLabel = (status: string) => {
  switch (status) {
    case 'EXTRACTED': return 'Extracted'
    case 'PARTIALLY_EXTRACTED': return 'Partially Extracted'
    case 'NEEDS_REVIEW': return 'Needs Review'
    case 'CLASSIFICATION_UNCERTAIN': return 'Uncertain'
    case 'DUPLICATE': return 'Duplicate'
    case 'FAILED': return 'Failed'
    case 'PROCESSING': return 'Processing'
    default: return status
  }
}

const getStatusPillClass = (status: string) => {
  switch (status) {
    case 'EXTRACTED': return 'success'
    case 'PARTIALLY_EXTRACTED': return 'warning'
    case 'NEEDS_REVIEW': return 'danger'
    case 'CLASSIFICATION_UNCERTAIN': return 'warning'
    case 'DUPLICATE': return 'info'
    case 'FAILED': return 'danger'
    default: return 'processing'
  }
}

const getRowClass = (item: any) => {
  if (item.status === 'NEEDS_REVIEW' || item.classification_mismatch) return 'row-needs-review'
  if (item.status === 'DUPLICATE') return 'row-duplicate'
  if (item.status === 'FAILED') return 'row-failed'
  return ''
}

const reprocessDocument = async (documentId: number) => {
  reprocessing.value = true
  uploadMessage.value = ''

  try {
    await axios.post(`/api/documents/reprocess/${documentId}`)
    uploadMessage.value = '✓ Document re-extracted successfully!'
    uploadMessageClass.value = 'success-message'
    duplicateInfo.value = null
    await loadBidderDocuments()
  } catch (error: any) {
    uploadMessage.value = '✗ Reprocessing failed: ' + (error.response?.data?.detail || error.message)
    uploadMessageClass.value = 'error-message'
  } finally {
    reprocessing.value = false
  }
}

const loadBidderDocuments = async () => {
  if (!bidderId.value) return

  try {
    const docsResponse = await axios.get(`/api/documents/bidder/${bidderId.value}`)
    documents.value = docsResponse.data

    const summaryResponse = await axios.get(`/api/documents/bidder/${bidderId.value}/summary`)
    summary.value = summaryResponse.data
  } catch (error) {
    console.error('Error loading documents:', error)
  }
}

const clearBidderData = async () => {
  if (!bidderId.value) return
  if (!confirm(`Are you sure you want to clear all data for bidder "${bidderId.value}"?`)) return

  clearing.value = true
  try {
    await axios.delete(`/api/documents/bidder/${bidderId.value}/clear`)
    uploadMessage.value = `✓ Cleared data for ${bidderId.value}`
    uploadMessageClass.value = 'success-message'
    batchSummary.value = null
    batchQueue.value = []
    await loadBidderDocuments()
  } catch (error: any) {
    uploadMessage.value = '✗ Failed to clear bidder data: ' + (error.response?.data?.detail || error.message)
    uploadMessageClass.value = 'error-message'
  } finally {
    clearing.value = false
  }
}

const clearAllData = async () => {
  if (!confirm('Are you sure you want to clear ALL document data for all bidders?')) return

  clearing.value = true
  try {
    await axios.delete('/api/documents/clear-all')
    uploadMessage.value = '✓ All document data cleared successfully'
    uploadMessageClass.value = 'success-message'
    batchSummary.value = null
    batchQueue.value = []
    await loadBidderDocuments()
  } catch (error: any) {
    uploadMessage.value = '✗ Failed to clear all data: ' + (error.response?.data?.detail || error.message)
    uploadMessageClass.value = 'error-message'
  } finally {
    clearing.value = false
  }
}

const formatDocumentType = (type?: string) => {
  if (!type) return 'Unknown'
  return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const runVerification = async () => {
  runningVerification.value = true
  try {
    router.push(`/verification/${bidderId.value}?run=true`)
  } finally {
    runningVerification.value = false
  }
}

onMounted(() => {
  loadBidderDocuments()
})

// Sync bidderId input when the global store switches bidder
watch(() => bidderStore.currentBidderId, (newId) => {
  bidderId.value = newId
  loadBidderDocuments()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.bidder-section {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.bidder-input-group {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex: 1;
  min-width: 300px;
}

.bidder-section label {
  font-weight: 600;
  color: #1e293b;
}

.bidder-section input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.bidder-section input:focus {
  border-color: #6366f1;
}

.action-buttons-group {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.summary-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.verification-section {
  margin-top: 25px;
  padding: 25px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border-radius: 12px;
  text-align: center;
}

.btn-verification, .btn-verification-lg {
  background: white;
  color: #4f46e5;
  padding: 15px 40px;
  font-size: 18px;
  font-weight: 700;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.4);
  transition: all 0.3s ease;
}

.btn-verification:hover:not(:disabled), .btn-verification-lg:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 30px -5px rgba(79, 70, 229, 0.5);
}

.verification-hint, .cta-hint {
  margin-top: 12px;
  color: rgba(255, 255, 255, 0.95);
  font-size: 14px;
  font-weight: 500;
}

.progress-bar {
  position: relative;
  width: 100%;
  height: 36px;
  background: #f1f5f9;
  border-radius: 18px;
  margin: 1rem 0;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
  transition: width 0.4s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: 700;
  color: #0f172a;
}

/* ============================================================ */
/* NEW BATCH HERO UPLOAD CARD STYLES */
/* ============================================================ */
.batch-hero-card {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  color: white;
  border-radius: 16px;
  padding: 2.25rem;
  margin-bottom: 2rem;
  box-shadow: 0 20px 25px -5px rgba(30, 27, 75, 0.25);
  position: relative;
  overflow: hidden;
}

.batch-hero-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.hero-badge {
  display: inline-block;
  background: rgba(129, 140, 248, 0.2);
  color: #a5b4fc;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  border: 1px solid rgba(165, 180, 252, 0.3);
  margin-bottom: 0.75rem;
}

.batch-hero-title h2 {
  font-size: 1.85rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  color: white;
}

.batch-hero-subtitle {
  color: #c7d2fe;
  font-size: 1.05rem;
  max-width: 650px;
  line-height: 1.5;
}

.hidden-file-input {
  display: none;
}

.btn-hero-batch {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  font-size: 1.15rem;
  font-weight: 700;
  padding: 1.15rem 2.25rem;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.5);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-hero-batch:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 15px 35px -5px rgba(99, 102, 241, 0.65);
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
}

.btn-hero-batch:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.batch-error-banner {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
  padding: 1rem 1.25rem;
  border-radius: 10px;
  margin-top: 1.5rem;
  font-weight: 600;
}

.batch-results-panel {
  margin-top: 2rem;
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 14px;
  padding: 1.75rem;
}

.batch-progress-bar-container {
  margin-bottom: 1.5rem;
}

.progress-info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.progress-title {
  color: #e0e7ff;
  font-weight: 600;
}

.progress-count-text {
  color: #818cf8;
}

.batch-progress-track {
  height: 12px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  overflow: hidden;
}

.batch-progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
  transition: width 0.4s ease;
}

.batch-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 1rem;
  margin-bottom: 1.75rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 10px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-num {
  font-size: 1.6rem;
  font-weight: 800;

}

.stat-label {
  font-size: 0.8rem;
  color: #cbd5e1;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.25rem;
}

.stat-total .stat-num { color: #38bdf8; }
.stat-success .stat-num { color: #4ade80; }
.stat-partial .stat-num { color: #fbbf24; }
.stat-review .stat-num { color: #f87171; }
.stat-duplicate .stat-num { color: #a78bfa; }
.stat-failed .stat-num { color: #f87171; }

.queue-table-wrapper {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  color: #0f172a;
}

.queue-title {
  padding: 1.25rem 1.5rem;
  font-size: 1.1rem;
  font-weight: 700;
  border-bottom: 1px solid #e2e8f0;
  margin: 0;
  background: #f8fafc;
}

.queue-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}

.queue-table th {
  background: #f1f5f9;
  padding: 0.9rem 1rem;
  text-align: left;
  font-weight: 700;
  color: #475569;
  border-bottom: 2px solid #e2e8f0;
}

.queue-table td {
  padding: 0.85rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.row-needs-review {
  background: #fff1f2 !important;
}

.row-duplicate {
  background: #f5f3ff !important;
}

.row-failed {
  background: #fef2f2 !important;
}

.idx-col {
  font-weight: 700;
  color: #64748b;
  width: 40px;
}

.expected-col {
  color: #1e293b;
  min-width: 180px;
}

.filename-col {
  font-family: monospace;
  color: #334155;
  word-break: break-all;
}

.type-badge {
  background: #e0e7ff;
  color: #3730a3;
  font-weight: 600;
  font-size: 0.8rem;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
}

.pill {
  display: inline-block;
  padding: 0.3rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.pill-success { background: #dcfce7; color: #166534; }
.pill-warning { background: #fef3c7; color: #92400e; }
.pill-danger { background: #fee2e2; color: #991b1b; }
.pill-info { background: #f3e8ff; color: #6b21a8; }
.pill-processing { background: #e0f2fe; color: #075985; }

.mismatch-box {
  background: #fecaca;
  border-left: 3px solid #dc2626;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  color: #7f1d1d;
  font-size: 0.85rem;
}

.batch-verification-cta {
  margin-top: 1.75rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  text-align: center;
  border: 1px dashed rgba(255, 255, 255, 0.25);
}

/* ============================================================ */
/* EXISTING UPLOAD & DISPLAY STYLES */
/* ============================================================ */
.upload-section {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.section-hint {
  color: #64748b;
  margin-top: 0.25rem;
  font-size: 0.9rem;
}

.upload-form {
  display: flex;
  gap: 1rem;
  margin: 1.25rem 0;
  flex-wrap: wrap;
}

.document-select, .file-input {
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
}

.document-select {
  flex: 1;
  min-width: 250px;
}

.btn-primary, .btn-upload {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.2s;
}

.btn-warning {
  padding: 0.75rem 1.25rem;
  background: #f59e0b;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  cursor: pointer;
  font-weight: 600;
}

.btn-danger {
  padding: 0.75rem 1.25rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  cursor: pointer;
  font-weight: 600;
}

.duplicate-banner {
  background: #fffbebf8;
  border: 2px solid #f59e0b;
  border-radius: 8px;
  padding: 1.25rem;
  margin: 1rem 0;
}

.duplicate-banner h3 {
  color: #b45309;
  margin-bottom: 0.5rem;
}

.duplicate-details {
  font-size: 0.9rem;
  color: #4b5563;
  margin: 0.5rem 0 1rem 0;
}

.duplicate-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-reprocess {
  padding: 0.5rem 1rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.btn-reprocess-sm {
  padding: 0.35rem 0.75rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  margin-right: 0.5rem;
}

.btn-dismiss {
  padding: 0.5rem 1rem;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.success-message { color: #16a34a; font-weight: 600; margin-top: 1rem; }
.warning-message { color: #d97706; font-weight: 600; margin-top: 1rem; }
.error-message { color: #dc2626; font-weight: 600; margin-top: 1rem; }

.documents-grid {
  margin: 2rem 0;
}

.document-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}

.document-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f1f5f9;
}

.doc-header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.doc-header-right {
  display: flex;
  align-items: center;
}

.file-name-label {
  font-size: 0.85rem;
  color: #64748b;
  background: #f1f5f9;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.status-badge {
  padding: 0.4rem 0.9rem;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 600;
}

.status-extracted { background: #dcfce7; color: #15803d; }
.status-partially_extracted { background: #fef3c7; color: #b45309; }
.status-failed { background: #fee2e2; color: #b91c1c; }

.missing-section {
  background: #fffbeb;
  padding: 1.5rem;
  border-radius: 12px;
  border-left: 5px solid #f59e0b;
}

.missing-section ul {
  margin-top: 1rem;
  padding-left: 1.5rem;
}

.missing-section li {
  margin: 0.5rem 0;
  color: #92400e;
  font-weight: 500;
}

.text-muted {
  color: #94a3b8;
  font-style: italic;
}
</style>

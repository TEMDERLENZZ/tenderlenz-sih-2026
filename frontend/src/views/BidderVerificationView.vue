<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Bidder Verification Profile</h1>
        <p class="page-subtitle">
          Bidder: <strong>{{ bidderStore.currentBidderName }}</strong> |
          ID: <code>{{ bidderStore.currentBidderId }}</code>
        </p>
      </div>

      <div class="header-actions">
        <button @click="router.push('/external-verification')" class="btn btn-primary">
          ⚡ Run External Verification
        </button>
        <button @click="router.push('/cross-checks')" class="btn btn-secondary">
          🔀 Document Cross-Checks
        </button>
      </div>
    </div>

    <!-- ERROR BANNER — shown when API call fails -->
    <div v-if="loadError" class="error-banner">
      <span class="error-icon">⚠️</span>
      <div>
        <strong>Failed to load documents for {{ bidderStore.currentBidderId }}</strong>
        <p class="error-detail">{{ loadError }}</p>
      </div>
      <button @click="retryLoad" class="btn btn-outline btn-sm">🔄 Retry</button>
    </div>

    <!-- OVERALL VERIFICATION KPI CARDS — always rendered, show 0s on empty -->
    <div class="kpi-grid">
      <div class="kpi-card score-card">
        <div class="kpi-title">VERIFICATION STATUS</div>
        <div class="kpi-value text-blue">{{ verifiedPct }}%</div>
        <div class="kpi-subtext">Overall Document Verification Score</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">TOTAL DOCUMENTS</div>
        <div class="kpi-value">{{ uniqueDocCount }} / 14</div>
        <div class="kpi-subtext">14 Standard Categories Required</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">VERIFIED</div>
        <div class="kpi-value text-green">{{ verifiedCount }}</div>
        <div class="kpi-subtext">Passed Extraction &amp; Sandbox Checks</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">MISSING / PENDING</div>
        <div class="kpi-value text-amber">{{ missingCount }}</div>
        <div class="kpi-subtext">Not Yet Uploaded</div>
      </div>
    </div>

    <!-- 14-DOCUMENT TABLE CARD -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">All 14 Bidder Document Verification Records</h3>
        <span class="badge badge-neutral">Provider: TenderVerify Sandbox</span>
      </div>

      <!-- LOADING STATE -->
      <div v-if="loading" class="state-box">
        <div class="loading-spinner"></div>
        <span>Loading documents for <strong>{{ bidderStore.currentBidderId }}</strong>…</span>
      </div>

      <!-- EMPTY STATE — new bidder with no uploads yet -->
      <div v-else-if="!loading && uniqueDocCount === 0 && !loadError" class="state-box empty-state">
        <div class="empty-icon">📂</div>
        <h4>No Documents Uploaded Yet</h4>
        <p>
          Bidder <strong>{{ bidderStore.currentBidderId }}</strong> has
          <strong>0 / 14</strong> required documents.
          Upload documents via the Dashboard to begin verification.
        </p>
        <button @click="router.push('/')" class="btn btn-primary mt-2">
          📤 Go to Upload Dashboard
        </button>
      </div>

      <!-- DOCUMENT TABLE — always renders the 14 rows, MISSING or populated -->
      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Document Name</th>
              <th>Category</th>
              <th>Verification Status</th>
              <th>Extraction Confidence</th>
              <th>Extracted Identity / Reference</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(doc, idx) in all14Documents"
              :key="doc.key"
              :class="['table-row-hover', doc.status === 'MISSING' ? 'row-missing' : '']"
            >
              <td><code>{{ String(idx + 1).padStart(2, '0') }}</code></td>
              <td>
                <div class="doc-title-text">
                  <span class="file-icon">{{ doc.record ? '📄' : '📭' }}</span>
                  {{ doc.name }}
                </div>
                <div class="file-path-text" v-if="doc.record && doc.record.file_name">
                  {{ doc.record.file_name }}
                </div>
              </td>
              <td><span class="badge badge-category">{{ doc.category }}</span></td>
              <td>
                <span :class="['result-pill', getStatusPill(doc.status)]">
                  {{ doc.status }}
                </span>
              </td>
              <td>
                <span v-if="doc.record" :class="['conf-text', getConfClass(doc.confidence)]">
                  {{ Math.round(doc.confidence * 100) }}%
                </span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="identity-cell">
                <span v-if="doc.identity" class="identity-text">{{ doc.identity }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td>
                <button
                  v-if="doc.record"
                  @click="viewEvidence(doc)"
                  class="btn-sm btn-outline"
                >
                  🔍 View Evidence
                </button>
                <span v-else class="text-muted text-xs">Not uploaded</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- EVIDENCE MODAL -->
    <div v-if="selectedDoc" class="modal-backdrop" @click.self="selectedDoc = null">
      <div class="modal-card">
        <div class="modal-header">
          <h3>📄 Evidence Trace — {{ selectedDoc.name }}</h3>
          <button @click="selectedDoc = null" class="close-btn">×</button>
        </div>

        <div class="modal-body">
          <div class="detail-row">
            <span class="detail-label">Status:</span>
            <span :class="['result-pill', getStatusPill(selectedDoc.status)]">
              {{ selectedDoc.status }}
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Confidence:</span>
            <span class="detail-val">{{ Math.round(selectedDoc.confidence * 100) }}%</span>
          </div>
          <div class="detail-row" v-if="selectedDoc.record && selectedDoc.record.file_name">
            <span class="detail-label">File Name:</span>
            <span class="detail-val">{{ selectedDoc.record.file_name }}</span>
          </div>
          <div
            class="fields-box mt-3"
            v-if="selectedDoc.record && selectedDoc.record.extracted_data && Object.keys(selectedDoc.record.extracted_data).length > 0"
          >
            <label class="font-bold text-sm">Extracted Structured Fields:</label>
            <pre class="json-box">{{ JSON.stringify(selectedDoc.record.extracted_data, null, 2) }}</pre>
          </div>
          <div v-else class="text-muted text-sm mt-3">
            No structured fields extracted for this document.
          </div>
        </div>

        <div class="modal-footer">
          <button @click="selectedDoc = null" class="btn btn-secondary w-full">
            Close Evidence Window
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { bidderApi } from '../api/bidderApi'
import { useBidderStore } from '../stores/bidder'

// ──────────────────────────────────────────────
// TYPE: local representation of an API document
// (defensive — only uses fields the API actually returns)
// ──────────────────────────────────────────────
interface ApiDoc {
  id?: number
  bidder_id?: string
  document_type: string
  file_name?: string
  status: string
  extraction_confidence?: number | null
  extracted_data?: Record<string, any> | null
  uploaded_at?: string | null
  processing_completed_at?: string | null
}

const router = useRouter()
const bidderStore = useBidderStore()

const documents   = ref<ApiDoc[]>([])
const loading     = ref(false)
const loadError   = ref<string | null>(null)
const selectedDoc = ref<any | null>(null)

// ──────────────────────────────────────────────
// 14 STANDARD DOCUMENT CATEGORIES (fixed list)
// ──────────────────────────────────────────────
const standard14List = [
  { key: 'GST_CERTIFICATE',              name: 'GST Certificate',              category: 'REGISTRATION' },
  { key: 'PAN_CARD',                     name: 'PAN Card',                     category: 'IDENTITY'     },
  { key: 'UDYAM_CERTIFICATE',            name: 'Udyam Certificate',            category: 'REGISTRATION' },
  { key: 'COMPANY_INCORPORATION',        name: 'MCA Incorporation',            category: 'REGISTRATION' },
  { key: 'INCOME_TAX_RETURN',            name: 'Income Tax Return (ITR)',      category: 'FINANCIAL'    },
  { key: 'BIS_CERTIFICATE',              name: 'BIS Certificate',              category: 'CERTIFICATE'  },
  { key: 'NSIC_CERTIFICATE',             name: 'NSIC Certificate',             category: 'CERTIFICATE'  },
  { key: 'STARTUP_CERTIFICATE',          name: 'Startup Certificate',          category: 'REGISTRATION' },
  { key: 'OEM_AUTHORIZATION',            name: 'OEM Authorization',            category: 'TECHNICAL'    },
  { key: 'FINANCIAL_TURNOVER_CERTIFICATE', name: 'Financial Turnover Certificate', category: 'FINANCIAL' },
  { key: 'NON_BLACKLISTING_DECLARATION', name: 'Non-Blacklisting Declaration', category: 'COMPLIANCE'  },
  { key: 'LOCAL_CONTENT_DECLARATION',    name: 'Local Content Declaration',    category: 'COMPLIANCE'  },
  { key: 'EPFO_REGISTRATION',            name: 'EPFO Registration',            category: 'COMPLIANCE'  },
  { key: 'ESIC_REGISTRATION',            name: 'ESIC Registration',            category: 'COMPLIANCE'  },
]

// ──────────────────────────────────────────────
// LOAD DOCUMENTS — safe, never throws to Vue
// ──────────────────────────────────────────────
const loadDocuments = async (bidderId: string) => {
  console.log('[BidderVerification] CURRENT_BIDDER_ID:', bidderId)
  console.log('[BidderVerification] API_URL:', `/api/documents/bidder/${bidderId}`)

  loading.value   = true
  loadError.value = null
  documents.value = []  // always clear first — bidder isolation

  try {
    const raw = await bidderApi.getBidderDocuments(bidderId)

    // Guard: discard if bidder changed while we were awaiting
    if (bidderId !== bidderStore.currentBidderId) {
      console.log('[BidderVerification] Bidder changed during fetch — discarding stale response')
      return
    }

    console.log('[BidderVerification] API_RESPONSE_STATUS: 200')
    console.log('[BidderVerification] API_RESPONSE_DATA (raw count):', Array.isArray(raw) ? raw.length : typeof raw)

    // Defensive: ensure we got an array
    const list: ApiDoc[] = Array.isArray(raw) ? raw : []
    documents.value = list

    console.log('[BidderVerification] DOCUMENT_COUNT (raw rows):', list.length)
    console.log('[BidderVerification] UNIQUE_TYPE_COUNT:', new Set(list.map(d => d.document_type)).size)

  } catch (err: any) {
    const msg = err?.response?.data?.detail || err?.message || String(err)
    console.error('[BidderVerification] API ERROR:', msg, err)
    loadError.value = msg
    documents.value = []
  } finally {
    loading.value = false
  }
}

const retryLoad = () => loadDocuments(bidderStore.currentBidderId)

// Load on mount
onMounted(() => {
  loadDocuments(bidderStore.currentBidderId)
})

// Re-load when user switches bidder (watch is safer than watchEffect with async)
watch(
  () => bidderStore.currentBidderId,
  (newId, oldId) => {
    if (newId !== oldId) {
      console.log('[BidderVerification] Bidder switched:', oldId, '->', newId)
      loadDocuments(newId)
    }
  }
)

// ──────────────────────────────────────────────
// DEDUPLICATION — keep most-recent per type
// ──────────────────────────────────────────────
const deduplicatedByType = computed(() => {
  const map = new Map<string, ApiDoc>()
  for (const doc of (documents.value ?? [])) {
    if (!doc || !doc.document_type) continue
    const existing = map.get(doc.document_type)
    if (!existing) {
      map.set(doc.document_type, doc)
    } else {
      const existTs = existing.uploaded_at || existing.processing_completed_at || ''
      const docTs   = doc.uploaded_at || doc.processing_completed_at || ''
      if (docTs > existTs) map.set(doc.document_type, doc)
    }
  }
  return map
})

// ──────────────────────────────────────────────
// BUILD all14Documents — ALWAYS returns 14 rows
// ──────────────────────────────────────────────
const all14Documents = computed(() => {
  return standard14List.map(std => {
    const record = deduplicatedByType.value.get(std.key) ?? null

    let status     = 'MISSING'
    let confidence = 0.0
    let identity   = ''

    if (record) {
      const s = (record.status || '').toUpperCase()
      if (s === 'EXTRACTED') {
        status     = 'VERIFIED'
        confidence = record.extraction_confidence ?? 0.95
      } else if (s === 'PARTIALLY_EXTRACTED') {
        status     = 'NEEDS_REVIEW'
        confidence = record.extraction_confidence ?? 0.6
      } else if (s === 'UPLOADED' || s === 'PROCESSING') {
        status     = 'PROCESSING'
        confidence = 0.5
      } else {
        status     = 'FAILED'
        confidence = 0.2
      }

      // Safe field extraction — extracted_data may be null/{}
      const ed = record.extracted_data ?? {}
      identity =
        ed.gstin ||
        ed.pan_number ||
        ed.udyam_registration_number ||
        ed.cin ||
        ed.license_number ||
        ed.legal_name ||
        ''
    }

    return { ...std, record, status, confidence, identity }
  })
})

// ──────────────────────────────────────────────
// KPI COUNTS — all safe, always return numbers
// ──────────────────────────────────────────────
const uniqueDocCount = computed(() => deduplicatedByType.value.size)
const verifiedCount  = computed(() => all14Documents.value.filter(d => d.status === 'VERIFIED').length)
const missingCount   = computed(() => all14Documents.value.filter(d => d.status === 'MISSING').length)
const verifiedPct    = computed(() =>
  verifiedCount.value > 0 ? Math.round((verifiedCount.value / 14) * 100) : 0
)

// ──────────────────────────────────────────────
// HELPERS
// ──────────────────────────────────────────────
const getStatusPill = (status: string) => {
  switch (status) {
    case 'VERIFIED':    return 'pill-verified'
    case 'NEEDS_REVIEW':return 'pill-review'
    case 'PROCESSING':  return 'pill-processing'
    case 'FAILED':      return 'pill-mismatch'
    case 'MISSING':
    default:            return 'pill-missing'
  }
}

const getConfClass = (conf: number) => {
  if (conf >= 0.8) return 'text-green'
  if (conf >= 0.5) return 'text-amber'
  return 'text-red'
}

const viewEvidence = (doc: any) => {
  selectedDoc.value = doc
}
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
.page-subtitle { font-size: 0.85rem; color: #64748b; margin-top: 2px; }

.header-actions { display: flex; gap: 0.5rem; }
.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary   { background: #2563eb; color: white; }
.btn-secondary { background: #0f172a; color: white; }
.btn-outline   { background: white; border: 1px solid #cbd5e1; color: #334155; }
.btn-sm        { padding: 0.3rem 0.65rem; font-size: 0.75rem; cursor: pointer; border-radius: 4px; }
.mt-2          { margin-top: 0.5rem; }

/* Error banner */
.error-banner {
  display: flex; align-items: flex-start; gap: 0.85rem;
  background: #fef2f2; border: 1px solid #fecaca;
  padding: 0.85rem 1.1rem; border-radius: 8px;
  font-size: 0.875rem; color: #7f1d1d;
}
.error-icon   { font-size: 1.2rem; }
.error-detail { font-size: 0.8rem; color: #991b1b; margin-top: 2px; }

/* KPI grid */
.kpi-grid  { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.kpi-card  { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem 1.25rem; }
.score-card{ background: #eff6ff; border-color: #bfdbfe; }
.kpi-title { font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }
.kpi-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; margin-top: 0.2rem; }
.kpi-subtext { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

/* Colors */
.text-blue  { color: #2563eb; }
.text-green { color: #16a34a; font-weight: 700; }
.text-amber { color: #d97706; font-weight: 700; }
.text-red   { color: #dc2626; font-weight: 700; }
.text-muted { color: #94a3b8; }
.text-xs    { font-size: 0.75rem; }
.text-sm    { font-size: 0.875rem; }

/* Card */
.card        { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.card-header { padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.card-title  { font-size: 0.95rem; font-weight: 700; color: #0f172a; }

/* Loading / empty state box */
.state-box {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 3rem 2rem; gap: 0.75rem;
  color: #64748b; font-size: 0.9rem; text-align: center;
}
.loading-spinner {
  width: 22px; height: 22px;
  border: 2px solid #e2e8f0; border-top-color: #2563eb;
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state { background: #f8fafc; }
.empty-icon  { font-size: 2.5rem; }
.empty-state h4 { font-size: 1rem; font-weight: 700; color: #0f172a; margin: 0; }
.empty-state p  { font-size: 0.875rem; color: #64748b; max-width: 400px; }

/* Table */
.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; }
.table-row-hover:hover { background: #f8fafc; }
.row-missing { opacity: 0.75; }

.doc-title-text  { font-weight: 700; color: #0f172a; display: flex; align-items: center; gap: 0.4rem; }
.file-path-text  { font-size: 0.75rem; color: #64748b; font-family: monospace; margin-top: 2px; }
.file-icon       { font-size: 1rem; }

/* Badges */
.badge          { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.badge-category { background: #f1f5f9; color: #334155; }
.badge-neutral  { background: #f1f5f9; color: #475569; }

/* Status pills */
.result-pill     { display: inline-block; padding: 0.25rem 0.65rem; border-radius: 20px; font-weight: 700; font-size: 0.75rem; }
.pill-verified   { background: #dcfce7; color: #15803d; }
.pill-missing    { background: #ffedd5; color: #c2410c; }
.pill-mismatch   { background: #fee2e2; color: #b91c1c; }
.pill-review     { background: #fef08a; color: #a16207; }
.pill-processing { background: #dbeafe; color: #1d4ed8; }

.conf-text     { font-weight: 700; font-size: 0.85rem; }
.identity-text { font-family: monospace; font-size: 0.8rem; background: #f1f5f9; padding: 0.15rem 0.4rem; border-radius: 4px; color: #334155; }

/* Modal */
.modal-backdrop { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15,23,42,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card     { background: white; width: 550px; max-height: 85vh; overflow-y: auto; padding: 1.5rem; border-radius: 10px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2); }
.modal-header   { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.75rem; }
.close-btn      { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #64748b; }
.detail-row     { display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px dashed #f1f5f9; font-size: 0.85rem; }
.detail-label   { color: #64748b; }
.detail-val     { font-weight: 600; color: #0f172a; }
.json-box       { background: #0f172a; color: #38bdf8; padding: 0.75rem; border-radius: 6px; font-size: 0.75rem; overflow-x: auto; max-height: 250px; margin-top: 0.3rem; }
.modal-footer   { margin-top: 1.5rem; }
.w-full         { width: 100%; }
.mt-3           { margin-top: 0.75rem; }
.font-bold      { font-weight: 700; }
</style>

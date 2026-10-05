<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">External Source Verification</h1>
        <p class="page-subtitle">Verify bidder registration & identity records against external government databases (TenderVerify Sandbox)</p>
      </div>

      <button @click="runVerification" class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Running Checks...' : '⚡ Execute Sandbox Verification' }}
      </button>
    </div>

    <!-- PROVIDER STATUS & WARNING BANNER -->
    <div class="sandbox-header-card">
      <div class="header-status-grid">
        <div class="status-block">
          <span class="block-label">PROVIDER:</span>
          <span class="block-val">TenderVerify Sandbox</span>
        </div>

        <div class="status-block">
          <span class="block-label">CONNECTION:</span>
          <span class="status-pill status-online">● Connected (http://localhost:8001)</span>
        </div>

        <div class="status-block">
          <span class="block-label">ENVIRONMENT:</span>
          <span class="badge badge-warning">SANDBOX / DEMO</span>
        </div>
      </div>

      <div class="warning-box">
        <span class="warning-icon">⚠️</span>
        <div>
          <strong>SANDBOX MODE — SYNTHETIC DEMONSTRATION DATA</strong>
          <p>Results are retrieved from TenderVerify Sandbox simulation environment and do NOT represent live Government database verification.</p>
        </div>
      </div>
    </div>

    <!-- EXTERNAL CHECKS TABLE -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">External Provider Check Results</h3>
        <span class="badge badge-neutral">{{ results.length }} External Checks</span>
      </div>

      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Check ID</th>
              <th>Requirement / Category</th>
              <th>Identifier / Document</th>
              <th>Provider</th>
              <th>Mode</th>
              <th>Status</th>
              <th>Timestamp</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in results" :key="r.id" class="table-row-hover">
              <td><code>{{ r.check_id }}</code></td>
              <td>
                <div class="req-title">{{ r.requirement }}</div>
                <div class="req-cat">{{ r.category }}</div>
              </td>
              <td>
                <code class="id-code">{{ getIdentifier(r) }}</code>
              </td>
              <td><strong>{{ r.verification_source }}</strong></td>
              <td><span class="mode-tag">{{ r.source_mode }}</span></td>
              <td>
                <span :class="['result-pill', getPillClass(r.status)]">
                  {{ r.status }}
                </span>
              </td>
              <td>{{ formatDate(r.timestamp) }}</td>
              <td>
                <button @click="openDrawer(r)" class="btn-sm btn-outline">
                  🔍 View Response
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- SIDE DRAWER FOR FORMATTED API RESPONSE -->
    <div v-if="selectedCheck" class="drawer-backdrop" @click.self="selectedCheck = null">
      <div class="side-drawer">
        <div class="drawer-header">
          <div>
            <h3><code>{{ selectedCheck.check_id }}</code> Verification Details</h3>
            <p class="drawer-sub">TenderVerify Sandbox Response Payload</p>
          </div>
          <button @click="selectedCheck = null" class="close-btn">×</button>
        </div>

        <div class="drawer-body">
          <!-- FORMATTED API FIELDS -->
          <div class="drawer-section">
            <h4 class="section-title">Verified Identity & Entity Fields</h4>
            
            <div class="fields-grid" v-if="selectedCheck.verified_value">
              <div 
                v-for="(val, key) in selectedCheck.verified_value" 
                :key="key"
                class="field-card"
              >
                <div class="field-key">{{ formatKey(String(key)) }}</div>
                <div class="field-val">{{ val || 'N/A' }}</div>
              </div>
            </div>
            <div v-else class="text-muted text-sm">
              No response fields returned for this check.
            </div>
          </div>

          <!-- EXPLANATION & EVIDENCE -->
          <div class="drawer-section">
            <h4 class="section-title">Verification Explanation & Evidence</h4>
            <div class="explanation-box">{{ selectedCheck.explanation }}</div>
          </div>

          <!-- RAW JSON TOGGLE -->
          <details class="raw-json-details mt-4">
            <summary class="cursor-pointer text-xs font-bold text-slate-500">View Raw API Response JSON</summary>
            <pre class="json-code">{{ JSON.stringify(selectedCheck.verified_value || selectedCheck.evidence, null, 2) }}</pre>
          </details>

          <!-- DRAWER FOOTER METADATA -->
          <div class="drawer-footer">
            <div class="footer-meta">
              <span>Source: <strong>TenderVerify Sandbox</strong></span>
              <span>Mode: <strong class="text-amber">SANDBOX</strong></span>
            </div>
            <div class="disclaimer-note">
              Synthetic data for prototype demonstration. Not connected to live Government databases.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { verificationApi, VerificationResultItem } from '../api/verificationApi'
import { sandboxApi } from '../api/sandboxApi'
import { useBidderStore } from '../stores/bidder'

const bidderStore = useBidderStore()
const loading = ref(false)
const bidderId = ref(bidderStore.currentBidderId)
const results = ref<VerificationResultItem[]>([])
const selectedCheck = ref<VerificationResultItem | null>(null)

onMounted(() => {
  loadLatestVerification()
})

// Re-run when bidder changes
watch(() => bidderStore.currentBidderId, (newId) => {
  bidderId.value = newId
  results.value = []
  loadLatestVerification()
})

const loadLatestVerification = async () => {
  try {
    const session = await verificationApi.getLatestSession(bidderId.value)
    if (session) {
      const resData = await verificationApi.getSessionResults(session.id)
      results.value = resData.results.filter((r: any) => r.category === 'EXTERNAL' || r.verification_source.includes('PROVIDER'))
    } else {
      await runVerification()
    }
  } catch (e) {
    await runVerification()
  }
}

const runVerification = async () => {
  loading.value = true
  try {
    const res = await verificationApi.runVerification(bidderId.value)
    const resData = await verificationApi.getSessionResults(res.session_id)
    results.value = resData.results.filter((r: any) => r.category === 'EXTERNAL' || r.verification_source.includes('PROVIDER'))
  } catch (e) {
    alert('External verification failed: ' + e)
  } finally {
    loading.value = false
  }
}

const getIdentifier = (r: VerificationResultItem) => {
  if (r.extracted_value_a) {
    return r.extracted_value_a.gstin || 
           r.extracted_value_a.pan_number || 
           r.extracted_value_a.udyam_registration_number || 
           r.extracted_value_a.cin || 'N/A'
  }
  return 'N/A'
}

const openDrawer = async (r: VerificationResultItem) => {
  selectedCheck.value = r
  // Dynamically query sandbox server if gstin/pan exists
  const gstin = r.extracted_value_a?.gstin
  if (gstin) {
    const res = await sandboxApi.fetchGstDetails(gstin)
    if (res.success && res.data) {
      selectedCheck.value = { ...r, verified_value: res.data }
    }
  }
}

const formatKey = (key: string) => {
  return key.replace(/_/g, ' ').toUpperCase()
}

const formatDate = (ts?: string) => {
  if (!ts) return '28 Sep 2026'
  return new Date(ts).toLocaleDateString()
}

const getPillClass = (status: string) => {
  switch (status) {
    case 'VERIFIED': return 'pill-verified'
    case 'MISMATCH': return 'pill-mismatch'
    case 'MISSING': return 'pill-missing'
    default: return 'pill-neutral'
  }
}
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
.page-subtitle { font-size: 0.85rem; color: #64748b; margin-top: 2px; }

.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: white; }
.btn-sm { padding: 0.35rem 0.65rem; font-size: 0.75rem; }
.btn-outline { background: white; border: 1px solid #cbd5e1; color: #334155; }

.sandbox-header-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem; }
.header-status-grid { display: flex; gap: 2rem; border-bottom: 1px solid #f1f5f9; padding-bottom: 0.85rem; margin-bottom: 0.85rem; }
.status-block { display: flex; flex-direction: column; gap: 2px; }
.block-label { font-size: 0.65rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }
.block-val { font-size: 0.9rem; font-weight: 700; color: #0f172a; }
.status-pill { font-weight: 600; font-size: 0.85rem; }
.status-online { color: #16a34a; }

.warning-box { background: #fffbeb; border: 1px solid #fef08a; border-radius: 6px; padding: 0.75rem 1rem; display: flex; gap: 0.75rem; align-items: center; color: #92400e; font-size: 0.8rem; }
.warning-icon { font-size: 1.25rem; }

.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.card-header { padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.card-title { font-size: 0.95rem; font-weight: 700; color: #0f172a; }

.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; }
.table-row-hover:hover { background: #f8fafc; }

.req-title { font-weight: 700; color: #0f172a; }
.req-cat { font-size: 0.75rem; color: #64748b; }
.id-code { font-family: monospace; background: #f1f5f9; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.8rem; }
.mode-tag { background: #dbeafe; color: #1e40af; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.7rem; font-weight: 700; }

.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.badge-warning { background: #fef08a; color: #854d0e; }
.badge-neutral { background: #f1f5f9; color: #475569; }

.result-pill { display: inline-block; padding: 0.25rem 0.65rem; border-radius: 20px; font-weight: 700; font-size: 0.75rem; }
.pill-verified { background: #dcfce7; color: #15803d; }
.pill-mismatch { background: #fee2e2; color: #b91c1c; }
.pill-missing { background: #ffedd5; color: #c2410c; }
.pill-neutral { background: #f1f5f9; color: #475569; }

/* SIDE DRAWER STYLES */
.drawer-backdrop { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15, 23, 42, 0.5); z-index: 1000; display: flex; justify-content: flex-end; }
.side-drawer { width: 480px; background: white; height: 100%; display: flex; flex-direction: column; box-shadow: -10px 0 25px rgba(0,0,0,0.15); animation: slideIn 0.2s ease-out; }
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }

.drawer-header { padding: 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: flex-start; background: #f8fafc; }
.drawer-sub { font-size: 0.75rem; color: #64748b; margin-top: 2px; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #64748b; }

.drawer-body { padding: 1.25rem; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 1.25rem; }
.section-title { font-size: 0.8rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.75rem; }

.fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.field-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.6rem 0.75rem; border-radius: 6px; }
.field-key { font-size: 0.65rem; font-weight: 700; color: #64748b; }
.field-val { font-size: 0.85rem; font-weight: 700; color: #0f172a; margin-top: 2px; word-break: break-all; }

.explanation-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 0.75rem; border-radius: 6px; font-size: 0.85rem; color: #166534; }
.json-code { background: #0f172a; color: #38bdf8; padding: 0.75rem; border-radius: 6px; font-size: 0.75rem; max-height: 200px; overflow-y: auto; margin-top: 0.5rem; }

.drawer-footer { padding: 1rem 1.25rem; border-top: 1px solid #e2e8f0; background: #f8fafc; font-size: 0.75rem; }
.footer-meta { display: flex; justify-content: space-between; color: #475569; }
.disclaimer-note { color: #64748b; font-size: 0.7rem; font-style: italic; margin-top: 0.5rem; }
.mt-4 { margin-top: 1rem; }
.text-amber { color: #d97706; }
</style>

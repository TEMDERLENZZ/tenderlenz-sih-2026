<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Requirement Compliance Engine</h1>
        <p class="page-subtitle">Matching tender rules against verified bidder evidence</p>
      </div>

      <div class="header-actions">
        <button @click="evaluate" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Evaluating Bidder...' : '⚡ Run Compliance Analysis' }}
        </button>
        <button @click="router.push('/reports')" class="btn btn-secondary">
          📄 Generate Final Report →
        </button>
      </div>
    </div>

    <!-- EMPTY STATE: No Bidder Selected -->
    <div v-if="!bidderStore.currentBidderId || !currentTenderId" class="card p-4">
      <div class="empty-state">
        <span class="empty-icon">⚖️</span>
        <p class="empty-title">Compliance evaluation has not been performed.</p>
        <p class="empty-hint">
          <span v-if="!currentTenderId">No tender available. Upload a tender first.</span>
          <span v-else>Register a bidder and submit documents, then run compliance analysis.</span>
        </p>
        <button v-if="!currentTenderId" @click="router.push('/tenders-list')" class="btn btn-primary mt-2">Upload Tender</button>
      </div>
    </div>

    <!-- SUMMARY METRICS GRID -->
    <div class="kpi-grid" v-if="summary">
      <div class="kpi-card score-card">
        <div class="kpi-title">COMPLIANCE RATE</div>
        <div class="kpi-value text-blue">{{ summary.compliance_percentage }}%</div>
        <div class="kpi-subtext">Automated Matching Score</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">TOTAL REQUIREMENTS</div>
        <div class="kpi-value">{{ summary.total_requirements }}</div>
        <div class="kpi-subtext">Extracted Tender Rules</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">SATISFIED</div>
        <div class="kpi-value text-green">{{ summary.satisfied }}</div>
        <div class="kpi-subtext">Evidence Verified</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">NOT SATISFIED</div>
        <div class="kpi-value text-red">{{ summary.not_satisfied }}</div>
        <div class="kpi-subtext">Non-Compliant Criteria</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">NEEDS REVIEW</div>
        <div class="kpi-value text-amber">{{ summary.review_required }}</div>
        <div class="kpi-subtext">Officer Confirmation Needed</div>
      </div>
    </div>

    <!-- CRITICAL COMPLIANCE FINDINGS SECTION -->
    <div class="card critical-card" v-if="summary && (summary.not_satisfied > 0 || summary.review_required > 0)">
      <div class="card-header bg-critical-header">
        <div class="flex-items">
          <span class="critical-icon">🚨</span>
          <h3 class="card-title text-red-700">Critical Compliance Findings & Gaps</h3>
        </div>
        <span class="badge badge-red">{{ summary.not_satisfied }} Non-Compliant Gap(s)</span>
      </div>

      <div class="critical-body">
        <div class="findings-grid">
          <!-- DYNAMIC FINDING CARDS FROM BACKEND -->
          <div
            v-for="finding in criticalFindings"
            :key="finding.id"
            :class="['finding-card', finding.result === 'NOT_SATISFIED' ? 'border-red' : 'border-amber']"
          >
            <div class="finding-header">
              <span :class="['badge', finding.result === 'NOT_SATISFIED' ? 'badge-red-dark' : 'badge-amber-dark']">
                {{ finding.requirement_code }}
              </span>
              <strong class="finding-title">{{ getReqTitle(finding.requirement_code) }}</strong>
            </div>
            <div class="gap-details">
              <div class="gap-row">
                <span class="gap-label">Required:</span>
                <span class="gap-val font-bold">{{ finding.required_value }}</span>
              </div>
              <div class="gap-row">
                <span class="gap-label">Evidence:</span>
                <span :class="['gap-val font-bold', finding.result === 'NOT_SATISFIED' ? 'text-red' : 'text-amber']">
                  {{ finding.actual_value }}
                </span>
              </div>
              <div class="gap-row highlight-gap">
                <span class="gap-label">Status:</span>
                <span :class="['gap-val font-extrabold', finding.result === 'NOT_SATISFIED' ? 'text-red-dark' : 'text-amber-dark']">
                  {{ finding.result === 'NOT_SATISFIED' ? 'Non-Compliant' : 'Needs Review' }}
                </span>
              </div>
              <div class="gap-row">
                <span class="gap-label">Source Document:</span>
                <span class="gap-val font-mono">
                  {{ finding.evidence?.document || 'Document Record' }}
                  <span v-if="finding.evidence?.page"> — Page {{ finding.evidence.page }}</span>
                </span>
              </div>
            </div>
          </div>

          <!-- Show message if no critical findings -->
          <div v-if="criticalFindings.length === 0" class="no-findings-message">
            <span class="text-green font-bold">✓ No critical compliance gaps detected</span>
          </div>
        </div>

        <div class="critical-notice mt-3">
          <span class="notice-icon font-bold text-amber">⚠️ OFFICER NOTICE:</span>
          <span>Do not automatically claim the bidder is legally disqualified. The AI provides advisory gap analysis; final qualification determination remains with the Procurement Officer.</span>
        </div>
      </div>
    </div>

    <!-- REQUIREMENT COMPLIANCE ENGINE TABLE -->
    <div class="card" v-if="summary">
      <div class="card-header">
        <h3 class="card-title">Requirement vs Verified Bidder Evidence Matrix</h3>
        <span class="badge badge-neutral">Tender: {{ currentTenderId || 'N/A' }} | Bidder: {{ bidderStore.currentBidderId || 'N/A' }}</span>
      </div>

      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Requirement</th>
              <th>Tender Rule</th>
              <th>Bidder Evidence</th>
              <th>Source Document</th>
              <th>Status</th>
              <th>Explanation</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="r in summary.results" 
              :key="r.id"
              :class="getRowClass(r.result)"
            >
              <td>
                <div class="req-code-title"><code>{{ r.requirement_code }}</code></div>
                <div class="req-title-bold">{{ getReqTitle(r.requirement_code) }}</div>
              </td>
              <td><span class="rule-box">{{ r.required_value || '-' }}</span></td>
              <td><span class="evidence-box-val">{{ r.actual_value || '-' }}</span></td>
              <td class="source-cell">
                <div class="src-doc" v-if="r.evidence?.document">
                  📁 {{ r.evidence.document }}
                  <span class="src-page" v-if="r.evidence.page">p. {{ r.evidence.page }}</span>
                </div>
                <div class="src-doc" v-else>Doc Intelligence Record</div>
              </td>
              <td>
                <span :class="['result-pill', getPillClass(r.result)]">
                  {{ getIcon(r.result) }} {{ formatStatus(r.result) }}
                </span>
              </td>
              <td class="explanation-text">{{ r.explanation }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { tenderApi, TenderComplianceSummary } from '../api/tenderApi'
import { useBidderStore } from '../stores/bidder'
import axios from 'axios'

const router = useRouter()
const bidderStore = useBidderStore()
const loading = ref(false)
const currentTenderId = ref('')
const bidderId = ref(bidderStore.currentBidderId)
const summary = ref<TenderComplianceSummary | null>(null)

const titleMap: Record<string, string> = {
  'REQ-001': 'Minimum Annual Turnover',
  'REQ-002': 'GST Registration Status',
  'REQ-003': 'BIS Certificate Requirement',
  'REQ-004': 'OEM Authorization',
  'REQ-005': 'Local Content Percentage',
  'REQ-006': 'Non-Blacklisting Declaration'
}

// Compute critical findings from actual backend data
const criticalFindings = computed(() => {
  if (!summary.value) return []
  return summary.value.results.filter(r =>
    r.result === 'NOT_SATISFIED' || r.result === 'REVIEW_REQUIRED'
  )
})

onMounted(async () => {
  // Load tender first — do NOT auto-evaluate, wait for user to click button
  await loadActiveTender()
})

// Re-check tender and clear when bidder changes
watch(() => bidderStore.currentBidderId, async (newId) => {
  bidderId.value = newId
  summary.value = null
})

const loadActiveTender = async () => {
  try {
    const res = await axios.get('/api/tenders/list')
    const tenders = res.data || []
    if (tenders.length > 0) {
      currentTenderId.value = tenders[0].tender_id
    } else {
      currentTenderId.value = ''
    }
  } catch (e) {
    currentTenderId.value = ''
  }
}

const evaluate = async () => {
  if (!currentTenderId.value || !bidderId.value) {
    alert('Please ensure a tender is uploaded and a bidder is registered before running compliance analysis.')
    return
  }
  loading.value = true
  try {
    const res = await tenderApi.evaluateBidder(currentTenderId.value, bidderId.value)
    summary.value = res
  } catch (e) {
    alert('Compliance evaluation failed: ' + e)
  } finally {
    loading.value = false
  }
}

const getReqTitle = (code: string) => titleMap[code] || code

const formatStatus = (s: string) => s.replace(/_/g, ' ')

const getIcon = (result: string) => {
  switch (result) {
    case 'SATISFIED': return '✅'
    case 'NOT_SATISFIED': return '❌'
    case 'MISSING': return '⚠️'
    case 'REVIEW_REQUIRED': return '🔍'
    default: return 'ℹ️'
  }
}

const getPillClass = (result: string) => {
  switch (result) {
    case 'SATISFIED': return 'pill-satisfied'
    case 'NOT_SATISFIED': return 'pill-not-satisfied'
    case 'MISSING': return 'pill-missing'
    case 'REVIEW_REQUIRED': return 'pill-review'
    default: return 'pill-unable'
  }
}

const getRowClass = (result: string) => {
  switch (result) {
    case 'NOT_SATISFIED': return 'row-not-satisfied'
    case 'MISSING': return 'row-missing'
    case 'REVIEW_REQUIRED': return 'row-review'
    default: return ''
  }
}
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
.page-subtitle { font-size: 0.85rem; color: #64748b; margin-top: 2px; }

.header-actions { display: flex; gap: 0.5rem; }
.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: white; }
.btn-secondary { background: #0f172a; color: white; }
.p-4 { padding: 1.5rem; }
.mt-2 { margin-top: 0.5rem; }
.empty-state { text-align: center; padding: 2rem; color: #64748b; }
.empty-icon { font-size: 3rem; display: block; margin-bottom: 0.75rem; }
.empty-title { font-size: 1rem; font-weight: 600; color: #334155; margin-bottom: 0.4rem; }
.empty-hint { font-size: 0.8rem; color: #94a3b8; }

.kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; }
.kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem 1.25rem; }
.score-card { background: #eff6ff; border-color: #bfdbfe; }
.kpi-title { font-size: 0.65rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }
.kpi-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; margin-top: 0.2rem; }
.kpi-subtext { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

.text-blue { color: #2563eb; }
.text-green { color: #16a34a; font-weight: 700; }
.text-red { color: #dc2626; font-weight: 700; }
.text-amber { color: #d97706; font-weight: 700; }

.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.critical-card { border: 2px solid #fecaca; }
.card-header { padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.bg-critical-header { background: #fef2f2; border-bottom: 1px solid #fecaca; }
.flex-items { display: flex; align-items: center; gap: 0.5rem; }
.critical-icon { font-size: 1.25rem; }
.card-title { font-size: 0.95rem; font-weight: 700; color: #0f172a; }
.text-red-700 { color: #b91c1c; }

.critical-body { padding: 1.25rem; }
.findings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
.finding-card { background: #fff; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; }
.border-red { border-left: 4px solid #dc2626; }
.border-amber { border-left: 4px solid #d97706; }

.finding-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.finding-title { font-size: 0.9rem; color: #0f172a; }

.gap-details { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.8rem; }
.gap-row { display: flex; justify-content: space-between; padding: 0.2rem 0; }
.highlight-gap { background: #fef2f2; padding: 0.35rem 0.5rem; border-radius: 4px; }
.gap-label { color: #64748b; }
.font-bold { font-weight: 700; }
.font-extrabold { font-weight: 800; }
.font-mono { font-family: monospace; font-size: 0.75rem; }
.text-red-dark { color: #991b1b; }
.text-amber-dark { color: #92400e; }

.critical-notice { background: #fefce8; border: 1px solid #fef08a; padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8rem; color: #854d0e; display: flex; gap: 0.5rem; align-items: center; }

.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; }

.row-not-satisfied { background: #fff5f5; }
.row-missing { background: #fffbeb; }
.row-review { background: #fefce8; }

.req-code-title { font-size: 0.75rem; }
.req-title-bold { font-weight: 700; color: #0f172a; margin-top: 2px; }

.rule-box { font-weight: 700; color: #2563eb; }
.evidence-box-val { font-weight: 700; color: #0f172a; }

.src-doc { font-size: 0.75rem; color: #475569; }
.src-page { background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.7rem; font-weight: 600; margin-left: 2px; }

.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-red-dark { background: #dc2626; color: white; }
.badge-amber-dark { background: #d97706; color: white; }
.badge-neutral { background: #f1f5f9; color: #475569; }

.result-pill { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem 0.65rem; border-radius: 20px; font-weight: 700; font-size: 0.75rem; }
.pill-satisfied { background: #dcfce7; color: #15803d; }
.pill-not-satisfied { background: #fee2e2; color: #b91c1c; }
.pill-missing { background: #ffedd5; color: #c2410c; }
.pill-review { background: #fef08a; color: #a16207; }
.pill-unable { background: #f1f5f9; color: #475569; }

.explanation-text { color: #334155; font-size: 0.8rem; }
.mt-3 { margin-top: 0.75rem; }

.no-findings-message {
  padding: 2rem;
  text-align: center;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  color: #15803d;
  font-size: 0.95rem;
}
</style>

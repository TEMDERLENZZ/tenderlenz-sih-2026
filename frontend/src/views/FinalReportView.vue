<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header print-hide">
      <div>
        <h1 class="page-title">Final Tender Compliance Report</h1>
        <p class="page-subtitle">Official advisory evaluation report for Procurement Officer approval</p>
      </div>

      <div class="header-actions">
        <button @click="downloadJson" class="btn btn-outline">📥 Export JSON</button>
        <button @click="printReport" class="btn btn-secondary">🖨️ Print Report</button>
        <button @click="printReport" class="btn btn-primary">📄 Generate PDF Report</button>
      </div>
    </div>

    <!-- REPORT PRINTABLE CONTAINER -->
    <div class="report-paper card p-5">
      <!-- REPORT BRANDING HEADER -->
      <div class="report-header-banner">
        <div class="brand-title-box">
          <div class="gov-seal">🛡️</div>
          <div>
            <h2 class="report-main-title">FINAL TENDER COMPLIANCE REPORT</h2>
            <div class="report-sub">AI PROCUREMENT INTELLIGENCE ADVISORY AUDIT</div>
          </div>
        </div>

        <div class="report-meta-box">
          <div class="meta-item"><span>Report Date:</span> <strong>28 September 2026</strong></div>
          <div class="meta-item"><span>Environment:</span> <span class="badge badge-warning">DEMO / SANDBOX</span></div>
          <div class="meta-item"><span>Report ID:</span> <code>REP-2026-0928-1042</code></div>
        </div>
      </div>

      <!-- TENDER & BIDDER METADATA -->
      <div class="entity-info-grid">
        <div class="info-card">
          <div class="card-label">TENDER SPECIFICATION</div>
          <div class="info-title">{{ tenderTitle || 'No Active Tender' }}</div>
          <div class="info-sub">Tender ID: <code>{{ tenderId || 'N/A' }}</code></div>
        </div>

        <div class="info-card">
          <div class="card-label">EVALUATED BIDDER ENTITY</div>
          <div class="info-title">{{ bidderStore.currentBidderName || 'No Bidder Selected' }}</div>
          <div class="info-sub">Bidder ID: <code>{{ bidderStore.currentBidderId || 'N/A' }}</code></div>
        </div>
      </div>

      <!-- EMPTY STATE WHEN NO COMPLIANCE DATA -->
      <div v-if="!complianceSummary" class="text-center p-5 text-slate-500">
        <span class="text-4xl block mb-2">📄</span>
        <p class="font-bold text-slate-700">No Final Report Available</p>
        <p class="text-sm">Upload a tender document and run compliance analysis for a bidder to generate the final advisory report.</p>
      </div>

      <!-- SUMMARY COMPLIANCE METRICS -->
      <div class="summary-metrics-bar" v-else-if="complianceSummary">
        <div class="score-block">
          <div class="score-num">{{ complianceSummary.compliance_percentage }}%</div>
          <div class="score-tag">OVERALL COMPLIANCE SCORE</div>
        </div>

        <div class="metrics-grid">
          <div class="m-card"><span class="m-val">{{ complianceSummary.total_requirements }}</span><span class="m-lbl">Total Requirements</span></div>
          <div class="m-card text-green"><span class="m-val">{{ complianceSummary.satisfied }}</span><span class="m-lbl">Satisfied</span></div>
          <div class="m-card text-red"><span class="m-val">{{ complianceSummary.not_satisfied }}</span><span class="m-lbl">Not Satisfied</span></div>
          <div class="m-card text-amber"><span class="m-val">{{ complianceSummary.review_required }}</span><span class="m-lbl">Needs Review</span></div>
        </div>
      </div>

      <!-- CRITICAL FINDINGS SUMMARY -->
      <div class="report-section border-red-left" v-if="complianceSummary && criticalFindings.length > 0">
        <h3 class="section-heading text-red">🚨 Critical Non-Compliance Findings</h3>

        <div class="finding-list">
          <div class="finding-item" v-for="finding in criticalFindings" :key="finding.id">
            <strong>{{ finding.requirement_code }} — {{ getRequirementTitle(finding.requirement_code) }}:</strong>
            <p>
              Required: {{ finding.required_value }} |
              Bidder Actual: {{ finding.actual_value }} |
              <span :class="finding.result === 'NOT_SATISFIED' ? 'text-red font-bold' : 'text-amber font-bold'">
                {{ finding.result === 'NOT_SATISFIED' ? 'Non-Compliant' : 'Needs Review' }}
              </span>
              <span v-if="finding.evidence?.document">
                (Source: {{ finding.evidence.document }}<span v-if="finding.evidence.page"> p. {{ finding.evidence.page }}</span>)
              </span>
            </p>
          </div>
        </div>
      </div>

      <!-- REQUIREMENT EVALUATION RESULTS -->
      <div class="report-section" v-if="complianceSummary">
        <h3 class="section-heading">Detailed Requirement Results</h3>

        <table class="report-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Requirement</th>
              <th>Rule Required</th>
              <th>Bidder Evidence</th>
              <th>Result</th>
              <th>Evidence Source</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="result in complianceSummary.results" :key="result.id">
              <td><code>{{ result.requirement_code }}</code></td>
              <td>{{ getRequirementTitle(result.requirement_code) }}</td>
              <td>{{ result.required_value || '-' }}</td>
              <td>{{ result.actual_value || '-' }}</td>
              <td>
                <span :class="['badge', getResultBadgeClass(result.result)]">
                  {{ formatResultStatus(result.result) }}
                </span>
              </td>
              <td>
                <span v-if="result.evidence?.document">
                  {{ result.evidence.document }}
                  <span v-if="result.evidence.page"> p. {{ result.evidence.page }}</span>
                </span>
                <span v-else>Document Record</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- MANDATORY ADVISORY DISCLAIMER FOOTER -->
      <div class="mandatory-disclaimer-card mt-4">
        <span class="disclaimer-icon">⚖️</span>
        <div>
          <strong>IMPORTANT LEGAL & PROCEDURAL NOTICE:</strong>
          <p>AI-generated compliance analysis is advisory. Final procurement decision remains with the authorized Procurement Officer.</p>
        </div>
      </div>
    </div>

    <!-- PROCUREMENT OFFICER DECISION PANEL -->
    <div class="card p-4 officer-decision-card print-hide">
      <h3 class="card-title mb-2">⚖️ Procurement Officer Final Decision Panel</h3>
      <p class="text-sm text-slate-600 mb-3">Please review all critical findings and supporting evidence before recording the final decision.</p>

      <!-- EXISTING DECISION DISPLAY -->
      <div v-if="existingDecision" class="existing-decision-alert mb-4">
        <span class="alert-icon">✅</span>
        <div>
          <strong>Decision Already Recorded</strong>
          <p>
            Decision: <strong>{{ existingDecision.decision }}</strong> by {{ existingDecision.officer_name || existingDecision.officer_id }}
            on {{ formatDate(existingDecision.decided_at) }}
          </p>
          <p v-if="existingDecision.remarks" class="remarks-text">Remarks: "{{ existingDecision.remarks }}"</p>
        </div>
      </div>

      <div v-if="!existingDecision" class="decision-options mb-4">
        <label :class="['decision-radio-card', { selected: decision === 'APPROVED' }]">
          <input type="radio" v-model="decision" value="APPROVED" />
          <div>
            <strong>Approve Bidder</strong>
            <p>Accept compliance findings and approve bidder for award.</p>
          </div>
        </label>

        <label :class="['decision-radio-card', { selected: decision === 'REJECTED' }]">
          <input type="radio" v-model="decision" value="REJECTED" />
          <div>
            <strong>Reject Bidder</strong>
            <p>Reject bidder due to non-compliance or critical gaps.</p>
          </div>
        </label>

        <label :class="['decision-radio-card', { selected: decision === 'REQUIRES_REVIEW' }]">
          <input type="radio" v-model="decision" value="REQUIRES_REVIEW" />
          <div>
            <strong>Requires Further Review</strong>
            <p>Send for committee review or request bidder clarification.</p>
          </div>
        </label>
      </div>

      <div v-if="!existingDecision" class="form-group mb-3">
        <label class="form-label">Officer Final Remarks / Justification:</label>
        <textarea v-model="officerNotes" class="form-control" rows="3" placeholder="Enter formal decision notes..."></textarea>
      </div>

      <button v-if="!existingDecision" @click="recordDecision" class="btn btn-primary w-full" :disabled="loading">
        {{ loading ? '⏳ Recording...' : '📝 Record Official Officer Decision' }}
      </button>

      <div v-if="decisionError" class="error-alert mt-3">
        <span class="alert-icon">❌</span>
        <div>
          <strong>Error Recording Decision</strong>
          <p>{{ decisionError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { reportApi } from '../api/reportApi'
import { tenderApi, TenderComplianceSummary } from '../api/tenderApi'
import { decisionApi, OfficerDecisionResponse } from '../api/decisionApi'
import { useBidderStore } from '../stores/bidder'

const bidderStore = useBidderStore()
const tenderId = ref('')
const tenderTitle = ref('')
const bidderId = ref(bidderStore.currentBidderId)
const decision = ref('REQUIRES_REVIEW')
const officerNotes = ref('')
const complianceSummary = ref<TenderComplianceSummary | null>(null)
const existingDecision = ref<OfficerDecisionResponse | null>(null)
const loading = ref(false)
const decisionError = ref('')

// Compute critical findings from backend data
const criticalFindings = computed(() => {
  if (!complianceSummary.value) return []
  return complianceSummary.value.results.filter(r =>
    r.result === 'NOT_SATISFIED' || r.result === 'REVIEW_REQUIRED'
  )
})

// Load compliance data on mount
onMounted(async () => {
  await initTenderAndLoad()
})

watch(() => bidderStore.currentBidderId, async (newId) => {
  bidderId.value = newId
  await loadComplianceData()
  await loadExistingDecision()
})

const initTenderAndLoad = async () => {
  try {
    const list = await tenderApi.listTenders()
    if (list && list.length > 0) {
      tenderId.value = list[0].tender_id
      tenderTitle.value = list[0].title
    } else {
      tenderId.value = ''
      tenderTitle.value = ''
    }
  } catch (e) {
    console.error('Failed to list tenders:', e)
  }
  await loadComplianceData()
  await loadExistingDecision()
}

const loadComplianceData = async () => {
  if (!tenderId.value || !bidderId.value) {
    complianceSummary.value = null
    return
  }
  loading.value = true
  try {
    complianceSummary.value = await tenderApi.getComplianceSummary(
      tenderId.value,
      bidderId.value
    )
  } catch (e) {
    complianceSummary.value = null
  } finally {
    loading.value = false
  }
}

const loadExistingDecision = async () => {
  if (!tenderId.value || !bidderId.value) {
    existingDecision.value = null
    return
  }
  try {
    existingDecision.value = await decisionApi.getDecision(
      tenderId.value,
      bidderId.value
    )
  } catch (e) {
    existingDecision.value = null
  }
}

const getRequirementTitle = (code: string): string => {
  const titleMap: Record<string, string> = {
    'REQ-001': 'Minimum Annual Turnover',
    'REQ-002': 'GST Registration Status',
    'REQ-003': 'BIS Certificate Requirement',
    'REQ-004': 'OEM Authorization',
    'REQ-005': 'Local Content Percentage',
    'REQ-006': 'Non-Blacklisting Declaration'
  }
  return titleMap[code] || code
}

const formatResultStatus = (status: string): string => {
  return status.replace(/_/g, ' ')
}

const getResultBadgeClass = (status: string): string => {
  switch (status) {
    case 'SATISFIED': return 'badge-green'
    case 'NOT_SATISFIED': return 'badge-red'
    case 'REVIEW_REQUIRED': return 'badge-warning'
    default: return 'badge-warning'
  }
}

const downloadJson = async () => {
  const payload = await reportApi.generateExportPayload(tenderId.value, bidderId.value, bidderStore.currentBidderName)
  reportApi.downloadJsonReport(payload, `compliance_report_${tenderId.value}.json`)
}

const printReport = () => {
  window.print()
}

const recordDecision = async () => {
  if (!decision.value) {
    decisionError.value = 'Please select a decision'
    return
  }

  loading.value = true
  decisionError.value = ''

  try {
    const result = await decisionApi.recordDecision(
      tenderId.value,
      bidderId.value,
      {
        decision: decision.value as 'PENDING' | 'APPROVED' | 'REJECTED' | 'REQUIRES_REVIEW',
        officer_id: 'OFFICER_001',
        officer_name: 'S. Sharma',
        remarks: officerNotes.value || undefined
      }
    )

    existingDecision.value = result
    alert(`✅ Decision '${result.decision}' recorded successfully! Audit event created.`)
  } catch (e: any) {
    console.error('Failed to record decision:', e)
    if (e.response?.status === 409) {
      decisionError.value = 'Decision already exists for this tender-bidder pair.'
    } else if (e.response?.status === 404) {
      decisionError.value = 'Tender not found. Please verify tender exists.'
    } else if (e.response?.status === 400) {
      decisionError.value = e.response.data.detail || 'Compliance evaluation not found. Run evaluation first.'
    } else {
      decisionError.value = 'Failed to record decision. Please try again.'
    }
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleString()
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
.btn-outline { background: white; border: 1px solid #cbd5e1; color: #334155; }

.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.p-4 { padding: 1.5rem; }
.p-5 { padding: 2rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-4 { margin-top: 1rem; }

.report-header-banner { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0f172a; padding-bottom: 1rem; margin-bottom: 1.5rem; }
.brand-title-box { display: flex; align-items: center; gap: 1rem; }
.gov-seal { font-size: 2.25rem; }
.report-main-title { font-size: 1.35rem; font-weight: 900; color: #0f172a; letter-spacing: -0.01em; }
.report-sub { font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.08em; }

.report-meta-box { font-size: 0.8rem; text-align: right; display: flex; flex-direction: column; gap: 0.2rem; color: #475569; }

.entity-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
.info-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 6px; }
.card-label { font-size: 0.65rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }
.info-title { font-size: 1rem; font-weight: 800; color: #0f172a; margin: 0.2rem 0; }
.info-sub { font-size: 0.75rem; color: #475569; }

.summary-metrics-bar { display: flex; gap: 1.5rem; background: #0f172a; color: white; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; }
.score-block { text-align: center; border-right: 1px solid #334155; padding-right: 1.5rem; }
.score-num { font-size: 2.25rem; font-weight: 900; color: #38bdf8; }
.score-tag { font-size: 0.65rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; }

.metrics-grid { flex: 1; display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center; }
.m-card { display: flex; flex-direction: column; justify-content: center; }
.m-val { font-size: 1.5rem; font-weight: 800; }
.m-lbl { font-size: 0.7rem; color: #94a3b8; margin-top: 2px; }

.report-section { margin-bottom: 1.5rem; }
.border-red-left { border-left: 4px solid #dc2626; padding-left: 1rem; background: #fff5f5; padding: 1rem; border-radius: 0 6px 6px 0; }
.section-heading { font-size: 1.05rem; font-weight: 800; color: #0f172a; margin-bottom: 0.75rem; }

.finding-list { display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.85rem; color: #334155; }

.report-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.report-table th, .report-table td { padding: 0.65rem 0.85rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
.report-table th { background: #f8fafc; font-weight: 700; color: #475569; }

.mandatory-disclaimer-card { background: #eff6ff; border: 1px solid #bfdbfe; padding: 1rem 1.25rem; border-radius: 6px; display: flex; gap: 1rem; align-items: center; color: #1e40af; font-size: 0.85rem; }
.disclaimer-icon { font-size: 1.5rem; }

.officer-decision-card { background: #f8fafc; border: 1px solid #cbd5e1; }
.decision-options { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.decision-radio-card { background: white; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 6px; display: flex; gap: 0.75rem; cursor: pointer; transition: all 0.15s; }
.decision-radio-card.selected { border-color: #2563eb; background: #eff6ff; }
.decision-radio-card strong { font-size: 0.85rem; color: #0f172a; }
.decision-radio-card p { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

.form-label { display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.3rem; color: #475569; }
.form-control { width: 100%; padding: 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; }
.w-full { width: 100%; }

.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.badge-green { background: #dcfce7; color: #15803d; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-warning { background: #fef08a; color: #854d0e; }

.text-green { color: #4ade80; }
.text-red { color: #f87171; }
.text-amber { color: #fbbf24; }
.font-bold { font-weight: 700; }

.existing-decision-alert {
  background: #dcfce7;
  border: 1px solid #86efac;
  padding: 1rem 1.25rem;
  border-radius: 6px;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  color: #15803d;
  font-size: 0.85rem;
}

.error-alert {
  background: #fee2e2;
  border: 1px solid #fecaca;
  padding: 1rem 1.25rem;
  border-radius: 6px;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  color: #991b1b;
  font-size: 0.85rem;
}

.alert-icon {
  font-size: 1.25rem;
}

.remarks-text {
  margin-top: 0.5rem;
  font-style: italic;
  color: #166534;
}

.mt-3 { margin-top: 0.75rem; }

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media print {
  .print-hide { display: none !important; }
  .report-paper { border: none; box-shadow: none; padding: 0; }
  .main-wrapper { margin-left: 0; }
}
</style>

<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Document-to-Document Cross-Checks</h1>
        <p class="page-subtitle">
          Cross-verify consistency of entity names, PAN, address, and registration values across uploaded bidder documents.
        </p>
      </div>

      <button @click="runCrossChecks" class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Running Checks...' : '⚡ Execute Cross-Checks' }}
      </button>
    </div>

    <!-- SUMMARY CARDS -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">TOTAL CROSS-CHECKS</div>
        <div class="kpi-value">{{ checks.length }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">CONSISTENT / VERIFIED</div>
        <div class="kpi-value text-green">{{ verifiedCount }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">MISMATCHES</div>
        <div class="kpi-value text-red">{{ mismatchCount }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">MISSING DOCUMENTS</div>
        <div class="kpi-value text-amber">{{ missingCount }}</div>
      </div>
    </div>

    <!-- CROSS-CHECK MATRIX TABLE -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Document Identity & Field Matching Matrix</h3>
        <span class="badge badge-neutral">Bidder: {{ bidderStore.currentBidderId }}</span>
      </div>

      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Check ID</th>
              <th>Cross-Check Requirement</th>
              <th>Documents Involved</th>
              <th>Status</th>
              <th>Confidence</th>
              <th>Explanation & Trace</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in checks" :key="c.id" class="table-row-hover">
              <td><code>{{ c.check_id }}</code></td>
              <td><strong>{{ c.requirement }}</strong></td>
              <td>
                <div class="docs-cell">
                  <span class="doc-badge">{{ c.document_source_a }}</span>
                  <span v-if="c.document_source_b" class="vs-text">↔</span>
                  <span v-if="c.document_source_b" class="doc-badge">{{ c.document_source_b }}</span>
                </div>
              </td>
              <td>
                <span :class="['result-pill', getPillClass(c.status)]">
                  {{ c.status }}
                </span>
              </td>
              <td>
                <span :class="['conf-text', c.confidence >= 0.8 ? 'text-green' : 'text-amber']">
                  {{ Math.round((c.confidence || 1.0) * 100) }}%
                </span>
              </td>
              <td class="explanation-cell">{{ c.explanation }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { verificationApi, VerificationResultItem } from '../api/verificationApi'
import { useBidderStore } from '../stores/bidder'

const bidderStore = useBidderStore()
const loading = ref(false)
const bidderId = ref(bidderStore.currentBidderId)
const checks = ref<VerificationResultItem[]>([])

onMounted(() => {
  loadCrossChecks()
})

// Re-run when bidder changes
watch(() => bidderStore.currentBidderId, (newId) => {
  bidderId.value = newId
  checks.value = []
  loadCrossChecks()
})

const loadCrossChecks = async () => {
  try {
    const session = await verificationApi.getLatestSession(bidderId.value)
    if (session) {
      const resData = await verificationApi.getSessionResults(session.id)
      checks.value = resData.results.filter((r: any) => r.category === 'CROSS_CHECK' || r.verification_source === 'DOCUMENT_CROSS_CHECK')
    } else {
      await runCrossChecks()
    }
  } catch (e) {
    await runCrossChecks()
  }
}

const runCrossChecks = async () => {
  loading.value = true
  try {
    const res = await verificationApi.runVerification(bidderId.value, 'DOCUMENT_CROSS_CHECK')
    const resData = await verificationApi.getSessionResults(res.session_id)
    checks.value = resData.results.filter((r: any) => r.category === 'CROSS_CHECK' || r.verification_source === 'DOCUMENT_CROSS_CHECK')
  } catch (e) {
    alert('Cross-checks execution failed: ' + e)
  } finally {
    loading.value = false
  }
}

const verifiedCount = computed(() => checks.value.filter(c => c.status === 'VERIFIED').length)
const mismatchCount = computed(() => checks.value.filter(c => c.status === 'MISMATCH').length)
const missingCount = computed(() => checks.value.filter(c => c.status === 'MISSING' || c.status === 'NOT_APPLICABLE').length)

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

.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem 1.25rem; }
.kpi-title { font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }
.kpi-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; margin-top: 0.2rem; }

.text-green { color: #16a34a; font-weight: 700; }
.text-red { color: #dc2626; font-weight: 700; }
.text-amber { color: #d97706; font-weight: 700; }

.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.card-header { padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.card-title { font-size: 0.95rem; font-weight: 700; color: #0f172a; }

.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; }
.table-row-hover:hover { background: #f8fafc; }

.docs-cell { display: flex; align-items: center; gap: 0.4rem; }
.doc-badge { background: #f1f5f9; color: #334155; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.vs-text { font-size: 0.75rem; color: #94a3b8; }

.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.badge-neutral { background: #f1f5f9; color: #475569; }

.result-pill { display: inline-block; padding: 0.25rem 0.65rem; border-radius: 20px; font-weight: 700; font-size: 0.75rem; }
.pill-verified { background: #dcfce7; color: #15803d; }
.pill-mismatch { background: #fee2e2; color: #b91c1c; }
.pill-missing { background: #ffedd5; color: #c2410c; }
.pill-neutral { background: #f1f5f9; color: #475569; }

.explanation-cell { color: #334155; font-size: 0.8rem; }
</style>

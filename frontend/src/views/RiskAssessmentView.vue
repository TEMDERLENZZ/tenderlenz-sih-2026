<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Risk Assessment</h1>
        <p class="page-subtitle">Deterministic risk evaluation based on compliance and verification results</p>
      </div>

      <div class="header-actions">
        <button @click="calculateRisk" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Calculating...' : '🔄 Recalculate Risk' }}
        </button>
      </div>
    </div>

    <!-- LOADING STATE -->
    <div v-if="loading && !riskAssessment" class="loading-card">
      <div class="spinner"></div>
      <p>Calculating risk assessment...</p>
    </div>

    <!-- EMPTY STATE -->
    <div v-if="!loading && !riskAssessment" class="loading-card">
      <span style="font-size:3rem;display:block;margin-bottom:0.75rem">🛡️</span>
      <p style="font-size:1rem;font-weight:700;color:#334155;margin-bottom:0.4rem">No risk assessment available.</p>
      <p style="font-size:0.8rem;color:#94a3b8;margin-bottom:1rem">Run compliance evaluation first, then calculate the risk assessment.</p>
      <button v-if="!currentTenderId" @click="router.push('/tenders-list')" class="btn btn-primary">Upload Tender →</button>
      <button v-else @click="calculateRisk" class="btn btn-primary">Calculate Risk Assessment</button>
    </div>

    <!-- RISK ASSESSMENT DISPLAY -->
    <div v-if="riskAssessment">
      <!-- RISK LEVEL CARD -->
      <div :class="['risk-level-card', `risk-${riskAssessment.risk_level.toLowerCase()}`]">
        <div class="risk-icon">{{ getRiskIcon(riskAssessment.risk_level) }}</div>
        <div class="risk-content">
          <div class="risk-level-label">RISK LEVEL</div>
          <div class="risk-level-value">{{ riskAssessment.risk_level }}</div>
          <div class="risk-score">Score: {{ riskAssessment.risk_score.toFixed(1) }}/100</div>
        </div>
      </div>

      <!-- RISK SUMMARY -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Risk Summary</h3>
          <span class="badge badge-neutral">{{ riskAssessment.factors.length }} Factor(s)</span>
        </div>
        <div class="card-body">
          <p class="summary-text">{{ riskAssessment.summary }}</p>
          <div class="metadata">
            <span class="meta-label">Calculated:</span>
            <span class="meta-value">{{ formatDate(riskAssessment.calculated_at) }}</span>
          </div>
        </div>
      </div>

      <!-- RISK FACTORS TABLE -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Risk Factors Breakdown</h3>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Severity</th>
                <th>Source</th>
                <th>Description</th>
                <th>Points</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(factor, idx) in riskAssessment.factors" :key="idx" :class="getRowClass(factor.severity)">
                <td>
                  <span class="factor-type">{{ formatFactorType(factor.type) }}</span>
                  <div v-if="factor.requirement" class="factor-ref">{{ factor.requirement }}</div>
                  <div v-if="factor.check" class="factor-ref">{{ factor.check }}</div>
                </td>
                <td>
                  <span :class="['severity-badge', `severity-${factor.severity.toLowerCase()}`]">
                    {{ factor.severity }}
                  </span>
                </td>
                <td class="source-cell">{{ factor.source }}</td>
                <td class="description-cell">{{ factor.description }}</td>
                <td class="points-cell">+{{ factor.points }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- RECOMMENDATION CARD -->
      <div :class="['recommendation-card', `rec-${riskAssessment.risk_level.toLowerCase()}`]">
        <div class="rec-icon">💡</div>
        <div class="rec-content">
          <h4 class="rec-title">Recommendation</h4>
          <p class="rec-text">{{ getRecommendation(riskAssessment.risk_level) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { riskApi, BidderRiskAssessment } from '../api/riskApi'
import { useBidderStore } from '../stores/bidder'
import axios from 'axios'

const router = useRouter()
const bidderStore = useBidderStore()
const currentTenderId = ref('')
const bidderId = ref(bidderStore.currentBidderId)
const riskAssessment = ref<BidderRiskAssessment | null>(null)
const loading = ref(false)

onMounted(async () => {
  await loadActiveTender()
  // Only try to load if we have both tender and bidder
  if (currentTenderId.value && bidderId.value) {
    await loadRisk()
  }
})

const loadActiveTender = async () => {
  try {
    const res = await axios.get('/api/tenders/list')
    const tenders = res.data || []
    currentTenderId.value = tenders.length > 0 ? tenders[0].tender_id : ''
  } catch (e) {
    currentTenderId.value = ''
  }
}

const loadRisk = async () => {
  if (!currentTenderId.value || !bidderId.value) return
  loading.value = true
  try {
    riskAssessment.value = await riskApi.getRisk(currentTenderId.value, bidderId.value)
  } catch (e) {
    console.error('Failed to load risk assessment:', e)
    riskAssessment.value = null
  } finally {
    loading.value = false
  }
}

const calculateRisk = async () => {
  if (!currentTenderId.value || !bidderId.value) {
    alert('Please ensure a tender and bidder are available before calculating risk.')
    return
  }
  loading.value = true
  try {
    riskAssessment.value = await riskApi.assessRisk(currentTenderId.value, bidderId.value)
  } catch (e) {
    alert('Failed to calculate risk: ' + e)
  } finally {
    loading.value = false
  }
}

const getRiskIcon = (level: string): string => {
  switch (level) {
    case 'HIGH': return '🚨'
    case 'MEDIUM': return '⚠️'
    case 'LOW': return '✅'
    default: return 'ℹ️'
  }
}

const formatFactorType = (type: string): string => {
  return type.replace(/_/g, ' ')
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleString()
}

const getRowClass = (severity: string): string => {
  switch (severity) {
    case 'HIGH': return 'row-high'
    case 'MEDIUM': return 'row-medium'
    case 'LOW': return 'row-low'
    default: return ''
  }
}

const getRecommendation = (level: string): string => {
  switch (level) {
    case 'HIGH':
      return 'HIGH RISK DETECTED: Procurement officer review is strongly recommended before proceeding. Critical compliance failures or verification mismatches require immediate attention.'
    case 'MEDIUM':
      return 'MEDIUM RISK: Manual verification recommended for flagged items. Some non-compliance or verification issues require officer review before final decision.'
    case 'LOW':
      return 'LOW RISK: Requirements generally satisfied. Standard procurement procedures apply. Officer may proceed with routine approval process.'
    default:
      return 'Risk assessment not available.'
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
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.loading-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
}

.spinner {
  margin: 0 auto 1rem;
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.risk-level-card {
  background: white;
  border: 2px solid;
  border-radius: 12px;
  padding: 2rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.risk-level-card.risk-high {
  border-color: #dc2626;
  background: linear-gradient(135deg, #fff5f5 0%, #fee2e2 100%);
}

.risk-level-card.risk-medium {
  border-color: #d97706;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.risk-level-card.risk-low {
  border-color: #16a34a;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.risk-icon {
  font-size: 3rem;
}

.risk-level-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.05em;
}

.risk-level-value {
  font-size: 2rem;
  font-weight: 900;
  color: #0f172a;
  margin-top: 0.25rem;
}

.risk-score {
  font-size: 1rem;
  font-weight: 600;
  color: #475569;
  margin-top: 0.5rem;
}

.card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.card-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8fafc;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
}

.card-body {
  padding: 1.25rem;
}

.summary-text {
  color: #334155;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.metadata {
  font-size: 0.8rem;
  color: #64748b;
}

.meta-label {
  font-weight: 600;
  margin-right: 0.5rem;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.data-table th,
.data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.data-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}

.row-high {
  background: #fff5f5;
}

.row-medium {
  background: #fffbeb;
}

.row-low {
  background: #f0fdf4;
}

.factor-type {
  font-weight: 600;
  color: #0f172a;
}

.factor-ref {
  font-size: 0.75rem;
  color: #64748b;
  font-family: monospace;
  margin-top: 2px;
}

.severity-badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.75rem;
}

.severity-badge.severity-high {
  background: #fee2e2;
  color: #991b1b;
}

.severity-badge.severity-medium {
  background: #fef3c7;
  color: #92400e;
}

.severity-badge.severity-low {
  background: #dcfce7;
  color: #15803d;
}

.source-cell {
  font-size: 0.8rem;
  color: #64748b;
}

.description-cell {
  color: #334155;
  font-size: 0.8rem;
}

.points-cell {
  font-weight: 700;
  color: #dc2626;
  text-align: right;
}

.recommendation-card {
  border: 2px solid;
  border-radius: 8px;
  padding: 1.5rem;
  display: flex;
  gap: 1rem;
}

.recommendation-card.rec-high {
  border-color: #dc2626;
  background: #fef2f2;
}

.recommendation-card.rec-medium {
  border-color: #d97706;
  background: #fffbeb;
}

.recommendation-card.rec-low {
  border-color: #16a34a;
  background: #f0fdf4;
}

.rec-icon {
  font-size: 1.5rem;
}

.rec-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.5rem;
}

.rec-text {
  color: #334155;
  font-size: 0.85rem;
  line-height: 1.5;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
}

.badge-neutral {
  background: #f1f5f9;
  color: #475569;
}
</style>

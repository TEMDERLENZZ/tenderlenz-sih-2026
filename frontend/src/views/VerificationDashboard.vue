<template>
  <div class="verification-dashboard">
    <!-- Header with Sandbox Warning -->
    <div class="header">
      <h1>Phase 2: Verification Results</h1>
      <p class="bidder-id">Bidder: {{ bidderId }}</p>

      <div v-if="isSandboxMode" class="sandbox-warning">
        ⚠️ Sandbox Demonstration — External verification uses demonstration data, not live government sources.
        <p v-if="sandboxWarning" class="warning-text">{{ sandboxWarning }}</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Running verification checks...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-message">
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- Verification Summary -->
    <div v-if="summary && !loading" class="summary-cards">
      <div class="card total">
        <div class="card-value">{{ summary.total }}</div>
        <div class="card-label">Total Checks</div>
      </div>
      <div class="card verified">
        <div class="card-value">{{ summary.verified }}</div>
        <div class="card-label">Verified</div>
      </div>
      <div class="card mismatch">
        <div class="card-value">{{ summary.mismatch }}</div>
        <div class="card-label">Mismatches</div>
      </div>
      <div class="card missing">
        <div class="card-value">{{ summary.missing }}</div>
        <div class="card-label">Missing</div>
      </div>
      <div class="card not-applicable">
        <div class="card-value">{{ summary.notApplicable }}</div>
        <div class="card-label">Not Applicable</div>
      </div>
    </div>

    <!-- Verification Results Tabs -->
    <div v-if="verificationResults.length > 0" class="results-section">
      <div class="tabs">
        <button
          @click="activeTab = 'cross_check'"
          :class="{ active: activeTab === 'cross_check' }"
        >
          Document Cross-Checks
        </button>
        <button
          @click="activeTab = 'external'"
          :class="{ active: activeTab === 'external' }"
        >
          External Verification
        </button>
        <button
          @click="activeTab = 'all'"
          :class="{ active: activeTab === 'all' }"
        >
          All Results
        </button>
      </div>

      <div class="tab-content">
        <!-- Cross-Check Results -->
        <div v-if="activeTab === 'cross_check'" class="results-table">
          <h3>Document-to-Document Cross-Checks</h3>
          <table>
            <thead>
              <tr>
                <th>Check ID</th>
                <th>Requirement</th>
                <th>Documents</th>
                <th>Status</th>
                <th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="result in crossCheckResults" :key="result.id" :class="getStatusClass(result.status)">
                <td>{{ result.check_id }}</td>
                <td>{{ result.requirement }}</td>
                <td>
                  {{ result.document_source_a }}
                  <span v-if="result.document_source_b"> vs {{ result.document_source_b }}</span>
                </td>
                <td>
                  <span class="status-badge" :class="result.status.toLowerCase()">
                    {{ formatStatus(result.status) }}
                  </span>
                </td>
                <td>{{ result.explanation }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- External Verification Results -->
        <div v-if="activeTab === 'external'" class="results-table">
          <h3>External Source Verification</h3>
          <table>
            <thead>
              <tr>
                <th>Check ID</th>
                <th>Requirement</th>
                <th>Source</th>
                <th>Mode</th>
                <th>Status</th>
                <th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="result in externalResults" :key="result.id" :class="getStatusClass(result.status)">
                <td>{{ result.check_id }}</td>
                <td>{{ result.requirement }}</td>
                <td>{{ result.verification_source }}</td>
                <td>
                  <span class="mode-badge" :class="result.source_mode.toLowerCase()">
                    {{ result.source_mode }}
                  </span>
                </td>
                <td>
                  <span class="status-badge" :class="result.status.toLowerCase()">
                    {{ formatStatus(result.status) }}
                  </span>
                </td>
                <td>{{ result.explanation }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- All Results -->
        <div v-if="activeTab === 'all'" class="results-table">
          <h3>All Verification Results</h3>
          <table>
            <thead>
              <tr>
                <th>Check ID</th>
                <th>Category</th>
                <th>Requirement</th>
                <th>Status</th>
                <th>Confidence</th>
                <th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="result in verificationResults" :key="result.id" :class="getStatusClass(result.status)">
                <td>{{ result.check_id }}</td>
                <td>{{ result.category }}</td>
                <td>{{ result.requirement }}</td>
                <td>
                  <span class="status-badge" :class="result.status.toLowerCase()">
                    {{ formatStatus(result.status) }}
                  </span>
                </td>
                <td>{{ formatConfidence(result.confidence) }}</td>
                <td>{{ result.explanation }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Footer Disclaimer -->
    <div class="footer-disclaimer">
      <p><strong>AI Verification Result</strong> - Final decision remains with the Procurement Officer</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVerificationStore } from '../stores/verification'
import { useBidderStore } from '../stores/bidder'

const route = useRoute()
const router = useRouter()
const verificationStore = useVerificationStore()
const bidderStore = useBidderStore()

// Prefer route param (for direct /verification/:id links), else use global store
const bidderId = ref(
  (route.params.bidderId as string) || bidderStore.currentBidderId
)
const activeTab = ref('cross_check')

const loading = computed(() => verificationStore.loading)
const error = computed(() => verificationStore.error)
const summary = computed(() => verificationStore.verificationSummary)
const verificationResults = computed(() => verificationStore.verificationResults)
const isSandboxMode = computed(() => verificationStore.isSandboxMode)
const sandboxWarning = computed(() => verificationStore.sandboxWarning)

const crossCheckResults = computed(() =>
  verificationResults.value.filter(r => r.category === 'CROSS_CHECK' || r.verification_source === 'DOCUMENT_CROSS_CHECK')
)

const externalResults = computed(() =>
  verificationResults.value.filter(r => r.category === 'EXTERNAL' || r.verification_source.includes('PROVIDER'))
)

onMounted(async () => {
  await verificationStore.fetchProvidersStatus()

  if (route.query.run === 'true') {
    await verificationStore.runVerification(bidderId.value)
  } else {
    try {
      await verificationStore.fetchLatestSession(bidderId.value)
    } catch (err) {
      // No existing verification, that's okay
    }
  }
})

// Re-load when bidder switches globally
watch(() => bidderStore.currentBidderId, async (newId) => {
  bidderId.value = newId
  verificationStore.clearVerificationData()
  try {
    await verificationStore.fetchLatestSession(newId)
  } catch {
    // New bidder has no verification yet — that's fine
  }
})

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ')
}

function formatConfidence(confidence: number | null): string {
  if (confidence === null || confidence === undefined) return 'N/A'
  return `${(confidence * 100).toFixed(0)}%`
}

function getStatusClass(status: string): string {
  return `status-${status.toLowerCase()}`
}

function goBack() {
  router.push('/')
}
</script>


<style scoped>
.verification-dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  margin-bottom: 30px;
}

.header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.bidder-id {
  color: #7f8c8d;
  font-size: 16px;
  margin-bottom: 15px;
}

.sandbox-warning {
  background: #fff3cd;
  border: 2px solid #ffc107;
  border-radius: 8px;
  padding: 15px;
  margin: 20px 0;
  font-weight: bold;
  color: #856404;
}

.warning-text {
  font-weight: normal;
  font-size: 14px;
  margin-top: 8px;
}

.loading {
  text-align: center;
  padding: 40px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  padding: 15px;
  margin: 20px 0;
  color: #721c24;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  text-align: center;
}

.card-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
}

.card-label {
  font-size: 14px;
  color: #7f8c8d;
  text-transform: uppercase;
}

.card.total .card-value { color: #3498db; }
.card.verified .card-value { color: #27ae60; }
.card.mismatch .card-value { color: #e74c3c; }
.card.missing .card-value { color: #95a5a6; }
.card.not-applicable .card-value { color: #bdc3c7; }

.results-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.tabs {
  display: flex;
  border-bottom: 2px solid #ecf0f1;
}

.tabs button {
  flex: 1;
  padding: 15px;
  border: none;
  background: white;
  cursor: pointer;
  font-size: 16px;
  color: #7f8c8d;
  transition: all 0.3s;
}

.tabs button:hover {
  background: #ecf0f1;
}

.tabs button.active {
  color: #3498db;
  border-bottom: 3px solid #3498db;
  font-weight: bold;
}

.tab-content {
  padding: 20px;
}

.results-table h3 {
  margin-bottom: 20px;
  color: #2c3e50;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #ecf0f1;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ecf0f1;
}

th {
  font-weight: bold;
  color: #2c3e50;
}

.status-badge, .mode-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.status-badge.verified {
  background: #d4edda;
  color: #155724;
}

.status-badge.mismatch {
  background: #f8d7da;
  color: #721c24;
}

.status-badge.missing, .status-badge.not_verified {
  background: #fff3cd;
  color: #856404;
}

.status-badge.not_applicable {
  background: #e2e3e5;
  color: #383d41;
}

.mode-badge.sandbox {
  background: #fff3cd;
  color: #856404;
}

.mode-badge.live {
  background: #d4edda;
  color: #155724;
}

.footer-disclaimer {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
  color: #495057;
}

.footer-disclaimer strong {
  color: #2c3e50;
}
</style>

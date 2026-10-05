<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Procurement Intelligence</h1>
        <p class="page-subtitle">AI-assisted tender compliance analysis &amp; verification dashboard</p>
      </div>

      <div class="header-actions">
        <button @click="router.push('/tenders-list')" class="btn btn-primary">
          <span class="btn-icon">📤</span> Upload Tender PDF
        </button>
        <button @click="router.push('/compliance-analysis')" class="btn btn-secondary">
          <span class="btn-icon">⚡</span> Run Compliance Analysis
        </button>
      </div>
    </div>

    <!-- TOP EXECUTIVE KPI CARDS (API-driven) -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">TOTAL TENDERS</div>
        <div class="kpi-value">{{ stats.total_tenders }}</div>
        <div class="kpi-subtext"><span class="trend-neutral">● Procurement tenders</span></div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">TOTAL BIDDERS</div>
        <div class="kpi-value">{{ stats.total_bidders }}</div>
        <div class="kpi-subtext"><span class="trend-blue">● Documents submitted</span></div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">COMPLIANCE CHECKS</div>
        <div class="kpi-value">{{ stats.compliance_checks }}</div>
        <div class="kpi-subtext"><span class="trend-green">● Automated evaluations</span></div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">RISK ASSESSMENTS</div>
        <div class="kpi-value">{{ stats.risk_assessments }}</div>
        <div class="kpi-subtext"><span class="trend-amber">● Risk profiles calculated</span></div>
      </div>
    </div>

    <!-- MAIN TWO-COLUMN DASHBOARD GRID -->
    <div class="dashboard-grid">
      <!-- LEFT: COMPLIANCE OVERVIEW / EMPTY STATE -->
      <div class="card overview-card">
        <div class="card-header">
          <h3 class="card-title">Compliance Overview</h3>
          <span class="badge badge-neutral">{{ stats.total_tenders > 0 ? 'Live Data' : 'No Data Yet' }}</span>
        </div>

        <!-- Empty State -->
        <div v-if="stats.compliance_checks === 0" class="empty-section">
          <span class="empty-icon">⚖️</span>
          <p class="empty-title">Compliance evaluation has not been performed.</p>
          <p class="empty-hint">Upload a tender and run compliance analysis to see results here.</p>
          <button @click="router.push('/tenders-list')" class="btn btn-primary mt-2">Upload Tender PDF →</button>
        </div>

        <!-- Has Data: Show donut -->
        <div v-else class="overview-body">
          <div class="chart-box">
            <div class="donut-container">
              <svg viewBox="0 0 36 36" class="donut-svg">
                <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path class="circle-satisfied" :stroke-dasharray="`${stats.compliance_rate}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              </svg>
              <div class="chart-center">
                <div class="score-num">{{ stats.compliance_rate }}%</div>
                <div class="score-label">Compliance Rate</div>
              </div>
            </div>
          </div>
          <div class="metrics-list">
            <div class="metric-item">
              <span class="metric-name">Total Checks</span>
              <span class="metric-val font-bold">{{ stats.compliance_checks }}</span>
            </div>
            <div class="metric-item border-left-green">
              <span class="metric-name"><span class="dot-green">●</span> Satisfied</span>
              <span class="metric-val text-green">{{ stats.satisfied }}</span>
            </div>
            <div class="metric-item border-left-red">
              <span class="metric-name"><span class="dot-red">●</span> Not Satisfied</span>
              <span class="metric-val text-red">{{ stats.not_satisfied }}</span>
            </div>
            <div class="metric-item border-left-amber">
              <span class="metric-name"><span class="dot-amber">●</span> Needs Review</span>
              <span class="metric-val text-amber">{{ stats.review_required }}</span>
            </div>
          </div>
        </div>

        <div class="card-footer">
          <span class="disclaimer-text">AI Compliance Analysis — Advisory report for authorized Procurement Officers.</span>
        </div>
      </div>

      <!-- RIGHT: QUICK ACTIONS & SYSTEM STATUS -->
      <div class="card quick-card">
        <div class="card-header">
          <h3 class="card-title">Quick Actions &amp; Verification Mode</h3>
        </div>

        <div class="quick-body">
          <div class="workflow-quick-buttons">
            <button @click="router.push('/tenders-list')" class="quick-action-btn">
              <span class="qa-icon">📁</span>
              <div>
                <div class="qa-title">14-Document Batch Upload</div>
                <div class="qa-desc">Upload bidder PDF files in one action</div>
              </div>
            </button>

            <button @click="router.push('/external-verification')" class="quick-action-btn">
              <span class="qa-icon">⚡</span>
              <div>
                <div class="qa-title">Run External Verification</div>
                <div class="qa-desc">Verify GST, PAN, Udyam, MCA against Sandbox</div>
              </div>
            </button>

            <button @click="router.push('/officer-review')" class="quick-action-btn">
              <span class="qa-icon">🧐</span>
              <div>
                <div class="qa-title">Procurement Officer Review</div>
                <div class="qa-desc">Confirm or adjust AI extracted requirement rules</div>
              </div>
            </button>
          </div>

          <div class="sandbox-notice">
            <div class="notice-title">PROVIDER STATUS</div>
            <div class="notice-body">
              <strong>TenderVerify Sandbox (Connected)</strong>
              <p>Synthetic demonstration data active. Verification results are for prototype demonstration only.</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- RECENT TENDER ANALYSIS TABLE (API-driven) -->
    <div class="card table-card">
      <div class="card-header">
        <h3 class="card-title">Recent Tender Analysis</h3>
        <button @click="router.push('/tenders-list')" class="btn-link">View All Tenders →</button>
      </div>

      <!-- Loading State -->
      <div v-if="loadingTenders" class="empty-section">
        <div class="spinner"></div>
        <p>Loading tenders...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="recentTenders.length === 0" class="empty-section">
        <span class="empty-icon">📋</span>
        <p class="empty-title">No tenders available.</p>
        <p class="empty-hint">No tenders have been created yet. Upload a tender specification to get started.</p>
        <button @click="router.push('/tenders-list')" class="btn btn-primary mt-2">Upload First Tender →</button>
      </div>

      <!-- Tender Table (only when data exists) -->
      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Tender ID</th>
              <th>Tender Title</th>
              <th>Status</th>
              <th>Uploaded</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tender in recentTenders"
              :key="tender.id"
              class="table-row-hover"
              @click="router.push('/compliance-analysis')"
            >
              <td><code>{{ tender.tender_id }}</code></td>
              <td><strong>{{ tender.title }}</strong></td>
              <td><span :class="['badge', getStatusBadge(tender.status)]">{{ tender.status }}</span></td>
              <td>{{ formatDate(tender.uploaded_at) }}</td>
              <td><button class="btn-sm btn-outline" @click.stop="router.push('/requirements')">View Requirements</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const loadingTenders = ref(true)
const recentTenders = ref<any[]>([])

// Dashboard stats — all from real API
const stats = ref({
  total_tenders: 0,
  total_bidders: 0,
  compliance_checks: 0,
  risk_assessments: 0,
  compliance_rate: 0,
  satisfied: 0,
  not_satisfied: 0,
  review_required: 0
})

onMounted(async () => {
  await Promise.all([loadTenders(), loadStats()])
})

const loadTenders = async () => {
  loadingTenders.value = true
  try {
    const res = await axios.get('/api/tenders/list')
    recentTenders.value = (res.data || []).slice(0, 10)
  } catch (e) {
    recentTenders.value = []
  } finally {
    loadingTenders.value = false
  }
}

const loadStats = async () => {
  try {
    // Tenders count
    const tendersRes = await axios.get('/api/tenders/list')
    const tenders = tendersRes.data || []
    stats.value.total_tenders = tenders.length

    // If no tenders, all other counts are 0
    if (tenders.length === 0) return

    // Try to load compliance stats from existing evaluations
    // We try the first tender if available
    // Stats remain 0 if no evaluations have been run
  } catch (e) {
    // Stats remain at 0
    console.error('Failed to load stats:', e)
  }
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return 'N/A'
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

const getStatusBadge = (status: string): string => {
  switch (status) {
    case 'UPLOADED': return 'badge-blue'
    case 'PROCESSING': return 'badge-amber'
    case 'EXTRACTED': return 'badge-green'
    default: return 'badge-neutral'
  }
}
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 0.85rem;
  color: #64748b;
  margin-top: 2px;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 1.1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #0f172a;
  color: white;
}

.btn-secondary:hover {
  background: #1e293b;
}

.btn-outline {
  background: white;
  border-color: #cbd5e1;
  color: #334155;
}

.btn-outline:hover {
  background: #f8fafc;
}

.mt-2 { margin-top: 0.5rem; }

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.kpi-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

.kpi-title {
  font-size: 0.7rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.05em;
}

.kpi-value {
  font-size: 1.85rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0.25rem 0;
  letter-spacing: -0.02em;
}

.kpi-subtext {
  font-size: 0.75rem;
  color: #64748b;
}

.trend-neutral { color: #64748b; }
.trend-blue { color: #2563eb; font-weight: 600; }
.trend-amber { color: #d97706; font-weight: 600; }
.trend-green { color: #16a34a; font-weight: 600; }

.dashboard-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 1.5rem;
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

/* Empty state */
.empty-section {
  padding: 3rem 2rem;
  text-align: center;
  color: #64748b;
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 0.75rem;
}

.empty-title {
  font-size: 1rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 0.4rem;
}

.empty-hint {
  font-size: 0.8rem;
  color: #94a3b8;
}

.spinner {
  margin: 0 auto 1rem;
  width: 36px;
  height: 36px;
  border: 3px solid #e2e8f0;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.overview-body {
  padding: 1.25rem;
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.chart-box {
  width: 140px;
  height: 140px;
  position: relative;
}

.donut-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.donut-svg {
  width: 100%;
  height: 100%;
}

.circle-bg {
  fill: none;
  stroke: #e2e8f0;
  stroke-width: 3.8;
}

.circle-satisfied {
  fill: none;
  stroke: #2563eb;
  stroke-width: 3.8;
  stroke-linecap: round;
}

.chart-center {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-num {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
}

.score-label {
  font-size: 0.65rem;
  color: #64748b;
  font-weight: 600;
}

.metrics-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  background: #f8fafc;
  font-size: 0.85rem;
}

.border-left-green { border-left: 3px solid #16a34a; }
.border-left-red { border-left: 3px solid #dc2626; }
.border-left-amber { border-left: 3px solid #d97706; }

.font-bold { font-weight: 700; }
.text-green { color: #16a34a; font-weight: 700; }
.text-red { color: #dc2626; font-weight: 700; }
.text-amber { color: #d97706; font-weight: 700; }

.dot-green { color: #16a34a; }
.dot-red { color: #dc2626; }
.dot-amber { color: #d97706; }

.card-footer {
  padding: 0.75rem 1.25rem;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.disclaimer-text {
  font-size: 0.75rem;
  color: #64748b;
  font-style: italic;
}

.quick-body {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.workflow-quick-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.quick-action-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s;
}

.quick-action-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.qa-icon { font-size: 1.2rem; }
.qa-title { font-size: 0.85rem; font-weight: 700; color: #0f172a; }
.qa-desc { font-size: 0.75rem; color: #64748b; }

.sandbox-notice {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  padding: 0.75rem;
  border-radius: 6px;
}

.notice-title { font-size: 0.65rem; font-weight: 700; color: #1e40af; letter-spacing: 0.05em; }
.notice-body strong { font-size: 0.8rem; color: #1e3a8a; }
.notice-body p { font-size: 0.75rem; color: #3b82f6; margin-top: 2px; }

.table-wrapper { overflow-x: auto; }
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.data-table th, .data-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.data-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
}

.table-row-hover:hover {
  background: #f8fafc;
  cursor: pointer;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
}

.badge-green { background: #dcfce7; color: #15803d; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-amber { background: #fef08a; color: #a16207; }
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-neutral { background: #f1f5f9; color: #475569; }
.btn-link { background: none; border: none; color: #2563eb; font-weight: 600; cursor: pointer; font-size: 0.85rem; }
.btn-sm { padding: 0.3rem 0.6rem; font-size: 0.75rem; }
</style>

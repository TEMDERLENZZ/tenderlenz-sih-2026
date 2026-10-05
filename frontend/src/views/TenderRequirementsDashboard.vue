<template>
  <div class="tender-dashboard">
    <!-- HERO HEADER -->
    <div class="hero-section">
      <div class="hero-content">
        <span class="hero-badge">PHASE 6 ENGINE</span>
        <h2>⚖️ Tender Requirement & Compliance Engine</h2>
        <p class="hero-subtitle">
          Extract tender requirements, review eligibility rules, match against verified bidder documents, and generate evidence-backed compliance analysis.
        </p>
      </div>
    </div>

    <!-- MAIN STEPS WORKFLOW -->
    <div class="workflow-tabs">
      <button 
        :class="['step-btn', { active: activeStep === 1 }]" 
        @click="activeStep = 1"
      >
        <span class="step-num">1</span>
        Tender Upload & Requirements
      </button>

      <button 
        :class="['step-btn', { active: activeStep === 2 }]" 
        @click="activeStep = 2"
        :disabled="!currentTenderId"
      >
        <span class="step-num">2</span>
        Procurement Officer Review ({{ requirements.length }})
      </button>

      <button 
        :class="['step-btn', { active: activeStep === 3 }]" 
        @click="activeStep = 3"
        :disabled="!currentTenderId || requirements.length === 0"
      >
        <span class="step-num">3</span>
        Bidder Compliance Evaluation
      </button>
    </div>

    <!-- STEP 1: TENDER UPLOAD & EXTRACTION -->
    <div v-if="activeStep === 1" class="step-panel">
      <div class="panel-header">
        <h3>📄 1. Tender Document Upload & Requirement Extraction</h3>
        <p class="section-desc">Upload a tender specification PDF/Image, or load the pre-configured Demo Tender.</p>
      </div>

      <div class="upload-grid">
        <!-- Quick Load Demo Tender Card -->
        <div class="card demo-card">
          <div class="card-badge">RECOMMENDED FOR DEMO</div>
          <h4>⚡ Load Canonical Demo Tender</h4>
          <p>Pre-loaded with minimum turnover (₹5 Cr), GST active, BIS mandatory, OEM authorization, local content (≥50%), and non-blacklisting conditions.</p>
          <button @click="loadDemoTender" class="btn-primary-lg" :disabled="loading">
            {{ loading ? 'Loading Tender...' : '⚡ Load & Extract Demo Tender' }}
          </button>
        </div>

        <!-- Custom Upload Card -->
        <div class="card upload-card">
          <h4>📤 Upload Custom Tender PDF</h4>
          <p>Extract digital text & OCR requirements dynamically from any custom tender specification.</p>
          
          <div class="form-group">
            <label>Tender Title (Optional):</label>
            <input v-model="tenderTitleInput" type="text" placeholder="e.g. Procurement of Networking Equipment 2026" class="form-control" />
          </div>

          <div class="form-group">
            <label>Select Tender PDF / Image File:</label>
            <input type="file" ref="tenderFileInput" accept=".pdf,.jpg,.jpeg,.png" @change="onTenderFileSelect" class="file-control" />
          </div>

          <button @click="uploadTenderFile" class="btn-secondary-lg" :disabled="!selectedTenderFile || loading">
            {{ loading ? 'Processing Tender...' : '📤 Upload & Extract Requirements' }}
          </button>
        </div>
      </div>

      <!-- Currently Selected Tender Banner -->
      <div v-if="currentTender" class="active-tender-banner">
        <div class="banner-left">
          <span class="tender-icon">📋</span>
          <div>
            <strong>Active Tender: {{ currentTender.title }}</strong>
            <div class="meta">ID: <code>{{ currentTender.tender_id }}</code> | Status: <span class="badge-active">{{ currentTender.status }}</span></div>
          </div>
        </div>
        <button @click="activeStep = 2" class="btn-next">
          Proceed to Officer Review →
        </button>
      </div>
    </div>

    <!-- STEP 2: PROCUREMENT OFFICER REVIEW -->
    <div v-if="activeStep === 2" class="step-panel">
      <div class="panel-header flex-between">
        <div>
          <h3>🧐 2. Procurement Officer Review & Requirement Confirmation</h3>
          <p class="section-desc">Review AI-extracted requirements. Edit required values or add custom rules before running evaluation to prevent OCR mistakes.</p>
        </div>
        <div class="action-buttons">
          <button @click="openAddModal" class="btn-outline">➕ Add Custom Rule</button>
          <button @click="extractRequirements" class="btn-secondary-sm" :disabled="loading">🔄 Re-Extract</button>
          <button @click="activeStep = 3" class="btn-success">✅ Confirm Requirements & Evaluate Bidder →</button>
        </div>
      </div>

      <!-- Requirements Table -->
      <div class="table-container">
        <table class="custom-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Category</th>
              <th>Requirement Title & Description</th>
              <th>Type</th>
              <th>Mandatory</th>
              <th>Required Criteria</th>
              <th>Source Snippet</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="req in requirements" :key="req.id">
              <td><code>{{ req.requirement_code }}</code></td>
              <td><span class="category-badge">{{ req.category }}</span></td>
              <td>
                <div class="req-title">{{ req.title }}</div>
                <div class="req-desc">{{ req.description }}</div>
              </td>
              <td><span class="type-badge">{{ req.requirement_type }}</span></td>
              <td>
                <span :class="['pill', req.mandatory ? 'pill-mandatory' : 'pill-optional']">
                  {{ req.mandatory ? 'YES' : 'NO' }}
                </span>
              </td>
              <td>
                <span class="criteria-val">{{ formatCriteria(req) }}</span>
              </td>
              <td class="evidence-snippet">
                <span :title="req.evidence_text">"{{ req.evidence_text || '-' }}"</span>
              </td>
              <td class="action-cells">
                <button @click="openEditModal(req)" class="btn-icon" title="Edit Requirement">✏️</button>
                <button @click="deleteRequirement(req.id)" class="btn-icon danger" title="Delete Requirement">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- STEP 3: BIDDER COMPLIANCE EVALUATION -->
    <div v-if="activeStep === 3" class="step-panel">
      <div class="panel-header">
        <h3>📊 3. Requirement-by-Requirement Compliance Analysis</h3>
        <p class="section-desc">Evaluate bidder data against verified tender requirements.</p>
      </div>

      <!-- Bidder Selector Control -->
      <div class="bidder-selector-card">
        <div class="selector-inputs">
          <label for="bidder-id-select">Bidder Identifier:</label>
          <input 
            id="bidder-id-select"
            v-model="bidderId" 
            type="text" 
            placeholder="e.g. BIDDER_001" 
            class="bidder-input"
          />
          <button @click="runEvaluation" class="btn-eval-primary" :disabled="evaluating">
            {{ evaluating ? 'Evaluating Bidder...' : '⚡ Run Compliance Analysis' }}
          </button>
        </div>
        <p class="selector-hint">Uses Phase 1 extracted fields, Phase 2 Sandbox verification, and document cross-checks.</p>
      </div>

      <!-- COMPLIANCE SUMMARY METRICS -->
      <div v-if="summary" class="summary-cards-grid">
        <div class="metric-card score-card">
          <div class="score-val">{{ summary.compliance_percentage }}%</div>
          <div class="metric-label">Compliance Score</div>
        </div>

        <div class="metric-card total-card">
          <div class="metric-num">{{ summary.total_requirements }}</div>
          <div class="metric-label">Total Requirements</div>
        </div>

        <div class="metric-card satisfied-card">
          <div class="metric-num">{{ summary.satisfied }}</div>
          <div class="metric-label">Satisfied</div>
        </div>

        <div class="metric-card unsatisfied-card">
          <div class="metric-num">{{ summary.not_satisfied }}</div>
          <div class="metric-label">Not Satisfied</div>
        </div>

        <div class="metric-card missing-card">
          <div class="metric-num">{{ summary.missing }}</div>
          <div class="metric-label">Missing</div>
        </div>

        <div class="metric-card review-card">
          <div class="metric-num">{{ summary.review_required }}</div>
          <div class="metric-label">Review Required</div>
        </div>
      </div>

      <!-- DETAILED COMPLIANCE RESULTS TABLE -->
      <div v-if="summary && summary.results.length > 0" class="results-table-wrapper">
        <table class="compliance-results-table">
          <thead>
            <tr>
              <th>Code</th>
              <th>Requirement</th>
              <th>Required Value</th>
              <th>Bidder Value</th>
              <th>Compliance Result</th>
              <th>Evidence & Source Document</th>
              <th>Explanation</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="res in summary.results" 
              :key="res.id"
              :class="getResultRowClass(res.result)"
            >
              <td><code>{{ res.requirement_code }}</code></td>
              <td>
                <strong>{{ getReqTitle(res.requirement_code) }}</strong>
              </td>
              <td><span class="required-val">{{ res.required_value || '-' }}</span></td>
              <td><span class="actual-val">{{ res.actual_value || '-' }}</span></td>
              <td>
                <span :class="['result-pill', getPillClass(res.result)]">
                  {{ getResultIcon(res.result) }} {{ formatResultStatus(res.result) }}
                </span>
              </td>
              <td class="evidence-col">
                <div class="doc-title" v-if="res.evidence?.document">
                  📁 {{ res.evidence.document }}
                  <span class="page-tag" v-if="res.evidence.page">p.{{ res.evidence.page }}</span>
                </div>
                <div class="snippet-text" v-if="res.evidence?.text">
                  "{{ res.evidence.text }}"
                </div>
              </td>
              <td class="explanation-col">{{ res.explanation }}</td>
            </tr>
          </tbody>
        </table>

        <!-- MANDATORY SAFETY DISCLAIMER -->
        <div class="mandatory-disclaimer-box">
          <span class="disclaimer-icon">⚖️</span>
          <div class="disclaimer-content">
            <strong>AI DECISION-SUPPORT SYSTEM DISCLAIMER:</strong>
            <p>{{ summary.disclaimer }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- EDIT REQUIREMENT MODAL -->
    <div v-if="showEditModal" class="modal-backdrop">
      <div class="modal-card">
        <h3>✏️ Edit Requirement Details</h3>
        <form @submit.prevent="saveRequirementEdit">
          <div class="form-group">
            <label>Title:</label>
            <input v-model="editForm.title" type="text" class="form-control" required />
          </div>

          <div class="form-group">
            <label>Category:</label>
            <input v-model="editForm.category" type="text" class="form-control" required />
          </div>

          <div class="form-group">
            <label>Requirement Type:</label>
            <select v-model="editForm.requirement_type" class="form-control">
              <option value="NUMERIC">NUMERIC</option>
              <option value="DOCUMENT_REQUIRED">DOCUMENT_REQUIRED</option>
              <option value="PERCENTAGE">PERCENTAGE</option>
              <option value="STATUS_CHECK">STATUS_CHECK</option>
              <option value="IDENTITY_MATCH">IDENTITY_MATCH</option>
              <option value="BOOLEAN">BOOLEAN</option>
              <option value="DATE_VALIDITY">DATE_VALIDITY</option>
              <option value="TEXT_MATCH">TEXT_MATCH</option>
            </select>
          </div>

          <div class="form-group">
            <label>Mandatory:</label>
            <select v-model="editForm.mandatory" class="form-control">
              <option :value="true">YES (Mandatory)</option>
              <option :value="false">NO (Optional)</option>
            </select>
          </div>

          <div class="form-group">
            <label>Required Value:</label>
            <input v-model="editForm.required_value" type="text" class="form-control" />
          </div>

          <div class="form-actions">
            <button type="button" @click="showEditModal = false" class="btn-cancel">Cancel</button>
            <button type="submit" class="btn-save">Save Changes</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { useBidderStore } from '../stores/bidder'

const API_BASE = '/api/tenders'

const bidderStore = useBidderStore()
const activeStep = ref(1)
const loading = ref(false)
const evaluating = ref(false)
const selectedTenderFile = ref<File | null>(null)
const tenderTitleInput = ref('')
const tenderFileInput = ref<HTMLInputElement | null>(null)

const currentTender = ref<any>(null)
const currentTenderId = computed(() => currentTender.value?.tender_id || '')
const requirements = ref<any[]>([])
const bidderId = ref(bidderStore.currentBidderId)
const summary = ref<any>(null)

// Edit Modal State
const showEditModal = ref(false)
const editForm = ref<any>({})

onMounted(() => {
  loadTendersList()
})

// Sync bidderId when global bidder switches
watch(() => bidderStore.currentBidderId, (newId) => {
  bidderId.value = newId
  summary.value = null  // clear stale results for old bidder
})

const loadTendersList = async () => {
  try {
    const res = await axios.get(`${API_BASE}/list`)
    if (res.data && res.data.length > 0) {
      currentTender.value = res.data[0]
      await fetchRequirements(currentTender.value.tender_id)
    }
  } catch (e) {
    console.error('Failed to list tenders:', e)
  }
}

const loadDemoTender = async () => {
  loading.value = true
  try {
    const res = await axios.post(`${API_BASE}/seed-demo`)
    currentTender.value = res.data
    await fetchRequirements(currentTender.value.tender_id)
    activeStep.value = 2
  } catch (e) {
    alert('Failed to load demo tender: ' + e)
  } finally {
    loading.value = false
  }
}

const onTenderFileSelect = (e: any) => {
  if (e.target.files && e.target.files.length > 0) {
    selectedTenderFile.value = e.target.files[0]
  }
}

const uploadTenderFile = async () => {
  if (!selectedTenderFile.value) return
  loading.value = true
  const formData = new FormData()
  formData.append('file', selectedTenderFile.value)
  if (tenderTitleInput.value) {
    formData.append('title', tenderTitleInput.value)
  }

  try {
    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    currentTender.value = res.data
    await extractRequirements()
    activeStep.value = 2
  } catch (e) {
    alert('Tender upload failed: ' + e)
  } finally {
    loading.value = false
  }
}

const extractRequirements = async () => {
  if (!currentTenderId.value) return
  loading.value = true
  try {
    const res = await axios.post(`${API_BASE}/${currentTenderId.value}/extract-requirements`)
    requirements.value = res.data.requirements
  } catch (e) {
    alert('Extraction failed: ' + e)
  } finally {
    loading.value = false
  }
}

const fetchRequirements = async (tId: string) => {
  try {
    const res = await axios.get(`${API_BASE}/${tId}/requirements`)
    requirements.value = res.data
  } catch (e) {
    console.error('Error fetching requirements:', e)
  }
}

const runEvaluation = async () => {
  if (!currentTenderId.value || !bidderId.value) return
  evaluating.value = true
  try {
    const res = await axios.post(`${API_BASE}/${currentTenderId.value}/bidders/${bidderId.value}/evaluate`)
    summary.value = res.data
  } catch (e) {
    alert('Evaluation failed: ' + e)
  } finally {
    evaluating.value = false
  }
}

const openEditModal = (req: any) => {
  editForm.value = { ...req }
  showEditModal.value = true
}

const saveRequirementEdit = async () => {
  try {
    await axios.put(`${API_BASE}/requirements/${editForm.value.id}`, editForm.value)
    showEditModal.value = false
    await fetchRequirements(currentTenderId.value)
  } catch (e) {
    alert('Save failed: ' + e)
  }
}

const deleteRequirement = async (id: number) => {
  if (!confirm('Delete requirement?')) return
  try {
    await axios.delete(`${API_BASE}/requirements/${id}`)
    await fetchRequirements(currentTenderId.value)
  } catch (e) {
    alert('Delete failed: ' + e)
  }
}

const openAddModal = () => {
  const code = `REQ-${(requirements.value.length + 1).toString().padStart(3, '0')}`
  editForm.value = {
    requirement_code: code,
    category: 'ELIGIBILITY',
    title: 'New Requirement',
    description: '',
    requirement_type: 'DOCUMENT_REQUIRED',
    mandatory: true,
    operator: 'EXISTS',
    required_value: 'DOCUMENT_NAME'
  }
  showEditModal.value = true
}

const formatCriteria = (req: any) => {
  if (req.requirement_type === 'NUMERIC') {
    if (req.required_value >= 10000000) return `≥ ₹${req.required_value / 10000000} Cr`
    return `≥ ₹${req.required_value}`
  }
  if (req.requirement_type === 'PERCENTAGE') return `≥ ${req.required_value}%`
  return req.required_value || 'Mandatory'
}

const getReqTitle = (code: string) => {
  const req = requirements.value.find(r => r.requirement_code === code)
  return req ? req.title : code
}

const getResultIcon = (result: string) => {
  switch (result) {
    case 'SATISFIED': return '✅'
    case 'NOT_SATISFIED': return '❌'
    case 'MISSING': return '⚠️'
    case 'REVIEW_REQUIRED': return '🔍'
    case 'UNABLE_TO_VERIFY': return 'ℹ️'
    default: return '⚪'
  }
}

const formatResultStatus = (status: string) => {
  return status.replace(/_/g, ' ')
}

const getPillClass = (result: string) => {
  switch (result) {
    case 'SATISFIED': return 'pill-satisfied'
    case 'NOT_SATISFIED': return 'pill-not-satisfied'
    case 'MISSING': return 'pill-missing'
    case 'REVIEW_REQUIRED': return 'pill-review'
    case 'UNABLE_TO_VERIFY': return 'pill-unable'
    default: return 'pill-default'
  }
}

const getResultRowClass = (result: string) => {
  switch (result) {
    case 'NOT_SATISFIED': return 'row-unsatisfied'
    case 'MISSING': return 'row-missing'
    case 'REVIEW_REQUIRED': return 'row-review'
    default: return ''
  }
}
</script>

<style scoped>
.tender-dashboard {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #1e293b;
}

.hero-section {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
  color: white;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.3);
}

.hero-badge {
  background: #6366f1;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.hero-section h2 {
  font-size: 1.75rem;
  margin: 0.5rem 0;
}

.hero-subtitle {
  color: #c7d2fe;
  font-size: 0.95rem;
  max-width: 800px;
}

.workflow-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.step-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.step-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.step-btn.active {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1d4ed8;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #cbd5e1;
  color: white;
  border-radius: 50%;
  font-size: 0.8rem;
}

.step-btn.active .step-num {
  background: #3b82f6;
}

.step-panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.panel-header h3 {
  font-size: 1.25rem;
  color: #0f172a;
  margin-bottom: 0.25rem;
}

.section-desc {
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.upload-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.card {
  padding: 1.5rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.demo-card {
  background: #f8fafc;
  border-color: #cbd5e1;

}

.card-badge {
  display: inline-block;
  background: #dbeafe;
  color: #1e40af;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.btn-primary-lg {
  width: 100%;
  padding: 0.85rem;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 1rem;
}

.btn-secondary-lg {
  width: 100%;
  padding: 0.85rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 1rem;
}

.active-tender-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  padding: 1rem 1.5rem;
  border-radius: 10px;
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-next {
  background: #16a34a;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.table-container {
  overflow-x: auto;
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.custom-table th, .custom-table td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.custom-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}

.pill-mandatory { background: #fee2e2; color: #991b1b; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
.pill-optional { background: #f1f5f9; color: #475569; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }

.bidder-selector-card {
  background: #f8fafc;
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.selector-inputs {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.bidder-input {
  padding: 0.6rem 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 1rem;
  width: 250px;
}

.btn-eval-primary {
  padding: 0.6rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 700;
  cursor: pointer;
}

.summary-cards-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metric-card {
  background: white;
  border: 1px solid #e2e8f0;
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
}

.score-card { background: #eff6ff; border-color: #bfdbfe; }
.score-val { font-size: 1.75rem; font-weight: 800; color: #1d4ed8; }
.satisfied-card { background: #f0fdf4; border-color: #bbf7d0; }
.unsatisfied-card { background: #fef2f2; border-color: #fecaca; }
.missing-card { background: #fff7ed; border-color: #ffedd5; }
.review-card { background: #fefce8; border-color: #fef08a; }

.metric-num { font-size: 1.5rem; font-weight: 700; color: #0f172a; }
.metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; font-weight: 600; }

.compliance-results-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.compliance-results-table th, .compliance-results-table td {
  padding: 0.85rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.result-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.8rem;
}

.pill-satisfied { background: #dcfce7; color: #15803d; }
.pill-not-satisfied { background: #fee2e2; color: #b91c1c; }
.pill-missing { background: #ffedd5; color: #c2410c; }
.pill-review { background: #fef08a; color: #a16207; }
.pill-unable { background: #f1f5f9; color: #475569; }

.mandatory-disclaimer-box {
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  color: #475569;
}

.disclaimer-icon { font-size: 1.5rem; }

.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-card {
  background: white;
  width: 500px;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.35rem;
}

.form-control {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn-cancel { background: #e2e8f0; border: none; padding: 0.6rem 1rem; border-radius: 6px; cursor: pointer; }
.btn-save { background: #2563eb; color: white; border: none; padding: 0.6rem 1rem; border-radius: 6px; font-weight: 600; cursor: pointer; }
</style>

<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Tender Requirements</h1>
        <p class="page-subtitle">
          Tender: <strong>{{ tenderTitle }}</strong> | ID: <code>{{ tenderId }}</code>
        </p>
      </div>

      <div class="header-actions">
        <button @click="router.push('/tenders-list')" class="btn btn-outline">📤 Upload Tender</button>
        <button @click="loadDemo" class="btn btn-primary" :disabled="loading">⚡ Load Demo Tender</button>
        <button @click="reExtract" class="btn btn-secondary" :disabled="loading">🔄 Re-extract Requirements</button>
      </div>
    </div>

    <!-- REQUIREMENTS SUMMARY CARDS -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">TOTAL RULES</div>
        <div class="kpi-value">{{ requirements.length }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">MANDATORY RULES</div>
        <div class="kpi-value text-red">{{ mandatoryCount }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">FINANCIAL & REGISTRATION</div>
        <div class="kpi-value text-blue">{{ categoryCount('FINANCIAL') + categoryCount('REGISTRATION') }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">OPTIONAL RULES</div>
        <div class="kpi-value text-green">{{ requirements.length - mandatoryCount }}</div>
      </div>
    </div>

    <!-- REQUIREMENTS PROFESSIONAL TABLE (or empty state) -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Extracted Requirement Rules</h3>
        <button @click="router.push('/officer-review')" class="btn btn-primary btn-sm" :disabled="requirements.length === 0">Proceed to Officer Review →</button>
      </div>

      <!-- Empty State -->
      <div v-if="requirements.length === 0 && !loading" class="empty-section">
        <span class="empty-icon">📋</span>
        <p class="empty-title">No requirements available.</p>
        <p class="empty-hint">Upload a tender PDF and extract requirements to see them here.</p>
        <button @click="router.push('/tenders-list')" class="btn btn-primary mt-2">Upload Tender →</button>
      </div>

      <div v-if="loading" class="empty-section">
        <div class="spinner"></div>
        <p>Loading requirements...</p>
      </div>

      <div v-if="requirements.length > 0" class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Requirement ID</th>
              <th>Requirement</th>
              <th>Category</th>
              <th>Tender Rule</th>
              <th>Mandatory</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="r in requirements" 
              :key="r.id" 
              class="table-row-hover"
              @click="selectRequirement(r)"
            >
              <td><code>{{ r.requirement_code }}</code></td>
              <td>
                <div class="req-title">{{ r.title }}</div>
                <div class="req-desc">{{ r.description }}</div>
              </td>
              <td><span class="badge badge-category">{{ r.category }}</span></td>
              <td><span class="rule-value">{{ formatRule(r) }}</span></td>
              <td>
                <span :class="['pill', r.mandatory ? 'pill-mandatory' : 'pill-optional']">
                  {{ r.mandatory ? 'YES' : 'NO' }}
                </span>
              </td>
              <td><span class="badge badge-green">EXTRACTED</span></td>
              <td>
                <button @click.stop="selectRequirement(r)" class="btn-sm btn-outline">Details</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      </div>
    </div>

    <!-- SELECTED REQUIREMENT DETAIL DRAWER / MODAL -->
    <div v-if="selectedReq" class="modal-backdrop" @click.self="selectedReq = null">
      <div class="modal-card">
        <div class="modal-header">
          <h3><code>{{ selectedReq.requirement_code }}</code> — {{ selectedReq.title }}</h3>
          <button @click="selectedReq = null" class="close-btn">×</button>
        </div>

        <div class="modal-body">
          <div class="detail-row">
            <span class="detail-label">Category:</span>
            <span class="detail-val">{{ selectedReq.category }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Requirement Type:</span>
            <span class="detail-val">{{ selectedReq.requirement_type }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Mandatory:</span>
            <span class="detail-val">{{ selectedReq.mandatory ? 'YES' : 'NO' }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Tender Rule Value:</span>
            <span class="detail-val text-blue font-bold">{{ formatRule(selectedReq) }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">Source Document:</span>
            <span class="detail-val">{{ selectedReq.source_document || 'Tender PDF' }} (p. {{ selectedReq.source_page || 1 }})</span>
          </div>

          <div class="evidence-box mt-3">
            <label class="font-bold text-sm text-slate-700">Source Evidence Snippet:</label>
            <blockquote class="snippet-quote">"{{ selectedReq.evidence_text || 'Rule extracted from tender text.' }}"</blockquote>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="router.push('/officer-review')" class="btn btn-primary w-full">
            Review in Procurement Officer Interface →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { tenderApi, TenderRequirement } from '../api/tenderApi'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)
const tenderId = ref('')
const tenderTitle = ref('No Tender Loaded')
const requirements = ref<TenderRequirement[]>([])
const selectedReq = ref<TenderRequirement | null>(null)

const mandatoryCount = computed(() => requirements.value.filter(r => r.mandatory).length)

const categoryCount = (cat: string) => requirements.value.filter(r => r.category === cat).length

onMounted(() => {
  fetchRequirements()
})

const fetchRequirements = async () => {
  loading.value = true
  try {
    // First get the list of tenders to determine which one to load
    const tendersRes = await axios.get('/api/tenders/list')
    const tenders = tendersRes.data || []
    if (tenders.length === 0) {
      requirements.value = []
      return
    }
    tenderId.value = tenders[0].tender_id
    tenderTitle.value = tenders[0].title || tenders[0].tender_id
    const list = await tenderApi.getRequirements(tenderId.value)
    requirements.value = list || []
  } catch (e) {
    requirements.value = []
  } finally {
    loading.value = false
  }
}

const reExtract = async () => {
  loading.value = true
  try {
    const res = await tenderApi.extractRequirements(tenderId.value)
    requirements.value = res.requirements
  } catch (e) {
    alert('Re-extract error: ' + e)
  } finally {
    loading.value = false
  }
}

const formatRule = (r: TenderRequirement) => {
  if (r.requirement_type === 'NUMERIC') {
    if (r.required_value >= 10000000) return `≥ ₹${r.required_value / 10000000} Crore`
    return `≥ ₹${r.required_value}`
  }
  if (r.requirement_type === 'PERCENTAGE') return `≥ ${r.required_value}%`
  return r.required_value || 'Mandatory'
}

const selectRequirement = (r: TenderRequirement) => {
  selectedReq.value = r
}
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
.page-subtitle { font-size: 0.85rem; color: #64748b; margin-top: 2px; }

.header-actions { display: flex; gap: 0.5rem; }
.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: #2563eb; color: white; }
.btn-secondary { background: #0f172a; color: white; }
.btn-outline { background: white; border: 1px solid #cbd5e1; color: #334155; }
.empty-section { padding: 3rem 2rem; text-align: center; color: #64748b; }
.empty-icon { font-size: 3rem; display: block; margin-bottom: 0.75rem; }
.empty-title { font-size: 1rem; font-weight: 600; color: #334155; margin-bottom: 0.4rem; }
.empty-hint { font-size: 0.8rem; color: #94a3b8; }
.mt-2 { margin-top: 0.5rem; }
.spinner { margin: 0 auto 1rem; width: 36px; height: 36px; border: 3px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.btn-sm { padding: 0.35rem 0.75rem; font-size: 0.75rem; }

.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem 1.25rem; }
.kpi-title { font-size: 0.7rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }
.kpi-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; margin-top: 0.2rem; }

.text-red { color: #dc2626; }
.text-blue { color: #2563eb; }
.text-green { color: #16a34a; }

.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.card-header { padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.card-title { font-size: 0.95rem; font-weight: 700; color: #0f172a; }

.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; }
.table-row-hover:hover { background: #f8fafc; cursor: pointer; }

.req-title { font-weight: 700; color: #0f172a; }
.req-desc { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.badge-category { background: #f1f5f9; color: #334155; }
.badge-green { background: #dcfce7; color: #15803d; }
.rule-value { font-weight: 700; color: #2563eb; }

.pill-mandatory { background: #fee2e2; color: #b91c1c; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
.pill-optional { background: #f1f5f9; color: #64748b; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }

.modal-backdrop { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15, 23, 42, 0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: white; width: 500px; padding: 1.5rem; border-radius: 10px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2); }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.75rem; }
.close-btn { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #64748b; }
.detail-row { display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px dashed #f1f5f9; font-size: 0.85rem; }
.detail-label { color: #64748b; }
.detail-val { font-weight: 600; color: #0f172a; }
.snippet-quote { background: #f8fafc; border-left: 3px solid #3b82f6; padding: 0.6rem; font-style: italic; font-size: 0.8rem; color: #334155; margin-top: 0.3rem; border-radius: 0 4px 4px 0; }
.modal-footer { margin-top: 1.5rem; }
.w-full { width: 100%; }
</style>

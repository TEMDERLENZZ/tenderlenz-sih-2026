<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Procurement Officer Review</h1>
        <p class="page-subtitle">Review, edit, and confirm AI-extracted tender requirements before running automated compliance matching.</p>
      </div>

      <button @click="router.push('/compliance-analysis')" class="btn btn-primary">
        Proceed to Compliance Analysis →
      </button>
    </div>

    <!-- OFFICER CONFIRMATION BANNER -->
    <div class="notice-banner">
      <span class="notice-icon">🧐</span>
      <div>
        <strong>PROCUREMENT OFFICER CONFIRMATION REQUIRED</strong>
        <p>AI extracted requirement — Procurement Officer confirmation required to prevent OCR mistakes from silently affecting compliance decisions.</p>
      </div>
    </div>

    <!-- EMPTY STATE: No Requirements -->
    <div v-if="requirements.length === 0 && !loading" class="card empty-section p-4">
      <span class="empty-icon">📋</span>
      <p class="empty-title">No requirements available for review.</p>
      <p class="empty-hint">Upload a tender and extract requirements before performing officer review.</p>
      <button @click="router.push('/tenders-list')" class="btn btn-primary mt-2">Upload Tender →</button>
    </div>

    <div v-if="loading" class="card empty-section p-4">
      <div class="spinner"></div>
      <p>Loading requirements...</p>
    </div>

    <!-- 3-PANE REVIEW INTERFACE -->
    <div class="review-3pane-grid" v-if="requirements.length > 0">
      <!-- LEFT PANE: REQUIREMENT LIST -->
      <div class="pane pane-left card">
        <div class="pane-header">
          <h3 class="card-title">Requirements List ({{ requirements.length }})</h3>
        </div>

        <div class="req-list">
          <div 
            v-for="r in requirements" 
            :key="r.id"
            :class="['req-list-item', { active: selectedReq?.id === r.id }]"
            @click="selectedReq = r"
          >
            <div class="item-top">
              <code>{{ r.requirement_code }}</code>
              <span :class="['status-dot', r.status === 'APPROVED' ? 'bg-green' : 'bg-amber']"></span>
            </div>
            <div class="item-title">{{ r.title }}</div>
            <div class="item-category">{{ r.category }} • {{ r.requirement_type }}</div>
          </div>
        </div>
      </div>

      <!-- CENTER PANE: SELECTED REQUIREMENT DETAILS & EDIT FORM -->
      <div class="pane pane-center card" v-if="selectedReq">
        <div class="pane-header">
          <h3 class="card-title">Requirement Rule Details</h3>
          <span class="badge badge-primary">ID: {{ selectedReq.requirement_code }}</span>
        </div>

        <div class="pane-body">
          <div class="form-group mb-3">
            <label class="form-label">Requirement Title:</label>
            <input v-model="selectedReq.title" type="text" class="form-control" />
          </div>

          <div class="form-group mb-3">
            <label class="form-label">Category:</label>
            <input v-model="selectedReq.category" type="text" class="form-control" />
          </div>

          <div class="form-row mb-3">
            <div class="form-group flex-1">
              <label class="form-label">Type:</label>
              <select v-model="selectedReq.requirement_type" class="form-control">
                <option value="NUMERIC">NUMERIC</option>
                <option value="DOCUMENT_REQUIRED">DOCUMENT_REQUIRED</option>
                <option value="PERCENTAGE">PERCENTAGE</option>
                <option value="STATUS_CHECK">STATUS_CHECK</option>
                <option value="IDENTITY_MATCH">IDENTITY_MATCH</option>
                <option value="BOOLEAN">BOOLEAN</option>
              </select>
            </div>

            <div class="form-group flex-1">
              <label class="form-label">Mandatory:</label>
              <select v-model="selectedReq.mandatory" class="form-control">
                <option :value="true">YES (Mandatory)</option>
                <option :value="false">NO (Optional)</option>
              </select>
            </div>
          </div>

          <div class="form-group mb-4">
            <label class="form-label">Required Criteria Value:</label>
            <input v-model="selectedReq.required_value" type="text" class="form-control font-bold text-blue" />
          </div>

          <!-- ACTION BUTTONS -->
          <div class="button-group">
            <button @click="approveRequirement" class="btn btn-success flex-1">
              ✓ Approve Requirement
            </button>
            <button @click="saveRequirement" class="btn btn-primary flex-1">
              💾 Save Edits
            </button>
            <button @click="markForReview" class="btn btn-amber flex-1">
              ⚠️ Mark for Review
            </button>
          </div>
        </div>
      </div>

      <!-- RIGHT PANE: AI EXTRACTION EVIDENCE -->
      <div class="pane pane-right card" v-if="selectedReq">
        <div class="pane-header">
          <h3 class="card-title">AI Extraction Evidence</h3>
        </div>

        <div class="pane-body">
          <div class="evidence-stat-card">
            <div class="stat-label">AI CONFIDENCE SCORE</div>
            <div class="stat-val text-green">{{ Math.round((selectedReq.extraction_confidence || 1.0) * 100) }}%</div>
          </div>

          <div class="info-block mt-3">
            <span class="block-label">Source Document:</span>
            <span class="block-val">{{ selectedReq.source_document || 'Tender Specification PDF' }}</span>
          </div>

          <div class="info-block mt-2">
            <span class="block-label">Page Reference:</span>
            <span class="block-val">Page {{ selectedReq.source_page || 1 }}</span>
          </div>

          <div class="info-block mt-2">
            <span class="block-label">Extraction Method:</span>
            <span class="block-val">NLP Rule Engine + Pattern Match</span>
          </div>

          <div class="evidence-quote-box mt-4">
            <label class="quote-label">EXTRACTED TENDER TEXT SNIPPET:</label>
            <div class="quote-content">
              "{{ selectedReq.evidence_text || 'Minimum requirement specified in tender eligibility section.' }}"
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { tenderApi, TenderRequirement } from '../api/tenderApi'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)
const tenderId = ref('')
const requirements = ref<any[]>([])
const selectedReq = ref<any | null>(null)

onMounted(() => {
  loadRequirements()
})

const loadRequirements = async () => {
  loading.value = true
  try {
    // First find available tenders
    const tendersRes = await axios.get('/api/tenders/list')
    const tenders = tendersRes.data || []
    if (tenders.length === 0) {
      requirements.value = []
      return
    }
    tenderId.value = tenders[0].tender_id
    const list = await tenderApi.getRequirements(tenderId.value)
    if (list && list.length > 0) {
      requirements.value = list
      selectedReq.value = list[0]
    } else {
      requirements.value = []
    }
  } catch (e) {
    console.error('Error loading requirements:', e)
    requirements.value = []
  } finally {
    loading.value = false
  }
}

const approveRequirement = async () => {
  if (!selectedReq.value) return
  selectedReq.value.status = 'APPROVED'
  await saveRequirement()
}

const markForReview = async () => {
  if (!selectedReq.value) return
  selectedReq.value.status = 'NEEDS_REVIEW'
  await saveRequirement()
}

const saveRequirement = async () => {
  if (!selectedReq.value) return
  try {
    await tenderApi.updateRequirement(selectedReq.value.id, selectedReq.value)
    alert('Requirement updated & confirmed!')
  } catch (e) {
    alert('Failed to update requirement: ' + e)
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
.btn-success { background: #16a34a; color: white; }
.btn-amber { background: #d97706; color: white; }
.flex-1 { flex: 1; }
.empty-section { padding: 3rem 2rem; text-align: center; color: #64748b; }
.empty-icon { font-size: 3rem; display: block; margin-bottom: 0.75rem; }
.empty-title { font-size: 1rem; font-weight: 600; color: #334155; margin-bottom: 0.4rem; }
.empty-hint { font-size: 0.8rem; color: #94a3b8; }
.mt-2 { margin-top: 0.5rem; }
.p-4 { padding: 1.5rem; }
.spinner { margin: 0 auto 1rem; width: 36px; height: 36px; border: 3px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.notice-banner { background: #fffbeb; border: 1px solid #fef08a; padding: 1rem 1.25rem; border-radius: 8px; display: flex; gap: 1rem; align-items: center; color: #92400e; font-size: 0.85rem; }
.notice-icon { font-size: 1.5rem; }

.review-3pane-grid { display: grid; grid-template-columns: 280px 1fr 300px; gap: 1.25rem; }
.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.pane-header { padding: 1rem; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 0.9rem; font-weight: 700; color: #0f172a; }

.req-list { max-height: 550px; overflow-y: auto; }
.req-list-item { padding: 0.75rem 1rem; border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: all 0.15s; }
.req-list-item:hover { background: #f8fafc; }
.req-list-item.active { background: #eff6ff; border-left: 3px solid #2563eb; }

.item-top { display: flex; justify-content: space-between; align-items: center; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.bg-green { background: #16a34a; }
.bg-amber { background: #d97706; }
.item-title { font-size: 0.85rem; font-weight: 700; color: #0f172a; margin-top: 0.2rem; }
.item-category { font-size: 0.7rem; color: #64748b; margin-top: 2px; }

.pane-body { padding: 1.25rem; }
.form-group { margin-bottom: 1rem; }
.form-row { display: flex; gap: 1rem; }
.form-label { display: block; font-size: 0.8rem; font-weight: 600; color: #475569; margin-bottom: 0.3rem; }
.form-control { width: 100%; padding: 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; }
.font-bold { font-weight: 700; }
.text-blue { color: #2563eb; }
.text-green { color: #16a34a; }

.button-group { display: flex; gap: 0.5rem; margin-top: 1.5rem; }

.evidence-stat-card { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 1rem; border-radius: 6px; text-align: center; }
.stat-label { font-size: 0.65rem; font-weight: 700; color: #15803d; letter-spacing: 0.05em; }
.stat-val { font-size: 1.75rem; font-weight: 800; margin-top: 0.2rem; }

.info-block { font-size: 0.8rem; }
.block-label { color: #64748b; font-weight: 600; display: inline-block; width: 120px; }
.block-val { font-weight: 700; color: #0f172a; }

.evidence-quote-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem; }
.quote-label { font-size: 0.65rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }
.quote-content { font-style: italic; font-size: 0.8rem; color: #334155; margin-top: 0.35rem; line-height: 1.4; }
.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.badge-primary { background: #dbeafe; color: #1e40af; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
</style>

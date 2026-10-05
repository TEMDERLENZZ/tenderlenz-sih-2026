<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Evidence Traceability Center</h1>
        <p class="page-subtitle">End-to-end evidence lineage from raw tender specification to extracted bidder documents and verification results.</p>
      </div>
    </div>

    <!-- LOADING STATE -->
    <div v-if="loading" class="card empty-card">
      <div class="spinner"></div>
      <p>Loading evidence data...</p>
    </div>

    <!-- EMPTY STATE: No Compliance Results -->
    <div v-else-if="complianceResults.length === 0" class="card empty-card">
      <span class="empty-icon">📑</span>
      <p class="empty-title">No evidence available.</p>
      <p class="empty-hint">
        Evidence lineage appears after running compliance evaluation for a tender-bidder pair.
        <br/>Upload a tender, submit bidder documents, and run compliance analysis to generate evidence traces.
      </p>
      <div class="empty-actions">
        <button @click="router.push('/tenders-list')" class="btn btn-primary">Upload Tender →</button>
        <button @click="router.push('/compliance-analysis')" class="btn btn-outline">Run Compliance Analysis →</button>
      </div>
    </div>

    <!-- EVIDENCE CHAIN: shown when compliance results exist -->
    <template v-else>
      <!-- SELECT REQUIREMENT FOR EVIDENCE CHAIN -->
      <div class="card p-3 mb-3">
        <div class="flex-between">
          <label class="font-bold text-sm text-slate-700">Select Requirement to View Lineage Chain:</label>
          <select v-model="selectedResultId" class="form-control select-dropdown">
            <option v-for="r in complianceResults" :key="r.id" :value="r.id">
              {{ r.requirement_code }}: {{ r.explanation?.substring(0, 60) }}...
            </option>
          </select>
        </div>
      </div>

      <!-- INTERACTIVE EVIDENCE CHAIN FLOW -->
      <div class="card p-4" v-if="activeResult">
        <div class="card-header border-none p-0 mb-4">
          <h3 class="card-title text-indigo-900">🔗 Interactive Evidence Lineage Chain — <code>{{ activeResult.requirement_code }}</code></h3>
        </div>

        <div class="evidence-chain-flow">
          <!-- NODE 1: TENDER REQUIREMENT -->
          <div class="chain-node node-tender">
            <div class="node-header">1. TENDER REQUIREMENT</div>
            <div class="node-body">
              <strong>{{ activeResult.requirement_code }}</strong>
              <div class="node-meta mt-1">Required: <span class="text-blue font-bold">{{ activeResult.required_value || 'N/A' }}</span></div>
            </div>
            <div class="node-footer">
              <span>📄 Tender Specification</span>
              <span>Source Document</span>
            </div>
          </div>

          <div class="chain-arrow">↓</div>

          <!-- NODE 2: BIDDER DOCUMENT EVIDENCE -->
          <div class="chain-node node-bidder">
            <div class="node-header">2. SUBMITTED BIDDER DOCUMENT</div>
            <div class="node-body">
              <strong>📁 {{ activeResult.evidence?.document || 'Bidder Document' }}</strong>
              <div class="node-meta mt-1">Extracted Value: <span class="font-bold text-slate-900">{{ activeResult.actual_value || 'N/A' }}</span></div>
            </div>
            <div class="node-footer">
              <span>Extracted via OCR</span>
              <span v-if="activeResult.evidence?.page">Page {{ activeResult.evidence.page }}</span>
            </div>
          </div>

          <div class="chain-arrow">↓</div>

          <!-- NODE 3: RULE EVALUATION ENGINE -->
          <div class="chain-node node-eval">
            <div class="node-header">3. COMPLIANCE RULE EVALUATION</div>
            <div class="node-body">
              <div class="result-badge-container">
                <span :class="['result-pill', getPillClass(activeResult.result)]">
                  {{ activeResult.result }}
                </span>
              </div>
              <p class="node-explanation mt-2">{{ activeResult.explanation }}</p>
            </div>
            <div class="node-footer">
              <span>Evaluator Engine v1.0</span>
              <span>Confidence: {{ Math.round((activeResult.confidence || 1) * 100) }}%</span>
            </div>
          </div>
        </div>

        <!-- NODE ACTIONS BUTTONS -->
        <div class="evidence-actions mt-4">
          <button @click="showSnippetModal = true" class="btn btn-outline" :disabled="!activeResult.evidence?.text">
            🔍 View Extracted Text Snippet
          </button>
          <button @click="showJsonModal = true" class="btn btn-secondary">
            ⚡ View Raw Evidence Payload
          </button>
        </div>
      </div>

      <!-- MODAL POPUPS -->
      <div v-if="showSnippetModal" class="modal-backdrop" @click.self="showSnippetModal = false">
        <div class="modal-card">
          <h3>🔍 Extracted Evidence Text Snippet</h3>
          <blockquote class="snippet-quote mt-3">"{{ activeResult?.evidence?.text || 'No text snippet available.' }}"</blockquote>
          <button @click="showSnippetModal = false" class="btn btn-secondary w-full mt-4">Close Window</button>
        </div>
      </div>

      <div v-if="showJsonModal" class="modal-backdrop" @click.self="showJsonModal = false">
        <div class="modal-card">
          <h3>⚡ Raw Evidence Payload JSON</h3>
          <pre class="json-code mt-3">{{ JSON.stringify(activeResult, null, 2) }}</pre>
          <button @click="showJsonModal = false" class="btn btn-secondary w-full mt-4">Close Window</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { tenderApi } from '../api/tenderApi'
import { useBidderStore } from '../stores/bidder'
import axios from 'axios'

const router = useRouter()
const bidderStore = useBidderStore()

const loading = ref(false)
const complianceResults = ref<any[]>([])
const selectedResultId = ref<number | null>(null)
const showSnippetModal = ref(false)
const showJsonModal = ref(false)

const activeResult = computed(() =>
  complianceResults.value.find(r => r.id === selectedResultId.value) || null
)

onMounted(async () => {
  if (bidderStore.currentBidderId) {
    await loadEvidence()
  }
})

watch(() => bidderStore.currentBidderId, async () => {
  await loadEvidence()
})

const loadEvidence = async () => {
  if (!bidderStore.currentBidderId) {
    complianceResults.value = []
    return
  }

  loading.value = true
  complianceResults.value = []
  selectedResultId.value = null

  try {
    // Load list of tenders first
    const tendersRes = await axios.get('/api/tenders/list')
    const tenders = tendersRes.data || []
    if (tenders.length === 0) return

    // Try to load compliance results for the first available tender
    const tenderId = tenders[0].tender_id
    const res = await tenderApi.getComplianceSummary(tenderId, bidderStore.currentBidderId)
    if (res && res.results && res.results.length > 0) {
      complianceResults.value = res.results
      selectedResultId.value = res.results[0].id
    }
  } catch (e) {
    // No compliance results available — show empty state
    complianceResults.value = []
  } finally {
    loading.value = false
  }
}

const getPillClass = (result: string) => {
  switch (result) {
    case 'SATISFIED': return 'pill-satisfied'
    case 'NOT_SATISFIED': return 'pill-not-satisfied'
    case 'MISSING': return 'pill-missing'
    default: return 'pill-review'
  }
}
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
.page-subtitle { font-size: 0.85rem; color: #64748b; margin-top: 2px; }

.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; transition: all 0.15s; }
.btn-secondary { background: #0f172a; color: white; }
.btn-outline { background: white; border: 1px solid #cbd5e1; color: #334155; }
.btn-primary { background: #2563eb; color: white; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.p-3 { padding: 1rem; }
.p-4 { padding: 1.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }

.empty-card {
  padding: 4rem 2rem;
  text-align: center;
  color: #64748b;
}

.empty-icon {
  font-size: 3.5rem;
  display: block;
  margin-bottom: 1rem;
}

.empty-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #334155;
  margin-bottom: 0.5rem;
}

.empty-hint {
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.5;
  margin-bottom: 1.5rem;
}

.empty-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
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

.flex-between { display: flex; justify-content: space-between; align-items: center; }
.select-dropdown { width: 450px; padding: 0.5rem; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 0.85rem; }

.evidence-chain-flow { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; max-width: 650px; margin: 0 auto; }
.chain-node { width: 100%; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; }
.node-header { background: #e2e8f0; color: #334155; font-size: 0.65rem; font-weight: 800; letter-spacing: 0.05em; padding: 0.4rem 0.75rem; }
.node-body { padding: 0.85rem; font-size: 0.85rem; }
.node-footer { background: #f1f5f9; padding: 0.35rem 0.75rem; font-size: 0.7rem; color: #64748b; display: flex; justify-content: space-between; border-top: 1px solid #e2e8f0; }

.chain-arrow { font-size: 1.25rem; font-weight: 800; color: #3b82f6; }

.result-pill { display: inline-block; padding: 0.25rem 0.65rem; border-radius: 20px; font-weight: 700; font-size: 0.75rem; }
.pill-satisfied { background: #dcfce7; color: #15803d; }
.pill-not-satisfied { background: #fee2e2; color: #b91c1c; }
.pill-missing { background: #ffedd5; color: #c2410c; }
.pill-review { background: #fef08a; color: #a16207; }

.evidence-actions { display: flex; justify-content: center; gap: 0.75rem; }

.modal-backdrop { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15, 23, 42, 0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-card { background: white; width: 500px; padding: 1.5rem; border-radius: 10px; }
.snippet-quote { background: #f8fafc; border-left: 3px solid #3b82f6; padding: 0.75rem; font-style: italic; font-size: 0.85rem; color: #334155; border-radius: 0 6px 6px 0; }
.json-code { background: #0f172a; color: #38bdf8; padding: 0.75rem; border-radius: 6px; font-size: 0.75rem; max-height: 250px; overflow-y: auto; }
.w-full { width: 100%; }
.text-blue { color: #2563eb; }
.font-bold { font-weight: 700; }
.card-header { padding: 0.75rem 0; border-none: none; }
.card-title { font-size: 1rem; font-weight: 700; color: #1e1b4b; }
</style>

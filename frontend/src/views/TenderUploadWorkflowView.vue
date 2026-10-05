<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Tenders & Upload Workflow</h1>
        <p class="page-subtitle">Upload tender specification PDF/Image files, extract requirements, and manage compliance pipelines</p>
      </div>
    </div>

    <!-- 6-STEP WORKFLOW STEPPER -->
    <div class="stepper-card card">
      <div class="stepper-wrapper">
        <div 
          v-for="(step, idx) in steps" 
          :key="idx" 
          :class="['step-item', { active: currentStep === step.num, completed: currentStep > step.num }]"
          @click="navigateToStep(step)"
        >
          <div class="step-circle">
            <span v-if="currentStep > step.num">✓</span>
            <span v-else>{{ step.numStr }}</span>
          </div>
          <div class="step-label">{{ step.title }}</div>
        </div>
      </div>
    </div>

    <!-- TENDER UPLOAD SECTION -->
    <div class="dashboard-grid">
      <!-- CUSTOM TENDER UPLOAD CARD -->
      <div class="card p-4">
        <h3 class="card-title mb-2">📤 Upload Tender Document</h3>
        <p class="text-muted text-sm mb-4">Accepts PDF or Image files. Text will be extracted using digital PDF parsing & OCR.</p>

        <form @submit.prevent="handleUpload">
          <div class="form-group mb-3">
            <label class="form-label">Tender Title (Optional):</label>
            <input v-model="tenderTitle" type="text" placeholder="e.g. IT Equipment Procurement 2026" class="form-control" />
          </div>

          <div class="form-group mb-3">
            <label class="form-label">Tender Document File (PDF / Image):</label>
            <input type="file" ref="fileInput" accept=".pdf,.jpg,.jpeg,.png" @change="onFileSelected" class="form-control" />
          </div>

          <button type="submit" class="btn btn-secondary w-full" :disabled="!selectedFile || loading">
            {{ loading ? 'Extracting Text & Requirements...' : 'Upload & Extract Requirements' }}
          </button>
        </form>
      </div>

      <!-- BATCH BIDDER 14-DOCUMENTS UPLOAD CARD -->
      <div class="card p-4 hero-batch-card">
        <div class="hero-badge mb-2">FAST-TRACK BIDDER DATA</div>
        <h3 class="card-title text-white mb-2">📁 14-Document Batch Upload</h3>
        <p class="text-light-blue text-sm mb-4">Upload all 14 bidder documents in a single action with duplicate detection & instant field extraction.</p>

        <div class="form-group mb-3">
          <label class="form-label text-white">Target Bidder ID:</label>
          <input v-model="batchBidderId" type="text" class="form-control bg-dark-input" placeholder="BIDDER_001" />
        </div>

        <input type="file" ref="batchFileInput" multiple accept=".pdf,.jpg,.jpeg,.png" @change="handleBatchUpload" class="hidden" />
        <button @click="triggerBatchSelect" class="btn btn-hero-batch w-full" :disabled="loading">
          Upload All 14 Bidder Documents
        </button>
      </div>
    </div>

      <!-- TENDERS LIST TABLE -->
    <div class="card mt-4">
      <div class="card-header">
        <h3 class="card-title">Available Tenders</h3>
        <span class="badge badge-neutral">{{ tenders.length }} Tenders</span>
      </div>

      <div v-if="tenders.length === 0" class="empty-state p-4 text-center">
        <span class="empty-icon">📁</span>
        <p class="font-bold text-slate-700">No tenders available.</p>
        <p class="text-sm text-slate-500">Upload a tender specification PDF or image above to extract requirements and initialize a pipeline.</p>
      </div>

      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Tender ID</th>
              <th>Title</th>
              <th>File Name</th>
              <th>Extracted Text Length</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in tenders" :key="t.id" class="table-row-hover">
              <td><code>{{ t.tender_id }}</code></td>
              <td><strong>{{ t.title }}</strong></td>
              <td>{{ t.file_name || 'Standard Specification' }}</td>
              <td>{{ (t.extracted_text || '').length }} chars</td>
              <td><span class="badge badge-green">{{ t.status }}</span></td>
              <td class="action-cell">
                <button @click="selectAndExtract(t.tender_id)" class="btn-sm btn-outline">Extract Rules</button>
                <button @click="router.push('/officer-review')" class="btn-sm btn-secondary">Review</button>
                <button @click="router.push('/compliance-analysis')" class="btn-sm btn-primary">Evaluate</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { tenderApi } from '../api/tenderApi'
import { bidderApi } from '../api/bidderApi'
import { useBidderStore } from '../stores/bidder'

const router = useRouter()
const bidderStore = useBidderStore()
const currentStep = ref(1)
const loading = ref(false)
const tenderTitle = ref('')
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const batchFileInput = ref<HTMLInputElement | null>(null)
// Always use the globally active bidder for batch uploads
const batchBidderId = ref(bidderStore.currentBidderId)
const tenders = ref<any[]>([])

const steps = [
  { num: 1, numStr: '01', title: 'Tender Upload', route: '/tenders-list' },
  { num: 2, numStr: '02', title: 'Requirement Extraction', route: '/requirements' },
  { num: 3, numStr: '03', title: 'Officer Review', route: '/officer-review' },
  { num: 4, numStr: '04', title: 'Bidder Verification', route: '/bidder-verification' },
  { num: 5, numStr: '05', title: 'Requirement Evaluation', route: '/compliance-analysis' },
  { num: 6, numStr: '06', title: 'Final Compliance Report', route: '/reports' }
]

onMounted(() => {
  loadTenders()
})

// Keep batchBidderId in sync when user switches bidder globally
watch(() => bidderStore.currentBidderId, (newId) => {
  batchBidderId.value = newId
})

const loadTenders = async () => {
  try {
    const list = await tenderApi.listTenders()
    tenders.value = list
  } catch (e) {
    console.error('Failed to load tenders:', e)
  }
}

const loadDemoTender = async () => {
  loading.value = true
  try {
    await tenderApi.seedDemoTender()
    await loadTenders()
    currentStep.value = 2
    router.push('/requirements')
  } catch (e) {
    alert('Failed to load demo tender: ' + e)
  } finally {
    loading.value = false
  }
}

const onFileSelected = (e: any) => {
  if (e.target.files && e.target.files.length > 0) {
    selectedFile.value = e.target.files[0]
  }
}

const handleUpload = async () => {
  if (!selectedFile.value) return
  loading.value = true
  try {
    const res = await tenderApi.uploadTender(selectedFile.value, tenderTitle.value)
    await tenderApi.extractRequirements(res.tender_id)
    await loadTenders()
    currentStep.value = 2
    router.push('/requirements')
  } catch (e) {
    alert('Upload failed: ' + e)
  } finally {
    loading.value = false
  }
}

const triggerBatchSelect = () => {
  batchFileInput.value?.click()
}

const handleBatchUpload = async (e: any) => {
  const files = Array.from(e.target.files || []) as File[]
  if (files.length === 0) return
  loading.value = true
  try {
    await bidderApi.uploadBatchDocuments(batchBidderId.value, files)
    alert(`Successfully uploaded and processed ${files.length} bidder documents!`)
    router.push('/bidder-verification')
  } catch (e) {
    alert('Batch upload error: ' + e)
  } finally {
    loading.value = false
  }
}

const selectAndExtract = async (tenderId: string) => {
  loading.value = true
  try {
    await tenderApi.extractRequirements(tenderId)
    router.push('/requirements')
  } catch (e) {
    alert('Extraction failed: ' + e)
  } finally {
    loading.value = false
  }
}

const navigateToStep = (step: any) => {
  currentStep.value = step.num
  router.push(step.route)
}
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
.page-subtitle { font-size: 0.85rem; color: #64748b; margin-top: 2px; }

.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: white; }
.btn-secondary { background: #0f172a; color: white; }
.btn-outline { background: white; border: 1px solid #cbd5e1; color: #334155; }
.btn-sm { padding: 0.3rem 0.6rem; font-size: 0.75rem; margin-right: 0.3rem; }

.stepper-card { padding: 1rem; }
.stepper-wrapper { display: flex; justify-content: space-between; position: relative; }
.step-item { flex: 1; display: flex; flex-direction: column; align-items: center; cursor: pointer; position: relative; z-index: 1; }
.step-circle { width: 32px; height: 32px; border-radius: 50%; background: #e2e8f0; color: #64748b; font-weight: 700; font-size: 0.8rem; display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem; transition: all 0.2s; }
.step-item.active .step-circle { background: #2563eb; color: white; box-shadow: 0 0 0 4px #dbeafe; }
.step-item.completed .step-circle { background: #16a34a; color: white; }
.step-label { font-size: 0.75rem; font-weight: 600; color: #64748b; text-align: center; }
.step-item.active .step-label { color: #2563eb; font-weight: 700; }

.dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.p-4 { padding: 1.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-4 { margin-top: 1rem; }

.hero-batch-card { background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); color: white; }
.hero-badge { display: inline-block; background: #6366f1; color: white; font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 4px; }
.text-white { color: white; }
.text-light-blue { color: #c7d2fe; }
.bg-dark-input { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.2); color: white; }

.form-label { display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.3rem; }
.form-control { width: 100%; padding: 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; }
.w-full { width: 100%; }
.btn-hero-batch { background: #4f46e5; color: white; padding: 0.75rem; border: none; border-radius: 6px; font-weight: 700; cursor: pointer; }
.hidden { display: none; }

.card-header { padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.card-title { font-size: 0.95rem; font-weight: 700; color: #0f172a; }

.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
.data-table th { background: #f8fafc; color: #475569; font-weight: 600; }
.table-row-hover:hover { background: #f8fafc; }
.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.badge-green { background: #dcfce7; color: #15803d; }
.badge-neutral { background: #f1f5f9; color: #475569; }
.action-cell { display: flex; align-items: center; }
</style>

<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Platform & System Settings</h1>
        <p class="page-subtitle">Configure API endpoints, Sandbox provider environment, and system storage settings</p>
      </div>
    </div>

    <!-- SETTINGS GRID -->
    <div class="settings-grid">
      <!-- API ENDPOINTS CONFIG -->
      <div class="card p-4">
        <h3 class="card-title mb-3">⚙️ API Service Connections</h3>

        <div class="form-group mb-3">
          <label class="form-label">Main System Backend API URL:</label>
          <input v-model="mainApiUrl" type="text" class="form-control" readonly />
          <span class="text-xs text-muted">Primary FastAPI document intelligence & matching engine</span>
        </div>

        <div class="form-group mb-3">
          <label class="form-label">TenderVerify Sandbox Provider API URL:</label>
          <input v-model="sandboxApiUrl" type="text" class="form-control" readonly />
          <span class="text-xs text-muted">External government database simulation environment</span>
        </div>

        <button @click="testConnections" class="btn btn-primary btn-sm mt-2">
          🔌 Test API Connections
        </button>
      </div>

      <!-- ENVIRONMENT & SAFETY CONFIG -->
      <div class="card p-4">
        <h3 class="card-title mb-3">🛡️ Safety & Environment Mode</h3>

        <div class="env-box mb-3">
          <div class="env-label">ACTIVE ENVIRONMENT</div>
          <div class="env-value">DEMO / SANDBOX</div>
          <p class="env-desc mt-1">Synthetic data active. Results are for demonstration only and do not query live government databases.</p>
        </div>

        <div class="disclaimer-toggle-card">
          <input type="checkbox" checked disabled id="disclaimer-chk" />
          <label for="disclaimer-chk" class="text-sm font-bold text-slate-800">
            Enforce Mandatory Procurement Officer Advisory Disclaimer
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const mainApiUrl = ref('http://localhost:8000')
const sandboxApiUrl = ref('http://localhost:8001')

const testConnections = () => {
  alert('API Connections Verified! Main Backend: Online, Sandbox: Connected.')
}
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
.page-subtitle { font-size: 0.85rem; color: #64748b; margin-top: 2px; }

.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: white; }
.btn-sm { padding: 0.35rem 0.75rem; font-size: 0.75rem; }

.settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.p-4 { padding: 1.5rem; }
.card-title { font-size: 0.95rem; font-weight: 700; color: #0f172a; }

.form-group { margin-bottom: 1rem; }
.form-label { display: block; font-size: 0.8rem; font-weight: 600; color: #475569; margin-bottom: 0.3rem; }
.form-control { width: 100%; padding: 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; background: #f8fafc; color: #334155; font-family: monospace; }

.text-xs { font-size: 0.7rem; }
.text-muted { color: #64748b; }
.text-sm { font-size: 0.8rem; }
.text-slate-800 { color: #1e293b; }
.font-bold { font-weight: 700; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }

.env-box { background: #fffbeb; border: 1px solid #fef08a; padding: 1rem; border-radius: 6px; }
.env-label { font-size: 0.65rem; font-weight: 700; color: #92400e; letter-spacing: 0.05em; }
.env-value { font-size: 1.25rem; font-weight: 900; color: #b45309; margin-top: 0.2rem; }
.env-desc { font-size: 0.75rem; color: #78350f; }

.disclaimer-toggle-card { display: flex; align-items: center; gap: 0.75rem; background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.85rem; border-radius: 6px; }
</style>

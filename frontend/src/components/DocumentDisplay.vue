<template>
  <div class="document-display">
    <!-- Header Banner: Document-Level Status & Confidence % -->
    <div v-if="document" class="doc-header-banner">
      <div class="status-summary">
        <span class="status-badge" :class="docStatusClass">
          {{ docStatusText }}
        </span>
        <span v-if="document.extraction_confidence !== null && document.extraction_confidence !== undefined" class="confidence-pill">
          Confidence: {{ Math.round(document.extraction_confidence * 100) }}%
        </span>
      </div>
    </div>

    <div v-if="hasData" class="extracted-fields">
      <!-- Dynamic Schema Grid showing ALL fields (null -> 'Not detected') -->
      <div class="field-grid">
        <div 
          v-for="(val, key) in data" 
          :key="key" 
          class="field"
          :class="{ 
            'full-width': key === 'address' || key === 'principal_place_of_business' || key === 'registered_office_address' || key === 'product_name' || key === 'declaration_statement',
            'is-null': !val
          }"
        >
          <div class="field-header">
            <label>{{ formatFieldName(String(key)) }}</label>
            <span v-if="getFieldTrace(String(key))" class="field-status-tag" :class="fieldStatusClass(getFieldTrace(String(key)))">
              {{ getFieldTrace(String(key))?.status || (val ? 'VALID' : 'NOT_FOUND') }}
            </span>
          </div>
          <value :class="getValueClass(String(key), val)">
            {{ formatValue(String(key), val) }}
          </value>
        </div>
      </div>

      <!-- Debug Panels section -->
      <div class="debug-panels">
        <!-- Extraction Trace Collapsible Panel -->
        <details v-if="document.extraction_trace && document.extraction_trace.length" class="debug-panel" open>
          <summary class="debug-summary">
            📊 Field-Level Extraction Trace & Evidence
          </summary>
          <div class="trace-table-container">
            <table class="trace-table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Value</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Extraction Method</th>
                  <th>Source Evidence</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(t, idx) in document.extraction_trace" :key="idx">
                  <td><code>{{ t.field }}</code></td>
                  <td><span :class="{'null-text': !t.value}">{{ t.value || 'Not detected' }}</span></td>
                  <td>
                    <span class="field-status-tag" :class="fieldStatusClass(t)">
                      {{ t.status || (t.value ? 'VALID' : 'NOT_FOUND') }}
                    </span>
                  </td>
                  <td>
                    <span class="conf-text" :class="t.confidence >= 0.8 ? 'high-conf' : (t.confidence >= 0.5 ? 'mid-conf' : 'low-conf')">
                      {{ t.confidence !== undefined ? Math.round(t.confidence * 100) + '%' : 'N/A' }}
                    </span>
                  </td>
                  <td><span class="method-badge">{{ t.extraction_method || t.method }}</span></td>
                  <td class="evidence-cell">
                    <span v-if="t.source_evidence || t.evidence" class="evidence-text" :title="t.source_evidence || t.evidence">"{{ t.source_evidence || t.evidence }}"</span>
                    <span v-else class="null-text">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </details>

        <!-- Raw Text Collapsible Panel -->
        <details v-if="document.raw_text" class="debug-panel">
          <summary class="debug-summary">
            🔍 Raw Extracted Text (OCR / PDF Text)
          </summary>
          <pre class="raw-text-box">{{ document.raw_text }}</pre>
        </details>
      </div>
    </div>

    <div v-else class="no-data">
      <p>{{ extractorMessage }}</p>
      <details v-if="document.raw_text" class="debug-panel" style="margin-top: 1rem; text-align: left;">
        <summary class="debug-summary">🔍 View Raw Text</summary>
        <pre class="raw-text-box">{{ document.raw_text }}</pre>
      </details>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  document: any
}>()

const data = computed(() => props.document.extracted_data || {})
const hasData = computed(() => Object.keys(data.value).length > 0 && !data.value.note)
const extractorMessage = computed(() => data.value.note || 'No data extracted')

const docStatusText = computed(() => {
  const status = props.document?.status || 'UNKNOWN'
  if (status === 'EXTRACTED') return '✓ EXTRACTED'
  if (status === 'PARTIALLY_EXTRACTED') return '⚠ PARTIALLY EXTRACTED'
  if (status === 'EXTRACTION_FAILED' || status === 'FAILED') return '✗ EXTRACTION FAILED'
  return status
})

const docStatusClass = computed(() => {
  const status = props.document?.status || ''
  if (status === 'EXTRACTED') return 'badge-success'
  if (status === 'PARTIALLY_EXTRACTED') return 'badge-warning'
  if (status.includes('FAIL')) return 'badge-danger'
  return 'badge-neutral'
})

const getFieldTrace = (fieldName: string) => {
  if (!props.document?.extraction_trace) return null
  return props.document.extraction_trace.find((t: any) => t.field === fieldName)
}

const fieldStatusClass = (t: any) => {
  if (!t) return 'tag-neutral'
  const st = t.status || (t.value ? 'VALID' : 'NOT_FOUND')
  if (st === 'VALID') return 'tag-valid'
  if (st === 'INVALID') return 'tag-invalid'
  if (st === 'NOT_FOUND') return 'tag-missing'
  return 'tag-neutral'
}

const formatFieldName = (key: string) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatValue = (key: string, val: any) => {
  if (val === null || val === undefined || val === '') {
    return 'Not detected'
  }
  if (key.includes('turnover') || key.includes('capital') || key.includes('income') || key.includes('tax_paid')) {
    if (typeof val === 'string' && !val.startsWith('₹') && !val.startsWith('Rs')) {
      return `₹${val}`
    }
  }
  return val
}

const getValueClass = (key: string, val: any) => {
  if (!val) return 'val-not-detected'
  if (key === 'status') {
    const lower = String(val).toLowerCase()
    if (lower.includes('active') || lower.includes('valid') || lower.includes('regular')) return 'status-active'
    if (lower.includes('cancel') || lower.includes('expired') || lower.includes('inactive')) return 'status-inactive'
  }
  return ''
}
</script>

<style scoped>
.document-display {
  padding: 0.5rem 0;
}

.doc-header-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f1f5f9;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  border-left: 4px solid #3b82f6;
}

.status-summary {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.status-badge {
  font-weight: 700;
  font-size: 0.8rem;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.badge-danger {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.badge-neutral {
  background: #e2e8f0;
  color: #475569;
}

.confidence-pill {
  font-size: 0.82rem;
  font-weight: 600;
  color: #1e293b;
  background: #ffffff;
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field.full-width {
  grid-column: 1 / -1;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.field label {
  font-weight: 600;
  color: #555;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field value {
  font-size: 0.95rem;
  color: #2c3e50;
  padding: 0.65rem 0.85rem;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #667eea;
  word-break: break-word;
}

.field.is-null value,
.val-not-detected {
  color: #999 !important;
  font-style: italic;
  border-left-color: #cbd5e0 !important;
  background: #f1f5f9;
}

.status-active {
  color: #15803d !important;
  font-weight: 600;
  background: #f0fdf4 !important;
  border-left-color: #22c55e !important;
}

.status-inactive {
  color: #b91c1c !important;
  font-weight: 600;
  background: #fef2f2 !important;
  border-left-color: #ef4444 !important;
}

.field-status-tag {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.tag-valid {
  background: #dcfce7;
  color: #15803d;
}

.tag-invalid {
  background: #fee2e2;
  color: #b91c1c;
}

.tag-missing {
  background: #f1f5f9;
  color: #64748b;
}

.tag-neutral {
  background: #e2e8f0;
  color: #475569;
}

.debug-panels {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.debug-panel {
  background: #1e293b;
  color: #f8fafc;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}

.debug-summary {
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  color: #38bdf8;
  user-select: none;
}

.raw-text-box {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 6px;
  font-family: monospace;
  font-size: 0.82rem;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

.trace-table-container {
  margin-top: 0.75rem;
  overflow-x: auto;
}

.trace-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  text-align: left;
}

.trace-table th,
.trace-table td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #334155;
}

.trace-table th {
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.trace-table code {
  color: #f472b6;
  font-family: monospace;
}

.method-badge {
  background: #334155;
  color: #38bdf8;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.78rem;
  font-family: monospace;
}

.conf-text {
  font-weight: 700;
  font-size: 0.8rem;
}

.high-conf {
  color: #4ade80;
}

.mid-conf {
  color: #fbbf24;
}

.low-conf {
  color: #f87171;
}

.evidence-cell {
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.evidence-text {
  color: #cbd5e1;
  font-style: italic;
  font-size: 0.8rem;
}

.null-text {
  color: #64748b;
  font-style: italic;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: #999;
  font-style: italic;
}
</style>


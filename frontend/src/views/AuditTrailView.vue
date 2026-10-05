<template>
  <div class="page-container">
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Audit Trail & Event Log</h1>
        <p class="page-subtitle">Immutable chronological audit log of all system extraction, verification, officer review, and report generation events.</p>
      </div>

      <button @click="refreshAudit" class="btn btn-outline" :disabled="loading">
        {{ loading ? '⏳ Loading...' : '🔄 Refresh Timeline' }}
      </button>
    </div>

    <!-- LOADING STATE -->
    <div v-if="loading && auditEvents.length === 0" class="card p-4">
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading audit events...</p>
      </div>
    </div>

    <!-- ERROR STATE -->
    <div v-else-if="error" class="card p-4">
      <div class="error-state">
        <span class="error-icon">❌</span>
        <div>
          <strong>Failed to Load Audit Trail</strong>
          <p>{{ error }}</p>
          <button @click="refreshAudit" class="btn btn-primary mt-2">Retry</button>
        </div>
      </div>
    </div>

    <!-- EMPTY STATE -->
    <div v-else-if="auditEvents.length === 0" class="card p-4">
      <div class="empty-state">
        <span class="empty-icon">📋</span>
        <p>No audit events found for this tender and bidder.</p>
        <p class="hint">Perform operations (upload documents, run compliance, etc.) to generate audit events.</p>
      </div>
    </div>

    <!-- TIMELINE CARD -->
    <div v-else class="card p-4">
      <div class="card-header border-none p-0 mb-4 flex-between">
        <h3 class="card-title">Chronological Event Timeline</h3>
        <span class="badge badge-neutral">{{ auditEvents.length }} Event(s) | Tender: {{ tenderId }}</span>
      </div>

      <div class="timeline-container">
        <div v-for="(event, idx) in auditEvents" :key="event.id" class="timeline-item">
          <div class="timeline-time font-mono">{{ formatTime(event.timestamp) }}</div>

          <div class="timeline-marker">
            <span :class="['marker-dot', getMarkerClass(event.event_type)]"></span>
            <div class="marker-line" v-if="idx < auditEvents.length - 1"></div>
          </div>

          <div class="timeline-content">
            <div class="event-title-row">
              <strong class="event-action">{{ event.action_description }}</strong>
              <span :class="['status-pill', getPillClass(event.event_type)]">{{ formatEventType(event.event_type) }}</span>
            </div>

            <div class="event-meta mt-1">
              <span v-if="event.user_name">Actor: <strong>{{ event.user_name }}</strong></span>
              <span v-else-if="event.user_id">Actor: <strong>{{ event.user_id }}</strong></span>
              <span v-else>Actor: <strong>System</strong></span>
              <span>Event: <code class="source-code">{{ event.event_type }}</code></span>
            </div>

            <div v-if="event.metadata" class="event-metadata mt-2">
              <details>
                <summary class="metadata-summary">View Details</summary>
                <pre class="metadata-content">{{ formatMetadata(event.metadata) }}</pre>
              </details>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { decisionApi, AuditLogEntry } from '../api/decisionApi'
import { tenderApi } from '../api/tenderApi'
import { useBidderStore } from '../stores/bidder'

const bidderStore = useBidderStore()
const tenderId = ref<string>('')
const bidderId = ref(bidderStore.currentBidderId)
const auditEvents = ref<AuditLogEntry[]>([])
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  await initAndLoadEvents()
})

watch(() => bidderStore.currentBidderId, async (newId) => {
  bidderId.value = newId
  await loadAuditEvents()
})

const initAndLoadEvents = async () => {
  try {
    const tenders = await tenderApi.listTenders()
    if (tenders && tenders.length > 0) {
      tenderId.value = tenders[0].tender_id
    } else {
      tenderId.value = ''
    }
  } catch (e) {
    console.error('Failed to load tenders for audit trail:', e)
  }
  await loadAuditEvents()
}

const loadAuditEvents = async () => {
  loading.value = true
  error.value = ''
  try {
    // Load audit events for current tender and bidder
    const events = await decisionApi.getAuditLogs(
      tenderId.value || undefined,
      bidderId.value || undefined,
      undefined, // No event type filter - get all events
      100 // Limit to 100 most recent events
    )
    auditEvents.value = events
  } catch (e: any) {
    console.error('Failed to load audit events:', e)
    error.value = e.response?.data?.detail || 'Failed to load audit trail. Please try again.'
  } finally {
    loading.value = false
  }
}

const refreshAudit = async () => {
  await loadAuditEvents()
}

const formatTime = (timestamp: string): string => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

const formatEventType = (eventType: string): string => {
  // Convert SNAKE_CASE to Title Case
  return eventType
    .split('_')
    .map(word => word.charAt(0) + word.slice(1).toLowerCase())
    .join(' ')
}

const formatMetadata = (metadata: string): string => {
  try {
    return JSON.stringify(JSON.parse(metadata), null, 2)
  } catch {
    return metadata
  }
}

const getMarkerClass = (eventType: string) => {
  // Map event types to colors
  const successEvents = [
    'BIDDER_DOCUMENTS_UPLOADED',
    'TENDER_UPLOADED',
    'REQUIREMENTS_EXTRACTED',
    'VERIFICATION_COMPLETED',
    'COMPLIANCE_EVALUATED',
    'RISK_ASSESSED'
  ]

  const warningEvents = [
    'REQUIREMENT_EDITED'
  ]

  const criticalEvents = [
    'DECISION_MADE'
  ]

  if (successEvents.includes(eventType)) return 'bg-green'
  if (criticalEvents.includes(eventType)) return 'bg-blue'
  if (warningEvents.includes(eventType)) return 'bg-amber'
  return 'bg-neutral'
}

const getPillClass = (eventType: string) => {
  const successEvents = [
    'BIDDER_DOCUMENTS_UPLOADED',
    'TENDER_UPLOADED',
    'REQUIREMENTS_EXTRACTED',
    'VERIFICATION_COMPLETED',
    'COMPLIANCE_EVALUATED',
    'RISK_ASSESSED'
  ]

  const criticalEvents = [
    'DECISION_MADE'
  ]

  if (successEvents.includes(eventType)) return 'pill-verified'
  if (criticalEvents.includes(eventType)) return 'pill-decision'
  return 'pill-review'
}
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.page-title { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
.page-subtitle { font-size: 0.85rem; color: #64748b; margin-top: 2px; }

.btn { padding: 0.55rem 1.1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; }
.btn-outline { background: white; border: 1px solid #cbd5e1; color: #334155; }
.btn-primary { background: #2563eb; color: white; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.p-4 { padding: 1.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.flex-between { display: flex; justify-content: space-between; align-items: center; }

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #64748b;
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

.error-state {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  justify-content: center;
  color: #991b1b;
}

.error-icon {
  font-size: 1.5rem;
}

.empty-state {
  color: #64748b;
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.hint {
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.timeline-container { display: flex; flex-direction: column; gap: 1rem; margin-top: 0.5rem; }
.timeline-item { display: grid; grid-template-columns: 90px 30px 1fr; align-items: flex-start; }
.timeline-time { font-size: 0.8rem; font-weight: 700; color: #64748b; padding-top: 2px; }

.timeline-marker { display: flex; flex-direction: column; align-items: center; height: 100%; }
.marker-dot { width: 12px; height: 12px; border-radius: 50%; z-index: 2; margin-top: 4px; }
.marker-line { width: 2px; flex: 1; background: #e2e8f0; margin-top: 2px; }

.timeline-content { background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.75rem 1rem; border-radius: 6px; }
.event-title-row { display: flex; justify-content: space-between; align-items: center; }
.event-action { font-size: 0.85rem; color: #0f172a; }

.event-meta { font-size: 0.75rem; color: #64748b; display: flex; gap: 1.5rem; }
.source-code { font-family: monospace; background: #e2e8f0; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.7rem; color: #334155; }

.event-metadata {
  font-size: 0.75rem;
  margin-top: 0.5rem;
}

.metadata-summary {
  cursor: pointer;
  color: #2563eb;
  font-weight: 600;
  user-select: none;
}

.metadata-content {
  margin-top: 0.5rem;
  background: #f1f5f9;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  overflow-x: auto;
  color: #334155;
}

.bg-green { background: #16a34a; }
.bg-amber { background: #d97706; }
.bg-blue { background: #2563eb; }
.bg-neutral { background: #64748b; }

.status-pill { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px; font-weight: 700; font-size: 0.7rem; }
.pill-verified { background: #dcfce7; color: #15803d; }
.pill-decision { background: #dbeafe; color: #1e40af; }
.pill-review { background: #fef08a; color: #a16207; }
.badge-neutral { background: #f1f5f9; color: #475569; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; }
.font-mono { font-family: monospace; }
</style>

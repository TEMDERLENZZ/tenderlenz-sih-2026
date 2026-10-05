<template>
  <div id="app" class="enterprise-app">
    <!-- PERMANENT LEFT SIDEBAR -->
    <aside class="app-sidebar">
      <div class="sidebar-header">
        <div class="logo-box">
          <div class="logo-icon">🛡️</div>
          <div>
            <h1 class="logo-title">Tender Compliance</h1>
            <div class="logo-subtitle">AI Procurement Intelligence</div>
          </div>
        </div>
      </div>

      <!-- MAIN NAVIGATION -->
      <nav class="sidebar-nav">
        <div class="nav-section-label">PLATFORM</div>
        <RouterLink to="/" class="nav-item" active-class="active">
          <span class="nav-icon">📊</span> Executive Dashboard
        </RouterLink>

        <RouterLink to="/tenders-list" class="nav-item" active-class="active">
          <span class="nav-icon">📁</span> Tenders & Upload
        </RouterLink>

        <RouterLink to="/requirements" class="nav-item" active-class="active">
          <span class="nav-icon">📋</span> Requirements
        </RouterLink>

        <RouterLink to="/officer-review" class="nav-item" active-class="active">
          <span class="nav-icon">🧐</span> Officer Review
        </RouterLink>

        <div class="nav-section-label">VERIFICATION & ANALYSIS</div>
        <RouterLink to="/bidder-verification" class="nav-item" active-class="active">
          <span class="nav-icon">🔍</span> Bidder Verification
        </RouterLink>

        <RouterLink to="/external-verification" class="nav-item" active-class="active">
          <span class="nav-icon">⚡</span> External Verification
        </RouterLink>

        <RouterLink to="/cross-checks" class="nav-item" active-class="active">
          <span class="nav-icon">🔀</span> Document Cross-Checks
        </RouterLink>

        <RouterLink to="/compliance-analysis" class="nav-item" active-class="active">
          <span class="nav-icon">⚖️</span> Compliance Analysis
        </RouterLink>

        <div class="nav-section-label">INTELLIGENCE & GOVERNANCE</div>
        <RouterLink to="/evidence-center" class="nav-item" active-class="active">
          <span class="nav-icon">📑</span> Evidence Center
        </RouterLink>

        <RouterLink to="/audit-trail" class="nav-item" active-class="active">
          <span class="nav-icon">📜</span> Audit Trail
        </RouterLink>

        <RouterLink to="/reports" class="nav-item" active-class="active">
          <span class="nav-icon">📄</span> Final Reports
        </RouterLink>

        <RouterLink to="/settings" class="nav-item" active-class="active">
          <span class="nav-icon">⚙️</span> Settings
        </RouterLink>
      </nav>

      <!-- BOTTOM SYSTEM STATUS BOX -->
      <div class="sidebar-footer">
        <div class="status-card">
          <div class="status-row">
            <span class="status-label">Main System</span>
            <span class="status-pill status-online">● Online</span>
          </div>
          <div class="status-row">
            <span class="status-label">Sandbox Provider</span>
            <span :class="['status-pill', sandboxConnected ? 'status-online' : 'status-offline']">
              ● {{ sandboxConnected ? 'Connected' : 'Offline' }}
            </span>
          </div>
        </div>

        <div class="env-banner">
          <div class="env-title">ENVIRONMENT</div>
          <div class="env-val">DEMO / SANDBOX</div>
          <div class="env-note">Synthetic Data • Not Live Govt Source</div>
        </div>
      </div>
    </aside>

    <!-- MAIN CONTENT WRAPPER -->
    <div class="main-wrapper">
      <!-- TOP HEADER -->
      <header class="app-topbar">
        <div class="topbar-left">
          <div class="info-block">
            <span class="block-label">CURRENT BIDDER:</span>
            <span v-if="bidderStore.currentBidderId" class="block-val">{{ bidderStore.currentBidderName }}</span>
            <code v-if="bidderStore.currentBidderId" class="block-code">{{ bidderStore.currentBidderId }}</code>
            <span v-else class="block-val text-muted-sm">No bidder selected</span>
            <button class="switch-bidder-btn" @click="bidderStore.openSwitcher()" title="Switch or Register Bidder">
              ⇄ {{ bidderStore.currentBidderId ? 'Switch' : 'Add Bidder' }}
            </button>
          </div>
        </div>

        <div class="topbar-right">
          <div class="sandbox-badge-btn" @click="checkSandbox">
            <span :class="['dot', sandboxConnected ? 'dot-green' : 'dot-red']"></span>
            Sandbox Provider: <strong>{{ sandboxConnected ? 'Connected' : 'Offline' }}</strong>
          </div>

          <button class="icon-btn" title="Notifications">
            🔔 <span class="badge-count">3</span>
          </button>

          <!-- Phase 7: Show authenticated user or logout -->
          <div v-if="authStore.isAuthenticated" class="officer-profile">
            <div class="avatar">{{ authStore.currentUsername.substring(0, 2).toUpperCase() }}</div>
            <div class="officer-details">
              <span class="officer-name">{{ authStore.currentUsername }}</span>
              <span class="officer-role">{{ authStore.user?.role || 'User' }}</span>
            </div>
            <button @click="handleLogout" class="logout-btn" title="Logout">🚪</button>
          </div>
        </div>
      </header>

      <!-- BIDDER SWITCHER MODAL -->
      <div v-if="bidderStore.switcherOpen" class="bidder-modal-backdrop" @click.self="bidderStore.closeSwitcher()">
        <div class="bidder-modal-card">
          <div class="bidder-modal-header">
            <h3>⇄ Switch / Register Bidder</h3>
            <button @click="bidderStore.closeSwitcher()" class="modal-close-btn">×</button>
          </div>

          <!-- Existing bidders list -->
          <div class="bidder-modal-section">
            <div class="modal-section-label">EXISTING BIDDERS</div>
            <div class="bidder-list">
              <div
                v-for="b in bidderStore.bidders"
                :key="b.id"
                :class="['bidder-list-item', { active: b.id === bidderStore.currentBidderId }]"
                @click="bidderStore.selectBidder(b.id)"
              >
                <div class="bidder-item-info">
                  <span class="bidder-item-name">{{ b.name }}</span>
                  <code class="bidder-item-id">{{ b.id }}</code>
                </div>
                <span v-if="b.id === bidderStore.currentBidderId" class="active-badge">● Active</span>
              </div>
            </div>
          </div>

          <!-- Register new bidder -->
          <div class="bidder-modal-section">
            <div class="modal-section-label">REGISTER NEW BIDDER</div>
            <div class="register-form">
              <input
                v-model="bidderStore.newBidderId"
                type="text"
                placeholder="Bidder ID (e.g. BIDDER_002)"
                class="modal-input"
              />
              <input
                v-model="bidderStore.newBidderName"
                type="text"
                placeholder="Company Name (e.g. XYZ Corp Pvt Ltd)"
                class="modal-input"
              />
              <button
                @click="bidderStore.registerBidder(bidderStore.newBidderId, bidderStore.newBidderName)"
                :disabled="!bidderStore.newBidderId.trim() || !bidderStore.newBidderName.trim()"
                class="register-btn"
              >
                ✚ Register &amp; Switch to New Bidder
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- PAGE ROUTER VIEW -->
      <main class="app-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView, RouterLink, useRouter } from 'vue-router'
import { sandboxApi } from './api/sandboxApi'
import { useBidderStore } from './stores/bidder'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const sandboxConnected = ref(true)
const bidderStore = useBidderStore()
const authStore = useAuthStore()

const checkSandbox = async () => {
  const conn = await sandboxApi.checkConnection()
  sandboxConnected.value = conn.connected
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  checkSandbox()
})
</script>

<style>
/* GLOBAL ENTERPRISE DESIGN SYSTEM STYLES */
:root {
  --bg-app: #f8fafc;
  --bg-sidebar: #0f172a;
  --bg-sidebar-hover: #1e293b;
  --bg-card: #ffffff;
  --border-color: #e2e8f0;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --text-light: #94a3b8;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  
  --color-success: #16a34a;
  --color-success-bg: #f0fdf4;
  --color-success-border: #bbf7d0;

  --color-danger: #dc2626;
  --color-danger-bg: #fef2f2;
  --color-danger-border: #fecaca;

  --color-amber: #d97706;
  --color-amber-bg: #fffbeb;
  --color-amber-border: #fef08a;

  --color-blue: #2563eb;
  --color-blue-bg: #eff6ff;
  --color-blue-border: #bfdbfe;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg-app);
  color: var(--text-main);
  -webkit-font-smoothing: antialiased;
}

.enterprise-app {
  display: flex;
  min-height: 100vh;
}

/* SIDEBAR STYLES */
.app-sidebar {
  width: 260px;
  background-color: var(--bg-sidebar);
  color: #f8fafc;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 100;
  border-right: 1px solid #1e293b;
}

.sidebar-header {
  padding: 1.25rem;
  border-bottom: 1px solid #1e293b;
}

.logo-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  font-size: 1.5rem;
}

.logo-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.01em;
}

.logo-subtitle {
  font-size: 0.7rem;
  color: #94a3b8;
  font-weight: 500;
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0.75rem;
  overflow-y: auto;
}

.nav-section-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.08em;
  padding: 0.75rem 0.75rem 0.35rem 0.75rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  color: #cbd5e1;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.15s ease-in-out;
  margin-bottom: 2px;
}

.nav-item:hover {
  background-color: var(--bg-sidebar-hover);
  color: #ffffff;
}

.nav-item.active {
  background-color: #2563eb;
  color: #ffffff;
  font-weight: 600;
}

.nav-icon {
  font-size: 1rem;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid #1e293b;
  background-color: #090d16;
}

.status-card {
  background-color: #1e293b;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  margin-bottom: 0.75rem;
  font-size: 0.75rem;
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.3rem;
}

.status-row:last-child {
  margin-bottom: 0;
}

.status-label {
  color: #94a3b8;
}

.status-pill {
  font-weight: 600;
  font-size: 0.7rem;
}

.status-online { color: #4ade80; }
.status-offline { color: #f87171; }
.text-muted-sm { color: #94a3b8; font-style: italic; font-size: 0.8rem; }

.env-banner {
  background: rgba(30, 41, 59, 0.5);
  border: 1px dashed #334155;
  border-radius: 6px;
  padding: 0.5rem;
  text-align: center;
}

.env-title {
  font-size: 0.6rem;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.05em;
}

.env-val {
  font-size: 0.75rem;
  font-weight: 800;
  color: #facc15;
}

.env-note {
  font-size: 0.65rem;
  color: #64748b;
  margin-top: 2px;
}

/* MAIN WRAPPER STYLES */
.main-wrapper {
  margin-left: 260px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* TOPBAR STYLES */
.app-topbar {
  height: 60px;
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  position: sticky;
  top: 0;
  z-index: 90;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.info-block {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
}

.block-label {
  color: var(--text-muted);
  font-weight: 600;
  font-size: 0.7rem;
}

.block-val {
  font-weight: 700;
  color: var(--text-main);
}

.block-code {
  background: #f1f5f9;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.75rem;
  color: #475569;
}

.divider {
  height: 20px;
  width: 1px;
  background: var(--border-color);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.sandbox-badge-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f8fafc;
  border: 1px solid var(--border-color);
  padding: 0.35rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  color: var(--text-muted);
  cursor: pointer;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.dot-green { background: #16a34a; }
.dot-red { background: #dc2626; }

.icon-btn {
  background: none;
  border: 1px solid var(--border-color);
  width: 34px;
  height: 34px;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

.badge-count {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #dc2626;
  color: white;
  font-size: 0.6rem;
  font-weight: 800;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.officer-profile {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-left: 1px solid var(--border-color);
  padding-left: 1rem;
}

.avatar {
  width: 32px;
  height: 32px;
  background: #1e293b;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}

.officer-details {
  display: flex;
  flex-direction: column;
}

.officer-name {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-main);
  line-height: 1.1;
}

.officer-role {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.logout-btn {
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.15s;
  margin-left: 0.5rem;
}

.logout-btn:hover {
  background: #fef2f2;
  border-color: #dc2626;
  color: #dc2626;
}

.app-content {
  padding: 1.5rem;
  flex: 1;
}

/* Switch Bidder button in topbar */
.switch-bidder-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.2rem 0.55rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;
  margin-left: 4px;
  transition: background 0.15s;
}
.switch-bidder-btn:hover { background: #1d4ed8; }

/* Bidder Switcher Modal */
.bidder-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bidder-modal-card {
  background: #fff;
  width: 480px;
  max-height: 80vh;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.35);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: modalPop 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalPop {
  from { transform: scale(0.9); opacity: 0; }
  to   { transform: scale(1);   opacity: 1; }
}

.bidder-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: #0f172a;
  color: white;
}

.bidder-modal-header h3 {
  font-size: 1rem;
  font-weight: 700;
  margin: 0;
}

.modal-close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.4rem;
  cursor: pointer;
  line-height: 1;
}
.modal-close-btn:hover { color: white; }

.bidder-modal-section {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-section-label {
  font-size: 0.65rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.08em;
  margin-bottom: 0.6rem;
}

.bidder-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 160px;
  overflow-y: auto;
}

.bidder-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.85rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.12s;
}
.bidder-list-item:hover { background: #f8fafc; border-color: #94a3b8; }
.bidder-list-item.active { background: #eff6ff; border-color: #2563eb; }

.bidder-item-info { display: flex; flex-direction: column; gap: 2px; }
.bidder-item-name { font-weight: 700; font-size: 0.85rem; color: #0f172a; }
.bidder-item-id { font-family: monospace; font-size: 0.75rem; color: #475569; background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; }
.active-badge { font-size: 0.7rem; font-weight: 700; color: #16a34a; }

.register-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.modal-input {
  padding: 0.6rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.15s;
}
.modal-input:focus { border-color: #2563eb; }

.register-btn {
  padding: 0.65rem;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.875rem;
  cursor: pointer;
  transition: opacity 0.15s;
}
.register-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.register-btn:not(:disabled):hover { opacity: 0.9; }
</style>


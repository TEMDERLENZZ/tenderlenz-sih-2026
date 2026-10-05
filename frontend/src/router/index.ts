import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import ExecutiveDashboardView from '../views/ExecutiveDashboardView.vue'
import TenderUploadWorkflowView from '../views/TenderUploadWorkflowView.vue'
import TenderRequirementsView from '../views/TenderRequirementsView.vue'
import OfficerReviewView from '../views/OfficerReviewView.vue'
import BidderVerificationView from '../views/BidderVerificationView.vue'
import ExternalVerificationView from '../views/ExternalVerificationView.vue'
import DocumentCrossChecksView from '../views/DocumentCrossChecksView.vue'
import ComplianceEngineView from '../views/ComplianceEngineView.vue'
import RiskAssessmentView from '../views/RiskAssessmentView.vue'
import EvidenceCenterView from '../views/EvidenceCenterView.vue'
import AuditTrailView from '../views/AuditTrailView.vue'
import FinalReportView from '../views/FinalReportView.vue'
import SettingsView from '../views/SettingsView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Public route - no auth required
    { path: '/login', name: 'login', component: LoginView },

    // Protected routes - require authentication
    { path: '/', name: 'executive-dashboard', component: ExecutiveDashboardView, meta: { requiresAuth: true } },
    { path: '/tenders-list', name: 'tenders-list', component: TenderUploadWorkflowView, meta: { requiresAuth: true } },
    { path: '/requirements', name: 'requirements', component: TenderRequirementsView, meta: { requiresAuth: true } },
    { path: '/officer-review', name: 'officer-review', component: OfficerReviewView, meta: { requiresAuth: true } },
    { path: '/bidder-verification', name: 'bidder-verification', component: BidderVerificationView, meta: { requiresAuth: true } },
    { path: '/external-verification', name: 'external-verification', component: ExternalVerificationView, meta: { requiresAuth: true } },
    { path: '/cross-checks', name: 'cross-checks', component: DocumentCrossChecksView, meta: { requiresAuth: true } },
    { path: '/compliance-analysis', name: 'compliance-analysis', component: ComplianceEngineView, meta: { requiresAuth: true } },
    { path: '/risk-assessment', name: 'risk-assessment', component: RiskAssessmentView, meta: { requiresAuth: true } },
    { path: '/evidence-center', name: 'evidence-center', component: EvidenceCenterView, meta: { requiresAuth: true } },
    { path: '/audit-trail', name: 'audit-trail', component: AuditTrailView, meta: { requiresAuth: true } },
    { path: '/reports', name: 'reports', component: FinalReportView, meta: { requiresAuth: true } },
    { path: '/settings', name: 'settings', component: SettingsView, meta: { requiresAuth: true } }
  ]
})

// Navigation guard - Phase 7 authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Public route - allow access
  if (to.name === 'login') {
    // If already authenticated, redirect to dashboard
    if (authStore.isAuthenticated) {
      next({ name: 'executive-dashboard' })
      return
    }
    next()
    return
  }

  // Protected route - check authentication
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // Not authenticated - redirect to login
      next({ name: 'login' })
      return
    }
  }

  // Allow navigation
  next()
})

export default router

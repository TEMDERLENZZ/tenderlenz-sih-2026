/**
 * Global Bidder Store — Single Source of Truth
 * All views must read/write the current bidder from this store.
 * Never use hardcoded BIDDER_001 or localStorage in individual views.
 */
import { defineStore } from 'pinia'
import axios from 'axios'

export interface BidderRecord {
  id: string
  name: string
  createdAt: string
}

// Fresh state — no pre-seeded bidders. All data must come from user input or real backend.
const INITIAL_BIDDERS: BidderRecord[] = []

export const useBidderStore = defineStore('bidder', {
  state: () => ({
    // The one currently active bidder for the entire UI
    // Starts empty — user must register or select a bidder
    currentBidderId: '' as string,
    currentBidderName: '' as string,

    // Registered bidders list — in-memory only, no localStorage
    bidders: [...INITIAL_BIDDERS] as BidderRecord[],

    // Whether the bidder switcher modal is open
    switcherOpen: false,

    // New-bidder registration form state
    newBidderId: '',
    newBidderName: '',

    // Document summary for the current bidder (fetched from API per-bidder)
    summary: null as any,
    summaryLoading: false,
    summaryError: null as string | null,
  }),

  getters: {
    currentBidder: (state): BidderRecord | undefined =>
      state.bidders.find(b => b.id === state.currentBidderId),
  },

  actions: {
    /**
     * Switch the active bidder. Clears stale summary so views re-fetch fresh data.
     */
    selectBidder(bidderId: string) {
      const found = this.bidders.find(b => b.id === bidderId)
      if (!found) {
        console.warn(`[BidderStore] Bidder ${bidderId} not found in registered list`)
        return
      }
      this.currentBidderId = bidderId
      this.currentBidderName = found.name
      // CRITICAL: reset summary so every view fetches data for the NEW bidder
      this.summary = null
      this.summaryError = null
      this.switcherOpen = false
      console.log(`[BidderStore] Switched to bidder: ${bidderId}`)
    },

    /**
     * Register a new bidder and immediately select it.
     * A brand-new bidder starts with zero documents — the backend has no records for it yet.
     */
    registerBidder(bidderId: string, bidderName: string) {
      const trimmedId = bidderId.trim()
      const trimmedName = bidderName.trim()
      if (!trimmedId || !trimmedName) return

      const existing = this.bidders.find(b => b.id === trimmedId)
      if (!existing) {
        this.bidders.push({
          id: trimmedId,
          name: trimmedName,
          createdAt: new Date().toISOString()
        })
      }
      this.newBidderId = ''
      this.newBidderName = ''
      this.selectBidder(trimmedId)
    },

    openSwitcher() {
      this.switcherOpen = true
    },

    closeSwitcher() {
      this.switcherOpen = false
      this.newBidderId = ''
      this.newBidderName = ''
    },

    /**
     * Fetch the document summary for the CURRENT bidder from the backend.
     * Always scoped by currentBidderId — never a hardcoded value.
     */
    async fetchSummary() {
      if (!this.currentBidderId) return
      this.summaryLoading = true
      this.summaryError = null
      try {
        const res = await axios.get(`/api/documents/bidder/${this.currentBidderId}/summary`)
        this.summary = res.data
      } catch (e: any) {
        this.summaryError = e.response?.data?.detail || 'Failed to load summary'
        this.summary = null
      } finally {
        this.summaryLoading = false
      }
    },
  }
})

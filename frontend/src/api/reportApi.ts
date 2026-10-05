import { tenderApi, TenderComplianceSummary } from './tenderApi'

export const reportApi = {
  async generateExportPayload(tenderId: string, bidderId: string, bidderName?: string) {
    const summary: TenderComplianceSummary = await tenderApi.getComplianceSummary(tenderId, bidderId)
    
    return {
      metadata: {
        report_title: "FINAL TENDER COMPLIANCE REPORT",
        tender_id: tenderId,
        tender_name: "Demo Procurement Tender (IT Equipment & Services)",
        bidder_id: bidderId,
        bidder_name: bidderName || bidderId,
        generated_at: new Date().toISOString(),
        system_version: "Tender Compliance Copilot v1.0",
        environment: "SANDBOX / DEMO"
      },
      summary_metrics: {
        total_requirements: summary.total_requirements,
        satisfied: summary.satisfied,
        not_satisfied: summary.not_satisfied,
        missing: summary.missing,
        review_required: summary.review_required,
        unable_to_verify: summary.unable_to_verify,
        compliance_percentage: summary.compliance_percentage
      },
      disclaimer: summary.disclaimer,
      requirements: summary.results
    }
  },

  downloadJsonReport(data: any, filename = 'compliance_report.json') {
    const jsonStr = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }
}

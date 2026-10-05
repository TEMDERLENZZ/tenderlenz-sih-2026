"""
End-to-End API Integration Test for Phase 6 Tender Requirement Engine
Tests all FastAPI endpoints created for Phase 6.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

from app.main import app

class TestPhase6APIE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Login as demo officer to obtain Bearer token
        res = cls.client.post("/api/auth/login", json={"username": "officer1", "password": "demo123"})
        token = res.json()["access_token"]
        cls.headers = {"Authorization": f"Bearer {token}"}

    def test_01_root_and_health(self):
        """Test root and health endpoints mention Phase 6"""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("phase_6", data)

        res_health = self.client.get("/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["phase"], "6")

    def test_02_seed_demo_tender_api(self):
        """Test POST /api/tenders/seed-demo"""
        res = self.client.post("/api/tenders/seed-demo", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["tender_id"], "DEMO_TENDER_001")

    def test_03_get_requirements_api(self):
        """Test GET /api/tenders/{tender_id}/requirements"""
        res = self.client.get("/api/tenders/DEMO_TENDER_001/requirements", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        reqs = res.json()
        self.assertGreaterEqual(len(reqs), 6)
        codes = [r["requirement_code"] for r in reqs]
        self.assertIn("REQ-001", codes)

    def test_04_update_requirement_api(self):
        """Test PUT /api/tenders/requirements/{requirement_id} (Procurement Officer Review)"""
        reqs = self.client.get("/api/tenders/DEMO_TENDER_001/requirements", headers=self.headers).json()
        req_id = reqs[0]["id"]

        update_payload = {
            "title": "Minimum Annual Turnover (Reviewed by Officer)",
            "mandatory": True,
            "required_value": 50000000
        }
        res = self.client.put(f"/api/tenders/requirements/{req_id}", json=update_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["title"], "Minimum Annual Turnover (Reviewed by Officer)")

    def test_05_evaluate_bidder_api(self):
        """Test POST /api/tenders/{tender_id}/bidders/{bidder_id}/evaluate"""
        res = self.client.post("/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/evaluate", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["tender_id"], "DEMO_TENDER_001")
        self.assertEqual(data["bidder_id"], "BIDDER_001")
        self.assertIn("satisfied", data)
        self.assertIn("disclaimer", data)
        self.assertIn("Final procurement decision remains with the authorized Procurement Officer.", data["disclaimer"])

    def test_06_get_compliance_summary_api(self):
        """Test GET /api/tenders/{tender_id}/bidders/{bidder_id}/compliance"""
        res = self.client.get("/api/tenders/DEMO_TENDER_001/bidders/BIDDER_001/compliance", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total_requirements"], 6)

if __name__ == "__main__":
    unittest.main()

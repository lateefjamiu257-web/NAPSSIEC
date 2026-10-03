import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.stdout.reconfigure(encoding='utf-8')

# Ensure app is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import init_db, get_db, save_smtp_config
from app.mailer import send_token_email, verify_smtp_connection
import app.main as main_module
from fastapi.testclient import TestClient

class TestEmailDispatchAndTokenVisibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(main_module.app)

    def test_01_smtp_unconfigured_status(self):
        """When SMTP is not configured, send_token_email must return 'NOT_SENT' and NOT 'sent'"""
        print("\n[TEST 1] Testing unconfigured SMTP...")
        save_smtp_config(host="smtp.gmail.com", port=587, user="", pass_="", sender_name="Test", base_url="http://test")
        res = send_token_email(
            to_email="test.student@example.com",
            voter_name="Test Student",
            matric_number="POS/2022/9999",
            level="300 Level",
            token="TEST-TOKEN-9999",
            election_title="Test Election"
        )
        self.assertIn(res.get("status").upper(), ["NOT_SENT", "ERROR", "FAILED"])
        self.assertFalse(res.get("success", False))
        self.assertIn("not configured", res.get("message").lower())
        print("✓ Passed: Status is 'NOT_SENT' when credentials are empty.")

    def test_02_smtp_failure_keeps_dispatched_zero_and_sets_error(self):
        """When SMTP fails, DB must keep token_dispatched = 0 and record token_dispatch_error"""
        print("\n[TEST 2] Testing SMTP failure handling...")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM voters WHERE is_accredited = 1 LIMIT 1")
        voter_row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(voter_row, "Should have at least 1 accredited voter")
        voter_id = voter_row["id"]

        with patch("app.main.send_token_email") as mock_send:
            mock_send.return_value = {
                "success": False,
                "status": "FAILED",
                "message": "Gmail / SMTP Authentication Failed (Code 535): 5.7.8 BadCredentials",
                "error_code": 535
            }

            # Authenticate as admin session
            client = TestClient(main_module.app)
            login_res = client.post("/api/admin/login", json={"password": "Chairman2026!"})
            self.assertEqual(login_res.status_code, 200)

            dispatch_res = client.post(f"/api/admin/dispatch-single-token/{voter_id}")
            self.assertEqual(dispatch_res.status_code, 200)
            data = dispatch_res.json()
            self.assertFalse(data["success"])
            self.assertEqual(data["status"], "FAILED")

            # Verify DB state
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT token_dispatched, token_dispatched_at, token_dispatch_error FROM voters WHERE id = ?", (voter_id,))
            updated_voter = cursor.fetchone()
            conn.close()

            self.assertEqual(updated_voter["token_dispatched"], 0)
            self.assertIsNone(updated_voter["token_dispatched_at"])
            self.assertIn("BadCredentials", updated_voter["token_dispatch_error"])
            print("✓ Passed: On SMTP failure, token_dispatched is 0 and token_dispatch_error is recorded.")

    def test_03_smtp_success_marks_dispatched_one_and_returns_sent_with_messageId(self):
        """When SMTP succeeds with 250 OK, DB marks token_dispatched = 1, returns status 'SENT' and messageId"""
        print("\n[TEST 3] Testing SMTP verified 250 OK success...")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM voters WHERE is_accredited = 1 LIMIT 1")
        voter_row = cursor.fetchone()
        conn.close()
        
        voter_id = voter_row["id"]

        with patch("app.main.send_token_email") as mock_send:
            mock_send.return_value = {
                "success": True,
                "status": "SENT",
                "messageId": "<msg-unique-12345@gmail.com>",
                "smtp_code": 250,
                "message": "250 OK: Email successfully delivered"
            }

            client = TestClient(main_module.app)
            client.post("/api/admin/login", json={"password": "Chairman2026!"})
            dispatch_res = client.post(f"/api/admin/dispatch-single-token/{voter_id}")
            self.assertEqual(dispatch_res.status_code, 200)
            data = dispatch_res.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["status"], "SENT")
            self.assertEqual(data["messageId"], "<msg-unique-12345@gmail.com>")

            # Verify DB state
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT token_dispatched, token_dispatched_at, token_dispatch_error FROM voters WHERE id = ?", (voter_id,))
            updated_voter = cursor.fetchone()
            conn.close()

            self.assertEqual(updated_voter["token_dispatched"], 1)
            self.assertIsNotNone(updated_voter["token_dispatched_at"])
            self.assertIsNone(updated_voter["token_dispatch_error"])
            print("✓ Passed: On verified 250 OK, token_dispatched is 1 and response returns status='SENT' with messageId.")

    def test_04_html_contains_voting_code_token_header_copy_and_test_connection_btn(self):
        """Check admin_dashboard.html renders VOTING CODE / TOKEN column, copy buttons, and Test Connection button"""
        print("\n[TEST 4] Testing Admin Dashboard UI markup...")
        client = TestClient(main_module.app)
        client.post("/api/admin/login", json={"password": "Chairman2026!"})
        dash_res = client.get("/admin/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        html = dash_res.text

        # Header requirement
        self.assertIn("VOTING CODE / TOKEN", html)
        # Copy button requirement
        self.assertIn("copyVoterToken", html)
        self.assertIn(">Copy<", html)
        # Test connection button requirement
        self.assertIn("testSmtpConnection", html)
        self.assertIn("Test Connection", html)
        # Error modal
        self.assertIn("dispatchErrorModal", html)
        print("✓ Passed: 'VOTING CODE / TOKEN' column, copy buttons, and 'Test Connection' button are all present.")

    def test_05_test_smtp_endpoint(self):
        """Test POST /api/admin/test-smtp endpoint returns JSON and strips spaces"""
        print("\n[TEST 5] Testing POST /api/admin/test-smtp...")
        client = TestClient(main_module.app)
        client.post("/api/admin/login", json={"password": "Chairman2026!"})

        with patch("app.main.verify_smtp_connection") as mock_verify:
            mock_verify.return_value = {
                "success": True,
                "message": "✓ Verified! Connected and authenticated successfully."
            }
            res = client.post("/api/admin/test-smtp", json={
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_user": "napssiec@gmail.com",
                "smtp_pass": "abcd efgh ijkl mnop"  # with spaces!
            })
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["status"], "SENT")
            print("✓ Passed: /api/admin/test-smtp works and returns JSON success.")

if __name__ == "__main__":
    unittest.main()

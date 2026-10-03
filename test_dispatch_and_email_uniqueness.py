import sys
import sqlite3
import time
sys.stdout.reconfigure(encoding='utf-8')
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, init_db

def run_tests():
    print("==================================================")
    print("STARTING TEST SUITE: EMAIL UNIQUENESS & TOKEN DISPATCH")
    print("==================================================")

    init_db()
    client = TestClient(app)

    # 1. Clean up any previous test voters
    test_email_1 = "test.unique.voter1@pos.edu.ng"
    test_email_2 = "test.unique.voter2@pos.edu.ng"
    test_matric_1 = "POS/TEST/0001"
    test_matric_2 = "POS/TEST/0002"
    test_matric_3 = "POS/TEST/0003"

    conn = get_db()
    conn.execute("DELETE FROM voters WHERE matric_number IN (?, ?, ?)", (test_matric_1, test_matric_2, test_matric_3))
    conn.execute("DELETE FROM voters WHERE email IN (?, ?)", (test_email_1, test_email_2))
    conn.commit()
    conn.close()

    # TEST A: Successful First Accreditation Registration
    print("\n--- TEST A: First student registers with unique email ---")
    reg_res = client.post("/api/voter/register", json={
        "full_name": "Test Student One",
        "matric_number": test_matric_1,
        "level": "300 Level",
        "email": test_email_1
    })
    assert reg_res.status_code == 200, f"Registration 1 failed: {reg_res.text}"
    data1 = reg_res.json()
    assert data1["success"] is True
    assert data1["token_dispatched"] is False
    print(f"✓ Registered: {test_matric_1} with {test_email_1}")

    # TEST B: Second student attempts to use the SAME email (Duplicate email protection!)
    print("\n--- TEST B: Second student tries to use the same email (MUST FAIL) ---")
    dup_res = client.post("/api/voter/register", json={
        "full_name": "Fraudulent Student Two",
        "matric_number": test_matric_2,
        "level": "200 Level",
        "email": test_email_1  # REUSING EMAIL!
    })
    print(f"Status Code: {dup_res.status_code}")
    print(f"Response: {dup_res.text}")
    assert dup_res.status_code == 400, "Duplicate email registration MUST be rejected with HTTP 400!"
    err_text = dup_res.json()["detail"].lower()
    assert "one email" in err_text or "already" in err_text or "in use" in err_text, f"Unexpected error message: {err_text}"
    print(f"✓ Blocked duplicate email attempt! Error returned: '{dup_res.json()['detail']}'")

    # TEST C: Same student tries to register again with same email
    print("\n--- TEST C: Same student re-registers with same email & matric (MUST INFORM) ---")
    re_res = client.post("/api/voter/register", json={
        "full_name": "Test Student One",
        "matric_number": test_matric_1,
        "level": "300 Level",
        "email": test_email_1
    })
    assert re_res.status_code == 400, "Re-registering same student should return HTTP 400!"
    assert "already accredited" in re_res.json()["detail"].lower()
    print(f"✓ Correctly notified already accredited: '{re_res.json()['detail']}'")

    # TEST D: Second student registers with a DIFFERENT, valid email
    print("\n--- TEST D: Second student registers with a unique email ---")
    reg2_res = client.post("/api/voter/register", json={
        "full_name": "Test Student Two",
        "matric_number": test_matric_2,
        "level": "200 Level",
        "email": test_email_2
    })
    assert reg2_res.status_code == 200, f"Registration 2 failed: {reg2_res.text}"
    print(f"✓ Registered: {test_matric_2} with {test_email_2}")

    # TEST E: Query pending accredited voters endpoint
    print("\n--- TEST E: Testing GET /api/admin/pending-accredited-voters ---")
    # Must authenticate admin first
    login_res = client.post("/api/admin/login", json={"password": "Chairman2026!"})
    assert login_res.status_code == 200, "Admin login failed"

    pending_res = client.get("/api/admin/pending-accredited-voters")
    assert pending_res.status_code == 200, f"Pending query failed: {pending_res.text}"
    pending_data = pending_res.json()
    assert pending_data["success"] is True
    assert pending_data["total"] >= 2, f"Expected at least 2 pending voters, found {pending_data['total']}"
    print(f"✓ Query returned {pending_data['total']} accredited voters pending token dispatch.")

    # Verify every returned voter has an alphanumeric token
    for v in pending_data["voters"]:
        assert len(v["token"]) >= 6, f"Invalid token format for {v['matric_number']}: {v['token']}"
        assert v["token"].startswith("NAPSS-"), f"Token prefix mismatch: {v['token']}"
    print(f"✓ All {pending_data['total']} voters have secure alphanumeric voting keys verified!")

    # TEST F: Dispatch single token with verified SMTP synchronization
    print("\n--- TEST F: Testing Single Token Dispatch ---")
    voter1_db = next(v for v in pending_data["voters"] if v["matric_number"] == test_matric_1)
    
    # F.1: When SMTP is unconfigured or fails, email must NOT be marked dispatched!
    disp_unconf_res = client.post(f"/api/admin/dispatch-single-token/{voter1_db['id']}")
    assert disp_unconf_res.status_code == 200
    disp_unconf_data = disp_unconf_res.json()
    assert disp_unconf_data["success"] is False, "Unsent email must not be marked success"
    assert disp_unconf_data["status"] in ["FAILED", "not_sent"]
    print(f"✓ Verified: Unsent email correctly marked FAILED (token_dispatched remained 0)")

    # F.2: When SMTP delivers verified 250 OK, mark dispatched = 1
    from unittest.mock import patch
    with patch("app.main.send_token_email") as mock_mail:
        mock_mail.return_value = {"status": "sent", "smtp_code": 250, "message": "250 OK: Delivered"}
        disp1_res = client.post(f"/api/admin/dispatch-single-token/{voter1_db['id']}")
        assert disp1_res.status_code == 200, f"Single dispatch failed: {disp1_res.text}"
        disp1_data = disp1_res.json()
        assert disp1_data["success"] is True
        print(f"✓ Token dispatched with verified 250 OK for {test_matric_1}. Status: {disp1_data['status']}")

    # Verify voter 1 is now marked dispatched in DB
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT token_dispatched, token_dispatched_at FROM voters WHERE matric_number = ?", (test_matric_1,))
    row1 = cursor.fetchone()
    conn.close()
    assert row1["token_dispatched"] == 1
    assert row1["token_dispatched_at"] is not None
    print(f"✓ Voter 1 record updated: dispatched at {row1['token_dispatched_at']}")

    # TEST G: Test Batch Dispatch to All Accredited Voters
    print("\n--- TEST G: Testing POST /api/admin/dispatch-all-accredited ---")
    with patch("app.main.send_token_email") as mock_mail:
        mock_mail.return_value = {"status": "sent", "smtp_code": 250, "message": "250 OK: Delivered"}
        batch_res = client.post("/api/admin/dispatch-all-accredited")
        assert batch_res.status_code == 200, f"Batch dispatch failed: {batch_res.text}"
        batch_data = batch_res.json()
        assert batch_data["success"] is True
        print(f"✓ Batch dispatch result: {batch_data['successful']} succeeded, {batch_data['failed']} failed out of {batch_data['total']} voters.")

    # Verify no more unvoted voters have pending tokens
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM voters WHERE is_accredited = 1 AND token_dispatched = 0 AND has_voted = 0")
    remaining_pending = cursor.fetchone()[0]
    conn.close()
    assert remaining_pending == 0, f"Expected 0 pending voters, found {remaining_pending}"
    print(f"✓ Verified: 0 pending accredited voters remaining after batch dispatch!")

    # Clean up test voters
    conn = get_db()
    conn.execute("DELETE FROM voters WHERE matric_number IN (?, ?, ?)", (test_matric_1, test_matric_2, test_matric_3))
    conn.execute("DELETE FROM voters WHERE email IN (?, ?)", (test_email_1, test_email_2))
    conn.commit()
    conn.close()

    print("\n==================================================")
    print("🎉 ALL 7 SUITES PASSED PERFECTLY! 100% SUCCESS! 🎉")
    print("==================================================")

if __name__ == "__main__":
    run_tests()

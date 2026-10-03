import sys
import sqlite3
sys.stdout.reconfigure(encoding='utf-8')
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, init_db

def run_tests():
    print("--- 1. Testing DB Initialization and Schema ---")
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(voters)")
    cols = {r["name"]: r for r in cursor.fetchall()}
    print(f"Voters columns: {list(cols.keys())}")
    assert "token_dispatched" in cols, "token_dispatched column missing!"
    assert "token_dispatched_at" in cols, "token_dispatched_at column missing!"
    conn.close()
    print("✓ Schema verified successfully!")

    client = TestClient(app)

    print("\n--- 2. Testing Voter Accreditation Registration (/api/voter/register) ---")
    test_voter = {
        "full_name": "Babajide Michael Adeyemi",
        "matric_number": "POS/2023/8888",
        "level": "200 Level",
        "email": "babajide.adeyemi.test@pos.edu.ng"
    }

    # Clean up if existed from prior run
    conn = get_db()
    conn.execute("DELETE FROM voters WHERE matric_number = ?", (test_voter["matric_number"],))
    conn.commit()
    conn.close()

    res = client.post("/api/voter/register", json=test_voter)
    assert res.status_code == 200, f"Register failed: {res.text}"
    reg_data = res.json()
    assert reg_data["success"] is True
    assert reg_data["token_dispatched"] is False
    assert "token" not in reg_data, "Token should NOT be exposed in registration response!"
    print("✓ Voter accredited successfully without premature token exposure!")

    print("\n--- 3. Testing Token Retrieval BEFORE Admin Dispatch ---")
    res = client.post("/api/voter/retrieve-code", json={"identifier": test_voter["matric_number"]})
    assert res.status_code == 200
    ret_data = res.json()
    assert ret_data["success"] is True
    assert ret_data["token_dispatched"] is False
    assert "token" not in ret_data or ret_data.get("token") is None, "Token must be withheld before dispatch!"
    assert "not yet dispatched" in ret_data["message"].lower() or "awaiting" in ret_data["message"].lower()
    print(f"✓ Voter received correct pending message: '{ret_data['message'][:60]}...'")

    print("\n--- 4. Testing Admin Auth & Token Dispatch by Level ---")
    login_res = client.post("/api/admin/login", json={"password": "Chairman2026!"})
    assert login_res.status_code == 200, "Admin login failed"

    # Dispatch to 200 Level only
    disp_res = client.post("/api/admin/dispatch-tokens", json={"level": "200 Level", "only_pending": True})
    assert disp_res.status_code == 200, f"Dispatch failed: {disp_res.text}"
    disp_data = disp_res.json()
    assert disp_data["success"] is True
    print(f"✓ Chairman dispatched tokens to {disp_data['total']} voters in 200 Level.")

    # Check DB state
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT token_dispatched, token_dispatched_at, token FROM voters WHERE matric_number = ?", (test_voter["matric_number"],))
    row = cursor.fetchone()
    conn.close()
    assert row["token_dispatched"] == 1, "token_dispatched should be 1"
    assert row["token_dispatched_at"] is not None
    voter_token = row["token"]
    print(f"✓ Database updated: token_dispatched=1 at {row['token_dispatched_at']}")

    print("\n--- 5. Testing Token Retrieval AFTER Admin Dispatch ---")
    res = client.post("/api/voter/retrieve-code", json={"identifier": test_voter["matric_number"]})
    assert res.status_code == 200
    after_data = res.json()
    assert after_data["success"] is True
    assert after_data["token_dispatched"] is True
    assert after_data["token"] == voter_token, "Dispatched token must match voter token!"
    assert "magic_link" in after_data
    print(f"✓ Voter now receives token ({after_data['token']}) and magic link!")

    print("\n--- 6. Testing Casting Ballot with Dispatched Token ---")
    # Authenticate voter
    auth_res = client.post("/api/voter/auth", json={"token": voter_token})
    assert auth_res.status_code == 200, f"Voter auth failed: {auth_res.text}"

    # Cast ballot (voting for President candidate 1 and void for Vice President)
    ballot_res = client.post("/api/voter/cast-ballot", json={
        "token": voter_token,
        "votes": {"1": 1, "2": 0}
    })
    assert ballot_res.status_code == 200
    ballot_data = ballot_res.json()
    assert ballot_data["success"] is True
    assert "receipt_hash" in ballot_data
    print(f"✓ Ballot cast successfully! Anonymous Receipt: {ballot_data['receipt_hash']}")

    print("\n--- 7. Testing Post-Vote Status Check ---")
    res = client.post("/api/voter/retrieve-code", json={"identifier": test_voter["matric_number"]})
    assert res.status_code == 200
    voted_data = res.json()
    assert voted_data["has_voted"] is True
    print("✓ Voter correctly marked as already voted!")

    print("\n--- 8. Testing Single Voter Dispatch Endpoint ---")
    # Test single dispatch on Jamiu Lateef
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM voters WHERE email = 'lateefjamiu251@gmail.com'")
    jamiu = cursor.fetchone()
    conn.close()

    single_res = client.post(f"/api/admin/dispatch-single-token/{jamiu['id']}")
    assert single_res.status_code == 200
    single_data = single_res.json()
    assert single_data["success"] is True
    print(f"✓ Single dispatch successful for {jamiu['email']}!")

    print("\n🎉 ALL ACCREDITATION & TOKEN DISPATCH TESTS PASSED PERFECTLY! 🎉")

if __name__ == "__main__":
    run_tests()

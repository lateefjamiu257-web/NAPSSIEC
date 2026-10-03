import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, get_db

def run_tests():
    print(">>> 1. Initializing database schema and seed data...")
    init_db()
    print("    [PASS] Database initialized successfully.")

    client = TestClient(app)

    print("\n>>> 2. Testing Homepage...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "TrustVote" in res.text
    print("    [PASS] Homepage rendered with election metadata.")

    print("\n>>> 3. Testing Voter Authentication with valid token...")
    # Use sample token TV-ENG101
    res = client.post("/api/voter/auth", json={"token": "TV-ENG101"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    auth_data = res.json()
    assert auth_data["success"] is True
    assert auth_data["student_id"] == "AUSU/2022/1001"
    print(f"    [PASS] Voter authenticated: {auth_data['full_name']} ({auth_data['student_id']})")

    print("\n>>> 4. Testing Ballot Casting (Office choices)...")
    # Fetch positions to get candidate IDs
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, position_id FROM candidates")
    candidates = cursor.fetchall()
    conn.close()

    # Map position_id to first candidate found for that position
    votes = {}
    for c in candidates:
        pos_id_str = str(c["position_id"])
        if pos_id_str not in votes:
            votes[pos_id_str] = c["id"]

    cast_payload = {
        "token": "TV-ENG101",
        "votes": votes
    }
    res = client.post("/api/voter/cast-ballot", json=cast_payload)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    ballot_res = res.json()
    assert ballot_res["success"] is True
    receipt_hash = ballot_res["receipt_hash"]
    assert receipt_hash.startswith("REC-")
    print(f"    [PASS] Ballot anonymously cast! Generated Receipt: {receipt_hash}")

    print("\n>>> 5. Testing Anti-Fraud: Replay / Double-Voting Block...")
    res_double = client.post("/api/voter/auth", json={"token": "TV-ENG101"})
    assert res_double.status_code == 403, f"Expected 403 Forbidden, got {res_double.status_code}"
    print("    [PASS] Double voting blocked! Token successfully invalidated.")

    print("\n>>> 6. Testing Public Ballot Verification by Receipt Hash...")
    res_receipt = client.get(f"/verify-receipt?hash={receipt_hash}")
    assert res_receipt.status_code == 200
    assert receipt_hash in res_receipt.text
    assert "Ballot Confirmed in Official Tally" in res_receipt.text
    print(f"    [PASS] Public audit successfully verified receipt {receipt_hash} in the ballot box.")

    print("\n>>> 7. Testing Results & Tabulation API...")
    res_results = client.get("/api/results/data")
    assert res_results.status_code == 200
    results_data = res_results.json()
    assert results_data["total_voted"] >= 1
    print(f"    [PASS] Live results tallied. Total ballots cast: {results_data['total_voted']}")

    print("\n>>> 8. Testing Chairman Portal Login...")
    res_admin = client.post("/api/admin/login", json={"password": "Chairman2026!"})
    assert res_admin.status_code == 200
    assert res_admin.json()["success"] is True
    print("    [PASS] Chairman authenticated successfully.")

    print("\n" + "=" * 60)
    print("  ALL ELECTORAL INTEGRITY & FAIRNESS TESTS PASSED (8/8)!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()

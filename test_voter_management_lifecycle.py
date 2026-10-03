import os
import sqlite3
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_voter_management_lifecycle():
    print("==================================================")
    print("STARTING TEST: VOTER DELETION & NEW ELECTION ROLL")
    print("==================================================")

    # 1. Login as Admin
    login_res = client.post("/api/admin/login", json={"password": "Chairman2026!"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    print("[1] Admin authenticated successfully.")

    # 2. Add a test voter
    add_res = client.post("/api/admin/add-voter", json={
        "matric_number": "TEST/MANAGE/001",
        "full_name": "Test Lifecycle Voter",
        "level": "300 Level",
        "email": "test.lifecycle@example.com"
    })
    assert add_res.status_code == 200, f"Add voter failed: {add_res.text}"
    voter_token = add_res.json()["token"]
    print(f"[2] Added test voter: TEST/MANAGE/001 with token {voter_token}")

    # Check voter is in database
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("SELECT id FROM voters WHERE matric_number = 'TEST/MANAGE/001'")
    row = c.fetchone()
    assert row is not None, "Voter not found in DB!"
    test_voter_id = row[0]
    conn.close()

    # 3. Test deleting this individual voter
    del_res = client.post(f"/api/admin/voters/delete/{test_voter_id}")
    assert del_res.status_code == 200, f"Delete failed: {del_res.text}"
    print(f"[3] Deleted single voter ID {test_voter_id}: {del_res.json()['message']}")

    # Verify deleted from DB
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("SELECT id FROM voters WHERE id = ?", (test_voter_id,))
    assert c.fetchone() is None, "Voter was not deleted from DB!"
    conn.close()
    print("[4] Verified voter removed from DB.")

    # 4. Test Batch Import
    batch_res = client.post("/api/admin/import-voters", json={
        "voters": [
            {"matric_number": "TEST/NEW/101", "full_name": "New Election Student A", "level": "100 Level", "email": "new.a@example.com"},
            {"matric_number": "TEST/NEW/102", "full_name": "New Election Student B", "level": "200 Level", "email": "new.b@example.com"}
        ]
    })
    assert batch_res.status_code == 200
    assert batch_res.json()["imported"] == 2
    print(f"[5] Batch imported 2 new voters: {batch_res.json()}")

    # 5. Clean up the test batch voters
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("DELETE FROM voters WHERE matric_number LIKE 'TEST/%'")
    conn.commit()
    conn.close()
    print("[6] Cleaned up temporary test voters.")

    print("==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_voter_management_lifecycle()

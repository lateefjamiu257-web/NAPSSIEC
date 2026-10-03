import urllib.request
import urllib.parse
import http.cookiejar
import json
import sqlite3

BASE_URL = "http://127.0.0.1:8000"

def test_accreditation_suite():
    print("=================================================================")
    print("      RUNNING AUTOMATED TEST FOR ACCREDITATION & CODE ISSUANCE   ")
    print("=================================================================")

    # Clean up any previous test voter
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("DELETE FROM voters WHERE matric_number = 'POS/2026/ACCRED01' OR email = 'accred_test@pos.edu.ng'")
    c.execute("UPDATE election_settings SET status = 'OPEN' WHERE id = 1")
    conn.commit()
    conn.close()

    # 1. Test Accreditation Portal Page Loads
    res = urllib.request.urlopen(f"{BASE_URL}/accredit")
    assert res.status == 200, f"Expected 200, got {res.status}"
    html = res.read().decode('utf-8')
    assert "Voter Accreditation & Registration" in html, "Page missing Accreditation header"
    assert "Register for Accreditation" in html, "Page missing Register tab"
    assert "Get Voting Code" in html, "Page missing Get Voting Code tab"
    print("[PASS] 1. Accreditation Portal loads with Registration and Code Retrieval tabs.")

    # 2. Test Voter Registration for Accreditation
    reg_payload = json.dumps({
        "full_name": "Fatima Abubakar",
        "matric_number": "POS/2026/ACCRED01",
        "level": "200 Level",
        "email": "accred_test@pos.edu.ng"
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/voter/register",
        data=reg_payload,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    assert res.status == 200, f"Registration failed: {res.status}"
    reg_data = json.loads(res.read().decode('utf-8'))
    assert reg_data["success"] is True
    assert reg_data["already_registered"] is False
    assert reg_data["voter"]["matric_number"] == "POS/2026/ACCRED01"
    print(f"[PASS] 2. Student self-accredited successfully: {reg_data['voter']['full_name']} ({reg_data['voter']['matric_number']})")

    # 3. Test Duplicate Registration Handling
    req_dup = urllib.request.Request(
        f"{BASE_URL}/api/voter/register",
        data=reg_payload,
        headers={"Content-Type": "application/json"}
    )
    res_dup = urllib.request.urlopen(req_dup)
    assert res_dup.status == 200
    dup_data = json.loads(res_dup.read().decode('utf-8'))
    assert dup_data["success"] is True
    assert dup_data["already_registered"] is True
    assert "already accredited" in dup_data["message"].lower()
    print("[PASS] 3. Duplicate registration safely detected and confirmed intact.")

    # 4. Test Code Retrieval / Dispatch when election is OPEN
    ret_payload = json.dumps({
        "identifier": "accred_test@pos.edu.ng"
    }).encode('utf-8')

    req_ret = urllib.request.Request(
        f"{BASE_URL}/api/voter/retrieve-code",
        data=ret_payload,
        headers={"Content-Type": "application/json"}
    )
    res_ret = urllib.request.urlopen(req_ret)
    assert res_ret.status == 200
    ret_data = json.loads(res_ret.read().decode('utf-8'))
    assert ret_data["success"] is True
    assert ret_data["election_open"] is True
    assert ret_data["has_voted"] is False
    token = ret_data["token"]
    assert token.startswith("NAPSS-"), f"Unexpected token: {token}"
    print(f"[PASS] 4. Secret Voting Code retrieved and issued: {token} with 1-click magic link.")

    # 5. Cast ballot with the retrieved code
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    cast_payload = json.dumps({
        "token": token,
        "votes": {
            "1": 1,
            "2": 0, # Void
            "3": 5,
            "4": 7,
            "5": 9,
            "6": 11,
            "7": 13,
            "8": 15,
            "9": 17,
            "10": 0 # Void
        }
    }).encode('utf-8')

    req_cast = urllib.request.Request(
        f"{BASE_URL}/api/voter/cast-ballot",
        data=cast_payload,
        headers={"Content-Type": "application/json"}
    )
    res_cast = opener.open(req_cast)
    assert res_cast.status == 200
    cast_data = json.loads(res_cast.read().decode('utf-8'))
    assert cast_data["message"] == "Vote submitted successfully."
    print(f"[PASS] 5. Ballot cast with accredited token. Anonymous Receipt: {cast_data['receipt_hash']}")

    # 6. Verify Code Retrieval after voting shows already voted
    res_post_vote = urllib.request.urlopen(req_ret)
    assert res_post_vote.status == 200
    post_vote_data = json.loads(res_post_vote.read().decode('utf-8'))
    assert post_vote_data["has_voted"] is True
    assert "/public-board" in post_vote_data.get("redirect_url", "")
    print("[PASS] 6. Post-vote retrieval correctly detects ballot already cast and routes to Public Board.")

    # 7. Test Code Retrieval when election is CLOSED
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("UPDATE election_settings SET status = 'CLOSED' WHERE id = 1")
    # Add a fresh voter for closed status check
    c.execute("INSERT OR REPLACE INTO voters (matric_number, full_name, level, email, token, token_hash, is_accredited, has_voted, created_at) VALUES ('POS/2026/ACCRED02', 'Ibrahim Sani', '100 Level', 'sani@pos.edu.ng', 'NAPSS-SANI', 'hash', 1, 0, '2026-10-01')")
    conn.commit()
    conn.close()

    ret_closed = json.dumps({"identifier": "sani@pos.edu.ng"}).encode('utf-8')
    req_closed = urllib.request.Request(f"{BASE_URL}/api/voter/retrieve-code", data=ret_closed, headers={"Content-Type": "application/json"})
    res_closed = urllib.request.urlopen(req_closed)
    data_closed = json.loads(res_closed.read().decode('utf-8'))
    assert data_closed["election_open"] is False
    assert "voting portal is currently closed" in data_closed["message"].lower()
    print("[PASS] 7. Closed election state correctly halts code entry with accreditation assurance.")

    # Reset election status to OPEN
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("UPDATE election_settings SET status = 'OPEN' WHERE id = 1")
    c.execute("DELETE FROM voters WHERE matric_number = 'POS/2026/ACCRED02'")
    conn.commit()
    conn.close()

    print("\n=================================================================")
    print("   ALL 7 ACCREDITATION SUITE TESTS PASSED WITH 100% SUCCESS!     ")
    print("=================================================================")

if __name__ == "__main__":
    test_accreditation_suite()

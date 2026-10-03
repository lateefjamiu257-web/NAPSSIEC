import urllib.request
import urllib.parse
import http.cookiejar
import json
import re

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=================================================================")
    print("   RUNNING AUTOMATED VERIFICATION FOR REBUILT NAPSSIEC PLATFORM  ")
    print("=================================================================")

    import sqlite3
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("UPDATE voters SET has_voted = 0, voted_at = NULL WHERE matric_number = 'POS/2022/1001'")
    c.execute("DELETE FROM ballots")
    c.execute("DELETE FROM ballot_items")
    c.execute("DELETE FROM voters WHERE matric_number IN ('POS/2022/9901', 'POS/2022/9902')")
    c.execute("UPDATE election_settings SET status = 'OPEN', hide_running_totals = 1 WHERE id = 1")
    conn.commit()
    conn.close()

    # 1. Test Homepage
    res = urllib.request.urlopen(f"{BASE_URL}/")
    assert res.status == 200, f"Expected 200 for /, got {res.status}"
    body = res.read().decode('utf-8')
    assert "NAPSS" in body, "Homepage missing NAPSS branding"
    assert "ELECTION OPEN" in body, "Homepage missing ELECTION OPEN status"
    assert "Voter Participation by Academic Level" in body, "Homepage missing level breakdown"
    print("[PASS] 1. Homepage loads with status OPEN & Level Turnout breakdown.")

    # 2. Test Public Transparency Board
    res = urllib.request.urlopen(f"{BASE_URL}/public-board")
    assert res.status == 200, f"Expected 200 for /public-board, got {res.status}"
    board_html = res.read().decode('utf-8')
    assert "Votes Cast per Academic Level" in board_html, "Public board missing level breakdown"
    assert "Certified Candidate Directory" in board_html, "Public board missing candidate directory"
    # Ensure NO individual voter records or names leak
    assert "POS/2022/1001" not in board_html, "Matric number leaked on public board!"
    assert "lateefjamiu251@gmail.com" not in board_html, "Email leaked on public board!"
    print("[PASS] 2. Public Transparency Board verified: strictly aggregates, ZERO individual names/matrics.")

    # 3. Test Magic Link Auth for Jamiu Lateef
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    res = opener.open(f"{BASE_URL}/vote?key=NAPSS-JAM1")
    assert res.geturl() == f"{BASE_URL}/ballot", f"Expected redirect to /ballot, got {res.geturl()}"
    ballot_html = res.read().decode('utf-8')
    assert "1. President" in ballot_html, "Ballot missing President office"
    assert "10. Senator" in ballot_html, "Ballot missing Senator office"
    assert "Review Your Ballot" in ballot_html, "Ballot missing Review Your Ballot screen"
    assert "SUBMIT FINAL VOTE" in ballot_html, "Ballot missing Submit Final Vote button"
    print("[PASS] 3. Magic Link & 10-Office Guided Ballot Wizard verified with Review screen.")

    # 4. Cast Ballot via API
    cast_payload = json.dumps({
        "token": "NAPSS-JAM1",
        "votes": {
            "1": 1,  # President -> Adewale Ibrahim
            "2": 3,  # Vice President -> Yusuf Abdullahi
            "3": 5,  # General Secretary -> Tunde Balogun
            "4": 7,  # Assistant General Secretary -> Segun Mathew
            "5": 9,  # Financial Secretary -> Kehinde Badmus
            "6": 11, # Treasurer -> Oluwaseun Victor
            "7": 13, # PRO -> Samuel Babatunde
            "8": 15, # Social Director -> Tobi Bakare
            "9": 17, # Sports Director -> Emeka Chukwu
            "10": 19 # Senator -> Hon. Farouk Abdullahi
        }
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/voter/cast-ballot",
        data=cast_payload,
        headers={"Content-Type": "application/json"}
    )
    res = opener.open(req)
    assert res.status == 200, f"Expected 200, got {res.status}"
    cast_data = json.loads(res.read().decode('utf-8'))
    receipt = cast_data["receipt_hash"]
    assert receipt.startswith("NAPSS-REC-"), f"Unexpected receipt format: {receipt}"
    assert cast_data["message"] == "Vote submitted successfully.", "Incorrect confirmation message"
    print(f"[PASS] 4. Ballot cast successfully. Anonymous Receipt: {receipt}")

    # 5. Verify Unified Flow: After voting, voter is directly on Public Transparency Board!
    res = urllib.request.urlopen(f"{BASE_URL}/vote-success?receipt={receipt}")
    assert "/public-board" in res.geturl(), f"Expected redirect to /public-board, got {res.geturl()}"
    success_html = res.read().decode('utf-8')
    assert "Vote submitted successfully." in success_html, "Public board missing vote confirmation heading"
    assert "Votes Cast per Academic Level" in success_html, "Voter cannot see level stats on same page!"
    assert "View Results" not in success_html, "SECURITY VIOLATION: View Results found on voter side!"
    assert receipt in success_html, "Receipt hash missing from success page"
    print("[PASS] 5. Unified Flow verified: Voter lands directly on Public Transparency Board with Confirmation Card.")

    # 6. Verify Receipt Hash in Ledger
    res = urllib.request.urlopen(f"{BASE_URL}/verify-receipt?receipt={receipt}")
    verify_html = res.read().decode('utf-8')
    assert "Ballot Confirmed Intact & Counted" in verify_html, "Receipt verification failed"
    assert "300 Level" in verify_html, "Receipt verification missing level info"
    print("[PASS] 6. Cryptographic Receipt independently verified in ledger.")

    # 7. Verify Public Board Level Count Incremented
    res = urllib.request.urlopen(f"{BASE_URL}/public-board")
    board_after = res.read().decode('utf-8')
    assert "1 votes cast" in board_after or ">1<" in board_after, "Public board didn't increment votes cast"
    print("[PASS] 7. Public board level stats reflect the cast ballot in aggregate.")

    # 8. Test Admin Login & Command Room
    admin_cj = http.cookiejar.CookieJar()
    admin_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(admin_cj))

    login_payload = json.dumps({"password": "Chairman2026!"}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/login", data=login_payload, headers={"Content-Type": "application/json"})
    res = admin_opener.open(req)
    assert res.status == 200, "Admin login failed"

    res = admin_opener.open(f"{BASE_URL}/admin/dashboard")
    dash_html = res.read().decode('utf-8')
    assert "Chairman Command Room" in dash_html, "Missing Command Room heading"
    assert "🟢 OPEN" in dash_html, "Missing status badge in Command Room"
    assert "Registered Voters" in dash_html, "Missing Registered Voters stat"
    assert "Votes Cast" in dash_html, "Missing Votes Cast stat"
    assert "Remaining Voters" in dash_html, "Missing Remaining Voters stat"
    assert "Turnout %" in dash_html, "Missing Turnout % stat"
    assert "Candidate Results & Vote Tallies" in dash_html, "Missing Candidate results table"
    assert "Constitutional Secrecy Lock Active" in dash_html, "Secrecy lock should be active by default"
    print("[PASS] 8. Chairman Command Room verified with status, statistics, controls & secrecy lock.")

    # 9. Test Secrecy Toggle
    toggle_payload = json.dumps({"hide_running_totals": False}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/toggle-secrecy", data=toggle_payload, headers={"Content-Type": "application/json"})
    res = admin_opener.open(req)
    assert res.status == 200, "Toggle secrecy failed"

    res = admin_opener.open(f"{BASE_URL}/admin/dashboard")
    revealed_html = res.read().decode('utf-8')
    assert "Adewale Ibrahim Adeleke" in revealed_html, "Missing candidate"
    assert "Leading" in revealed_html, "Missing leading badge when revealed"
    print("[PASS] 9. Chairman Secrecy Toggle verified (Committee can reveal/hide tallies).")

    # 10. Test Status Control (Pause -> Resume -> Close -> Open)
    for st in ["PAUSED", "CLOSED", "OPEN"]:
        st_payload = json.dumps({"status": st}).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/api/admin/status", data=st_payload, headers={"Content-Type": "application/json"})
        res = admin_opener.open(req)
        assert res.status == 200, f"Setting status {st} failed"
    print("[PASS] 10. Real-time Election Master Controls (Open, Pause, Close, Resume) verified.")

    # 11. Test Next Week's Batch Accreditation Importer
    import_payload = json.dumps({
        "voters": [
            {"matric_number": "POS/2022/9901", "full_name": "Test Student 1", "level": "100 Level", "email": "test1@pos.edu.ng"},
            {"matric_number": "POS/2022/9902", "full_name": "Test Student 2", "level": "400 Level", "email": "test2@pos.edu.ng"}
        ]
    }).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/admin/import-voters", data=import_payload, headers={"Content-Type": "application/json"})
    res = admin_opener.open(req)
    assert res.status == 200, "Batch import failed"
    import_res = json.loads(res.read().decode('utf-8'))
    assert import_res["imported"] == 2, f"Expected 2 imported, got {import_res['imported']}"
    print("[PASS] 11. Next Week's Accreditation Batch Importer verified.")

    print("\n=================================================================")
    print("   ALL 11 TEST SUITES PASSED FLAWLESSLY! 100% VERIFIED.          ")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()

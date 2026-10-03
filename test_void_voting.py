import urllib.request
import urllib.parse
import http.cookiejar
import json
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def test_void_vote():
    print("=================================================================")
    print("   RUNNING AUTOMATED TEST FOR VOID VOTE / ABSTAIN FUNCTIONALITY  ")
    print("=================================================================")

    # Setup a clean test voter
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("UPDATE voters SET has_voted = 0, voted_at = NULL WHERE matric_number = 'POS/2022/1001'")
    c.execute("DELETE FROM ballots WHERE voter_level = '300 Level'")
    c.execute("DELETE FROM ballot_items WHERE ballot_id NOT IN (SELECT id FROM ballots)")
    c.execute("UPDATE election_settings SET status = 'OPEN', hide_running_totals = 0 WHERE id = 1")
    conn.commit()
    conn.close()

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Open Ballot with token
    res = opener.open(f"{BASE_URL}/vote?key=NAPSS-JAM1")
    assert "/ballot" in res.geturl(), "Failed to open ballot"
    html = res.read().decode('utf-8')
    assert "Void Vote / None of the Above" in html, "Ballot missing Void Vote option"
    assert 'value="0"' in html, "Missing value=0 for void radio"
    print("[PASS] 1. Ballot page renders 'Void Vote / None of the Above' option for all offices.")

    # 2. Cast ballot with a mix of candidates and VOID votes:
    # President (pos 1): Candidate ID 1 (Adewale Ibrahim)
    # Vice President (pos 2): VOID (value 0)
    # General Secretary (pos 3): VOID (value 0)
    # Remaining positions 4-10: Valid candidates
    votes = {
        "1": 1,  # President -> Candidate 1
        "2": 0,  # Vice President -> VOID
        "3": 0,  # General Secretary -> VOID
        "4": 7,  # Assistant Gen Sec
        "5": 9,  # Financial Sec
        "6": 11, # Treasurer
        "7": 13, # PRO
        "8": 15, # Social Director
        "9": 17, # Sports Director
        "10": 0  # Senator -> VOID
    }

    cast_payload = json.dumps({
        "token": "NAPSS-JAM1",
        "votes": votes
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/voter/cast-ballot",
        data=cast_payload,
        headers={"Content-Type": "application/json"}
    )
    res = opener.open(req)
    assert res.status == 200, f"Ballot cast failed: {res.status}"
    data = json.loads(res.read().decode('utf-8'))
    receipt = data["receipt_hash"]
    assert receipt.startswith("NAPSS-REC-"), "Invalid receipt format"
    print(f"[PASS] 2. Ballot with mixed Candidate & Void votes cast successfully: {receipt}")

    # 3. Verify Database Records
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("SELECT id FROM ballots WHERE receipt_hash = ?", (receipt,))
    ballot_row = c.fetchone()
    assert ballot_row is not None, "Ballot not recorded in DB"
    ballot_id = ballot_row[0]

    c.execute("SELECT position_id, candidate_id, is_void FROM ballot_items WHERE ballot_id = ? ORDER BY position_id", (ballot_id,))
    items = c.fetchall()
    conn.close()

    items_dict = {row[0]: (row[1], row[2]) for row in items}
    # Pos 1: Cand 1, is_void 0
    assert items_dict[1] == (1, 0), f"Expected (1, 0) for pos 1, got {items_dict[1]}"
    # Pos 2: Cand None, is_void 1
    assert items_dict[2] == (None, 1), f"Expected (None, 1) for pos 2 (VOID), got {items_dict[2]}"
    # Pos 3: Cand None, is_void 1
    assert items_dict[3] == (None, 1), f"Expected (None, 1) for pos 3 (VOID), got {items_dict[3]}"
    # Pos 10: Cand None, is_void 1
    assert items_dict[10] == (None, 1), f"Expected (None, 1) for pos 10 (VOID), got {items_dict[10]}"
    print("[PASS] 3. Database correctly stores candidate_id=NULL and is_void=1 for void votes.")

    # 4. Verify Chairman Command Room reflects Void Votes
    admin_cj = http.cookiejar.CookieJar()
    admin_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(admin_cj))
    login_data = json.dumps({"password": "Chairman2026!"}).encode('utf-8')
    admin_opener.open(urllib.request.Request(f"{BASE_URL}/api/admin/login", data=login_data, headers={"Content-Type": "application/json"}))
    
    res = admin_opener.open(f"{BASE_URL}/admin/dashboard")
    dash_html = res.read().decode('utf-8')
    assert "Void Votes (None of the Above)" in dash_html, "Command room missing Void Votes row"
    print("[PASS] 4. Chairman Command Room displays official Void Votes tally per position.")

    # 5. Verify Public Board receives the redirected voter
    res = urllib.request.urlopen(f"{BASE_URL}/public-board?success=1&receipt={receipt}")
    board_html = res.read().decode('utf-8')
    assert "Vote submitted successfully." in board_html
    assert receipt in board_html
    print("[PASS] 5. Public Transparency Board successfully displays confirmation for the void-inclusive ballot.")

    print("\n=================================================================")
    print("   ALL 5 VOID VOTE SUITE TESTS PASSED WITH 100% SUCCESS!         ")
    print("=================================================================")

if __name__ == "__main__":
    test_void_vote()

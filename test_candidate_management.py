import urllib.request
import urllib.parse
import http.cookiejar
import json
import os

BASE_URL = "http://127.0.0.1:8000"

def test_candidates():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Login as Chairman
    login_data = json.dumps({"password": "Chairman2026!"}).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    res = opener.open(req)
    assert res.status == 200, f"Login failed: {res.status}"
    print("[PASS] 1. Chairman logged in successfully.")

    # 2. Check Admin Dashboard loads and contains Candidate Management
    res = opener.open(f"{BASE_URL}/admin/dashboard")
    assert res.status == 200, f"Dashboard failed: {res.status}"
    html = res.read().decode('utf-8')
    assert "Candidate Profiles & Nomination Management" in html, "Missing Candidate Management Section"
    assert "addCandidateModal" in html, "Missing Add Candidate Modal"
    assert "editCandidateModal" in html, "Missing Edit Candidate Modal"
    assert "quickAddForPosition" in html, "Missing quickAddForPosition script"
    assert "uploadCandidatePhoto" in html, "Missing uploadCandidatePhoto script"
    print("[PASS] 2. Admin Dashboard has Candidate Profiles Management UI and Modals.")

    # 3. Test Add Candidate API
    add_payload = json.dumps({
        "position_id": 1,  # President
        "full_name": "Test Nominee Jamiu",
        "nickname": "The Reformer",
        "level": "400 Level",
        "department": "Department of Political Science",
        "photo_url": "/static/uploads/candidates/sample.jpg",
        "manifesto": "Transforming political science student unionism through digital empowerment."
    }).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/candidates/add",
        data=add_payload,
        headers={"Content-Type": "application/json"}
    )
    res = opener.open(req)
    assert res.status == 200, f"Add candidate failed: {res.status}"
    add_data = json.loads(res.read().decode('utf-8'))
    cand_id = add_data["id"]
    print(f"[PASS] 3. Successfully added candidate ID #{cand_id}: {add_data['full_name']}")

    # 4. Test Get Candidate API
    req = urllib.request.Request(f"{BASE_URL}/api/admin/candidates/{cand_id}")
    res = opener.open(req)
    assert res.status == 200, f"Get candidate failed: {res.status}"
    get_data = json.loads(res.read().decode('utf-8'))
    assert get_data["candidate"]["full_name"] == "Test Nominee Jamiu"
    assert get_data["candidate"]["nickname"] == "The Reformer"
    print(f"[PASS] 4. Successfully fetched candidate details for ID #{cand_id}.")

    # 5. Test Edit Candidate API
    edit_payload = json.dumps({
        "position_id": 1,
        "full_name": "Test Nominee Jamiu (Updated)",
        "nickname": "The Great Reformer",
        "level": "400 Level",
        "department": "Department of Political Science",
        "photo_url": "/static/uploads/candidates/updated.jpg",
        "manifesto": "Updated manifesto statement with new policy initiatives."
    }).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/candidates/edit/{cand_id}",
        data=edit_payload,
        headers={"Content-Type": "application/json"}
    )
    res = opener.open(req)
    assert res.status == 200, f"Edit candidate failed: {res.status}"
    edit_data = json.loads(res.read().decode('utf-8'))
    assert edit_data["full_name"] == "Test Nominee Jamiu (Updated)"
    print(f"[PASS] 5. Successfully edited candidate ID #{cand_id}.")

    # 6. Verify that updated candidate shows on Public Board
    res = urllib.request.urlopen(f"{BASE_URL}/public-board")
    board_html = res.read().decode('utf-8')
    assert "Test Nominee Jamiu (Updated)" in board_html
    print("[PASS] 6. Updated candidate appears on Public Transparency Board.")

    # 7. Test Delete Candidate API
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/candidates/delete/{cand_id}",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    res = opener.open(req)
    assert res.status == 200, f"Delete candidate failed: {res.status}"
    print(f"[PASS] 7. Successfully deleted candidate ID #{cand_id}.")

    # 8. Verify candidate no longer appears on Public Board
    res = urllib.request.urlopen(f"{BASE_URL}/public-board")
    board_html = res.read().decode('utf-8')
    assert "Test Nominee Jamiu (Updated)" not in board_html
    print("[PASS] 8. Deleted candidate is cleanly removed from Public Transparency Board.")

    # 9. Test Photo Upload endpoint with multipart data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    filename = "test_avatar.jpg"
    file_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00\xFF\xD9"  # Valid tiny JPEG bytes
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode('utf-8') + file_content + f"\r\n--{boundary}--\r\n".encode('utf-8')

    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/upload-photo",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    res = opener.open(req)
    assert res.status == 200, f"Upload photo failed: {res.status}"
    upload_res = json.loads(res.read().decode('utf-8'))
    assert upload_res["success"] is True
    assert upload_res["url"].startswith("/static/uploads/candidates/cand_")
    print(f"[PASS] 9. Candidate photograph upload succeeded: {upload_res['url']}.")

    print("\n=================================================================")
    print("  ALL 9 CANDIDATE MANAGEMENT SUITE TESTS PASSED WITH 100% SUCCESS ")
    print("=================================================================")

if __name__ == "__main__":
    test_candidates()

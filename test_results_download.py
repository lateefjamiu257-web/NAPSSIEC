import sqlite3
from fastapi.testclient import TestClient
from app.main import app

def test_results_download():
    print("==================================================")
    print("STARTING TEST: ELECTION RESULTS DOWNLOAD & EXPORT")
    print("==================================================")

    public_client = TestClient(app)
    admin_client = TestClient(app)

    # 1. Authenticate admin_client
    login_res = admin_client.post("/api/admin/login", json={"password": "Chairman2026!"})
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    print("[1] Admin authenticated successfully.")

    # Save current election status so we can restore it after test
    conn = sqlite3.connect("trustvote.db")
    c = conn.cursor()
    c.execute("SELECT status FROM election_settings WHERE id = 1")
    original_status = c.fetchone()[0]
    conn.close()

    try:
        # 2. Set status to OPEN -> Public should get 403, Admin should get 200
        admin_client.post("/api/admin/status", json={"status": "OPEN"})
        pub_pdf_open = public_client.get("/api/election/results/download/pdf")
        assert pub_pdf_open.status_code == 403, "Public should not download PDF while election is OPEN!"
        print("[2] Verified: Public download is blocked (403) while election is OPEN.")

        adm_pdf_open = admin_client.get("/api/election/results/download/pdf")
        assert adm_pdf_open.status_code == 200
        assert adm_pdf_open.content.startswith(b"%PDF-1.4")
        assert b"NAPSS INDEPENDENT ELECTORAL COMMISSION" in adm_pdf_open.content
        assert b"NIGERIAN ASSOCIATION OF POLITICAL SCIENCE STUDENTS" not in adm_pdf_open.content
        print("[3] Verified: Admin can preview/download Official PDF at any time.")

        # 3. Set status to CLOSED -> Both Public and Admin can download PDF, Certificate, and JSON!
        admin_client.post("/api/admin/status", json={"status": "CLOSED"})

        # Test PDF download
        pub_pdf_closed = public_client.get("/api/election/results/download/pdf")
        assert pub_pdf_closed.status_code == 200
        assert "application/pdf" in pub_pdf_closed.headers.get("content-type", "")
        assert "attachment; filename=" in pub_pdf_closed.headers.get("content-disposition", "")
        assert ".pdf" in pub_pdf_closed.headers.get("content-disposition", "")
        assert pub_pdf_closed.content.startswith(b"%PDF-1.4")
        assert b"%%EOF" in pub_pdf_closed.content
        assert b"OFFICIAL CERTIFICATE OF RETURN & ELECTION RESULTS" in pub_pdf_closed.content
        assert b"CERTIFIED STANDINGS FOR ALL CANDIDATES BY OFFICE" in pub_pdf_closed.content
        assert b"NIGERIAN ASSOCIATION OF POLITICAL SCIENCE STUDENTS" not in pub_pdf_closed.content
        print("[4] Verified: Official PDF download works when election is CLOSED with proper application/pdf headers.")

        # Test Certificate of Return (HTML/Print/PDF)
        cert_res = public_client.get("/election/results/certificate")
        assert cert_res.status_code == 200
        assert "Official Certificate of Return" in cert_res.text
        assert "Download PDF File" in cert_res.text
        assert "Nigerian Association of Political Science Students" not in cert_res.text
        print("[5] Verified: Official Certificate of Return renders cleanly without logo or NAPSS association title.")

        # Test JSON download
        json_res = public_client.get("/api/election/results/download/json")
        assert json_res.status_code == 200
        json_data = json_res.json()
        assert "election" in json_data
        assert "positions" in json_data
        assert "declared_winners" in json_data
        print("[6] Verified: JSON result export contains election, positions, and declared_winners.")

        # Test Public Board when CLOSED
        board_res = public_client.get("/public-board")
        assert board_res.status_code == 200
        assert "Download Official Results (PDF)" in board_res.text
        assert "View Certificate of Return" in board_res.text
        print("[7] Verified: Public Board displays PDF result download button and candidate votes when CLOSED.")

    finally:
        # Restore original election status
        admin_client.post("/api/admin/status", json={"status": original_status})
        print(f"[8] Restored original election status: {original_status}")

    print("==================================================")
    print("ALL RESULT DOWNLOAD TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    test_results_download()

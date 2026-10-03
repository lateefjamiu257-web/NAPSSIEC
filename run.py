import os
import sys
import uvicorn
from app.database import init_db

def main():
    # Detect local LAN IP address for multi-device network access
    import socket
    lan_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = "127.0.0.1"

    print("=" * 75)
    print("      NAPSS INDEPENDENT ELECTORAL COMMISSION (NAPSSIEC)")
    print("      Department of Political Science - E-Voting Platform")
    print("=" * 75)
    print("\n[+] Database initialized with 10 executive & senatorial offices.")
    print(f"[+] Total accredited voters: 10 (covering 100L, 200L, 300L, 400L)")
    print("\n[+] NAPSSIEC Election Platform is LIVE:")
    print(f"    - On this Laptop:              http://127.0.0.1:8000")
    print(f"    - For Other Phones / Devices:  http://{lan_ip}:8000")
    print(f"    - Voter Booth (Paste Key):     http://{lan_ip}:8000/vote")
    print(f"    - Public Transparency Board:   http://{lan_ip}:8000/public-board")
    print(f"    - Verify Receipt Hash:         http://{lan_ip}:8000/verify-receipt")
    print(f"    - Chairman Command Room:       http://{lan_ip}:8000/admin/login")
    print("      (Master Chairman Key:        Chairman2026!)")
    print("=" * 75)
    print("Press CTRL+C to stop the server.\n")

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()


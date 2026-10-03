import subprocess
import re
import sys
import os
import time

URL_FILE = os.path.join(os.path.dirname(__file__), "public_url.txt")

def main():
    print("=" * 72)
    print("      NAPSS INDEPENDENT ELECTORAL COMMISSION (NAPSSIEC)")
    print("      Department of Political Science - Global Online Tunnel")
    print("=" * 72)
    print("\n[+] Initializing secure HTTPS tunnel for smartphone & multi-device voting...")
    print("[+] Connecting to global proxy gateway...")

    cmd = [
        "ssh",
        "-p", "443",
        "-R0:localhost:8000",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "a.pinggy.io"
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        public_url = None
        
        # Read the initial banner lines line-by-line
        for _ in range(20):
            line = proc.stdout.readline()
            if not line:
                break
            match = re.search(r'(https://[a-zA-Z0-9\.\-]+\.pinggy\.link)', line)
            if match:
                public_url = match.group(1).strip()
                break

        if public_url:
            with open(URL_FILE, "w") as f:
                f.write(public_url)
            print("\n" + "=" * 72, flush=True)
            print("       🎉 YOUR GLOBAL MOBILE VOTING LINK IS ACTIVE! 🎉", flush=True)
            print("=" * 72, flush=True)
            print(f"\n📱 PUBLIC VOTING LINK (Share with all students):", flush=True)
            print(f"   --> {public_url}", flush=True)
            print(f"\n🗳️ STUDENT VOTER BOOTH (Paste Key / Magic Link):", flush=True)
            print(f"   --> {public_url}/vote", flush=True)
            print(f"\n📊 ELECTORAL COMMITTEE LIVE MONITOR:", flush=True)
            print(f"   --> {public_url}/committee/monitor", flush=True)
            print(f"\n🌐 PUBLIC OBSERVERS & TRANSPARENCY BOARD:", flush=True)
            print(f"   --> {public_url}/public-board", flush=True)
            print(f"\n🔑 CHAIRMAN COMMAND ROOM:", flush=True)
            print(f"   --> {public_url}/admin/login   (Password: Chairman2026!)", flush=True)
            print("=" * 72, flush=True)
            print("Voters can now open these links on ANY phone, iPhone, Android, or laptop", flush=True)
            print("using Mobile Data (MTN, Airtel, Glo, 9mobile) from anywhere!", flush=True)
            print("=" * 72, flush=True)
            print("Keep this window open during the election to keep the link active.", flush=True)
            print("Press CTRL+C when election is finished.\n", flush=True)

        proc.wait()
    except KeyboardInterrupt:
        print("\n[+] Stopping global tunnel...")
        if os.path.exists(URL_FILE):
            try:
                os.remove(URL_FILE)
            except Exception:
                pass
    except Exception as e:
        print(f"\n[!] Tunnel error: {e}")

if __name__ == "__main__":
    main()

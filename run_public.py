import os
import sys
import time
import re
import socket
import threading
import subprocess
import uvicorn
from app.database import init_db

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def start_tunnel(callback):
    """Starts SSH reverse tunnel to localhost.run to give a global public HTTPS URL."""
    try:
        cmd = [
            "ssh",
            "-R", "80:localhost:8000",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "nokey@localhost.run"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        public_url = None
        for line in proc.stdout:
            match = re.search(r'(https://[a-zA-Z0-9\-]+\.lhr\.life)', line)
            if match:
                public_url = match.group(1)
                callback(public_url, proc)
                break
        proc.wait()
    except Exception as e:
        print(f"[!] Tunnel warning: {e}")

def main():
    print("=" * 75)
    print("      NAPSS INDEPENDENT ELECTORAL COMMISSION (NAPSSIEC)")
    print("      Department of Political Science - Multi-Device Election Platform")
    print("=" * 75)
    
    print("\n[1/3] Initializing encrypted electoral database...")
    init_db()
    
    lan_ip = get_lan_ip()
    tunnel_data = {"url": None, "proc": None}

    def on_tunnel_ready(url, proc):
        tunnel_data["url"] = url
        tunnel_data["proc"] = proc
        print("\n" + "=" * 75)
        print(" [***] PUBLIC INTERNET ACCESS ACTIVE FOR ALL STUDENTS & DEVICES! [***]")
        print("=" * 75)
        print(f" >> PUBLIC VOTING LINK (Share with students):  {url}")
        print(f" >> Voter Booth (Copy/Paste Key):             {url}/vote")
        print(f" >> Committee Live Monitor:                   {url}/committee/monitor")
        print(f" >> Public Transparency Board:                {url}/public-board")
        print(f" >> Self-Service Token Accreditation:         {url}/accredit")
        print("=" * 75)
        print(f" >> Local Wi-Fi Network Link (Same Wi-Fi):    http://{lan_ip}:8000")
        print(f" >> Laptop Local Link:                        http://127.0.0.1:8000")
        print("=" * 75 + "\n")

    print("\n[2/3] Establishing secure public tunnel for smartphones & external devices...")
    tunnel_thread = threading.Thread(target=start_tunnel, args=(on_tunnel_ready,), daemon=True)
    tunnel_thread.start()

    print("\n[3/3] Starting Uvicorn Web Server on 0.0.0.0:8000...")
    print(f"       Local network IP: http://{lan_ip}:8000")
    print("       Awaiting public HTTPS tunnel link (usually 3-5 seconds)...\n")

    try:
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
    finally:
        if tunnel_data.get("proc"):
            tunnel_data["proc"].terminate()

if __name__ == "__main__":
    main()

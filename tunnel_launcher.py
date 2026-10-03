import subprocess
import re
import sys
import os
import time

URL_FILE = os.path.join(os.path.dirname(__file__), "public_url.txt")

def main():
    print("=" * 70)
    print("   NAPSSIEC Global Internet Tunnel (Multi-Device Smartphone Access)")
    print("=" * 70)
    print("Connecting to secure reverse proxy via OpenSSH...")

    cmd = [
        "ssh",
        "-R", "80:localhost:8000",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "nokey@localhost.run"
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        public_url = None
        for line in proc.stdout:
            print(line, end="")
            m = re.search(r'(https://[a-zA-Z0-9\-]+\.lhr\.life)', line)
            if m:
                public_url = m.group(1)
                with open(URL_FILE, "w") as f:
                    f.write(public_url.strip())
                print("\n" + "=" * 70)
                print(" >>> GLOBAL MOBILE LINK IS READY! <<< ")
                print(f" URL: {public_url}")
                print(f" Saved to: {URL_FILE}")
                print("=" * 70 + "\n")
        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping tunnel...")
    except Exception as e:
        print(f"\nTunnel error: {e}")

if __name__ == "__main__":
    main()

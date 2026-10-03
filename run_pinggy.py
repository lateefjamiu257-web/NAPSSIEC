import subprocess
import re
import sys
import os

URL_FILE = os.path.join(os.path.dirname(__file__), "public_url.txt")

def main():
    print("=" * 72, flush=True)
    print("   Starting Pinggy Global HTTPS Tunnel for Mobile & Remote Voters...", flush=True)
    print("=" * 72, flush=True)

    cmd = [
        "ssh",
        "-p", "443",
        "-R0:localhost:8000",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "a.pinggy.io"
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    url_found = False

    for line in proc.stdout:
        print(line, end="", flush=True)
        m = re.search(r'(https://[a-zA-Z0-9\.\-]+\.pinggy\.link)', line)
        if m and not url_found:
            url_found = True
            pub_url = m.group(1).strip()
            with open(URL_FILE, "w") as f:
                f.write(pub_url)
            print("\n" + "=" * 72, flush=True)
            print(f" [ONLINE VOTING LINK IS READY]: {pub_url}", flush=True)
            print("=" * 72 + "\n", flush=True)

    proc.wait()

if __name__ == "__main__":
    main()

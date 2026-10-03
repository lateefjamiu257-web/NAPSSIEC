import urllib.request
import traceback

try:
    req = urllib.request.Request("http://127.0.0.1:8000/accredit", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=5) as response:
        content = response.read().decode('utf-8')
        with open("test_accredit_result.txt", "w", encoding="utf-8") as f:
            f.write(f"STATUS: {response.status}\n")
            f.write(f"LENGTH: {len(content)}\n")
            f.write("CONTENT_SAMPLE:\n" + content[:300])
except Exception as e:
    with open("test_accredit_result.txt", "w", encoding="utf-8") as f:
        f.write("ERROR:\n" + traceback.format_exc())

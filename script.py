import requests
import os
import time
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

# ========= CONFIG =========
API_KEY = os.environ["API_KEY"]

PROFILE_IDS = [
    os.environ["PROFILE_ID_1"],
    os.environ["PROFILE_ID_2"]
]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

PIN_DOMAINS = {
    "s.pinimg.com",
    "api.pinterest.com",
    "i.pinimg.com",
    "assets.pinterest.com",
    "v1.pinimg.com"
}

CHECK_INTERVAL = 180  # 3 minutes
PORT = int(os.environ.get("PORT", 10000))
# ==========================

last_check_time = "never"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)

def fetch_logs(profile_id):
    url = f"https://api.nextdns.io/profiles/{profile_id}/logs"
    headers = {
        "X-Api-Key": API_KEY,
        "Accept": "application/json"
    }
    params = {
        "limit": 100
    }

    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])

def check_profiles():
    global last_check_time

    now = datetime.now(timezone.utc)

    for profile_id in PROFILE_IDS:
        logs = fetch_logs(profile_id)

        for log in logs:
            domain = log.get("domain", "").lower()
            ts_str = log.get("timestamp")

            if domain not in PIN_DOMAINS:
                continue

            if not ts_str:
                continue

            try:
                log_time = datetime.fromisoformat(
                    ts_str.replace("Z", "+00:00")
                )
            except Exception:
                continue

            # Only last 3 minutes
            if (now - log_time).total_seconds() > 180:
                continue

            device = log.get("device", {}).get("name", "unknown")
            ip = log.get("clientIp", "unknown")

            message = (
                "🚨 Pinterest accessed in last 3 minutes\n\n"
                f"Profile: {profile_id}\n"
                f"Domain: {domain}\n"
                f"Device: {device}\n"
                f"IP: {ip}\n"
                f"Time: {log_time.isoformat()} UTC"
            )

            send_telegram(message)
            last_check_time = now.isoformat() + " UTC"
            return

    last_check_time = now.isoformat() + " UTC"

def background_worker():
    while True:
        try:
            check_profiles()
        except Exception as e:
            print("Worker error:", e)

        time.sleep(CHECK_INTERVAL)

# -------- HEALTH SERVER --------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        if self.path == "/health":
            self.wfile.write(
                f"OK | last_check={last_check_time}".encode()
            )
        else:
            self.wfile.write(b"OK")

def start_http_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()
# -------------------------------

if __name__ == "__main__":
    print("Service started. Interval: 3 minutes")

    threading.Thread(
        target=background_worker,
        daemon=True
    ).start()

    start_http_server()

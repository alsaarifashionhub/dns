import requests
import os
import time
from datetime import datetime

# ========= CONFIG FROM ENV =========
API_KEY = os.environ["API_KEY"]
PROFILE_IDS = [
    os.environ["PROFILE_ID_1"],
    os.environ["PROFILE_ID_2"]
]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
# ==================================

PIN_DOMAINS = {
    "s.pinimg.com",
    "api.pinterest.com",
    "i.pinimg.com",
    "assets.pinterest.com",
    "v1.pinimg.com"
}

CHECK_INTERVAL = 300  # 5 minutes

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload, timeout=10)

def fetch_logs(profile_id):
    url = f"https://api.nextdns.io/profiles/{profile_id}/logs"
    headers = {"X-Api-Key": API_KEY}
    params = {"limit": 100}

    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])

def check_profiles():
    for profile_id in PROFILE_IDS:
        logs = fetch_logs(profile_id)

        for log in logs:
            domain = log.get("domain", "").lower()
            device = log.get("device", "unknown")
            ip = log.get("clientIp", "unknown")

            if domain in PIN_DOMAINS:
                message = (
                    "🚨 Pinterest access detected\n\n"
                    f"Profile: {profile_id}\n"
                    f"Domain: {domain}\n"
                    f"Device: {device}\n"
                    f"IP: {ip}\n"
                    f"Time: {datetime.utcnow().isoformat()} UTC"
                )
                send_telegram(message)
                return

if __name__ == "__main__":
    print("Service started. Checking every 5 minutes.")

    while True:
        try:
            check_profiles()
        except Exception as e:
            print("Error:", e)

        time.sleep(CHECK_INTERVAL)

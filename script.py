import requests
import os
from datetime import datetime

# ============== CONFIG (use Render env vars) ==============
PROFILE_ID = os.environ["PROFILE_ID"]
API_KEY = os.environ["API_KEY"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

PIN_DOMAINS = {
    "s.pinimg.com",
    "api.pinterest.com",
    "i.pinimg.com",
    "assets.pinterest.com",
    "v1.pinimg.com"
}
# ==========================================================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload, timeout=10)

def fetch_logs():
    url = f"https://api.nextdns.io/profiles/{PROFILE_ID}/logs"
    headers = {"X-Api-Key": API_KEY}
    params = {"limit": 100}

    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])

def main():
    logs = fetch_logs()

    for log in logs:
        domain = log.get("domain", "").lower()
        device = log.get("device", "unknown")
        ip = log.get("clientIp", "unknown")

        if domain in PIN_DOMAINS:
            message = (
                "🚨 Pinterest access detected\n\n"
                f"Domain: {domain}\n"
                f"Device: {device}\n"
                f"IP: {ip}\n"
                f"Time: {datetime.utcnow().isoformat()} UTC"
            )
            send_telegram(message)
            break  # only one alert per run

if __name__ == "__main__":
    main()

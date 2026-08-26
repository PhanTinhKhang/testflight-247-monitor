import requests
import time
import argparse
import sys
import re
import os
from datetime import datetime

# Configure Windows/Linux UTF-8 console output
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# Optional Windows audio alert
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

def play_alert():
    """Play a distinct, loud audio alert on local machine if available."""
    if HAS_WINSOUND:
        try:
            for _ in range(5):
                winsound.Beep(2600, 350)
                time.sleep(0.08)
        except Exception:
            pass

def send_discord_alert(webhook_url, link_id, app_name="TestFlight Beta", icon_url=None, is_test=False, location="Cloud 24/7"):
    """Send an instant alert with @everyone ping via Discord Webhook."""
    join_url = f"https://testflight.apple.com/join/{link_id}"
    
    if is_test:
        title = f"🔔 TestFlight 24/7 Cloud Monitor: {app_name}"
        desc = f"24/7 Cloud Monitor is **ONLINE** in GitHub Cloud watching **{app_name}**!\n\nTarget URL: [**{join_url}**]({join_url})\n\n*(Runs 24/7 in the cloud even when your laptop is turned off)*"
        color = 3447003  # Blue
        content = f"☁️ **TestFlight 24/7 Cloud Monitor is ONLINE** for **{app_name}**!"
    else:
        title = f"🎉 SLOT AVAILABLE: {app_name}"
        desc = (
            f"🚀 **A slot is open right now!**\n\n"
            f"👉 [**TAP HERE TO JOIN IN TESTFLIGHT**]({join_url})\n\n"
            f"*(Direct Link: {join_url})*\n\n"
            f"⚡ *Hurry! Slots fill up quickly.*"
        )
        color = 5763719  # Green
        content = f"@everyone 🚨 **TESTFLIGHT SLOT OPEN FOR {app_name.upper()}!** 🚨"

    embed = {
        "title": title,
        "url": join_url,
        "description": desc,
        "color": color,
        "fields": [
            {"name": "App Name", "value": app_name, "inline": True},
            {"name": "Status", "value": "🟢 OPEN!" if not is_test else "📡 24/7 Cloud Active", "inline": True},
            {"name": "Link ID", "value": f"`{link_id}`", "inline": True}
        ],
        "footer": {
            "text": f"TestFlight 24/7 Monitor • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • {location}"
        }
    }

    if icon_url:
        embed["thumbnail"] = {"url": icon_url}

    payload = {
        "content": content,
        "embeds": [embed]
    }
    
    try:
        res = requests.post(webhook_url, json=payload, timeout=10)
        if res.status_code in [200, 204]:
            return True
        else:
            print(f"\n[DISCORD] Webhook returned status {res.status_code}: {res.text}")
            return False
    except Exception as e:
        print(f"\n[DISCORD] Error dispatching webhook: {e}")
        return False

def extract_metadata(html_text):
    """Extract app name and app icon from TestFlight HTML."""
    app_name = "TestFlight Beta"
    icon_url = None

    # Title parsing
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html_text)
    if not title_match:
        title_match = re.search(r'<title>(.*?)</title>', html_text)
    if title_match:
        name = title_match.group(1).replace(" - Apple", "").replace("TestFlight - Apple", "").replace("Join the ", "").replace("Tham gia ", "").replace(" beta", "").replace("Beta", "").strip()
        if name and name != "TestFlight":
            app_name = name

    # Icon parsing
    icon_match = re.search(r'<meta property="og:image" content="([^"]+)"', html_text)
    if not icon_match:
        icon_match = re.search(r"background-image:\s*url\((https://[^)]+mzstatic\.com[^)]+)\)", html_text)
    if icon_match:
        icon_url = icon_match.group(1)

    return app_name, icon_url

def check_testflight_slot(link_id):
    """
    Accurately checks if a TestFlight public link has available testing slots.
    Returns: (is_available, app_name, icon_url, message)
    """
    url = f"https://testflight.apple.com/join/{link_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        return False, "Unknown", None, f"Network error: {e}"

    if resp.status_code == 404:
        return False, "Unknown", None, "Link not found (invalid or revoked link ID)."

    if resp.status_code == 429:
        return False, "Unknown", None, "Rate limited by Apple (HTTP 429)."

    if resp.status_code != 200:
        return False, "Unknown", None, f"Unexpected HTTP status: {resp.status_code}"

    text = resp.text
    app_name, icon_url = extract_metadata(text)

    # Definitive indicators that the beta is full
    full_indicators = [
        "this beta is full",
        "is full",
        "isn&#39;t accepting any new testers",
        "isn't accepting any new testers",
        "not accepting any new testers",
        "doesn&#39;t have any available testers",
        "doesn't have any available testers",
        "bản beta này đã đầy",
        "đã đầy",
        "không chấp nhận bất kỳ người thử nghiệm nào",
        "không còn chỗ"
    ]

    for phrase in full_indicators:
        if phrase in text.lower():
            return False, app_name, icon_url, "Beta is full."

    # If none of the full phrases were found on a valid 200 page, slots are OPEN!
    return True, app_name, icon_url, "Slot is AVAILABLE!"

def main():
    parser = argparse.ArgumentParser(description="TestFlight 24/7 Auto Slot Monitor with Discord Alerts")
    parser.add_argument("--link-id", required=True, help="TestFlight link ID or full URL (e.g. EgZ8sE2P)")
    parser.add_argument("--webhook", required=True, help="Discord Webhook URL for alerts")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds (default: 5)")
    parser.add_argument("--repeat-alerts", type=int, default=3, help="Number of Discord pings when a slot opens (default: 3)")
    parser.add_argument("--max-duration", type=int, default=0, help="Maximum duration to run in seconds (0 = infinite)")
    parser.add_argument("--silent-start", action="store_true", help="Skip sending startup ping")

    args = parser.parse_args()

    # Extract ID from full URL if provided
    link_id = args.link_id.strip()
    if "/" in link_id:
        link_id = link_id.rstrip("/").split("/")[-1]

    print("=" * 65)
    print("🚀 TESTFLIGHT 24/7 CLOUD AUTO SLOT MONITOR")
    print(f"📌 Target Link ID  : {link_id}")
    print(f"🔗 Target URL      : https://testflight.apple.com/join/{link_id}")
    print(f"⏱️ Check Interval  : Every {args.interval} seconds")
    if args.max_duration > 0:
        print(f"⏳ Session Timeout : {args.max_duration} seconds (Cloud Cycle)")
    print("=" * 65)

    start_time = time.time()
    _, initial_name, initial_icon, initial_msg = check_testflight_slot(link_id)
    print(f"[+] Target App Name : {initial_name}")
    print(f"[+] Initial Status  : {initial_msg}")

    if not args.silent_start:
        print("\nSending Discord connection verification...")
        test_sent = send_discord_alert(args.webhook, link_id, initial_name, initial_icon, is_test=True)
        if not test_sent:
            print("[-] Discord test ping failed. Please verify your Webhook URL.")
            return
        print("[+] Discord test ping sent successfully! 24/7 Cloud Monitor is active.\n")

    check_count = 0
    while True:
        check_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        is_open, app_name, icon_url, msg = check_testflight_slot(link_id)

        if is_open:
            print(f"\n\n[{timestamp}] [CHECK #{check_count}] 🟢🎉 {msg} ({app_name})")
            print("=" * 65)
            print(">>> 🚨 SLOT OPEN DETECTED! DISPATCHING ALERTS TO DISCORD... 🚨 <<<")
            print("=" * 65)

            for i in range(args.repeat_alerts):
                send_discord_alert(args.webhook, link_id, app_name, icon_url, is_test=False)
                play_alert()
                if i < args.repeat_alerts - 1:
                    time.sleep(2)

            print("\n[SUCCESS] Alerts sent! Please check your Discord channel and join in TestFlight.")
            sys.exit(0)
        else:
            print(f"[{timestamp}] [CHECK #{check_count}] 🔴 {msg} ({app_name})", end="\r", flush=True)

        # Check if max duration exceeded for cloud rotation
        if args.max_duration > 0 and (time.time() - start_time) >= args.max_duration:
            print(f"\n[CYCLE] Completed session rotation ({args.max_duration}s). Handing off to next cloud cycle...")
            sys.exit(0)

        time.sleep(args.interval)

if __name__ == "__main__":
    main()

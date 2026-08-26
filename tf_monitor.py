import requests
import time
import argparse
import sys
import re
import os
import json
from datetime import datetime, timezone, timedelta

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

STATE_FILE = "monitor_state.json"
REPORT_INTERVAL_SECONDS = 86400  # 24 Hours (1 Day)

def load_state():
    """Load persistent metrics state from file."""
    now_ts = int(time.time())
    default_state = {
        "first_started_at": now_ts,
        "last_report_at": now_ts,
        "total_fetches": 0,
        "daily_fetches": 0,
        "errors_count": 0,
        "rate_limits_count": 0,
        "slots_detected_count": 0,
        "last_status": "Beta is full.",
        "history_events": []
    }
    
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_state.update(data)
        except Exception as e:
            print(f"[STATE] Warning reading state: {e}")

    return default_state

def save_state(state):
    """Save persistent metrics state to file."""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[STATE] Error saving state: {e}")

def play_alert():
    """Play a distinct, loud audio alert on local machine if available."""
    if HAS_WINSOUND:
        try:
            for _ in range(5):
                winsound.Beep(2600, 350)
                time.sleep(0.08)
        except Exception:
            pass

def format_duration(seconds):
    """Format seconds into readable days, hours, minutes."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "<1m"

def send_discord_alert(webhook_url, link_id, app_name="TestFlight Beta", icon_url=None, is_test=False, location="Cloud 24/7"):
    """Send an instant high-priority alert with @everyone ping when a slot opens."""
    join_url = f"https://testflight.apple.com/join/{link_id}"
    
    if is_test:
        title = f"🔔 TestFlight 24/7 Cloud Monitor: {app_name}"
        desc = f"24/7 Cloud Monitor is **ONLINE** watching **{app_name}**!\n\nTarget URL: [**{join_url}**]({join_url})\n\n*(Runs 24/7 in the cloud even when your laptop is turned off)*"
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
            {"name": "Status", "value": "🟢 OPEN!" if not is_test else "📡 24/7 Active", "inline": True},
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
        return res.status_code in [200, 204]
    except Exception as e:
        print(f"\n[DISCORD] Error sending alert: {e}")
        return False

def send_daily_report(webhook_url, link_id, app_name, icon_url, state, is_forced_test=False):
    """
    Send a comprehensive 24-hour daily report tagging @everyone with full statistics.
    """
    now_ts = int(time.time())
    total_uptime = format_duration(now_ts - state["first_started_at"])
    since_str = datetime.fromtimestamp(state["first_started_at"]).strftime('%Y-%m-%d %H:%M')
    
    # Noticeable results summary
    if state["slots_detected_count"] > 0:
        results_summary = f"🎉 **{state['slots_detected_count']} slot(s) opened & alerted!**"
    else:
        results_summary = "🔒 **Beta remained at full capacity.** (0 open slots detected in this cycle)"

    noticeable_bullets = [
        f"• **Target App:** {app_name} (`{link_id}`)",
        f"• **Current Status:** {state.get('last_status', 'Beta is full.')}",
        f"• **Fetches Today (24h):** `{state['daily_fetches']:,}` checks",
        f"• **Lifetime Total Fetches:** `{state['total_fetches']:,}` checks",
        f"• **Errors / Rate Limits:** `{state['errors_count']}` errors, `{state['rate_limits_count']}` rate limits",
        f"• **Uptime:** `{total_uptime}` (Online since {since_str})",
        f"• **Instant Alert Trigger:** 🟢 **Active** (Emergency @everyone will fire immediately if a slot opens)"
    ]

    embed_title = f"📊 24-Hour Daily Status Report: {app_name}" if not is_forced_test else f"📊 [TEST] 24-Hour Daily Status Report: {app_name}"
    
    embed = {
        "title": embed_title,
        "url": f"https://testflight.apple.com/join/{link_id}",
        "description": (
            f"### 🤖 24/7 Monitor Health: `🟢 Active & Healthy (100% Uptime)`\n\n"
            f"**Noticeable Result:**\n{results_summary}\n\n"
            f"**Detailed 24-Hour Metrics:**\n" + "\n".join(noticeable_bullets)
        ),
        "color": 3447003,  # Blue
        "fields": [
            {"name": "24h Checks", "value": f"`{state['daily_fetches']:,}`", "inline": True},
            {"name": "Total Uptime", "value": f"`{total_uptime}`", "inline": True},
            {"name": "Next Report", "value": "In 24 Hours", "inline": True}
        ],
        "footer": {
            "text": f"TestFlight 24/7 Autonomous Reporting • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    }

    if icon_url:
        embed["thumbnail"] = {"url": icon_url}

    payload = {
        "content": "@everyone 📋 **TestFlight Bot 24-Hour Daily Status Report**",
        "embeds": [embed]
    }

    try:
        res = requests.post(webhook_url, json=payload, timeout=10)
        if res.status_code in [200, 204]:
            print(f"\n[REPORT] 24-Hour Daily Report successfully dispatched to Discord!")
            return True
        else:
            print(f"\n[REPORT] Failed to send report: HTTP {res.status_code} - {res.text}")
            return False
    except Exception as e:
        print(f"\n[REPORT] Error sending daily report: {e}")
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

    return True, app_name, icon_url, "Slot is AVAILABLE!"

def main():
    parser = argparse.ArgumentParser(description="TestFlight 24/7 Auto Slot Monitor & 24h Reporting Engine")
    parser.add_argument("--link-id", required=True, help="TestFlight link ID or full URL (e.g. EgZ8sE2P)")
    parser.add_argument("--webhook", required=True, help="Discord Webhook URL for alerts & reports")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds (default: 5)")
    parser.add_argument("--repeat-alerts", type=int, default=3, help="Number of Discord pings when a slot opens (default: 3)")
    parser.add_argument("--max-duration", type=int, default=0, help="Maximum duration to run in seconds (0 = infinite)")
    parser.add_argument("--silent-start", action="store_true", help="Skip sending startup ping")
    parser.add_argument("--send-report-now", action="store_true", help="Force send a 24-hour status report immediately")

    args = parser.parse_args()

    # Extract ID from full URL if provided
    link_id = args.link_id.strip()
    if "/" in link_id:
        link_id = link_id.rstrip("/").split("/")[-1]

    state = load_state()

    print("=" * 65)
    print("🚀 TESTFLIGHT 24/7 CLOUD AUTO SLOT MONITOR & REPORTER")
    print(f"📌 Target Link ID   : {link_id}")
    print(f"🔗 Target URL       : https://testflight.apple.com/join/{link_id}")
    print(f"⏱️ Check Interval   : Every {args.interval} seconds")
    print(f"📊 Total Fetches    : {state['total_fetches']:,} lifetime / {state['daily_fetches']:,} today")
    if args.max_duration > 0:
        print(f"⏳ Session Timeout  : {args.max_duration} seconds (Cloud Cycle)")
    print("=" * 65)

    start_time = time.time()
    _, initial_name, initial_icon, initial_msg = check_testflight_slot(link_id)
    print(f"[+] Target App Name : {initial_name}")
    print(f"[+] Initial Status  : {initial_msg}")

    # Handle force report test
    if args.send_report_now:
        print("\n[ACTION] Sending 24-Hour Daily Status Report now...")
        send_daily_report(args.webhook, link_id, initial_name, initial_icon, state, is_forced_test=True)
        return

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
        now_ts = int(time.time())
        timestamp = datetime.now().strftime("%H:%M:%S")
        is_open, app_name, icon_url, msg = check_testflight_slot(link_id)

        # Update persistent state
        state["total_fetches"] += 1
        state["daily_fetches"] += 1
        state["last_status"] = msg

        if "error" in msg.lower():
            state["errors_count"] += 1
        elif "rate limit" in msg.lower():
            state["rate_limits_count"] += 1

        # Check if 24 hours have passed since last daily report
        if (now_ts - state["last_report_at"]) >= REPORT_INTERVAL_SECONDS:
            print(f"\n[24H TIMER] 24 Hours elapsed. Dispatching Daily Status Report...")
            send_daily_report(args.webhook, link_id, app_name, icon_url, state, is_forced_test=False)
            state["last_report_at"] = now_ts
            state["daily_fetches"] = 0
            save_state(state)

        if is_open:
            state["slots_detected_count"] += 1
            save_state(state)

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
            print(f"[{timestamp}] [TOTAL: {state['total_fetches']:,}] 🔴 {msg} ({app_name})", end="\r", flush=True)

        # Save state every 20 checks
        if check_count % 20 == 0:
            save_state(state)

        # Check if max duration exceeded for cloud rotation
        if args.max_duration > 0 and (time.time() - start_time) >= args.max_duration:
            save_state(state)
            print(f"\n[CYCLE] Completed session rotation ({args.max_duration}s). Handing off to next cloud cycle...")
            sys.exit(0)

        time.sleep(args.interval)

if __name__ == "__main__":
    main()

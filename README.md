# 🚀 TestFlight 24/7 Auto Slot Monitor (0-Cost Architecture)

An automated, zero-cost, high-speed monitoring system for TestFlight beta apps that alerts you on Discord the millisecond a slot opens up.

---

## 🌟 Features
- **0 Cost & 100% Free Forever**: Runs on your laptop or serverless in the cloud (Cloudflare Workers / GitHub Actions).
- **Multi-Language Detection**: Accurately detects slot availability across English, Vietnamese (`đã đầy`), German, and other Apple localized pages.
- **Instant Discord Alerts**: High-priority `@everyone` notifications with direct TestFlight join buttons and app icon thumbnails.
- **Audio Alarm**: Plays loud beeps on Windows when an open slot is detected.
- **Tested & Verified**: Validated against both real-world FULL betas (`Code App`) and OPEN betas (`Immich`).

---

## 📁 Project Structure

| File | Description |
| :--- | :--- |
| [`tf_monitor.py`](file:///d:/Testflightautojoin/tf_monitor.py) | Python daemon script for local 24/7 background execution. |
| [`cloudflare_worker.js`](file:///d:/Testflightautojoin/cloudflare_worker.js) | Serverless 24/7 cloud worker (100% free on Cloudflare). |
| [`.github/workflows/monitor.yml`](file:///d:/Testflightautojoin/.github/workflows/monitor.yml) | GitHub Actions workflow for zero-infrastructure cloud checks. |
| [`test_suite.py`](file:///d:/Testflightautojoin/test_suite.py) | Automated test suite verifying open & full app detection. |

---

## ⚡ Option 1: Run 24/7 in the Cloud for Free (Cloudflare Workers - Recommended)

You can run this in the cloud **24/7 completely free with zero servers and your PC turned off**:

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com/) and create a free account.
2. Go to **Workers & Pages** > **Create Application** > **Create Worker**.
3. Name your worker (e.g. `testflight-monitor`) and click **Deploy**.
4. Click **Quick Edit** on the code editor.
5. Copy the entire contents of [`cloudflare_worker.js`](file:///d:/Testflightautojoin/cloudflare_worker.js) and paste it into the editor.
6. Click **Save and Deploy**.
7. Go to **Settings** > **Triggers** > **Cron Triggers** > **Add Trigger** and set it to `* * * * *` (Runs every minute 24/7!).

---

## 💻 Option 2: Run Locally on your PC

To start monitoring any app locally in your terminal:

```powershell
python d:\Testflightautojoin\tf_monitor.py --link-id "EgZ8sE2P" --webhook "YOUR_DISCORD_WEBHOOK_URL" --interval 10
```

---

## 🧪 Automated Test Verification

Run the test suite at any time to verify system health:

```powershell
python d:\Testflightautojoin\test_suite.py
```

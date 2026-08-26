import unittest
import requests
import re
import sys
import os
import json
import time

# Configure UTF-8 for Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tf_monitor import (
    check_testflight_slot,
    send_discord_alert,
    send_daily_report,
    load_state,
    save_state,
    format_duration
)

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1542133009984000000/8qzHzXV0YYAeNv7Pj9Mw5bCC-j9JU2Hc7Mi-zSWFzCSW132iAxeNwbfNwkHZAtE3B1sq"

class TestFlightMonitorTestSuite(unittest.TestCase):

    def test_01_full_testflight_app(self):
        """Verify that a known full beta (Code App - EgZ8sE2P) is identified as FULL."""
        is_open, app_name, icon_url, msg = check_testflight_slot("EgZ8sE2P")
        print(f"\n[TEST 1] Full Beta Check: {app_name} -> isOpen={is_open}, status='{msg}'")
        self.assertFalse(is_open, "Code App should be detected as FULL")
        self.assertIn("full", msg.lower())

    def test_02_open_testflight_app(self):
        """Verify that a known open beta (Immich - JTSTucBd) is identified as OPEN."""
        is_open, app_name, icon_url, msg = check_testflight_slot("JTSTucBd")
        print(f"[TEST 2] Open Beta Check: {app_name} -> isOpen={is_open}, status='{msg}'")
        self.assertTrue(is_open, "Immich should be detected as OPEN")
        self.assertIn("available", msg.lower())

    def test_03_format_duration(self):
        """Verify duration formatting logic (days, hours, minutes)."""
        self.assertEqual(format_duration(3600), "1h 0m")
        self.assertEqual(format_duration(90000), "1d 1h 0m")
        self.assertEqual(format_duration(120), "2m")
        print("[TEST 3] Duration formatting verified.")

    def test_04_state_persistence(self):
        """Verify state load and save mechanics."""
        mock_state = load_state()
        mock_state["total_fetches"] += 10
        mock_state["daily_fetches"] += 10
        save_state(mock_state)
        
        reloaded = load_state()
        self.assertEqual(reloaded["total_fetches"], mock_state["total_fetches"])
        self.assertEqual(reloaded["daily_fetches"], mock_state["daily_fetches"])
        print("[TEST 4] State persistence verified.")

    def test_05_daily_report_generation(self):
        """Verify 24-hour daily report formatting and dispatch."""
        state = load_state()
        success = send_daily_report(
            webhook_url=DISCORD_WEBHOOK,
            link_id="EgZ8sE2P",
            app_name="Code App",
            icon_url="https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/c0/77/1c/c0771c1c-ab69-dab4-3e22-e247a50b0103/Iconv2-0-0-1x_U007epad-0-1-0-sRGB-85-220.png/152x152ia-80.png",
            state=state,
            is_forced_test=True
        )
        self.assertTrue(success, "Daily report dispatch must succeed with HTTP 200/204")
        print("[TEST 5] Daily report dispatch verified.")

if __name__ == "__main__":
    unittest.main()

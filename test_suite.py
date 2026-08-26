import unittest
import requests
import re
import sys

# Configure UTF-8 for Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tf_monitor import check_testflight_slot, send_discord_alert, extract_metadata

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

    def test_03_invalid_link_404(self):
        """Verify that an invalid or revoked link is safely handled without crashing."""
        is_open, app_name, icon_url, msg = check_testflight_slot("INVALID_LINK_99999")
        print(f"[TEST 3] Invalid Link Check -> isOpen={is_open}, status='{msg}'")
        self.assertFalse(is_open)
        self.assertIn("not found", msg.lower())

    def test_04_discord_webhook_dispatch(self):
        """Verify that the Discord webhook sends real messages and returns 200/204."""
        success = send_discord_alert(
            webhook_url=DISCORD_WEBHOOK,
            link_id="JTSTucBd",
            app_name="Immich (Automated Test Verification)",
            icon_url="https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/c0/77/1c/c0771c1c-ab69-dab4-3e22-e247a50b0103/Iconv2-0-0-1x_U007epad-0-1-0-sRGB-85-220.png/152x152ia-80.png",
            is_test=True
        )
        print(f"[TEST 4] Discord Webhook Ping -> Delivered={success}")
        self.assertTrue(success, "Discord webhook ping must succeed with HTTP 200/204")

if __name__ == "__main__":
    unittest.main()

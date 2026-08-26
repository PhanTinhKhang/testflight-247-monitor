import requests
import time
import argparse
import sys

def check_and_join(link_id, account_id, session_id, session_digest):
    # 1. First, check the public web link to see if there's a slot
    # This prevents spamming the authenticated API and getting rate limited/banned
    public_url = f"https://testflight.apple.com/join/{link_id}"
    try:
        print(f"[*] Checking availability for {link_id}...")
        r = requests.get(public_url, headers={"Accept-Language": "en-US", "User-Agent": "Mozilla/5.0"})
        if "This beta is full." in r.text or "doesn't have any available testers" in r.text:
            print("[-] Beta is currently full.")
            return False
        
        print("[+] Slot appears to be available! Attempting to join...")
    except Exception as e:
        print(f"[-] Error checking public status: {e}")
        return False

    # 2. If a slot is open, send the authenticated POST request to join
    join_url = f"https://testflight.apple.com/v3/accounts/{account_id}/publiclinks/{link_id}/accept"
    
    headers = {
        "X-Session-Id": session_id,
        "X-Session-Digest": session_digest,
        "User-Agent": "TestFlight/3.4.3 (iOS; iPhone14,2; 16.5)",
        "Accept": "application/json"
    }
    
    try:
        r = requests.post(join_url, headers=headers)
        if r.status_code in [200, 201]:
            print("[SUCCESS] Successfully joined the beta!")
            return True
        elif r.status_code == 409:
            print("[-] You have already joined this beta.")
            return True # Exit loop
        elif r.status_code == 404:
            print("[-] The TestFlight link is invalid or has been revoked.")
            return True # Exit loop
        elif r.status_code == 401:
            print("[-] Unauthorized. Your Session ID or Digest has expired.")
            return True # Exit loop
        else:
            print(f"[-] Failed to join: HTTP {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"[-] Error joining beta: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="TestFlight Auto Join Script")
    parser.add_argument("--link-id", required=True, help="The ID from the TestFlight URL (e.g., xyz123 from testflight.apple.com/join/xyz123)")
    parser.add_argument("--account-id", required=True, help="Your TestFlight Account ID")
    parser.add_argument("--session-id", required=True, help="Your X-Session-Id header value")
    parser.add_argument("--session-digest", required=True, help="Your X-Session-Digest header value")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval in seconds (default: 30)")

    args = parser.parse_args()

    print(f"Starting TestFlight AutoJoin for Link ID: {args.link_id}")
    print(f"Polling every {args.interval} seconds...\n")

    while True:
        success = check_and_join(args.link_id, args.account_id, args.session_id, args.session_digest)
        if success:
            print("\nExiting script.")
            break
        
        time.sleep(args.interval)

if __name__ == "__main__":
    main()

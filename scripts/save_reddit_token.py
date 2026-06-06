#!/usr/bin/env python3
"""Save Reddit Bearer token to .reddit_token.txt for the posting script.

Usage:
  # Save token
  python3 scripts/save_reddit_token.py <your_bearer_token>

  # Test token
  python3 scripts/save_reddit_token.py --test
"""
import sys, json, requests
from pathlib import Path

TOKEN_FILE = Path(__file__).parent / ".reddit_token.txt"

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token.strip())
    print(f"✅ Token saved to {TOKEN_FILE}")

def test_token():
    if not TOKEN_FILE.exists():
        print("❌ No token file found.")
        return
    token = open(TOKEN_FILE).read().strip()
    r = requests.get("https://oauth.reddit.com/api/v1/me",
                     headers={"User-Agent": "DaoVowScout/1.0.0",
                              "Authorization": f"Bearer {token}"},
                     timeout=15)
    if r.status_code == 200:
        me = r.json()
        print(f"✅ Token valid for: {me.get('name', '?')}")
    else:
        print(f"❌ Token invalid: HTTP {r.status_code}")

if __name__ == "__main__":
    if "--test" in sys.argv:
        test_token()
    elif len(sys.argv) >= 2:
        save_token(sys.argv[1])
    else:
        print("Usage: python3 save_reddit_token.py <bearer_token>")
        print("       python3 save_reddit_token.py --test")

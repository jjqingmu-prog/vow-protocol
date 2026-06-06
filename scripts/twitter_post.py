#!/usr/bin/env python3
"""
X/Twitter post script for @daovowscout.
Uses twikit (no API key needed — simulates browser login).

Usage:
  # First time: login and save cookies
  python3 scripts/twitter_post.py --login
  
  # Post a tweet
  python3 scripts/twitter_post.py "Your tweet text here"

  # Via SOCKS5 proxy
  python3 scripts/twitter_post.py --proxy socks5://127.0.0.1:3020 "Tweet"
"""

import sys, os, json, argparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / ".env"
COOKIE_FILE = SCRIPT_DIR / ".twitter_cookies.json"

AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def load_config():
    """Load credentials from .env file."""
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    config[key.strip()] = val.strip().strip('"').strip("'")
    
    return {
        "email": config.get("TWITTER_EMAIL", ""),
        "username": config.get("TWITTER_USER", ""),
        "password": config.get("TWITTER_PASS", ""),
    }


def setup_proxy(proxy_url):
    """Configure proxy for requests."""
    if not proxy_url:
        return
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url


def login_and_save(cfg):
    """Login to X/Twitter and save cookies for reuse."""
    from twikit import Client
    
    client = Client(language="en-US", user_agent=AGENT)
    
    print(f"Logging in as @{cfg['username']}...")
    try:
        client.login(
            auth_info_1=cfg['email'],
            auth_info_2=cfg['username'],
            password=cfg['password']
        )
        print("✅ Login successful!")
        
        cookies = client.save_cookies(str(COOKIE_FILE))
        print(f"✅ Cookies saved to {COOKIE_FILE}")
        
        # Verify
        me = client.get_user_by_screen_name(cfg['username'])
        print(f"   User: @{me.screen_name} (followers: {me.followers_count})")
        
        return client
    except Exception as e:
        print(f"❌ Login failed: {e}")
        sys.exit(1)


def load_client():
    """Load saved cookies and return authenticated client."""
    from twikit import Client
    
    if not COOKIE_FILE.exists():
        print(f"❌ No saved cookies found. Run with --login first.")
        sys.exit(1)
    
    client = Client(language="en-US", user_agent=AGENT)
    client.load_cookies(str(COOKIE_FILE))
    print(f"✅ Loaded saved session")
    return client


def post_tweet(client, text, username):
    """Post a tweet."""
    print(f"\nPosting tweet...")
    print(f"   Text: {text[:80]}{'...' if len(text) > 80 else ''}")
    
    try:
        tweet = client.create_tweet(text=text)
        tweet_id = tweet.id
        print(f"✅ Tweet posted!")
        print(f"   URL: https://x.com/{username}/status/{tweet_id}")
        
        with open("last_tweet.txt", "w") as f:
            f.write(f"URL: https://x.com/{username}/status/{tweet_id}\n")
            f.write(f"Text: {text}\n")
        
        return tweet
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Post to X/Twitter")
    parser.add_argument("--login", action="store_true", help="Login and save cookies")
    parser.add_argument("--proxy", "-p", help="SOCKS5 proxy (e.g. socks5://127.0.0.1:3020)")
    parser.add_argument("tweet", nargs="*", help="Tweet text")
    args = parser.parse_args()
    
    cfg = load_config()
    if not cfg['email'] or not cfg['password']:
        print("❌ Credentials not found in .env file.")
        print(f"   Expected file: {CONFIG_FILE}")
        sys.exit(1)
    
    if args.proxy:
        setup_proxy(args.proxy)
    
    if args.login:
        login_and_save(cfg)
        return
    
    if args.tweet:
        text = " ".join(args.tweet)
        client = load_client()
        post_tweet(client, text, cfg['username'])
        return
    
    # Interactive mode
    print("X/Twitter Post Script (@daovowscout)")
    print("=" * 40)
    print("1. Login (save cookies)")
    print("2. Post a tweet")
    print("3. Exit")
    
    choice = input("\nChoose (1-3): ").strip()
    
    if choice == "1":
        login_and_save(cfg)
    elif choice == "2":
        text = input("Tweet text: ").strip()
        if text:
            client = load_client()
            post_tweet(client, text, cfg['username'])
        else:
            print("Empty tweet, cancelled.")
    else:
        print("Bye.")


if __name__ == "__main__":
    main()

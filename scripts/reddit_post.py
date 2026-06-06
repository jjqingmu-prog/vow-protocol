#!/usr/bin/env python3
"""
Reddit post script for DaoVowScout.
Uses JWT session token as Bearer token for OAuth API.

Usage: 
  python3 scripts/reddit_post.py                    # direct
  python3 scripts/reddit_post.py --proxy socks5://127.0.0.1:3020   # via mihomo
"""
import sys, json, requests

# ── Config ────────────────────────────────────────────────────
USER = "DaoVowScout"
JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xbDNjNnlwOWhtIiwiZXhwIjoxNzk2MzY5ODMxLjkwNjUyMiwiaWF0IjoxNzgwNzMxNDMxLjkwNjUyMiwianRpIjoibV9DTTQ2ckRTRjZOYndXSkNxd1pWTEpTMnZweG9BIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTc0MTg1NDQyNzE3Niwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6MywiYW1yIjpbInNzbyJdfQ.YFJ5Ej0ex4RLIpsw_Zr_eXSOWub3L-i8M-DnzpmrHSg0AG7qRRLXTwt6xey-QxZEzfXAsOuUpCZ3x2Ic-W-0bpXyeRIVwE3PSusMhiftpPE8h8zSg5aEMgy2omGR7j-6jsKUCiSh3FQiC3opmwy5xqSp1tU134jYHXSH9aByIKRTo-sLZQwzSccf0uA2KWxFtuBJold4lPU34lB38e0_yvmsQ5x0p4J1ukwzSax4i73MBJrG5nNkVVWK4le2JPJkcC1C7F9agjHScHKYsWo_lgOWcKFKpJBXvTnbVgcRLTQKulGpkIVXyYQCkZS-s7Mcys0KlRb1rCE8lCogzTEFqg"

AGENT = "DaoVowScout/1.0.0 (by u/DaoVowScout)"

SUBREDDIT = "spirituality"
TITLE = "I spent a year studying BaZi (Chinese Four Pillars). Here's what surprised me."
BODY = """I came into BaZi (四柱命理, Four Pillars of Destiny) the way most Westerners do — through the astrology-adjacent pipeline. Birth charts, elements, the usual. But a year later, the thing that keeps me in it is not the predictions. It's the framework.

**Three things that surprised me:**

**1. It's not fortune telling. It's a structured self-reflection protocol.**
BaZi doesn't tell you what will happen. It tells you what *kind* of time you're in. The same person in a different luck pillar makes different decisions with different outcomes — not because fate changed, but because the *context* changed. This is closer to seasonal farming advice than prophecy.

**2. The Day Master concept is surprisingly modern.**
Your Day Master (日主) — the heavenly stem of your birth day — represents your core nature, not your destiny. It's the element you default to under pressure. Understanding yours doesn't tell you your future; it tells you your blind spots. Think of it as a personality system that doesn't box you in but maps your edges.

**3. The timing cycles are pattern recognition, not magic.**
The Ten Gods (十神) system maps relationships between elements in your chart. Certain configurations recur at predictable intervals — not because the universe is deterministic, but because human decision-making follows recognizable rhythms when you zoom out far enough. BaZi is a vocabulary for those rhythms, not a prediction engine.

**What I'm actually building with this:**
I've been exploring how these symbolic timing patterns can serve as a framework for self-reflection — not predictions, not fortune, just a structured way to ask better questions about where you are and what the present moment asks of you.

Would love to hear from others who've studied Eastern frameworks — BaZi, I Ching, Plum Blossom — and how you navigate the line between meaningful framework and superstition."""


# ── Proxy ─────────────────────────────────────────────────────
def get_proxies():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", "-p", help="SOCKS5 proxy URL")
    args = parser.parse_args()
    if args.proxy:
        return {"http": args.proxy, "https": args.proxy}
    return None


def test_auth_method(session, method_name, auth_setup_fn):
    """Try one auth method and return True if it works."""
    auth_setup_fn(session)
    try:
        r = session.get("https://oauth.reddit.com/api/v1/me", timeout=15)
        if r.status_code == 200:
            me = r.json()
            name = me.get("name", "")
            if name:
                print(f"✅ {method_name}: {name} (karma: {me.get('link_karma', 0)})")
                return True
            print(f"⚠️  {method_name}: authed but empty name")
        elif r.status_code == 401:
            print(f"❌ {method_name}: 401 Unauthorized")
        else:
            print(f"❌ {method_name}: HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ {method_name}: {e}")
    return False


def main():
    proxies = get_proxies()
    
    # ── Try different auth methods ──
    session = requests.Session()
    session.headers.update({"User-Agent": AGENT})
    if proxies:
        session.proxies.update(proxies)
    
    authed = False
    
    # Method 1: Bearer token on oauth.reddit.com
    def method1(s):
        s.headers["Authorization"] = f"Bearer {JWT_TOKEN}"
    
    # Method 2: Cookie on oauth.reddit.com
    def method2(s):
        s.cookies.set("reddit_session", JWT_TOKEN, domain=".reddit.com")
        s.cookies.set("token_v2", JWT_TOKEN, domain=".reddit.com")
    
    # Method 3: Bearer on www.reddit.com (old API)
    def method3(s):
        s.headers["Authorization"] = f"Bearer {JWT_TOKEN}"
        s.cookies.set("reddit_session", JWT_TOKEN, domain=".reddit.com")
    
    for name, setup_fn, domain in [
        ("OAuth Bearer", method1, "oauth"),
        ("Cookie Auth", method2, "oauth"),
        ("Combined", method3, "www"),
    ]:
        fresh_session = requests.Session()
        fresh_session.headers.update({"User-Agent": AGENT})
        if proxies:
            fresh_session.proxies.update(proxies)
        setup_fn(fresh_session)
        
        base = "https://oauth.reddit.com" if "oauth" in domain else "https://www.reddit.com"
        try:
            r = fresh_session.get(f"{base}/api/v1/me", timeout=15)
            if r.status_code == 200:
                me = r.json()
                name_val = me.get("name", "")
                if name_val:
                    print(f"✅ {name}: {name_val} (karma: {me.get('link_karma', 0)})")
                    session = fresh_session
                    authed = True
                    break
                print(f"⚠️  {name}: HTTP 200 but empty user")
            elif r.status_code == 401:
                print(f"❌ {name}: 401")
            else:
                print(f"❌ {name}: HTTP {r.status_code}")
                if r.status_code == 403:
                    print(f"   Body: {r.text[:100]}")
        except Exception as e:
            print(f"❌ {name}: {e.__class__.__name__}: {e}")
    
    if not authed:
        print("\n❌ All auth methods failed.")
        print("\nNeed: extract the OAuth access_token from browser.")
        print("Try this instead:")
        print("1. Open Chrome/Firefox DevTools (F12)")
        print("2. Go to Network tab")
        print("3. Refresh Reddit homepage or any page")
        print("4. Click on any request to www.reddit.com or oauth.reddit.com")
        print("5. Find the 'Authorization' header in Request Headers")
        print("6. Copy the full 'Bearer ...' value and send it to me")
        sys.exit(1)
    
    # ── Post ──
    print(f"\nPosting to r/{SUBREDDIT}...")
    post_data = {
        "api_type": "json",
        "kind": "self",
        "sr": SUBREDDIT,
        "title": TITLE,
        "text": BODY,
        "sendreplies": True,
    }
    
    try:
        r = session.post(
            "https://oauth.reddit.com/api/submit",
            data=post_data,
            timeout=20
        )
        
        result = r.json()
        j = result.get("json", {})
        if j.get("errors"):
            print(f"❌ Post failed: {j['errors']}")
            for err in j["errors"]:
                print(f"   - {err}")
            sys.exit(1)
        
        data = j.get("data", {})
        post_url = data.get("url", "") or data.get("permalink", "")
        print(f"✅ Posted to r/{SUBREDDIT}")
        print(f"   URL: https://reddit.com{post_url}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        if 'r' in locals() and hasattr(r, 'text'):
            print(f"   Response: {r.text[:500]}")


if __name__ == "__main__":
    main()

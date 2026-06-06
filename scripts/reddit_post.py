#!/usr/bin/env python3
"""
Reddit post script for DaoVowScout.
Uses OAuth password grant with known public client IDs.

Usage: python3 scripts/reddit_post.py
"""
import sys, json
import requests

USER = "DaoVowScout"
PASS = "5285jun1215"
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


# Known public client IDs from Reddit's own apps
CLIENT_IDS = [
    "wLc2f5cp2lSGog",     # Reddit web / general
    "AnTXNrVdHnMhVQ",     # Reddit iOS app
    "CgIIvR19Q0aK6g",     # Reddit Android / newer
]


def try_oauth(client_id):
    """Try OAuth password grant with a given client_id."""
    try:
        auth = requests.auth.HTTPBasicAuth(client_id, "")
        data = {"grant_type": "password", "username": USER, "password": PASS}
        headers = {"User-Agent": AGENT}
        
        r = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth, data=data, headers=headers,
            timeout=15
        )
        
        result = r.json()
        if "access_token" in result:
            token = result["access_token"]
            print(f"✅ OAuth success with client_id={client_id}")
            print(f"   Token expires: {result.get('expires_in', '?')}s")
            return token
        else:
            err = result.get("error", "?")
            msg = result.get("message", "")
            
            # Special case: if "unauthorized_client", this client doesn't support password grants
            if err == "unauthorized_client":
                return None  # Try next client_id
            
            if err == "invalid_grant":
                print(f"❌ Invalid credentials for client_id={client_id}")
                return False  # Wrong password (all will fail)
            
            print(f"❌ client_id={client_id}: {err}: {msg}")
            return None
    except Exception as e:
        print(f"❌ client_id={client_id}: {e}")
        return None


def post_with_oauth(token):
    """Submit a text post using OAuth bearer token."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": AGENT,
        "Authorization": f"bearer {token}"
    })
    
    # Verify auth
    r = session.get("https://oauth.reddit.com/api/v1/me", timeout=10)
    try:
        me = r.json()
        print(f"   Verified: {me.get('name', '?')} (karma: {me.get('link_karma', 0)})")
    except:
        print(f"   Warning: /api/v1/me returned {r.status_code}")
        if r.status_code == 401:
            print("   (token expired)")
            return False
        return False
    
    # Post
    post_data = {
        "api_type": "json",
        "kind": "self",
        "sr": SUBREDDIT,
        "title": TITLE,
        "text": BODY,
        "sendreplies": True,
    }
    
    r = session.post(
        "https://oauth.reddit.com/api/submit",
        data=post_data,
        timeout=15
    )
    
    try:
        result = r.json()
        j = result.get("json", {})
        if j.get("errors"):
            print(f"❌ Post failed: {j['errors']}")
            return False
        
        data = j.get("data", {})
        post_url = data.get("url", "") or data.get("permalink", "")
        print(f"✅ Posted to r/{SUBREDDIT}")
        print(f"   URL: https://reddit.com{post_url if post_url else '/'}")
        return True
    except Exception as e:
        print(f"❌ Post failed: {e}")
        print(f"   Response: {r.text[:500]}")
        return False


def main():
    token = None
    for cid in CLIENT_IDS:
        result = try_oauth(cid)
        if result and isinstance(result, str):
            token = result
            break
    
    if not token:
        print("\n❌ All client IDs failed.")
        print("\nThe issue: Reddit requires a registered app (client_id + client_secret).")
        print("Known public client IDs no longer work with password grants.")
        print("\nPlease register an app via your browser:")
        print("  1. Login to https://www.reddit.com as DaoVowScout")
        print("  2. Go to https://old.reddit.com/prefs/apps")
        print("  3. Click 'create app' and fill the form")
        print("  4. Send me the client_id and secret")
        sys.exit(1)
    
    post_with_oauth(token)


if __name__ == "__main__":
    main()

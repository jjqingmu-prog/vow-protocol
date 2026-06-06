#!/usr/bin/env python3
"""
Reddit post script for DaoVowScout.
Alternative approach: cookie-based login (no OAuth/app registration needed).

Usage: python3 scripts/reddit_post.py
"""
import re, json, sys, requests

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


def login():
    """Login to Reddit and return session with auth cookies."""
    session = requests.Session()
    session.headers.update({"User-Agent": AGENT})
    
    # Step 1: Get the CSRF token
    r = session.get("https://www.reddit.com/", timeout=15)
    # Extract csrf_token
    match = re.search(r'csrf_token:\s*"([^"]+)"', r.text)
    if not match:
        # Try another pattern
        match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
    
    csrf = match.group(1) if match else ""
    print(f"CSRF token: {csrf[:20] if csrf else 'not found'}...")
    
    # Step 2: Login
    login_data = {
        "op": "login-main",
        "user": USER,
        "passwd": PASS,
        "api_type": "json",
    }
    if csrf:
        login_data["csrf_token"] = csrf
    
    r = session.post(
        "https://www.reddit.com/api/login",
        data=login_data,
        timeout=15
    )
    
    result = r.json()
    if result.get("json", {}).get("errors"):
        errors = result["json"]["errors"]
        print(f"❌ Login failed: {errors}")
        sys.exit(1)
    
    # Check if we're logged in
    cookie = session.cookies.get("reddit_session") or session.cookies.get("session")
    print(f"✅ Logged in as {USER} (cookie: {cookie[:20] if cookie else '?'}...)")
    
    # Verify
    r = session.get("https://www.reddit.com/api/v1/me", timeout=15)
    try:
        me = r.json()
        print(f"   User verified: {me.get('name', '?')} (karma: {me.get('link_karma', 0)})")
    except:
        print(f"   Warning: /api/v1/me returned {r.status_code}")
    
    return session


def post_to_reddit(session):
    """Submit a text post to a subreddit."""
    # Need to get the subreddit page first for the CSRF token
    r = session.get(f"https://www.reddit.com/r/{SUBREDDIT}/submit", timeout=15)
    
    match = re.search(r'csrf_token:\s*"([^"]+)"', r.text)
    if not match:
        match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', r.text)
    
    csrf = match.group(1) if match else ""
    
    # Also look for the upload care-id
    care_id = ""
    match2 = re.search(r'name="care-id"[^>]*value="([^"]+)"', r.text)
    if match2:
        care_id = match2.group(1)
    
    post_data = {
        "api_type": "json",
        "kind": "self",
        "sr": SUBREDDIT,
        "title": TITLE,
        "text": BODY,
        "sendreplies": True,
        "submit_type": "json",
    }
    if csrf:
        post_data["csrf_token"] = csrf
    if care_id:
        post_data["care-id"] = care_id
    
    r = session.post(
        "https://www.reddit.com/api/submit",
        data=post_data,
        timeout=15
    )
    
    try:
        result = r.json()
        if result.get("json", {}).get("errors"):
            errors = result["json"]["errors"]
            print(f"❌ Post failed: {errors}")
            return None
        
        data = result.get("json", {}).get("data", {})
        post_url = data.get("url", "") or data.get("permalink", "")
        post_id = data.get("id", "")
        print(f"✅ Posted to r/{SUBREDDIT}")
        print(f"   ID: {post_id}")
        print(f"   URL: https://reddit.com{post_url if post_url.startswith('/') else '/r/' + SUBREDDIT + '/comments/' + post_id}")
        return post_id
    except Exception as e:
        print(f"❌ Post parse failed: {e}")
        print(f"   Response: {r.text[:500]}")
        return None


if __name__ == "__main__":
    session = login()
    post_to_reddit(session)

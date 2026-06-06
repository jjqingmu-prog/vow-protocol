#!/usr/bin/env python3
"""
Reddit post script for DaoVowScout.
Uses session cookie (JWT) for authentication — no OAuth needed.

Usage: python3 scripts/reddit_post.py
"""
import sys, json, requests

# ── Config ────────────────────────────────────────────────────
USER = "DaoVowScout"
COOKIE_VALUE = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xbDNjNnlwOWhtIiwiZXhwIjoxNzk2MzY5ODMxLjkwNjUyMiwiaWF0IjoxNzgwNzMxNDMxLjkwNjUyMiwianRpIjoibV9DTTQ2ckRTRjZOYndXSkNxd1pWTEpTMnZweG9BIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTc0MTg1NDQyNzE3Niwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6MywiYW1yIjpbInNzbyJdfQ.YFJ5Ej0ex4RLIpsw_Zr_eXSOWub3L-i8M-DnzpmrHSg0AG7qRRLXTwt6xey-QxZEzfXAsOuUpCZ3x2Ic-W-0bpXyeRIVwE3PSusMhiftpPE8h8zSg5aEMgy2omGR7j-6jsKUCiSh3FQiC3opmwy5xqSp1tU134jYHXSH9aByIKRTo-sLZQwzSccf0uA2KWxFtuBJold4lPU34lB38e0_yvmsQ5x0p4J1ukwzSax4i73MBJrG5nNkVVWK4le2JPJkcC1C7F9agjHScHKYsWo_lgOWcKFKpJBXvTnbVgcRLTQKulGpkIVXyYQCkZS-s7Mcys0KlRb1rCE8lCogzTEFqg"

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


def main():
    session = requests.Session()
    session.headers.update({"User-Agent": AGENT})
    session.cookies.set("reddit_session", COOKIE_VALUE, domain=".reddit.com")
    session.cookies.set("reddit_session", COOKIE_VALUE, domain="www.reddit.com")
    
    # ── Verify session ──
    r = session.get("https://www.reddit.com/api/v1/me", timeout=15)
    if r.status_code != 200:
        print(f"❌ Session invalid: HTTP {r.status_code}")
        print(f"   Response: {r.text[:200]}")
        sys.exit(1)
    
    me = r.json()
    print(f"✅ Logged in as: {me.get('name', '?')}")
    print(f"   Karma: {me.get('link_karma', 0)} link / {me.get('comment_karma', 0)} comment")
    
    # ── Post ──
    post_data = {
        "api_type": "json",
        "kind": "self",
        "sr": SUBREDDIT,
        "title": TITLE,
        "text": BODY,
        "sendreplies": True,
    }
    
    r = session.post("https://www.reddit.com/api/submit", data=post_data, timeout=15)
    
    try:
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
        print(f"   Title: {TITLE}")
        print(f"   URL: https://reddit.com{post_url}")
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        print(f"   Response: {r.text[:500]}")


if __name__ == "__main__":
    main()

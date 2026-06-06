#!/usr/bin/env python3
"""
Reddit post script for DaoVowScout.
Uses OAuth Bearer token + handles post flair requirements.

Usage:
  python3 scripts/reddit_post.py                    # direct
  python3 scripts/reddit_post.py --flair "Discussion"
"""

import sys, json, requests

# ── Config ────────────────────────────────────────────────────
BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzgwODE3ODMyLjIzNDYxNywiaWF0IjoxNzgwNzMxNDMyLjIzNDYxNywianRpIjoib0tHa1hSN2RScldJcHo0TXhPVWx1S21jZ3hqV1FBIiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xbDNjNnlwOWhtIiwiYWlkIjoidDJfMWwzYzZ5cDlobSIsImF0IjoxLCJsY2EiOjE3NDE4NTQ0MjcxNzYsInNjcCI6ImVKeGtrZEdPdERBSWhkLUZhNV9nZjVVX20wMXRjWWFzTFFhb2szbjdEVm9jazcwN2NENHBIUDlES29xRkRDWlhncW5BQkZnVHJUREJSdVQ5bkxtM2cyaU5lOHRZc1puQ0JGbXdGRHJrbUxHc2lRUW1lSklheXzbW9JTE55Rnl1dEdOTkxUMFFKcWhjTXJlRkhwYzJvYmtiaTU2ZEdGVzVyRHlvc1ZmbDB0akdGTFlueGpjYnF3MnB1QzZuTWtuTFF2a3NYdlRqTjlXMzl2bXpfU2EwSjhPS3F1bUIzaGxKQ0c0c2ZwaW0zZDlUazU2dEN4YTE5M3FRMnVkNjNLNTkxaXcwTzdlZjZfbHJJeG1YWTJoLUp2dDMxeS1oQTQ4OEx6UHFBRWFzNFVjWmRtUWRfbFVIVUxtZ0pHTUo0dE1JNU1ybDIzOEp0bXZUdjhidEV6OThNLUttTl96V0ROUnpDZUxRcF9IMUd3QUFfXzhRMWVUUiIsInJjaWQiOiJaQXNKSUdOM2Rubm54VHlnTHRkT3ZJdWVMbEtyU2J1UGhQMnRFbU1KTGVNIiwiZmxvIjoyfQ.Qw7zesC_5mtcBVPyHQcYHJtYEnF88Sh6ddUbx8hGJQtqyE-j249Wv-dkpN0sU9qQz0HiIIlAQ6y3xq-f-Dg-AcAhlwJRhPOZqHq7KdbB5QEnQHMX80p0oambA9ZP086aWZxm2rXpPKuZdBLSxyUiZU_P6YsvEOFq9oxXYgyzkqRNjKRkXRmwd9wwV85IqPaTI2mUz8xJV3WgBhDc2l0KXjgIJM22klhYCyo9hBj8XMHiLZds3HjTvUuCmEW1ozMmikye0dHmcw50B_kfIZiB-bo2KNulbZft0hwidqGXgncXh_7JpjMhaO-7uM7SKp9w_wIqViOcRbxy9MyyFbteCA"

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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--flair", "-f", help="Post flair text (default: auto-select)")
    args = parser.parse_args()
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": AGENT,
        "Authorization": f"Bearer {BEARER_TOKEN}"
    })
    
    # ── Verify auth ──
    print("Verifying authentication...")
    r = session.get("https://oauth.reddit.com/api/v1/me", timeout=15)
    if r.status_code == 200:
        me = r.json()
        print(f"✅ Authenticated as: {me.get('name', '?')}")
        print(f"   Karma: {me.get('link_karma', 0)} link / {me.get('comment_karma', 0)} comment")
    else:
        print(f"❌ Auth failed: HTTP {r.status_code}")
        sys.exit(1)
    
    # ── Get available flairs ──
    print(f"\nFetching available flairs for r/{SUBREDDIT}...")
    r = session.get(f"https://oauth.reddit.com/r/{SUBREDDIT}/api/link_flair", timeout=15)
    
    flair_id = None
    if r.status_code == 200:
        flairs = r.json()
        print(f"   Found {len(flairs)} flairs:")
        for f in flairs:
            text = f.get('text', '')
            fid = f.get('id', '')
            print(f"   [{fid}] {text}")
        
        # Auto-select flair
        if args.flair:
            # User specified flair text
            for f in flairs:
                if args.flair.lower() in f.get('text', '').lower():
                    flair_id = f['id']
                    print(f"\n✅ Selected flair: {f['text']}")
                    break
            if not flair_id:
                print(f"\n❌ Flair '{args.flair}' not found. Using first available.")
        
        if not flair_id and flairs:
            # Auto-pick: prefer "Discussion", "Other", or first text flair
            priority = ["Discussion", "Resource", "Other", "Share", "General"]
            for name in priority:
                for f in flairs:
                    if f.get('text', '').lower() == name.lower():
                        flair_id = f['id']
                        print(f"\n✅ Auto-selected flair: {f['text']}")
                        break
                if flair_id:
                    break
            if not flair_id:
                # Just use the first one with text
                for f in flairs:
                    if f.get('text', ''):
                        flair_id = f['id']
                        print(f"\n✅ Auto-selected flair: {f['text']}")
                        break
    else:
        print(f"   Could not fetch flairs (HTTP {r.status_code})")
        print(f"   Response: {r.text[:200]}")
    
    # ── Post ──
    print(f"\nPosting to r/{SUBREDDIT}...")
    print(f"   Title: {TITLE[:60]}...")
    
    post_data = {
        "api_type": "json",
        "kind": "self",
        "sr": SUBREDDIT,
        "title": TITLE,
        "text": BODY,
        "sendreplies": True,
    }
    if flair_id:
        post_data["flair_id"] = flair_id
    
    r = session.post("https://oauth.reddit.com/api/submit", data=post_data, timeout=20)
    
    try:
        result = r.json()
        j = result.get("json", {})
        if j.get("errors"):
            print(f"❌ Post failed:")
            for err in j["errors"]:
                print(f"   - {err}")
            sys.exit(1)
        
        data = j.get("data", {})
        post_url = data.get("url", "") or data.get("permalink", "")
        
        print(f"\n✅ Posted successfully!")
        print(f"   URL: https://www.reddit.com{post_url}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        print(f"   Response: {r.text[:500]}")


if __name__ == "__main__":
    main()

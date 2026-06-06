#!/usr/bin/env python3
"""
Reddit post script for DaoVowScout.
Run: python3 reddit_post.py

Posts the first value-first introduction to r/spirituality.
"""
import os, sys, json
import praw

# ── Credentials ──────────────────────────────────────────────
REDDIT_USER = "DaoVowScout"
REDDIT_PASS = "5285jun1215"
USER_AGENT = "DaoVowScout/v1.0 (building a modern Eastern destiny archive)"

# ── Post content ──────────────────────────────────────────────
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

# ── Post ──────────────────────────────────────────────────────
def main():
    try:
        reddit = praw.Reddit(
            client_id="wLc2f5cp2lSGog",
            client_secret="",
            username=REDDIT_USER,
            password=REDDIT_PASS,
            user_agent=USER_AGENT
        )
        me = reddit.user.me()
        print(f"✅ Logged in as: {me.name}")
        
        sub = reddit.subreddit(SUBREDDIT)
        submission = sub.submit(title=TITLE, selftext=BODY)
        print(f"✅ Posted to r/{SUBREDDIT}")
        print(f"   Title: {TITLE}")
        print(f"   URL: https://reddit.com{submission.permalink}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

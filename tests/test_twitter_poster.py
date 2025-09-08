#!/usr/bin/env python3
"""
Simple test script for Twitter Poster
Run this to test your configuration before using the main script
"""

import os
from dotenv import load_dotenv, find_dotenv
import requests
from pathlib import Path
import sys

# Make `src` importable without fiddling with PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

# Load environment variables
load_dotenv(find_dotenv())

def test_config():
    """Test if all required environment variables are set"""
    print("🔍 Testing Twitter Poster Configuration...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("twitter_apiio_key")
    if api_key:
        print(f"✅ API Key: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("❌ API Key: Not set")
        return False
    
    # Check proxy
    proxy_http = os.getenv("PROXY_HTTP")
    if proxy_http:
        print(f"✅ Proxy HTTP: {proxy_http}")
    else:
        print("❌ Proxy HTTP: Not set")
        return False
    
    # Check if proxy format looks correct
    if "@" in proxy_http and ":" in proxy_http:
        print("✅ Proxy format: Looks correct")
    else:
        print("⚠️  Proxy format: May be incorrect")
    
    print("\n" + "=" * 50)
    print("🎯 Configuration Test Complete!")
    
    if api_key and proxy_http:
        print("✅ All required variables are set!")
        print("🚀 You can now run: uv run python src/twitter_poster.py")
        return True
    else:
        print("❌ Some required variables are missing!")
        print("📝 Check your .env file and try again")
        return False


def test_fetch_20_tweets_by_user():
    """Fetch 20 tweets using advanced search wrapper."""
    api_key = os.getenv("twitter_apiio_key")
    if not api_key:
        print("❌ twitter_apiio_key not set; skipping fetch test")
        return False

    from users import get_user_tweets

    resp = get_user_tweets(
        api_key=api_key,
        username=os.getenv("TEST_TW_USER", "nelvOfficial"),
        limit=20,
        include_replies=True,
    )
    tweets = resp.get("tweets", [])
    print(f"Fetched {len(tweets)} tweets")

    for tweet in tweets:
        print(tweet['text'])

    assert isinstance(tweets, list)
    assert len(tweets) <= 20
    return True

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "test_config":
        test_config()

    elif cmd == "fetch_20":
        test_fetch_20_tweets_by_user()
        
    else:
        ok = test_config()
        if ok:
            test_fetch_20_tweets_by_user()

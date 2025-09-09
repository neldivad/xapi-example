import os
import json
import hashlib
from typing import Dict, List, Optional
from pathlib import Path

import requests
from dotenv import find_dotenv, load_dotenv

# Load environment variables
load_dotenv(find_dotenv())

API_KEY = os.getenv("twitterapiio_key")
if not API_KEY:
    raise RuntimeError("twitterapiio_key not set in environment")

BASE_URL = "https://api.twitterapi.io"


def _headers(api_key: Optional[str] = None) -> Dict[str, str]:
    key = api_key or API_KEY
    return {"X-API-Key": key}


def _followings_endpoint() -> str:
    return f"{BASE_URL}/twitter/user/followings"


def _followers_endpoint() -> str:
    return f"{BASE_URL}/twitter/user/followers"


def get_recent_followings(
    username: str,
    limit: int = 20,
    api_key: Optional[str] = None,
    page_size: int = 20,
    start_cursor: Optional[str] = None,
) -> Dict:
    """
    Fetch user followings sorted by follow date (most recent first).

    Args:
        username: Twitter handle (with or without leading @)
        limit: Maximum number of followings to return
        api_key: Optional override of API key
        page_size: Page size for each request (20-200)
        start_cursor: Optional starting cursor token (first page is empty string or omitted)

    Returns:
        Dict with keys: followings (list), has_next_page (bool), next_cursor (str|None)
    """
    if not username:
        raise ValueError("username is required")
    handle = username[1:] if username.startswith("@") else username

    # Clamp page_size per API constraints
    if page_size < 20:
        page_size = 20
    if page_size > 200:
        page_size = 200

    url = _followings_endpoint()
    headers = _headers(api_key)

    collected: List[Dict] = []
    cursor: Optional[str] = start_cursor or None
    has_next_page: bool = True

    while has_next_page and len(collected) < limit:
        params = {"userName": handle, "pageSize": page_size}
        if cursor is not None:
            # First page can be "" or omitted. If explicitly provided, pass it through.
            if cursor == "":
                # Ensure we don't send stale value from previous iteration
                params.pop("cursor", None)
            else:
                params["cursor"] = cursor

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        page_followings = data.get("followings", [])
        remaining = max(0, limit - len(collected))
        if remaining <= 0:
            break
        if page_followings:
            collected.extend(page_followings[:remaining])

        has_next_page = bool(data.get("has_next_page"))
        cursor = data.get("next_cursor") if has_next_page else None

        if not page_followings:
            break

    # Trim to limit
    collected = collected[:limit]

    return {
        "followings": collected,
        "has_next_page": has_next_page,
        "next_cursor": cursor,
        "status": "success",
        "message": f"Fetched {len(collected)} followings for {handle}",
    }


def get_recent_followers(
    username: str,
    limit: int = 20,
    api_key: Optional[str] = None,
    page_size: int = 20,
    start_cursor: Optional[str] = None,
) -> Dict:
    """
    Fetch user followers sorted by follow date (most recent first).
    
    Identical to get_followings() but uses the followers endpoint.
    Returns recent followers with pagination support for caching/resuming.

    Args:
        username: Twitter handle (with or without leading @)
        limit: Maximum number of followers to return
        api_key: Optional override of API key
        page_size: Page size for each request (20-200)
        start_cursor: Optional starting cursor token (first page is empty string or omitted)

    Returns:
        Dict with keys: followers (list), has_next_page (bool), next_cursor (str|None)
        
    Notes:
        - Use has_next_page to know if more data is available
        - Use next_cursor to resume pagination later (avoid re-fetching)
        - Caching strategy: cache by username + cursor position
        - Cost control: limit pages to control API usage
    """
    if not username:
        raise ValueError("username is required")
    handle = username[1:] if username.startswith("@") else username

    # Clamp page_size per API constraints
    if page_size < 20:
        page_size = 20
    if page_size > 200:
        page_size = 200

    url = _followers_endpoint()
    headers = _headers(api_key)

    collected: List[Dict] = []
    cursor: Optional[str] = start_cursor or None
    has_next_page: bool = True

    while has_next_page and len(collected) < limit:
        params = {"userName": handle, "pageSize": page_size}
        if cursor is not None:
            # First page can be "" or omitted. If explicitly provided, pass it through.
            if cursor == "":
                # Ensure we don't send stale value from previous iteration
                params.pop("cursor", None)
            else:
                params["cursor"] = cursor

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        page_followers = data.get("followers", [])
        remaining = max(0, limit - len(collected))
        if remaining <= 0:
            break
        if page_followers:
            collected.extend(page_followers[:remaining])

        has_next_page = bool(data.get("has_next_page"))
        cursor = data.get("next_cursor") if has_next_page else None

        if not page_followers:
            break

    # Trim to limit
    collected = collected[:limit]

    return {
        "followers": collected,
        "has_next_page": has_next_page,
        "next_cursor": cursor,
        "status": "success",
        "message": f"Fetched {len(collected)} followers for {handle}",
    }


def _follow_cache_path(
    username: str, 
    is_followings: bool
) -> str:
    """Return JSON cache path under project-root `data/jsons`."""
    if is_followings:
        prefix = "followings"
    else:
        prefix = "followers"
        
    safe = username.replace("@", "")
    project_root = Path(__file__).resolve().parents[1]
    json_dir = project_root / "data" / "jsons"
    json_dir.mkdir(parents=True, exist_ok=True)
    return str(json_dir / f"{prefix}_{safe}.json")

def save_follow_cache(
    username: str, 
    is_followings: bool,
    data: Dict, 
) -> str:
    """Save followings JSON cache; return JSON path."""
    json_path = _follow_cache_path(username, is_followings)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return json_path

def load_follow_cache(
    username: str, 
    is_followings: bool
) -> Optional[Dict]:
    """Load followings JSON cache if exists; else None."""
    json_path = _follow_cache_path(username, is_followings)
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ---------------------------------
# Advanced search (general-purpose)
# ---------------------------------

def _advanced_search_endpoint() -> str:
    return f"{BASE_URL}/twitter/tweet/advanced_search"


def search_tweets_advanced(
    *,
    query: str,
    limit: int = 20,
    start_cursor: Optional[str] = None,
    api_key: Optional[str] = None,
    query_type: str = "Latest",
) -> Dict:
    """
    Generalized advanced search with count-based pagination control.

    Args:
        query: The full advanced search query string
        limit: Total number of tweets to return (approx. 20 per page)
        start_cursor: Optional cursor to resume
        api_key: Optional API key override
        query_type: API queryType, default 'Latest'

    Returns:
        Dict with keys: tweets (list), has_next_page (bool), next_cursor (str|None)
    """
    url = _advanced_search_endpoint()
    headers = _headers(api_key)

    collected: List[Dict] = []
    cursor: Optional[str] = start_cursor or None
    has_next_page: bool = True

    while has_next_page and len(collected) < limit:
        params: Dict[str, object] = {"query": query, "queryType": query_type}
        if cursor:
            params["cursor"] = cursor

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        page = data.get("tweets", [])
        remaining = max(0, limit - len(collected))
        if remaining <= 0:
            break
        if page:
            collected.extend(page[:remaining])

        has_next_page = bool(data.get("has_next_page"))
        cursor = data.get("next_cursor") if has_next_page else None

        if not page:
            break

    collected = collected[:limit]
    return {
        "tweets": collected,
        "has_next_page": has_next_page,
        "next_cursor": cursor,
        "status": "success",
        "message": f"Fetched {len(collected)} tweets for query: `{query}`",
    }

# ---------------------------------
# Specific wrapper (no cursor param)
# ---------------------------------

def get_user_tweets(
    api_key: str,
    username: str,
    limit: int=20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_faves: Optional[int] = None,
    include_replies: bool = True,
) -> Dict:
    """
    Fetch up to `limit` tweets for a user using advanced search, without exposing cursor.

    Args:
        api_key: API key
        username: user handle (preferred) or id (if supported by search)
        limit: total tweets desired. Multiple of 20. Default 20.
        start_date: YYYY-MM-DD (inclusive) for since:
        end_date: YYYY-MM-DD (exclusive) for until:
        min_faves: minimum number of favorites for tweets. WARNING: API might not match frontend value. 
        include_replies: include reply tweets when True

    Returns:
        Dict with keys: tweets (list), has_next_page (bool), next_cursor (str|None)
    """
    # Normalize handle
    handle = username[1:] if username.startswith("@") else username

    parts = [f"from:{handle}"]
    if start_date:
        parts.append(f"since:{start_date}")
    if end_date:
        parts.append(f"until:{end_date}")
    if min_faves:
        parts.append(f"min_faves:{min_faves}")
    if not include_replies:
        parts.append("-is:reply")

    query = " ".join(parts)

    return search_tweets_advanced(
        query=query,
        limit=limit,
        start_cursor=None,
        api_key=api_key,
        query_type="Latest",
    )


# ---------------------------------
# Tweet caching utilities
# ---------------------------------

def generate_query_hash(query: str) -> str:
    """
    Generate a short hash for the query string. We do this to avoid having to store the full query string as a filename. 

    The limit is not included in the hash because it is not part of the query. Check the metadata of the file for the limit.

    Args:
        query: EG: `from:elonmusk since:2025-01-01 until:2025-09-09 min_faves:10`

    Returns:
        str: EG: `56a894d2360a`
    """
    return hashlib.md5(query.encode()).hexdigest()[:12]


def _tweet_cache_path(username: str, query_hash: str) -> str:
    """Generate organized cache path: tweets/jsons/{username}/{hash}.json"""
    safe_username = username.replace("@", "")
    project_root = Path(__file__).resolve().parents[1]
    cache_dir = project_root / "data" / "jsons" / "tweets" / safe_username
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir / f"{query_hash}.json")


def save_tweet_cache(
    username: str, 
    query:str, 
    limit: int, 
    query_hash: str, 
    data: Dict
) -> str:
    """
    Save tweet data to cache with query metadata.

    Args:
        username: Twitter handle (with or without leading @)
        query: The full advanced search query string
        query_hash: Hash of the query string produced by generate_query_hash
        data: The tweet data to save
    """
    cache_path = _tweet_cache_path(username, query_hash)
    
    # Add metadata to the data
    cache_data = {
        "metadata": {
            "username": username,
            "query": query,
            "limit": limit,
        },
        "tweets": data.get("tweets", []),
        "has_next_page": data.get("has_next_page", False),
        "next_cursor": data.get("next_cursor")
    }
    
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    return cache_path


def load_tweet_cache(
    username: str, 
    query_hash: str,
) -> Optional[Dict]:
    """
    Load tweet data from cache if exists.

    Args:
        username: Twitter handle (with or without leading @)
        query_hash: Hash of the query string produced by generate_query_hash
    """
    cache_path = _tweet_cache_path(username, query_hash)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
        
        # Return in the same format as get_user_tweets
        return {
            "tweets": cached_data.get("tweets", []),
            "query": cached_data.get("metadata", {}).get("query", ""),
            "has_next_page": cached_data.get("has_next_page", False),
            "next_cursor": cached_data.get("next_cursor"),
            "status": "success",
            "message": f"Loaded {len(cached_data.get('tweets', []))} tweets from cache"
        }
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Cache file corrupted: {e}")
        return None


def get_user_tweets_cached(
    api_key: str,
    username: str,
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_faves: Optional[int] = None,
    include_replies: bool = True,
) -> Dict:
    """get_user_tweets with automatic caching."""
    # Build query (same as get_user_tweets)
    handle = username[1:] if username.startswith("@") else username
    parts = [f"from:{handle}"]
    if start_date:
        parts.append(f"since:{start_date}")
    if end_date:
        parts.append(f"until:{end_date}")
    if min_faves:
        parts.append(f"min_faves:{min_faves}")
    if not include_replies:
        parts.append("-is:reply")
    
    query = " ".join(parts)
    query_hash = generate_query_hash(query)
    
    # Check cache first
    cached = load_tweet_cache(username, query_hash)
    if cached:
        print(f"✅ C-Hit: Q: `{query}`")
        return cached
    
    # Cache miss - fetch from API
    print(f"🔄 C-Miss: Fetching with Q: `{query}`")
    data = get_user_tweets(api_key, username, limit, start_date, end_date, min_faves, include_replies)
    
    # Save to cache
    save_tweet_cache(username, query, limit, query_hash, data)
    print(f"💾 Cached {len(data.get('tweets', []))} tweets")
    
    return data


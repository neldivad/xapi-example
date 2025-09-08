import os
import json
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


def _json_cache_path(username: str) -> str:
    """Return JSON cache path under project-root `data/jsons`."""
    safe = username.replace("@", "")
    project_root = Path(__file__).resolve().parents[1]
    json_dir = project_root / "data" / "jsons"
    json_dir.mkdir(parents=True, exist_ok=True)
    return str(json_dir / f"followings_{safe}.json")


def get_followings(
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


def save_followings_cache(username: str, data: Dict) -> str:
    """Save followings JSON cache; return JSON path."""
    json_path = _json_cache_path(username)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return json_path


def load_followings_cache(username: str) -> Optional[Dict]:
    """Load followings JSON cache if exists; else None."""
    json_path = _json_cache_path(username)
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


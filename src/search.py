import requests
import time
from typing import List, Dict
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())  # reliably loads .env from project root

api_key = os.getenv("twitterapiio_key")
if not api_key:
    raise RuntimeError("TWITTER_API_KEY not set in environment")


def fetch_all_tweets(query: str, api_key: str, max_results: int | None = None) -> List[Dict]:
    """
    Fetches all tweets matching the given query from Twitter API, handling deduplication.

    Args:
        query (str): The search query for tweets
        api_key (str): Twitter API key for authentication

    Returns:
        List[Dict]: List of unique tweets matching the query

    Notes:
        - Handles pagination using cursor and max_id parameters
        - Deduplicates tweets based on tweet ID to handle max_id overlap
        - Implements rate limiting handling
        - Continues fetching beyond Twitter's initial 800-1200 tweet limit
        - Includes error handling for API failures
    """
    base_url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    headers = {"x-api-key": api_key}
    all_tweets = []
    seen_tweet_ids = set()  # Set to track unique tweet IDs
    cursor = None
    last_min_id = None
    max_retries = 3

    while True:
        # Prepare query parameters
        params = {
            "query": query,
            "queryType": "Latest"
        }

        # Add cursor if available (for regular pagination)
        if cursor:
            params["cursor"] = cursor
        elif last_min_id:
            # Add max_id if available (for fetching beyond initial limit)
            params["query"] = f"{query} max_id:{last_min_id}"

        retry_count = 0
        while retry_count < max_retries:
            try:
                # Make API request
                response = requests.get(base_url, headers=headers, params=params)
                response.raise_for_status()  # Raise exception for bad status codes
                data = response.json()

                # Extract tweets and metadata
                tweets = data.get("tweets", [])
                has_next_page = data.get("has_next_page", False)
                cursor = data.get("next_cursor", None)

                # Filter out duplicate tweets
                new_tweets = [tweet for tweet in tweets if tweet.get("id") not in seen_tweet_ids]
                
                # Add new tweet IDs to the set and tweets to the collection
                for tweet in new_tweets:
                    seen_tweet_ids.add(tweet.get("id"))
                    all_tweets.append(tweet)

                # Respect max_results if provided (useful for quick tests)
                if max_results is not None and len(all_tweets) >= max_results:
                    return all_tweets[:max_results]

                # If no new tweets and no next page, break the loop
                if not new_tweets and not has_next_page:
                    return all_tweets

                # Update last_min_id from the last tweet if available
                if new_tweets:
                    last_min_id = new_tweets[-1].get("id")

                # If no next page but we have new tweets, try with max_id
                if not has_next_page and new_tweets:
                    cursor = None  # Reset cursor for max_id pagination
                    break

                # If has next page, continue with cursor
                if has_next_page:
                    break

            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count == max_retries:
                    print(f"Failed to fetch tweets after {max_retries} attempts: {str(e)}")
                    return all_tweets

                # Handle rate limiting
                if hasattr(response, 'status_code') and response.status_code == 429:
                    #For users in the free trial period, the QPS is very low—only one API request can be made every 5 seconds. Once you complete the recharge, the QPS limit will be increased to 20.
                    print("Rate limit reached. Waiting for 1 second...")
                    time.sleep(1)  # Wait 1 second for rate limit reset
                else:
                    print(f"Error occurred: {str(e)}. Retrying {retry_count}/{max_retries}")
                    time.sleep(2 ** retry_count)  # Exponential backoff

        # If no more pages and no new tweets with max_id, we're done
        if not has_next_page and not new_tweets:
            break

    return all_tweets

# Convenience: fetch tweets by user handle
def fetch_user_tweets(user_handle: str, api_key: str, max_results: int = 10) -> List[Dict]:
    """
    Fetch up to max_results tweets from a specific user handle.

    Args:
        user_handle (str): Twitter handle (with or without leading @)
        api_key (str): API key
        max_results (int): Maximum number of tweets to return (default 10)
    """
    if user_handle.startswith("@"):
        user_handle = user_handle[1:]
    query = f"from:{user_handle}"
    return fetch_all_tweets(query, api_key, max_results=max_results)

# Example usage
if __name__ == "__main__":
    # Example 1: query by keywords
    query = "python programming"

    # Retrieving all tweets from a specific account within a specified time period.and you can also filter data based on the number of likes. 
    # For the usage of query parameters, please refer to the relevant documentation.
    # https://github.com/igorbrigadir/twitter-advanced-search 
    #query = "from:elonmusk since:2009-01-01 until:2019-01-01 min_faves:10"
    
    #

    # Quick test: limit to 10 results
    # tweets = fetch_all_tweets(query, api_key, max_results=10)

    # Example 2: fetch by user handle (max 10 by default)
    handle = "ern1337"
    tweets = fetch_user_tweets(handle, api_key)  # defaults to 10
    
    print(f"Fetched {len(tweets)} unique tweets")
    
    # Save to file
    import json
    with open('tweets1.json', 'w') as f:
        json.dump(tweets, f, indent=2)

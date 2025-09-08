# Smoke tests

## Env and proxy

```bash
uv run python tests/test_twitter_poster.py
```

Check output shows API key and proxy.

## Fetch tweets (20)

Paste into a notebook cell or Python REPL:

```python
from users import get_user_tweets
import os

api_key = os.getenv("twitterapiio_key")
resp = get_user_tweets(api_key=api_key, username="nelvOfficial", limit=20, include_replies=True)
print(len(resp["tweets"]))
```

Expected: 20 (subject to availability).



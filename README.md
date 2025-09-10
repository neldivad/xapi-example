# xapi-ex1 Quickstart

Minimal utilities to query TwitterAPI.io for followings and tweets, plus notebook helpers.

## Setup

Using uv (recommended):

```bash
cd xapi-ex1
uv venv
source .venv/Scripts/activate
uv sync
```

Or pip:

```bash
cd xapi-ex1
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -U pip
pip install -r <(uv pip compile pyproject.toml || echo "python-dotenv requests pandas")
```

Installing new packages
```bash
# from root dir

uv add statsmodels
```


Create a .env with:

```bash
twitterapiio_key=YOUR_API_KEY
```

## Fetch last tweets (advanced search wrapper)

```python
from users import get_user_tweets
import os

api_key = os.getenv("twitterapiio_key")
resp = get_user_tweets(api_key=api_key, username="nelvOfficial", limit=20, include_replies=True)
tweets = resp["tweets"]
print(len(tweets))
```

## Notebook

- Activate kernel for `.venv`, open `notebooks/nb.ipynb`, run cells.
- CSVs save to `data/csvs`; JSON caches to `data/jsons`.

## Tests

Configuration check and simple tweet fetchers live in `tests/`.

Run:

```bash
uv run python tests/test_twitter_poster.py test_config
```

```bash
uv run python tests/test_twitter_poster.py fetch_20
```



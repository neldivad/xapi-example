from __future__ import annotations

from typing import Any, Dict, Iterable, List

# Define the canonical field list (dotted paths allowed)
DEFAULT_TWEET_FIELDS: List[str] = [
    "type",
    "id",
    "url",
    "twitterUrl",
    "text",
    "source",
    "retweetCount",
    "replyCount",
    "likeCount",
    "quoteCount",
    "viewCount",
    "createdAt",
    "lang",
    "bookmarkCount",
    "isReply",
    "inReplyToId",
    "conversationId",
    "displayTextRange",
    "inReplyToUserId",
    "inReplyToUsername",
    "card",
    "quoted_tweet",
    "retweeted_tweet",
    "isLimitedReply",
    "article",
    "author.type",
    "author.userName",   
    "author.url",
    "author.twitterUrl",
    "author.id",
    "author.name",
    "author.isVerified",
    "author.isBlueVerified",
    "author.verifiedType",
    "author.profilePicture",
    "author.coverPicture",
    "author.description",
    "author.location",
    "author.followers",
    "author.following",
    "author.status",
    "author.canDm",
    "author.canMediaTag",
    "author.createdAt",
    "author.entities.description.urls",
    "author.fastFollowersCount",
    "author.favouritesCount",
    "author.hasCustomTimelines",
    "author.isTranslator",
    "author.mediaCount",
    "author.statusesCount",
    "author.withheldInCountries",
    "author.possiblySensitive",
    "author.pinnedTweetIds",
    "author.profile_bio.description",
    "author.profile_bio.entities.url.urls",
    "author.isAutomated",
    "author.automatedBy",
    "entities.user_mentions",
    "card.binding_values",
    "card.card_platform.platform.audience.name",
    "card.card_platform.platform.device.name",
    "card.card_platform.platform.device.version",
    "card.name",
    "card.url",
    "entities.urls",
    "extendedEntities.media",
    "quoted_tweet.type",
    "quoted_tweet.id",
    "quoted_tweet.url",
    "quoted_tweet.twitterUrl",
    "quoted_tweet.text",
    "quoted_tweet.source",
    "quoted_tweet.retweetCount",
    "quoted_tweet.replyCount",
    "quoted_tweet.likeCount",
    "quoted_tweet.quoteCount",
    "quoted_tweet.viewCount",
    "quoted_tweet.createdAt",
    "quoted_tweet.lang",
    "quoted_tweet.bookmarkCount",
    "quoted_tweet.isReply",
    "quoted_tweet.inReplyToId",
    "quoted_tweet.conversationId",
    "quoted_tweet.displayTextRange",
    "quoted_tweet.inReplyToUserId",
    "quoted_tweet.inReplyToUsername",
    "quoted_tweet.author.type",
    "quoted_tweet.author.userName",
    "quoted_tweet.author.url",
    "quoted_tweet.author.twitterUrl",
    "quoted_tweet.author.id",
    "quoted_tweet.author.name",
    "quoted_tweet.author.isVerified",
    "quoted_tweet.author.isBlueVerified",
    "quoted_tweet.author.verifiedType",
    "quoted_tweet.author.profilePicture",
    "quoted_tweet.author.coverPicture",
    "quoted_tweet.author.description",
    "quoted_tweet.author.location",
    "quoted_tweet.author.followers",
    "quoted_tweet.author.following",
    "quoted_tweet.author.status",
    "quoted_tweet.author.status",
    "quoted_tweet.author.canDm",
    "quoted_tweet.author.canMediaTag",
    "quoted_tweet.author.createdAt",
    "quoted_tweet.author.entities.description.urls",
    "quoted_tweet.author.fastFollowersCount",
    "quoted_tweet.author.favouritesCount",
    "quoted_tweet.author.hasCustomTimelines",
    "quoted_tweet.author.isTranslator",
    "quoted_tweet.author.mediaCount",
    "quoted_tweet.author.statusesCount",
    "quoted_tweet.author.withheldInCountries",
    "quoted_tweet.author.possiblySensitive",
    "quoted_tweet.author.pinnedTweetIds",
    "quoted_tweet.author.profile_bio.description",
    "quoted_tweet.author.profile_bio.entities.url.urls",
    "quoted_tweet.author.isAutomated",
    "quoted_tweet.author.automatedBy",
    "quoted_tweet.card",
    "quoted_tweet.quoted_tweet",
    "quoted_tweet.retweeted_tweet",
    "quoted_tweet.isLimitedReply",
    "quoted_tweet.article",
]

TRUNCATED_TWEET_FIELDS: List[str] = [
    # basic
    "type",
    "id",
    "url",
    "createdAt",
    "lang",
    "text",

    # stats
    "retweetCount",
    "replyCount",
    "likeCount",
    "quoteCount",
    "viewCount",
    "bookmarkCount",

    # reply
    "isReply",
    "inReplyToId",
    "inReplyToUsername",

    # author
    "author.userName",   
    "author.url",
    "author.id",
    "author.isBlueVerified",
    "author.followers",
    "author.following",
]


def _pluck_path(obj: Dict[str, Any], path: str) -> Any:
    """Safely pluck a dotted path from a nested dict."""
    parts = path.split(".")
    cur: Any = obj
    for part in parts:
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def project_tweet(tweet: Dict[str, Any], fields: Iterable[str] = DEFAULT_TWEET_FIELDS) -> Dict[str, Any]:
    """
    Return a new dict with only the selected fields (dotted-path aware).
    Missing fields are included with value None.
    """
    return {field: _pluck_path(tweet, field) for field in fields}


def collapse_dicts(tweets: Iterable[Dict[str, Any]], fields: Iterable[str] = TRUNCATED_TWEET_FIELDS) -> List[Dict[str, Any]]:
    """
    Collapse a list of tweet dicts to a truncated schema.

    - Keeps only known fields (dotted paths supported)
    - Missing fields are set to None
    - Extra fields are dropped
    """
    return [project_tweet(t, fields) for t in tweets]


def collapse_dataframe(df, fields: Iterable[str] = TRUNCATED_TWEET_FIELDS):
    """
    Collapse a pandas DataFrame to the truncated schema safely.

    - Keeps only columns present in `fields` and in df
    - Adds any missing columns with NaN
    - Returns columns in the order of `fields`
    """
    try:
        import pandas as pd  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        raise RuntimeError("pandas and numpy are required for collapse_dataframe")

    fields = list(fields)
    # Start with only existing columns
    existing = [c for c in fields if c in df.columns]
    out = df[existing].copy()
    # Add missing columns as NaN
    for c in fields:
        if c not in out.columns:
            out[c] = np.nan
    # Reorder to match fields
    out = out[fields]
    return out


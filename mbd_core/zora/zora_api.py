"""Zora API utils functions."""

import os
import time

import pandas as pd
import requests

from mbd_core.zora import schema

ZORA_API_KEY = os.getenv("ZORA_API_KEY")
EXPLORE_URL = "https://api-sdk.zora.engineering/explore?count=10"
WAIT_BETWEEN_CALLS = 0.100
MAX_API_CALLS = 250
MAX_POLLING_TIME = 180


def _parse_farcaster_id(node):
    try:
        return (
            node.get("creatorProfile", {})
            .get("socialAccounts", {})
            .get("farcaster", {})
            .get("id")
        )
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_price_in_usdc(node):
    try:
        return node.get("tokenPrice", {}).get("priceInUsdc")
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_media_content_type(node):
    try:
        return node.get("mediaContent", {}).get("mimeType")
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_media_content_url(node):
    try:
        return node.get("mediaContent", {}).get("originalUri")
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_preview_small_url(node):
    try:
        return node.get("mediaContent", {}).get("previewImage", {}).get("small")
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_preview_medium_url(node):
    try:
        return node.get("mediaContent", {}).get("previewImage", {}).get("medium")
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_node(node):
    return {
        schema.ZORA_COIN_ID: node.get("id"),
        schema.ZORA_COIN_URI: node.get("tokenUri"),
        schema.ZORA_CHAIN_ID: node.get("chainId"),
        schema.ZORA_NAME: node.get("name"),
        schema.ZORA_DESCRIPTION: node.get("description"),
        schema.ZORA_ADDRESS: node.get("address"),
        schema.ZORA_SYMBOL: node.get("symbol"),
        schema.ZORA_TOTAL_SUPPLY: node.get("totalSupply"),
        schema.ZORA_TOTAL_VOLUME: node.get("totalVolume"),
        schema.ZORA_VOLUME_24H: node.get("volume24h"),
        schema.ZORA_CREATED_AT: node.get("createdAt"),
        schema.ZORA_CREATOR_ADDRESS: node.get("creatorAddress"),
        schema.ZORA_PRICE_IN_USDC: _parse_price_in_usdc(node),
        schema.ZORA_MARKET_CAP: node.get("marketCap"),
        schema.ZORA_MARKET_CAP_DELTA_24H: node.get("marketCapDelta24h"),
        schema.ZORA_UNIQUE_HOLDERS: node.get("uniqueHolders"),
        schema.ZORA_PLATFORM_REFERRER_ADDRESS: node.get("platformReferrerAddress"),
        schema.ZORA_PAYOUT_RECIPIENT_ADDRESS: node.get("payoutRecipientAddress"),
        schema.ZORA_CREATOR_FARCASTER_ID: _parse_farcaster_id(node),
        schema.ZORA_MEDIA_CONTENT_TYPE: _parse_media_content_type(node),
        schema.ZORA_MEDIA_CONTENT_URL: _parse_media_content_url(node),
        schema.ZORA_PREVIEW_SMALL_URL: _parse_preview_small_url(node),
        schema.ZORA_PREVIEW_MEDIUM_URL: _parse_preview_medium_url(node),
    }


def _make_explore_api_call(array, list_type, last_cursor):
    url = EXPLORE_URL
    if list_type:
        url = url + f"&listType={list_type}"
    if last_cursor:
        url = url + f"&after={last_cursor}"
    headers = {"apiKey": ZORA_API_KEY}
    response = requests.get(url, headers=headers, timeout=30).json()
    if "exploreList" not in response:
        return 0, False, None
    has_next_page = response["exploreList"]["pageInfo"]["hasNextPage"]
    cursor = response["exploreList"]["pageInfo"]["endCursor"]
    nodes = [x["node"] for x in response["exploreList"]["edges"]]
    parsed = [_parse_node(node) for node in nodes]
    array.extend(parsed)
    return len(parsed), has_next_page, cursor


def explore(list_type, max_api_calls=MAX_API_CALLS, max_polling_time=MAX_POLLING_TIME):
    """Explore Zora API and return a DataFrame with parsed data.

    Args:
        list_type: Type of list to explore from Zora API
        max_api_calls: Maximum number of API calls to make (default: 250)
        max_polling_time: Maximum time to spend polling in seconds (default: 180)

    Returns:
        tuple: (DataFrame with parsed data, list of log messages)
    """
    start_time = time.time()
    array = []
    has_next_page = True
    last_cursor = None
    num_calls = 0
    logs = []
    while (
        has_next_page
        and num_calls < max_api_calls
        and time.time() - start_time < max_polling_time
    ):
        if num_calls > 0:
            time.sleep(WAIT_BETWEEN_CALLS)
        num_calls += 1
        logs.append(f"call to Zora API:{num_calls}")
        num_rows, has_next_page, last_cursor = _make_explore_api_call(
            array, list_type, last_cursor
        )
        logs.append(f"num_rows:{num_rows} has_next_page:{has_next_page}")
    logs.append(f"Finished polling Zora API. Total records pulled: {len(array)}")
    logs.append(f"Time taken to pull data: {time.time() - start_time} seconds")
    return pd.DataFrame(array), logs

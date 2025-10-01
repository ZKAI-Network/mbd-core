"""Zora API utils functions."""

import datetime
import json
import logging
import os
import time
from typing import Any

import pandas as pd
import requests

from mbd_core.zora import schema

logger = logging.getLogger()
ZORA_API_KEY = os.getenv("ZORA_API_KEY")
EXPLORE_URL = "https://api-sdk.zora.engineering/explore?count=10"
COIN_URL = "https://api-sdk.zora.engineering/coin"
WAIT_BETWEEN_CALLS = 0.100
MAX_API_CALLS = 250
MAX_POLLING_TIME = 180


def _parse_int(node: dict[str, Any], key: str) -> int | None:
    try:
        result = node.get(key)
        return int(result) if result else None
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def _parse_float(node: dict[str, Any], key: str) -> float | None:
    try:
        result = node.get(key)
        return float(result) if result else None
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def _parse_price_in_usdc(node: dict[str, Any]) -> float | None:
    try:
        result = node.get("tokenPrice", {}).get("priceInUsdc")
        return float(result) if result else None
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def _parse_farcaster_id(node: dict[str, Any]) -> str | None:
    try:
        result = (
            node.get("creatorProfile", {})
            .get("socialAccounts", {})
            .get("farcaster", {})
            .get("id")
        )
        return str(result) if result else None
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def _parse_media_content_type(node: dict[str, Any]) -> str | None:
    try:
        result = node.get("mediaContent", {}).get("mimeType")
        return str(result) if result else None
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_media_content_url(node: dict[str, Any]) -> str | None:
    try:
        result = node.get("mediaContent", {}).get("originalUri")
        return str(result) if result else None
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_preview_small_url(node: dict[str, Any]) -> str | None:
    try:
        result = node.get("mediaContent", {}).get("previewImage", {}).get("small")
        return str(result) if result else None
    except (KeyError, TypeError, AttributeError):
        return None


def _parse_preview_medium_url(node: dict[str, Any]) -> str | None:
    try:
        result = node.get("mediaContent", {}).get("previewImage", {}).get("medium")
        return str(result) if result else None
    except (KeyError, TypeError, AttributeError):
        return None


def _make_explore_api_call(
    array: list[dict[str, Any]], list_type: str | None, last_cursor: str | None
) -> tuple[int, bool, str | None]:
    try:
        url = EXPLORE_URL
        if list_type:
            url = url + f"&listType={list_type}"
        if last_cursor:
            url = url + f"&after={last_cursor}"
        headers: dict[str, str] = {"apiKey": ZORA_API_KEY or ""}
        response = requests.get(url, headers=headers, timeout=30).json()
        if "exploreList" not in response:
            return 0, False, None
        has_next_page = response["exploreList"]["pageInfo"]["hasNextPage"]
        cursor = response["exploreList"]["pageInfo"]["endCursor"]
        nodes = [x["node"] for x in response["exploreList"]["edges"]]
        parsed = [parse_info(node) for node in nodes]
        array.extend(parsed)
        return len(parsed), has_next_page, cursor
    except (requests.RequestException, KeyError, ValueError, json.JSONDecodeError):
        logger.exception("Error making explore API call")
        return 0, False, None


def explore(
    list_type: str | None,
    max_api_calls: int = MAX_API_CALLS,
    max_polling_time: int = MAX_POLLING_TIME,
) -> tuple[pd.DataFrame, list[str]]:
    """Explore Zora API and return a DataFrame with parsed data.

    Args:
        list_type: Type of list to explore from Zora API
        max_api_calls: Maximum number of API calls to make (default: 250)
        max_polling_time: Maximum time to spend polling in seconds (default: 180)

    Returns:
        tuple: (DataFrame with parsed data, list of log messages)
    """
    start_time = time.time()
    array: list[dict[str, Any]] = []
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


def get_coin(address: str, chain_id: int = 8453) -> dict[str, Any] | None:
    """Get Zora coin data from Zora API."""
    url = COIN_URL + f"?address={address}&chain={chain_id}"
    headers: dict[str, str] = {"apiKey": ZORA_API_KEY or ""}
    response = requests.get(url, headers=headers, timeout=30).json()
    if "zora20Token" not in response:
        return None
    return parse_info(response["zora20Token"])


def parse_info(node: dict[str, Any]) -> dict[str, Any]:
    """Parse Zora coin data."""
    return {
        schema.ZORA_COIN_ID: node.get("id"),
        schema.ZORA_COIN_URI: node.get("tokenUri"),
        schema.ZORA_CHAIN_ID: node.get("chainId"),
        schema.ZORA_NAME: node.get("name"),
        schema.ZORA_DESCRIPTION: node.get("description"),
        schema.ZORA_ADDRESS: node.get("address"),
        schema.ZORA_SYMBOL: node.get("symbol"),
        schema.ZORA_TOTAL_SUPPLY: _parse_float(node, "totalSupply"),
        schema.ZORA_TOTAL_VOLUME: _parse_float(node, "totalVolume"),
        schema.ZORA_VOLUME_24H: _parse_float(node, "volume24h"),
        schema.ZORA_CREATED_AT: node.get("createdAt"),
        schema.ZORA_CREATOR_ADDRESS: node.get("creatorAddress"),
        schema.ZORA_PRICE_IN_USDC: _parse_price_in_usdc(node),
        schema.ZORA_MARKET_CAP: _parse_float(node, "marketCap"),
        schema.ZORA_MARKET_CAP_DELTA_24H: _parse_float(node, "marketCapDelta24h"),
        schema.ZORA_UNIQUE_HOLDERS: _parse_int(node, "uniqueHolders"),
        schema.ZORA_PLATFORM_REFERRER_ADDRESS: node.get("platformReferrerAddress"),
        schema.ZORA_PAYOUT_RECIPIENT_ADDRESS: node.get("payoutRecipientAddress"),
        schema.ZORA_CREATOR_FARCASTER_ID: _parse_farcaster_id(node),
        schema.ZORA_MEDIA_CONTENT_TYPE: _parse_media_content_type(node),
        schema.ZORA_MEDIA_CONTENT_URL: _parse_media_content_url(node),
        schema.ZORA_PREVIEW_SMALL_URL: _parse_preview_small_url(node),
        schema.ZORA_PREVIEW_MEDIUM_URL: _parse_preview_medium_url(node),
        schema.ZORA_UPDATED_AT: datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

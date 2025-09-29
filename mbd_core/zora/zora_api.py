import os
import time

import pandas as pd
import requests

ZORA_API_KEY = os.getenv("ZORA_API_KEY")
EXPLORE_URL = "https://api-sdk.zora.engineering/explore?count=10"
WAIT_BETWEEN_CALLS = 0.100
MAX_API_CALLS = 250
MAX_POLLING_TIME = 180


def parse_farcaster_id(node):
    try:
        return (
            node.get("creatorProfile", {})
            .get("socialAccounts", {})
            .get("farcaster", {})
            .get("id")
        )
    except:
        return None


def parse_price_in_usdc(node):
    try:
        return node.get("tokenPrice", {}).get("priceInUsdc")
    except:
        return None


def parse_media_content_type(node):
    try:
        return node.get("mediaContent", {}).get("mimeType")
    except:
        return None


def parse_media_content_url(node):
    try:
        return node.get("mediaContent", {}).get("originalUri")
    except:
        return None


def parse_preview_small_url(node):
    try:
        return node.get("mediaContent", {}).get("previewImage", {}).get("small")
    except:
        return None


def parse_preview_medium_url(node):
    try:
        return node.get("mediaContent", {}).get("previewImage", {}).get("medium")
    except:
        return None


def parse_node(node):
    return {
        "id": node.get("id"),
        "token_uri": node.get("tokenUri"),
        "chain_id": node.get("chainId"),
        "name": node.get("name"),
        "description": node.get("description"),
        "address": node.get("address"),
        "symbol": node.get("symbol"),
        "total_supply": node.get("totalSupply"),
        "total_volume": node.get("totalVolume"),
        "volume_24h": node.get("volume24h"),
        "created_at": node.get("createdAt"),
        "creator_address": node.get("creatorAddress"),
        "price_in_usdc": parse_price_in_usdc(node),
        "market_cap": node.get("marketCap"),
        "market_cap_delta_24h": node.get("marketCapDelta24h"),
        "unique_holders": node.get("uniqueHolders"),
        "platform_referrer_address": node.get("platformReferrerAddress"),
        "payout_recipient_address": node.get("payoutRecipientAddress"),
        "creator_farcaster_id": parse_farcaster_id(node),
        "media_content_type": parse_media_content_type(node),
        "media_content_url": parse_media_content_url(node),
        "preview_small_url": parse_preview_small_url(node),
        "preview_medium_url": parse_preview_medium_url(node),
    }


def make_explore_api_call(array, list_type, last_cursor):
    url = EXPLORE_URL
    if list_type:
        url = url + f"&listType={list_type}"
    if last_cursor:
        url = url + f"&after={last_cursor}"
    headers = {"apiKey": ZORA_API_KEY}
    response = requests.get(url, headers=headers).json()
    if "exploreList" not in response:
        return 0, False, None
    has_next_page = response["exploreList"]["pageInfo"]["hasNextPage"]
    cursor = response["exploreList"]["pageInfo"]["endCursor"]
    nodes = [x["node"] for x in response["exploreList"]["edges"]]
    parsed = [parse_node(node) for node in nodes]
    array.extend(parsed)
    return len(parsed), has_next_page, cursor


def explore(list_type, max_api_calls=MAX_API_CALLS, max_polling_time=MAX_POLLING_TIME):
    start_time = time.time()
    array = []
    has_next_page = True
    last_cursor = None
    num_calls = 0
    while (
        has_next_page
        and num_calls < max_api_calls
        and time.time() - start_time < max_polling_time
    ):
        if num_calls > 0:
            time.sleep(WAIT_BETWEEN_CALLS)
        num_calls += 1
        print(f"call to Zora API:{num_calls}")
        num_rows, has_next_page, last_cursor = make_explore_api_call(
            array, list_type, last_cursor
        )
        print(f"num_rows:{num_rows} has_next_page:{has_next_page}")
    print(f"Finished polling Zora API. Total records pulled: {len(array)}")
    print(f"Time taken to pull data: {time.time() - start_time} seconds")
    return pd.DataFrame(array)

"""Tests for Zora API functions."""

import os
import time
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from mbd_core.zora import schema
from mbd_core.zora.zora_api import (
    _make_explore_api_call,
    _parse_farcaster_id,
    _parse_float,
    _parse_int,
    _parse_media_content_type,
    _parse_media_content_url,
    _parse_node,
    _parse_preview_medium_url,
    _parse_preview_small_url,
    _parse_price_in_usdc,
    explore,
)


class TestParsingFunctions:
    """Test all parsing helper functions."""

    def test_parse_int_valid(self):
        """Test _parse_int with valid integer values."""
        node = {"count": "123", "total": 456, "zero": 0}
        assert _parse_int(node, "count") == 123
        assert _parse_int(node, "total") == 456
        assert _parse_int(node, "zero") == 0

    def test_parse_int_invalid(self):
        """Test _parse_int with invalid values."""
        node = {"invalid": "abc", "none": None, "empty": ""}
        assert _parse_int(node, "invalid") is None
        assert _parse_int(node, "none") is None
        assert _parse_int(node, "empty") is None
        assert _parse_int(node, "missing") is None

    def test_parse_int_exceptions(self):
        """Test _parse_int with various exception cases."""
        # Test with non-dict node
        assert _parse_int("not_a_dict", "key") is None
        # Test with dict that raises AttributeError
        bad_dict = Mock()
        bad_dict.get.side_effect = AttributeError("test")
        assert _parse_int(bad_dict, "key") is None

    def test_parse_float_valid(self):
        """Test _parse_float with valid float values."""
        node = {"price": "123.45", "volume": 456.78, "zero": 0.0}
        assert _parse_float(node, "price") == 123.45
        assert _parse_float(node, "volume") == 456.78
        assert _parse_float(node, "zero") == 0.0

    def test_parse_float_invalid(self):
        """Test _parse_float with invalid values."""
        node = {"invalid": "abc", "none": None, "empty": ""}
        assert _parse_float(node, "invalid") is None
        assert _parse_float(node, "none") is None
        assert _parse_float(node, "empty") is None
        assert _parse_float(node, "missing") is None

    def test_parse_float_exceptions(self):
        """Test _parse_float with various exception cases."""
        # Test with non-dict node
        assert _parse_float("not_a_dict", "key") is None
        # Test with dict that raises AttributeError
        bad_dict = Mock()
        bad_dict.get.side_effect = AttributeError("test")
        assert _parse_float(bad_dict, "key") is None

    def test_parse_price_in_usdc_valid(self):
        """Test _parse_price_in_usdc with valid price data."""
        node = {
            "tokenPrice": {
                "priceInUsdc": "123.45"
            }
        }
        assert _parse_price_in_usdc(node) == 123.45

    def test_parse_price_in_usdc_invalid(self):
        """Test _parse_price_in_usdc with invalid data."""
        node = {
            "tokenPrice": {
                "priceInUsdc": "invalid"
            }
        }
        assert _parse_price_in_usdc(node) is None

        node = {
            "tokenPrice": {
                "priceInUsdc": None
            }
        }
        assert _parse_price_in_usdc(node) is None

        node = {}
        assert _parse_price_in_usdc(node) is None

    def test_parse_price_in_usdc_exceptions(self):
        """Test _parse_price_in_usdc with exception cases."""
        # Test with non-dict node
        assert _parse_price_in_usdc("not_a_dict") is None
        # Test with dict that raises AttributeError
        bad_dict = Mock()
        bad_dict.get.side_effect = AttributeError("test")
        assert _parse_price_in_usdc(bad_dict) is None

    def test_parse_farcaster_id_valid(self):
        """Test _parse_farcaster_id with valid data."""
        node = {
            "creatorProfile": {
                "socialAccounts": {
                    "farcaster": {
                        "id": "12345"
                    }
                }
            }
        }
        assert _parse_farcaster_id(node) == "12345"

    def test_parse_farcaster_id_invalid(self):
        """Test _parse_farcaster_id with invalid data."""
        node = {
            "creatorProfile": {
                "socialAccounts": {
                    "farcaster": {
                        "id": None
                    }
                }
            }
        }
        assert _parse_farcaster_id(node) is None

        node = {}
        assert _parse_farcaster_id(node) is None

    def test_parse_farcaster_id_exceptions(self):
        """Test _parse_farcaster_id with exception cases."""
        # Test with non-dict node
        assert _parse_farcaster_id("not_a_dict") is None
        # Test with dict that raises AttributeError
        bad_dict = Mock()
        bad_dict.get.side_effect = AttributeError("test")
        assert _parse_farcaster_id(bad_dict) is None

    def test_parse_media_content_type_valid(self):
        """Test _parse_media_content_type with valid data."""
        node = {
            "mediaContent": {
                "mimeType": "image/jpeg"
            }
        }
        assert _parse_media_content_type(node) == "image/jpeg"

    def test_parse_media_content_type_invalid(self):
        """Test _parse_media_content_type with invalid data."""
        node = {
            "mediaContent": {
                "mimeType": None
            }
        }
        assert _parse_media_content_type(node) is None

        node = {}
        assert _parse_media_content_type(node) is None

    def test_parse_media_content_type_exceptions(self):
        """Test _parse_media_content_type with exception cases."""
        # Test with non-dict node
        assert _parse_media_content_type("not_a_dict") is None
        # Test with dict that raises AttributeError
        bad_dict = Mock()
        bad_dict.get.side_effect = AttributeError("test")
        assert _parse_media_content_type(bad_dict) is None

    def test_parse_media_content_url_valid(self):
        """Test _parse_media_content_url with valid data."""
        node = {
            "mediaContent": {
                "originalUri": "https://example.com/image.jpg"
            }
        }
        assert _parse_media_content_url(node) == "https://example.com/image.jpg"

    def test_parse_media_content_url_invalid(self):
        """Test _parse_media_content_url with invalid data."""
        node = {
            "mediaContent": {
                "originalUri": None
            }
        }
        assert _parse_media_content_url(node) is None

        node = {}
        assert _parse_media_content_url(node) is None

    def test_parse_media_content_url_exceptions(self):
        """Test _parse_media_content_url with exception cases."""
        # Test with non-dict node
        assert _parse_media_content_url("not_a_dict") is None
        # Test with dict that raises AttributeError
        bad_dict = Mock()
        bad_dict.get.side_effect = AttributeError("test")
        assert _parse_media_content_url(bad_dict) is None

    def test_parse_preview_small_url_valid(self):
        """Test _parse_preview_small_url with valid data."""
        node = {
            "mediaContent": {
                "previewImage": {
                    "small": "https://example.com/small.jpg"
                }
            }
        }
        assert _parse_preview_small_url(node) == "https://example.com/small.jpg"

    def test_parse_preview_small_url_invalid(self):
        """Test _parse_preview_small_url with invalid data."""
        node = {
            "mediaContent": {
                "previewImage": {
                    "small": None
                }
            }
        }
        assert _parse_preview_small_url(node) is None

        node = {}
        assert _parse_preview_small_url(node) is None

    def test_parse_preview_small_url_exceptions(self):
        """Test _parse_preview_small_url with exception cases."""
        # Test with non-dict node
        assert _parse_preview_small_url("not_a_dict") is None
        # Test with dict that raises AttributeError
        bad_dict = Mock()
        bad_dict.get.side_effect = AttributeError("test")
        assert _parse_preview_small_url(bad_dict) is None

    def test_parse_preview_medium_url_valid(self):
        """Test _parse_preview_medium_url with valid data."""
        node = {
            "mediaContent": {
                "previewImage": {
                    "medium": "https://example.com/medium.jpg"
                }
            }
        }
        assert _parse_preview_medium_url(node) == "https://example.com/medium.jpg"

    def test_parse_preview_medium_url_invalid(self):
        """Test _parse_preview_medium_url with invalid data."""
        node = {
            "mediaContent": {
                "previewImage": {
                    "medium": None
                }
            }
        }
        assert _parse_preview_medium_url(node) is None

        node = {}
        assert _parse_preview_medium_url(node) is None

    def test_parse_preview_medium_url_exceptions(self):
        """Test _parse_preview_medium_url with exception cases."""
        # Test with non-dict node
        assert _parse_preview_medium_url("not_a_dict") is None
        # Test with dict that raises AttributeError
        bad_dict = Mock()
        bad_dict.get.side_effect = AttributeError("test")
        assert _parse_preview_medium_url(bad_dict) is None


class TestParseNode:
    """Test the _parse_node function."""

    def test_parse_node_complete(self):
        """Test _parse_node with complete data."""
        node = {
            "id": "coin123",
            "tokenUri": "https://example.com/token",
            "chainId": "1",
            "name": "Test Coin",
            "description": "A test coin",
            "address": "0x123",
            "symbol": "TEST",
            "totalSupply": "1000",
            "totalVolume": "5000.50",
            "volume24h": "100.25",
            "createdAt": "2023-01-01T00:00:00Z",
            "creatorAddress": "0x456",
            "tokenPrice": {"priceInUsdc": "1.50"},
            "marketCap": "1500.00",
            "marketCapDelta24h": "50.00",
            "uniqueHolders": "100",
            "platformReferrerAddress": "0x789",
            "payoutRecipientAddress": "0xabc",
            "creatorProfile": {
                "socialAccounts": {
                    "farcaster": {"id": "farcaster123"}
                }
            },
            "mediaContent": {
                "mimeType": "image/jpeg",
                "originalUri": "https://example.com/image.jpg",
                "previewImage": {
                    "small": "https://example.com/small.jpg",
                    "medium": "https://example.com/medium.jpg"
                }
            }
        }

        result = _parse_node(node)

        assert result[schema.ZORA_COIN_ID] == "coin123"
        assert result[schema.ZORA_COIN_URI] == "https://example.com/token"
        assert result[schema.ZORA_CHAIN_ID] == "1"
        assert result[schema.ZORA_NAME] == "Test Coin"
        assert result[schema.ZORA_DESCRIPTION] == "A test coin"
        assert result[schema.ZORA_ADDRESS] == "0x123"
        assert result[schema.ZORA_SYMBOL] == "TEST"
        assert result[schema.ZORA_TOTAL_SUPPLY] == 1000.0
        assert result[schema.ZORA_TOTAL_VOLUME] == 5000.50
        assert result[schema.ZORA_VOLUME_24H] == 100.25
        assert result[schema.ZORA_CREATED_AT] == "2023-01-01T00:00:00Z"
        assert result[schema.ZORA_CREATOR_ADDRESS] == "0x456"
        assert result[schema.ZORA_PRICE_IN_USDC] == 1.50
        assert result[schema.ZORA_MARKET_CAP] == 1500.00
        assert result[schema.ZORA_MARKET_CAP_DELTA_24H] == 50.00
        assert result[schema.ZORA_UNIQUE_HOLDERS] == 100
        assert result[schema.ZORA_PLATFORM_REFERRER_ADDRESS] == "0x789"
        assert result[schema.ZORA_PAYOUT_RECIPIENT_ADDRESS] == "0xabc"
        assert result[schema.ZORA_CREATOR_FARCASTER_ID] == "farcaster123"
        assert result[schema.ZORA_MEDIA_CONTENT_TYPE] == "image/jpeg"
        assert result[schema.ZORA_MEDIA_CONTENT_URL] == "https://example.com/image.jpg"
        assert result[schema.ZORA_PREVIEW_SMALL_URL] == "https://example.com/small.jpg"
        assert result[schema.ZORA_PREVIEW_MEDIUM_URL] == "https://example.com/medium.jpg"

    def test_parse_node_minimal(self):
        """Test _parse_node with minimal data."""
        node = {"id": "coin123"}

        result = _parse_node(node)

        assert result[schema.ZORA_COIN_ID] == "coin123"
        assert result[schema.ZORA_COIN_URI] is None
        assert result[schema.ZORA_CHAIN_ID] is None
        assert result[schema.ZORA_NAME] is None
        assert result[schema.ZORA_DESCRIPTION] is None
        assert result[schema.ZORA_ADDRESS] is None
        assert result[schema.ZORA_SYMBOL] is None
        assert result[schema.ZORA_TOTAL_SUPPLY] is None
        assert result[schema.ZORA_TOTAL_VOLUME] is None
        assert result[schema.ZORA_VOLUME_24H] is None
        assert result[schema.ZORA_CREATED_AT] is None
        assert result[schema.ZORA_CREATOR_ADDRESS] is None
        assert result[schema.ZORA_PRICE_IN_USDC] is None
        assert result[schema.ZORA_MARKET_CAP] is None
        assert result[schema.ZORA_MARKET_CAP_DELTA_24H] is None
        assert result[schema.ZORA_UNIQUE_HOLDERS] is None
        assert result[schema.ZORA_PLATFORM_REFERRER_ADDRESS] is None
        assert result[schema.ZORA_PAYOUT_RECIPIENT_ADDRESS] is None
        assert result[schema.ZORA_CREATOR_FARCASTER_ID] is None
        assert result[schema.ZORA_MEDIA_CONTENT_TYPE] is None
        assert result[schema.ZORA_MEDIA_CONTENT_URL] is None
        assert result[schema.ZORA_PREVIEW_SMALL_URL] is None
        assert result[schema.ZORA_PREVIEW_MEDIUM_URL] is None


class TestMakeExploreApiCall:
    """Test the _make_explore_api_call function."""

    @patch('mbd_core.zora.zora_api.requests.get')
    def test_make_explore_api_call_success(self, mock_get):
        """Test successful API call."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "exploreList": {
                "pageInfo": {
                    "hasNextPage": True,
                    "endCursor": "cursor123"
                },
                "edges": [
                    {
                        "node": {
                            "id": "coin1",
                            "name": "Coin 1"
                        }
                    },
                    {
                        "node": {
                            "id": "coin2",
                            "name": "Coin 2"
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        array = []
        num_rows, has_next_page, cursor = _make_explore_api_call(array, "trending", "prev_cursor")

        assert num_rows == 2
        assert has_next_page is True
        assert cursor == "cursor123"
        assert len(array) == 2
        assert array[0][schema.ZORA_COIN_ID] == "coin1"
        assert array[1][schema.ZORA_COIN_ID] == "coin2"

        # Verify the API call was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "listType=trending" in call_args[0][0]
        assert "after=prev_cursor" in call_args[0][0]

    @patch('mbd_core.zora.zora_api.requests.get')
    def test_make_explore_api_call_no_explore_list(self, mock_get):
        """Test API call with missing exploreList."""
        mock_response = Mock()
        mock_response.json.return_value = {"other": "data"}
        mock_get.return_value = mock_response

        array = []
        num_rows, has_next_page, cursor = _make_explore_api_call(array, None, None)

        assert num_rows == 0
        assert has_next_page is False
        assert cursor is None
        assert len(array) == 0

    @patch('mbd_core.zora.zora_api.requests.get')
    def test_make_explore_api_call_no_list_type(self, mock_get):
        """Test API call without list_type."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "exploreList": {
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": None
                },
                "edges": []
            }
        }
        mock_get.return_value = mock_response

        array = []
        num_rows, has_next_page, cursor = _make_explore_api_call(array, None, None)

        assert num_rows == 0
        assert has_next_page is False
        assert cursor is None
        assert len(array) == 0

        # Verify the API call was made without listType parameter
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "listType=" not in call_args[0][0]
        assert "after=" not in call_args[0][0]


class TestExplore:
    """Test the explore function."""

    @patch('mbd_core.zora.zora_api._make_explore_api_call')
    @patch('mbd_core.zora.zora_api.time.sleep')
    @patch('mbd_core.zora.zora_api.time.time')
    def test_explore_single_page(self, mock_time, mock_sleep, mock_api_call):
        """Test explore with single page of results."""
        mock_time.side_effect = [0, 1]  # start_time, then time.time() in loop
        mock_api_call.return_value = (5, False, None)  # num_rows, has_next_page, cursor

        df, logs = explore("trending", max_api_calls=10, max_polling_time=60)

        assert len(df) == 5
        assert len(logs) == 3  # call log, num_rows log, finished log
        assert "call to Zora API:1" in logs[0]
        assert "num_rows:5 has_next_page:False" in logs[1]
        assert "Finished polling Zora API" in logs[2]
        assert "Time taken to pull data: 1.0 seconds" in logs[2]

        mock_api_call.assert_called_once_with([], "trending", None)
        mock_sleep.assert_not_called()

    @patch('mbd_core.zora.zora_api._make_explore_api_call')
    @patch('mbd_core.zora.zora_api.time.sleep')
    @patch('mbd_core.zora.zora_api.time.time')
    def test_explore_multiple_pages(self, mock_time, mock_sleep, mock_api_call):
        """Test explore with multiple pages."""
        mock_time.side_effect = [0, 1, 2, 3]  # start_time, then time.time() in loop
        mock_api_call.side_effect = [
            (5, True, "cursor1"),   # First call
            (3, False, None)        # Second call
        ]

        df, logs = explore("trending", max_api_calls=10, max_polling_time=60)

        assert len(df) == 8  # 5 + 3
        assert len(logs) == 5  # 2 calls + 2 num_rows + 1 finished
        assert "call to Zora API:1" in logs[0]
        assert "call to Zora API:2" in logs[2]
        assert "num_rows:5 has_next_page:True" in logs[1]
        assert "num_rows:3 has_next_page:False" in logs[3]

        assert mock_api_call.call_count == 2
        mock_api_call.assert_any_call([], "trending", None)
        mock_api_call.assert_any_call([], "trending", "cursor1")
        mock_sleep.assert_called_once()

    @patch('mbd_core.zora.zora_api._make_explore_api_call')
    @patch('mbd_core.zora.zora_api.time.sleep')
    @patch('mbd_core.zora.zora_api.time.time')
    def test_explore_max_calls_reached(self, mock_time, mock_sleep, mock_api_call):
        """Test explore when max_api_calls is reached."""
        mock_time.side_effect = [0, 1, 2, 3, 4, 5]  # start_time, then time.time() in loop
        mock_api_call.return_value = (5, True, "cursor")  # Always has next page

        df, logs = explore("trending", max_api_calls=3, max_polling_time=60)

        assert len(df) == 15  # 3 calls * 5 rows each
        assert len(logs) == 7  # 3 calls + 3 num_rows + 1 finished
        assert mock_api_call.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between calls (not before first)

    @patch('mbd_core.zora.zora_api._make_explore_api_call')
    @patch('mbd_core.zora.zora_api.time.sleep')
    @patch('mbd_core.zora.zora_api.time.time')
    def test_explore_max_polling_time_reached(self, mock_time, mock_sleep, mock_api_call):
        """Test explore when max_polling_time is reached."""
        mock_time.side_effect = [0, 1, 61, 62]  # start_time, then time.time() in loop (exceeds 60s)
        mock_api_call.return_value = (5, True, "cursor")  # Always has next page

        df, logs = explore("trending", max_api_calls=10, max_polling_time=60)

        assert len(df) == 5  # Only first call
        assert len(logs) == 3  # 1 call + 1 num_rows + 1 finished
        assert mock_api_call.call_count == 1
        assert "Time taken to pull data: 61.0 seconds" in logs[2]

    @patch('mbd_core.zora.zora_api._make_explore_api_call')
    @patch('mbd_core.zora.zora_api.time.sleep')
    @patch('mbd_core.zora.zora_api.time.time')
    def test_explore_default_parameters(self, mock_time, mock_sleep, mock_api_call):
        """Test explore with default parameters."""
        mock_time.side_effect = [0, 1]
        mock_api_call.return_value = (0, False, None)

        df, logs = explore()

        assert len(df) == 0
        assert len(logs) == 3
        mock_api_call.assert_called_once_with([], None, None)

    @patch('mbd_core.zora.zora_api._make_explore_api_call')
    @patch('mbd_core.zora.zora_api.time.sleep')
    @patch('mbd_core.zora.zora_api.time.time')
    def test_explore_no_list_type(self, mock_time, mock_sleep, mock_api_call):
        """Test explore without list_type."""
        mock_time.side_effect = [0, 1]
        mock_api_call.return_value = (3, False, None)

        df, logs = explore(None, max_api_calls=5, max_polling_time=30)

        assert len(df) == 3
        assert len(logs) == 3
        mock_api_call.assert_called_once_with([], None, None)

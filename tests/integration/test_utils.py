import pandas as pd
import pytest
import asyncio

from mbd_core.data.farcaster.utils import (
    _get_url_enrichment,
    clean_text,
    enrich_df_with_url_metadata,
    get_urls_list_metadata,
)


def test_clean_text(farcaster_casts_dataframe):
    clean_df = clean_text(farcaster_casts_dataframe, "text", "timestamp")
    assert clean_df.shape[0] <= farcaster_casts_dataframe.shape[0]


@pytest.mark.asyncio
async def test_get_urls_list_metadata():
    target_urls = ["https://google.com", "https://twitter.com"]
    batch_size = 100

    # Split URLs into batches
    url_batches = [
        target_urls[i : i + batch_size] for i in range(0, len(target_urls), batch_size)
    ]

    # Get metadata for all URLs
    results = await get_urls_list_metadata(url_batches)

    # Print results in a more readable format
    print("\nURL Metadata Results:")
    print(f"Raw results: {results}")  # Print raw results for debugging

    # Basic structure checks
    assert isinstance(results, list), "Results should be a list"
    assert len(results) > 0, "Results list should not be empty"
    assert isinstance(results[0], dict), "First result should be a dictionary"

    # Verify specific metadata for Google and Twitter
    metadata = results[0]
    assert "https://google.com" in metadata, "Google metadata should be present"
    assert "https://twitter.com" in metadata, "Twitter metadata should be present"

    # Verify Google metadata structure
    google_meta = metadata["https://google.com"]
    assert "title" in google_meta, "Google metadata should have a title"
    assert "description" in google_meta, "Google metadata should have a description"
    assert "image" in google_meta, "Google metadata should have an image"
    assert google_meta["publisher"] == "google.com", "Publisher should be google.com"

    # Verify Twitter metadata structure
    twitter_meta = metadata["https://twitter.com"]
    assert "title" in twitter_meta, "Twitter metadata should have a title"
    assert "description" in twitter_meta, "Twitter metadata should have a description"
    assert "publisher" in twitter_meta, "Twitter metadata should have a publisher"

    # Print detailed results for debugging
    print("\nDetailed Metadata:")
    for url, meta in metadata.items():
        print(f"\nURL: {url}")
        for key, value in meta.items():
            print(f"  {key}: {value}")


def test_get_url_enrichment():
    # Test with title and description
    df = pd.DataFrame(
        {
            "url_meta": [
                {
                    "title": "Test Title",
                    "description": "Test Description",
                    "customOpenGraph": {"fc:frame": True},
                },
                {"title": "Only Title"},
                {"description": "Only Description"},
                {"customOpenGraph": {"fc:frame": True}},
            ]
        }
    )

    result = _get_url_enrichment(df, "url_text", "is_frame")
    assert (
        result["url_text"] == "Test Title Test Description Only Title Only Description"
    )
    assert result["is_frame"] is True

    # Test with empty metadata
    df_empty = pd.DataFrame({"url_meta": [{}]})
    result_empty = _get_url_enrichment(df_empty, "url_text", "is_frame")
    assert result_empty["url_text"] == ""
    assert result_empty["is_frame"] is False


def test_enrich_df_with_url_metadata():
    # Test DataFrame with URLs
    df = pd.DataFrame(
        {"id": [1, 2], "urls": [["https://example1.com"], ["https://example2.com"]]}
    )

    # Test with empty result (no metadata found)
    result_df = enrich_df_with_url_metadata(
        df=df,
        url_column="urls",
        item_id_col="id",
        enrich_url_text_col="url_text",
        enrich_frame_col="is_frame",
        batch_size=1,
    )

    assert "url_text" in result_df.columns
    assert "is_frame" in result_df.columns
    assert all(result_df["url_text"] == "")
    assert all(result_df["is_frame"] == False)  # noqa: E712

    # Test with empty URLs
    df_empty = pd.DataFrame({"id": [1], "urls": [[]]})
    result_empty = enrich_df_with_url_metadata(
        df=df_empty,
        url_column="urls",
        item_id_col="id",
        enrich_url_text_col="url_text",
        enrich_frame_col="is_frame",
    )
    assert all(result_empty["url_text"] == "")
    assert all(result_empty["is_frame"] == False)  # noqa: E712

    # Test with real URLs that should return metadata
    df_real = pd.DataFrame({
        "id": [1, 2],
        "urls": [["https://google.com"], ["https://twitter.com"]]
    })
    result_real = enrich_df_with_url_metadata(
        df=df_real,
        url_column="urls",
        item_id_col="id",
        enrich_url_text_col="url_text",
        enrich_frame_col="is_frame",
    )
    
    # Verify we got metadata
    assert not all(result_real["url_text"] == ""), "Should have some URL text metadata"
    assert "url_text" in result_real.columns
    assert "is_frame" in result_real.columns
    
    # Print results for debugging
    print("\nEnriched DataFrame Results:")
    print(result_real[["id", "url_text", "is_frame"]])

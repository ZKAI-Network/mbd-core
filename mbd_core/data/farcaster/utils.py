"""Utility functions for farcaster data processing."""

import asyncio
import json
import os
import time
from typing import cast

import aiohttp
import pandas as pd
from aiohttp.client_exceptions import ContentTypeError

EMBEDS_METADATA_URL = os.getenv("EMBEDS_METADATA_URL")


async def get_urls_metadata(urls: list[str], session: aiohttp.ClientSession) -> dict:
    """Get metadata for a list of urls."""
    params = json.dumps(urls)
    headers = {"Content-Type": "application/json"}
    while True:
        try:
            async with session.post(
                cast(str, EMBEDS_METADATA_URL), headers=headers, data=params
            ) as response:
                result = await response.json()
                return cast(dict, result)
        except ContentTypeError as e:  # pragma: no cover
            print(f"HTTP client error occurred: {e} for {urls}, retring...")  # noqa: T201
            time.sleep(1)


async def get_urls_list_metadata(mylist: list[list[str]]) -> list[dict]:
    """Get metadata for a list of lists of urls."""
    # Create a session that will be used for all requests
    async with aiohttp.ClientSession() as session:
        tasks = [get_urls_metadata(urls, session) for urls in mylist]
        # Gather runs tasks concurrently and waits for all to complete
        return await asyncio.gather(*tasks)


def _get_url_enrichment(
    df: pd.DataFrame, enrich_url_text_col: str, enrich_frame_col: str
) -> pd.Series:
    url_text = []
    frame = False
    for d in df["url_meta"]:
        assert isinstance(d, dict)
        if "title" in d:
            url_text.append(d["title"])
        if "description" in d:
            url_text.append(d["description"])
        if "fc:frame" in d.get("customOpenGraph", {}):
            frame = True
    cat_url_text = " ".join(url_text)
    return pd.Series({enrich_url_text_col: cat_url_text, enrich_frame_col: frame})


def enrich_df_with_url_metadata(  # noqa: PLR0913
    df: pd.DataFrame,
    url_column: str,
    item_id_col: str,
    enrich_url_text_col: str,
    enrich_frame_col: str,
    batch_size: int = 100,
) -> pd.DataFrame:
    """Enrich dataframe with url metadata.

    df: the dataframe
    url_column: the column name contains urls. Each value of the column is a list of urls
    """
    exploded_df = df.explode(url_column)[[item_id_col, url_column]].dropna(
        subset=[url_column]
    )
    target_urls = exploded_df[url_column].unique().tolist()
    results = asyncio.run(
        get_urls_list_metadata(
            [
                target_urls[i : i + batch_size]
                for i in range(0, len(target_urls), batch_size)
            ]
        )
    )
    # merge url meta
    merged_dict = {}
    for d in results:
        merged_dict.update(d)
    exploded_df = exploded_df.join(
        pd.Series(merged_dict, name="url_meta"), on=url_column, how="left"
    ).dropna(subset=["url_meta"])

    # agg based on item_id
    if not exploded_df.empty:
        exploded_df = (
            exploded_df.groupby(item_id_col)
            .apply(
                _get_url_enrichment,
                enrich_url_text_col=enrich_url_text_col,
                enrich_frame_col=enrich_frame_col,
            )
            .reset_index()
        )

        # join back to enrich original df
        enriched_df = df.join(
            exploded_df.set_index(item_id_col), on=item_id_col, how="left"
        )
        enriched_df[enrich_url_text_col] = enriched_df[enrich_url_text_col].fillna("")
        enriched_df[enrich_frame_col] = enriched_df[enrich_frame_col].fillna(
            value=False
        )
    else:  # pragma: no cover
        enriched_df = df
        enriched_df[enrich_url_text_col] = ""
        enriched_df[enrich_frame_col] = False
    return enriched_df

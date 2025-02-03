"""Transformation functions for farcaster data."""

import re

import pandas as pd  # comment this line if you want to use modin
from ftlangdetect import detect as ftdetect
from pandas.api.types import is_datetime64_ns_dtype

from mbd_core.data.farcaster.utils import enrich_df_with_url_metadata
from mbd_core.data.schema import (
    APP_COLUMN,
    AUTHOR_ID_COLUMN,
    EDGE_TYPE_COLUMN,
    EMBED_ITEMS_COLUMN,
    EMBED_USERS_COLUMN,
    ITEM_COLUMN,
    ITEM_CREATION_TIME_COLUMN,
    ITEM_TEXT_COLUMN,
    ITEM_UPDATE_TIME_COLUMN,
    LANG_COLUMN,
    LANG_SCORE_COLUMN,
    LIST_COLUMN,
    LOCATION_COLUMN,
    PROTOCOL_COLUMN,
    PROTOCOLS,
    PUBLICATION_TYPE_COLUMN,
    PUBLICATION_TYPES,
    ROOT_ITEM_COLUMN,
    TIME_COLUMN,
    USER_BIO_COLUMN,
    USER_COLUMN,
    USER_CREATION_TIME_COLUMN,
    USER_NAME_COLUMN,
    USER_PHOTO_URL_COLUMN,
    USER_PROFILE_COLUMN,
    USER_UPDATE_TIME_COLUMN,
)

REACT_TYPE_MAP = {1: "like", 2: "share"}


def apply_ftdetect(text: str) -> tuple[str, float]:
    """Function to apply ftdetect and return both 'lang' and 'score'."""
    result = ftdetect(text=text.replace("\n", " "), low_memory=False)
    return result["lang"], result["score"]


def derive_root_item_column(item_df: pd.DataFrame) -> pd.DataFrame:
    """Derive root item column."""
    item_df["root_parent_hash"] = "0x" + item_df["root_parent_hash"]
    item_df.loc[item_df["parent_hash"].isna(), "root_parent_hash"] = "root"
    item_df[ROOT_ITEM_COLUMN] = item_df["root_parent_hash"]

    return item_df


def _format_timestamp(df: pd.DataFrame, col: str) -> None:  # pragma: no cover
    if not is_datetime64_ns_dtype(df[col]):
        df[col] = pd.to_datetime(df[col])
    if df[col].dt.tz is None:
        df[col] = df[col].dt.tz_localize("UTC")


def get_item_df(
    casts_df: pd.DataFrame, carry_columns: list | None = None
) -> pd.DataFrame:
    """Get item dataframe from casts dataframe."""
    item_df = casts_df.copy()
    item_df = item_df.drop_duplicates(subset=["hash"]).reset_index(drop=True)

    # to mbd schema
    item_df[ITEM_COLUMN] = "0x" + item_df["hash"]
    item_df[AUTHOR_ID_COLUMN] = item_df["fid"].astype(str)
    item_df[PROTOCOL_COLUMN] = PROTOCOLS.farcaster.value
    item_df[ITEM_CREATION_TIME_COLUMN] = item_df["timestamp"]
    item_df[ITEM_UPDATE_TIME_COLUMN] = item_df["timestamp"]
    item_df[APP_COLUMN] = item_df["app_fid"].astype(str)
    item_df[LOCATION_COLUMN] = item_df["location"].astype(str)
    item_df = derive_root_item_column(item_df)

    # enrich url metadata
    # Extract URLs from both text and embeds, deduplicating them
    item_df[EMBED_ITEMS_COLUMN] = item_df.apply(
        lambda row: list(
            dict.fromkeys(  # Use dict.fromkeys to preserve order while deduplicating
                re.findall(r"https?://\S+", row["text"])
                + [
                    embed["url"]
                    for embed in row["embeds"]
                    if isinstance(embed, dict) and "url" in embed
                ]
            )
        ),
        axis=1,
    )

    item_df = enrich_df_with_url_metadata(
        df=item_df,
        url_column=EMBED_ITEMS_COLUMN,
        item_id_col=ITEM_COLUMN,
        enrich_url_text_col="_url_text",
        enrich_frame_col="_frame",
    )

    # Only concatenate URL metadata text when it exists and is not empty
    item_df["text"] = item_df.apply(
        lambda row: row["text"]
        + (
            f". {row['_url_text']}"
            if pd.notna(row["_url_text"]) and row["_url_text"].strip()
            else ""
        ),
        axis=1,
    )

    # clean text
    item_df[ITEM_TEXT_COLUMN] = item_df["text"].apply(
        lambda x: {"full": x, "summary": x}
    )
    item_df[PUBLICATION_TYPE_COLUMN] = PUBLICATION_TYPES.text_only.value
    item_df.loc[item_df["_frame"], PUBLICATION_TYPE_COLUMN] = (
        PUBLICATION_TYPES.frame.value
    )
    item_df["_lang_res"] = item_df[ITEM_TEXT_COLUMN].apply(
        lambda x: apply_ftdetect(x["full"])
    )
    item_df[LANG_COLUMN] = item_df["_lang_res"].apply(lambda x: x[0]).astype(str)
    item_df[LANG_SCORE_COLUMN] = (
        item_df["_lang_res"].apply(lambda x: x[1]).astype(float)
    )
    item_df[LIST_COLUMN] = item_df["root_parent_url"].apply(
        lambda x: [x] if isinstance(x, str) else []
    )
    item_df[EMBED_USERS_COLUMN] = item_df["mentions"].apply(
        lambda xs: [str(x) for x in xs]
    )

    selected_columns = [
        ITEM_COLUMN,
        AUTHOR_ID_COLUMN,
        PROTOCOL_COLUMN,
        ITEM_CREATION_TIME_COLUMN,
        ITEM_UPDATE_TIME_COLUMN,
        ITEM_TEXT_COLUMN,
        PUBLICATION_TYPE_COLUMN,
        ROOT_ITEM_COLUMN,
        LANG_COLUMN,
        LANG_SCORE_COLUMN,
        LIST_COLUMN,
        EMBED_ITEMS_COLUMN,
        EMBED_USERS_COLUMN,
        APP_COLUMN,
        LOCATION_COLUMN,
    ]
    if carry_columns:  # pragma: no cover
        selected_columns += carry_columns
    item_df = item_df[selected_columns].copy()
    _format_timestamp(item_df, ITEM_CREATION_TIME_COLUMN)
    _format_timestamp(item_df, ITEM_UPDATE_TIME_COLUMN)
    return item_df


def _format_interaction_df(interaction_df: pd.DataFrame) -> pd.DataFrame:
    interaction_df[ITEM_COLUMN] = "0x" + interaction_df[ITEM_COLUMN]
    interaction_df[USER_COLUMN] = interaction_df[USER_COLUMN].astype(str)
    interaction_df[PROTOCOL_COLUMN] = PROTOCOLS.farcaster.value
    interaction_df[APP_COLUMN] = interaction_df[APP_COLUMN].astype(str)
    interaction_df[LOCATION_COLUMN] = interaction_df[LOCATION_COLUMN].astype(str)
    _format_timestamp(interaction_df, TIME_COLUMN)
    return interaction_df.reset_index(drop=True)


def get_post_comment_interaction_df(casts_df: pd.DataFrame) -> pd.DataFrame:
    """Get post and comment interactions dataframe from casts dataframe."""
    ## publish interactions
    publish_df = casts_df[["fid", "hash", "timestamp", "app_fid", "location"]].rename(
        columns={
            "fid": USER_COLUMN,
            "hash": ITEM_COLUMN,
            "timestamp": TIME_COLUMN,
            "app_fid": APP_COLUMN,
            "location": LOCATION_COLUMN,
        }
    )
    publish_df[EDGE_TYPE_COLUMN] = "post"

    ## comment interactions
    comment_df = casts_df[casts_df["parent_hash"].notna()][
        ["fid", "parent_hash", "timestamp", "app_fid", "location"]
    ].rename(
        columns={
            "fid": USER_COLUMN,
            "parent_hash": ITEM_COLUMN,
            "timestamp": TIME_COLUMN,
            "app_fid": APP_COLUMN,
            "location": LOCATION_COLUMN,
        }
    )
    comment_df[EDGE_TYPE_COLUMN] = "comment"

    return _format_interaction_df(pd.concat([publish_df, comment_df]))


def get_reaction_df(react_df: pd.DataFrame) -> pd.DataFrame:
    """Transform reaction dataframe from reaction dataframe."""
    react_df = react_df[react_df["target_hash"].notna()][
        ["fid", "target_hash", "timestamp", "reaction_type", "app_fid", "location"]
    ].rename(
        columns={
            "fid": USER_COLUMN,
            "target_hash": ITEM_COLUMN,
            "timestamp": TIME_COLUMN,
            "reaction_type": EDGE_TYPE_COLUMN,
            "app_fid": APP_COLUMN,
            "location": LOCATION_COLUMN,
        }
    )
    react_df[EDGE_TYPE_COLUMN] = react_df[EDGE_TYPE_COLUMN].apply(
        lambda x: REACT_TYPE_MAP[x]
    )

    return _format_interaction_df(react_df)


def get_interaction_df(
    casts_df: pd.DataFrame, react_df: pd.DataFrame
) -> pd.DataFrame:  # pragma: no cover
    """Get interaction dataframe from casts and reaction dataframe."""
    post_comment_interaction_df = get_post_comment_interaction_df(casts_df)
    reaction_df = get_reaction_df(react_df)
    return pd.concat([post_comment_interaction_df, reaction_df]).reset_index(drop=True)


def get_user_df(user_df: pd.DataFrame) -> pd.DataFrame:
    """Transform user dataframe from user dataframe."""
    user_df[USER_COLUMN] = user_df["fid"].astype(str)
    user_df[PROTOCOL_COLUMN] = PROTOCOLS.farcaster.value
    user_df[USER_CREATION_TIME_COLUMN] = pd.to_datetime(
        user_df["created_at"]
    ).dt.tz_localize("UTC")
    user_df[USER_UPDATE_TIME_COLUMN] = user_df["registered_at"]
    user_df[USER_PROFILE_COLUMN] = user_df["fname"]
    user_df[USER_PHOTO_URL_COLUMN] = user_df["avatar_url"]
    user_df[USER_NAME_COLUMN] = user_df["display_name"]
    user_df[APP_COLUMN] = user_df["app_fid"].apply(lambda x: [str(i) for i in x])
    user_df[LOCATION_COLUMN] = user_df["location"].astype(str)
    user_df = user_df[
        [
            USER_COLUMN,
            PROTOCOL_COLUMN,
            USER_CREATION_TIME_COLUMN,
            USER_UPDATE_TIME_COLUMN,
            USER_PROFILE_COLUMN,
            USER_PHOTO_URL_COLUMN,
            USER_NAME_COLUMN,
            USER_BIO_COLUMN,
            APP_COLUMN,
            LOCATION_COLUMN,
        ]
    ].copy()

    # drop duplicates keep the most recent
    return (
        user_df.sort_values(by=USER_UPDATE_TIME_COLUMN, ascending=True)
        .drop_duplicates(subset=USER_COLUMN, keep="last")
        .reset_index(drop=True)
    )

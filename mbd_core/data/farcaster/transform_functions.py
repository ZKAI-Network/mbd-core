"""Transformation functions for farcaster data."""

import re

import emoji
import pandas as pd  # comment this line if you want to use modin
from ftlangdetect import detect as ftdetect
from pandas.api.types import is_datetime64_ns_dtype

from mbd_core.data.farcaster.utils import enrich_df_with_url_metadata
from mbd_core.data.schema import (
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
    PROTOCOL_COLUMN,
    PROTOCOLS,
    PUBLICATION_TYPE_COLUMN,
    PUBLICATION_TYPES,
    ROOT_ITEM_COLUMN,
    TIME_COLUMN,
    USER_COLUMN,
    USER_CREATION_TIME_COLUMN,
    USER_PROFILE_COLUMN,
    USER_UPDATE_TIME_COLUMN,
)

REACT_TYPE_MAP = {1: "like", 2: "share"}
USER_BIO_TYPE = 3
MIN_TEXT_LENGTH = 20


def filter_text(text: str) -> bool:
    """Filter text based on length at least larger than 20."""
    return not len(text) <= MIN_TEXT_LENGTH


def remove_emojis(text: str) -> str:
    """Remove emojis from the text."""
    return emoji.replace_emoji(text, replace="")


def remove_degen(text: str) -> str:
    """Remove degen. Regex to find "$degen" with optional space and adjacent numbers, case-insensitive."""
    pattern = r"(\d*\s*\$[\s]*degen\s*\d*)"
    return re.sub(pattern, "", text, flags=re.IGNORECASE)


def transform_text(text: str) -> str:
    """Remove urls from text."""
    url_pattern = re.compile(r"https?://[^\s]+")
    return url_pattern.sub("", text)


def clean_text(item_df: pd.DataFrame, text_col: str, time_col: str) -> pd.DataFrame:
    """Clean text column in the item_df."""
    # transform cast text
    item_df[text_col] = item_df[text_col].apply(transform_text)
    # Apply emoji removal
    item_df[text_col] = item_df[text_col].apply(remove_emojis)
    # Apply degen term removal
    item_df[text_col] = item_df[text_col].apply(remove_degen)

    # Filter items with less than 10 characters
    item_df = item_df[item_df[text_col].apply(filter_text)].copy()
    # Filter duplicate items
    return (
        item_df.sort_values(time_col, ascending=False)
        .drop_duplicates(text_col)
        .reset_index(drop=True)
    )


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
    item_df = derive_root_item_column(item_df)

    # enrich url metadata
    item_df[EMBED_ITEMS_COLUMN] = item_df["embeds"].apply(
        lambda xs: [x["url"] for x in xs if "url" in x and x["url"] is not None]
    )
    item_df = enrich_df_with_url_metadata(
        df=item_df,
        url_column=EMBED_ITEMS_COLUMN,
        item_id_col=ITEM_COLUMN,
        enrich_url_text_col="_url_text",
        enrich_frame_col="_frame",
    )
    item_df["text"] = item_df["text"].str.cat(item_df["_url_text"], sep=". ", na_rep="")

    # clean text
    item_df = clean_text(item_df, text_col="text", time_col=ITEM_CREATION_TIME_COLUMN)
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
    _format_timestamp(interaction_df, TIME_COLUMN)
    return interaction_df.reset_index(drop=True)


def get_post_comment_interaction_df(casts_df: pd.DataFrame) -> pd.DataFrame:
    """Get post and comment interactions dataframe from casts dataframe."""
    ## publish interactions
    publish_df = casts_df[["fid", "hash", "timestamp"]].rename(
        columns={
            "fid": USER_COLUMN,
            "hash": ITEM_COLUMN,
            "timestamp": TIME_COLUMN,
        }
    )
    publish_df[EDGE_TYPE_COLUMN] = "post"

    ## comment interactions
    comment_df = casts_df[casts_df["parent_hash"].notna()][
        ["fid", "parent_hash", "timestamp"]
    ].rename(
        columns={
            "fid": USER_COLUMN,
            "parent_hash": ITEM_COLUMN,
            "timestamp": TIME_COLUMN,
        }
    )
    comment_df[EDGE_TYPE_COLUMN] = "comment"

    return _format_interaction_df(pd.concat([publish_df, comment_df]))


def get_reaction_df(react_df: pd.DataFrame) -> pd.DataFrame:
    """Transform reaction dataframe from reaction dataframe."""
    react_df = react_df[react_df["target_hash"].notna()][
        ["fid", "target_hash", "timestamp", "reaction_type"]
    ].rename(
        columns={
            "fid": USER_COLUMN,
            "target_hash": ITEM_COLUMN,
            "timestamp": TIME_COLUMN,
            "reaction_type": EDGE_TYPE_COLUMN,
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
    user_df = user_df[user_df["type"] == USER_BIO_TYPE].copy()
    user_df[USER_COLUMN] = user_df["fid"].astype(str)
    user_df[PROTOCOL_COLUMN] = PROTOCOLS.farcaster.value
    user_df[USER_CREATION_TIME_COLUMN] = pd.to_datetime(
        user_df["created_at"]
    ).dt.tz_localize("UTC")
    user_df[USER_UPDATE_TIME_COLUMN] = user_df["timestamp"]
    user_df[USER_PROFILE_COLUMN] = user_df["value"]
    user_df = user_df[
        [
            USER_COLUMN,
            PROTOCOL_COLUMN,
            USER_CREATION_TIME_COLUMN,
            USER_UPDATE_TIME_COLUMN,
            USER_PROFILE_COLUMN,
        ]
    ].copy()

    # drop duplicates keep the most recent
    return (
        user_df.sort_values(by=USER_UPDATE_TIME_COLUMN, ascending=True)
        .drop_duplicates(subset=USER_COLUMN, keep="last")
        .reset_index(drop=True)
    )

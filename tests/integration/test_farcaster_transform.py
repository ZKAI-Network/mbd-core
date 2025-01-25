import re

import pandas as pd

from mbd_core.data.farcaster.transform_functions import (
    REACT_TYPE_MAP,
    get_item_df,
    get_post_comment_interaction_df,
    get_reaction_df,
    get_user_df,
)
from mbd_core.data.schema import (
    APP_COLUMN,
    AUTHOR_ID_COLUMN,
    EDGE_TYPE_COLUMN,
    EMBED_ITEMS_COLUMN,
    EMBED_USERS_COLUMN,
    INTERACTION_SCHEMA,
    ITEM_COLUMN,
    ITEM_CREATION_TIME_COLUMN,
    ITEM_META_SCHEMA,
    ITEM_TEXT_COLUMN,
    ITEM_UPDATE_TIME_COLUMN,
    LANG_COLUMN,
    LANG_SCORE_COLUMN,
    PROTOCOL_COLUMN,
    PROTOCOLS,
    PUBLICATION_TYPE_COLUMN,
    PUBLICATION_TYPES,
    ROOT_ITEM_COLUMN,
    TIME_COLUMN,
    USER_COLUMN,
    USER_CREATION_TIME_COLUMN,
    USER_META_SCHEMA,
    USER_NAME_COLUMN,
    USER_PHOTO_URL_COLUMN,
    USER_PROFILE_COLUMN,
    USER_UPDATE_TIME_COLUMN,
)


def test_get_item_df(farcaster_casts_dataframe):
    item_df = get_item_df(farcaster_casts_dataframe)

    # Test basic shape
    assert item_df.shape[0] == farcaster_casts_dataframe.shape[0]

    # Test schema validation
    ITEM_META_SCHEMA.validate(item_df)

    # Test all records
    for idx in range(len(farcaster_casts_dataframe)):
        cast = farcaster_casts_dataframe.iloc[idx]
        item = item_df.iloc[idx]

        # Test basic field transformations
        assert item[ITEM_COLUMN] == "0x" + cast["hash"]
        assert item[AUTHOR_ID_COLUMN] == str(cast["fid"])
        assert item[PROTOCOL_COLUMN] == PROTOCOLS.farcaster.value
        assert item[APP_COLUMN] == str(cast["app_fid"])
        assert pd.Timestamp(item[ITEM_CREATION_TIME_COLUMN]).tz_convert(
            "UTC"
        ) == pd.Timestamp(cast["timestamp"]).tz_localize("UTC")
        assert pd.Timestamp(item[ITEM_UPDATE_TIME_COLUMN]).tz_convert(
            "UTC"
        ) == pd.Timestamp(cast["timestamp"]).tz_localize("UTC")

        # Test root item derivation
        expected_root = (
            "root" if pd.isna(cast["parent_hash"]) else "0x" + cast["root_parent_hash"]
        )
        assert item[ROOT_ITEM_COLUMN] == expected_root, (
            f"Root item doesn't match for record {idx}. Expected {expected_root}, got {item[ROOT_ITEM_COLUMN]}"
        )

        # Test text processing
        assert isinstance(item[ITEM_TEXT_COLUMN], dict)
        assert "full" in item[ITEM_TEXT_COLUMN]
        assert "summary" in item[ITEM_TEXT_COLUMN]
        assert item[ITEM_TEXT_COLUMN]["full"] == cast["text"]

        # Test URL and embed lists
        assert isinstance(item[EMBED_ITEMS_COLUMN], list)
        # Verify URLs from both text and embeds are included, without duplicates
        expected_urls = list(
            dict.fromkeys(
                re.findall(r"https?://\S+", cast["text"])
                + [
                    embed["url"]
                    for embed in cast["embeds"]
                    if isinstance(embed, dict) and "url" in embed
                ]
            )
        )
        assert item[EMBED_ITEMS_COLUMN] == expected_urls, (
            f"URLs don't match for record {idx}"
        )
        # Verify no duplicates
        assert len(item[EMBED_ITEMS_COLUMN]) == len(set(item[EMBED_ITEMS_COLUMN])), (
            f"Duplicate URLs found in record {idx}"
        )

        # Test user mentions
        assert isinstance(item[EMBED_USERS_COLUMN], list)
        assert item[EMBED_USERS_COLUMN] == [str(x) for x in cast["mentions"]], (
            f"Mentions don't match for record {idx}"
        )

        # Test publication type
        assert item[PUBLICATION_TYPE_COLUMN] in [t.value for t in PUBLICATION_TYPES]

        # Test language detection
        assert isinstance(item[LANG_COLUMN], str)
        assert isinstance(item[LANG_SCORE_COLUMN], float)


def test_get_interaction_df(farcaster_casts_dataframe, farcaster_reactions_dataframe):
    # Test post and comment interactions
    post_comment_df = get_post_comment_interaction_df(farcaster_casts_dataframe)
    INTERACTION_SCHEMA.validate(post_comment_df)

    # Test all post/comment records
    for idx, cast in farcaster_casts_dataframe.iterrows():
        # Every cast should have a post interaction
        post_interaction = post_comment_df[
            (post_comment_df[USER_COLUMN] == str(cast["fid"]))
            & (post_comment_df[ITEM_COLUMN] == "0x" + cast["hash"])
            & (post_comment_df[EDGE_TYPE_COLUMN] == "post")
        ]
        assert len(post_interaction) == 1, f"Missing post interaction for cast {idx}"
        post = post_interaction.iloc[0]

        # Verify post interaction fields
        assert post[USER_COLUMN] == str(cast["fid"])
        assert post[ITEM_COLUMN] == "0x" + cast["hash"]
        assert post[EDGE_TYPE_COLUMN] == "post"
        assert post[PROTOCOL_COLUMN] == PROTOCOLS.farcaster.value
        assert post[APP_COLUMN] == str(cast["app_fid"])
        assert pd.Timestamp(post[TIME_COLUMN]).tz_convert("UTC") == pd.Timestamp(
            cast["timestamp"]
        ).tz_localize("UTC")

        # If it's a comment (has parent_hash), should also have a comment interaction
        if pd.notna(cast["parent_hash"]):
            comment_interaction = post_comment_df[
                (post_comment_df[USER_COLUMN] == str(cast["fid"]))
                & (post_comment_df[ITEM_COLUMN] == "0x" + cast["parent_hash"])
                & (post_comment_df[EDGE_TYPE_COLUMN] == "comment")
            ]
            assert len(comment_interaction) == 1, (
                f"Missing comment interaction for cast {idx}"
            )
            comment = comment_interaction.iloc[0]

            # Verify comment interaction fields
            assert comment[USER_COLUMN] == str(cast["fid"])
            assert comment[ITEM_COLUMN] == "0x" + cast["parent_hash"]
            assert comment[EDGE_TYPE_COLUMN] == "comment"
            assert comment[PROTOCOL_COLUMN] == PROTOCOLS.farcaster.value
            assert comment[APP_COLUMN] == str(cast["app_fid"])
            assert pd.Timestamp(comment[TIME_COLUMN]).tz_convert("UTC") == pd.Timestamp(
                cast["timestamp"]
            ).tz_localize("UTC")

    # Test reactions
    other_reactions_df = get_reaction_df(farcaster_reactions_dataframe)
    INTERACTION_SCHEMA.validate(other_reactions_df)

    # Test all reaction records
    for idx, reaction in farcaster_reactions_dataframe.iterrows():
        if pd.isna(reaction["target_hash"]):
            continue

        reaction_row = other_reactions_df[
            (other_reactions_df[USER_COLUMN] == str(reaction["fid"]))
            & (other_reactions_df[ITEM_COLUMN] == "0x" + reaction["target_hash"])
        ]
        assert len(reaction_row) == 1, f"Missing reaction for record {idx}"
        react = reaction_row.iloc[0]

        # Verify reaction fields
        assert react[USER_COLUMN] == str(reaction["fid"])
        assert react[ITEM_COLUMN] == "0x" + reaction["target_hash"]
        assert react[EDGE_TYPE_COLUMN] == REACT_TYPE_MAP[reaction["reaction_type"]]
        assert react[PROTOCOL_COLUMN] == PROTOCOLS.farcaster.value
        assert react[APP_COLUMN] == str(reaction["app_fid"])
        assert pd.Timestamp(react[TIME_COLUMN]).tz_convert("UTC") == pd.Timestamp(
            reaction["timestamp"]
        ).tz_localize("UTC")


def test_get_user_df(farcaster_users_dataframe):
    user_df = get_user_df(farcaster_users_dataframe)
    USER_META_SCHEMA.validate(user_df)

    # Test all user records
    for idx, user in farcaster_users_dataframe.iterrows():
        # Find the corresponding transformed user
        transformed_user = user_df[user_df[USER_COLUMN] == str(user["fid"])]
        assert len(transformed_user) == 1, f"Missing or duplicate user for record {idx}"
        transformed = transformed_user.iloc[0]

        # Verify user fields
        assert transformed[USER_COLUMN] == str(user["fid"])
        assert transformed[PROTOCOL_COLUMN] == PROTOCOLS.farcaster.value
        assert pd.Timestamp(transformed[USER_CREATION_TIME_COLUMN]) == pd.Timestamp(
            user["created_at"]
        ).tz_localize("UTC")
        assert pd.Timestamp(transformed[USER_UPDATE_TIME_COLUMN]) == pd.Timestamp(
            user["registered_at"]
        )
        assert transformed[USER_PROFILE_COLUMN] == user["fname"]
        assert transformed[USER_PHOTO_URL_COLUMN] == user["avatar_url"]
        assert transformed[USER_NAME_COLUMN] == user["display_name"]
        assert transformed[APP_COLUMN] == [str(i) for i in user["app_fid"]]

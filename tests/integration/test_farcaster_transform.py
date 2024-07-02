from mbd_core.data.farcaster.transform_functions import (
    get_item_df,
    get_post_comment_interaction_df,
    get_reaction_df,
    get_user_df,
)
from mbd_core.data.schema import INTERACTION_SCHEMA, ITEM_META_SCHEMA, USER_META_SCHEMA


def test_get_item_df(farcaster_casts_dataframe):
    item_df = get_item_df(farcaster_casts_dataframe)
    ITEM_META_SCHEMA.validate(item_df)


def test_get_interaction_df(farcaster_casts_dataframe, farcaster_reactions_dataframe):
    post_comment_df = get_post_comment_interaction_df(farcaster_casts_dataframe)
    other_reactions_df = get_reaction_df(farcaster_reactions_dataframe)
    INTERACTION_SCHEMA.validate(post_comment_df)
    INTERACTION_SCHEMA.validate(other_reactions_df)


def test_get_user_df(farcaster_users_dataframe):
    user_df = get_user_df(farcaster_users_dataframe)
    USER_META_SCHEMA.validate(user_df)

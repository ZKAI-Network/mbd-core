"""Mbd unified data schema in pandera format."""

from enum import Enum

import pandera as pa
from typing_extensions import TypedDict

from mbd_core.data.languages import LANG_CODES


class PROTOCOLS(Enum):
    """Protocols for different data sources."""

    farcaster = "farcaster"
    mirror = "mirror"
    lens = "lens"


class EVENT_TYPES(Enum):  # noqa: N801
    """Event types for interactions."""

    like = "like"
    share = "share"
    post = "post"
    comment = "comment"
    collect = "collect"


class PUBLICATION_TYPES(Enum):  # noqa: N801
    """Publication types."""

    text_only = "text_only"
    frame = "frame"
    article = "article"
    image = "image"


class TextContent(TypedDict):
    """Text content fields for items."""

    full: str
    summary: str


# interaction schema
USER_COLUMN = "user_id"
ITEM_COLUMN = "item_id"
TIME_COLUMN = "timestamp"
EDGE_TYPE_COLUMN = "event_type"
EVENT_VALUE_COLUMN = "event_value"
PROTOCOL_COLUMN = "protocol"
APP_COLUMN = "app"
CONTEXT_COLUMN = "context"
DEFAULT_EVENT_VALUE = 1.0

INTERACTION_SCHEMA = pa.DataFrameSchema(
    {
        USER_COLUMN: pa.Column(str),
        ITEM_COLUMN: pa.Column(str),
        TIME_COLUMN: pa.Column("datetime64[ns, UTC]"),
        EDGE_TYPE_COLUMN: pa.Column(
            str, checks=pa.Check.isin([et.value for et in EVENT_TYPES])
        ),
        EVENT_VALUE_COLUMN: pa.Column(float, checks=pa.Check.ge(0), required=False),
        PROTOCOL_COLUMN: pa.Column(
            str, checks=pa.Check.isin([prc.value for prc in PROTOCOLS])
        ),
        APP_COLUMN: pa.Column(str, nullable=True, required=False),
        CONTEXT_COLUMN: pa.Column(str, nullable=True, required=False),
    },
    strict=True,
)

# ITEM schema
AUTHOR_ID_COLUMN = "protocol_author_id"
ITEM_CREATION_TIME_COLUMN = "item_creation_timestamp"
ITEM_UPDATE_TIME_COLUMN = "item_update_timestamp"
ITEM_TEXT_COLUMN = "text"
ITEM_IMAGE_COLUMN = "image"
ITEM_AUDIO_COLUMN = "audio"
PUBLICATION_TYPE_COLUMN = "publication_type"
ROOT_ITEM_COLUMN = "root_item"
LANG_COLUMN = "lang"
LANG_SCORE_COLUMN = "lang_score"  # feed-quality: enables control over what gets upserted/filtered as english text
LIST_COLUMN = "lists"
EMBED_ITEMS_COLUMN = "embed_items"
EMBED_USERS_COLUMN = "embed_users"


ITEM_META_SCHEMA = pa.DataFrameSchema(
    {
        ITEM_COLUMN: pa.Column(str),
        AUTHOR_ID_COLUMN: pa.Column(str),
        PROTOCOL_COLUMN: pa.Column(
            str, checks=pa.Check.isin([prc.value for prc in PROTOCOLS])
        ),
        APP_COLUMN: pa.Column(str, nullable=True, required=False),
        ITEM_CREATION_TIME_COLUMN: pa.Column("datetime64[ns, UTC]"),
        ITEM_UPDATE_TIME_COLUMN: pa.Column("datetime64[ns, UTC]"),
        ITEM_TEXT_COLUMN: pa.Column(TextContent, required=False),
        ITEM_IMAGE_COLUMN: pa.Column(object, required=False),
        ITEM_AUDIO_COLUMN: pa.Column(object, required=False),
        PUBLICATION_TYPE_COLUMN: pa.Column(
            str, checks=pa.Check.isin([it.value for it in PUBLICATION_TYPES])
        ),
        ROOT_ITEM_COLUMN: pa.Column(str),
        LANG_COLUMN: pa.Column(
            str, checks=pa.Check.isin(LANG_CODES), nullable=True, required=False
        ),
        LANG_SCORE_COLUMN: pa.Column(float),
        LIST_COLUMN: pa.Column(list[str], nullable=True, required=False),
        EMBED_ITEMS_COLUMN: pa.Column(list[str], nullable=True, required=False),
        EMBED_USERS_COLUMN: pa.Column(list[str], nullable=True, required=False),
    },
    strict=True,
)

# USER schema
USER_CREATION_TIME_COLUMN = "user_creation_timestamp"
USER_UPDATE_TIME_COLUMN = "user_update_timestamp"
USER_PROFILE_COLUMN = "profile"

USER_META_SCHEMA = pa.DataFrameSchema(
    {
        USER_COLUMN: pa.Column(str),
        PROTOCOL_COLUMN: pa.Column(
            str, checks=pa.Check.isin([prc.value for prc in PROTOCOLS])
        ),
        APP_COLUMN: pa.Column(str, nullable=True, required=False),
        USER_CREATION_TIME_COLUMN: pa.Column("datetime64[ns, UTC]"),
        USER_UPDATE_TIME_COLUMN: pa.Column("datetime64[ns, UTC]"),
        USER_PROFILE_COLUMN: pa.Column(str, nullable=True, required=False),
    },
    strict=True,
)


# other
PARTITION_DATE_COLUMN = "date"
UNIX_HOUR = "unix_hour"

# mbd schema generic directory
ITEM_META_DIR = "items_meta_data"
USER_META_DIR = "users_meta_data"
INTERACTION_DIR = "interactions"
MESSAGE_FOLDER = "message"
MERGED_MESSAGE_FILE = "merging_job_finished.txt"

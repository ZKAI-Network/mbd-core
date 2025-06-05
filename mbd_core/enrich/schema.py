"""Enrich schema for users and items."""

from typing import cast

import numpy as np
import pandas as pd
import pandera as pa

from mbd_core.data.schema import (
    EDGE_TYPE_COLUMN,
    ITEM_COLUMN,
    MBD_ID_COLUMN,
    PROTOCOL_COLUMN,
    USER_COLUMN,
    USER_UPDATE_TIME_COLUMN,
)
from mbd_core.enrich.labelling.load_config import load_label_columns

LABEL_COLUMNS = load_label_columns()

ITEM_SEM_EMBED_COLUMN = "item_sem_embed"
ITEM_AI_LABELS_COLUMN = "ai_labels"
EMBED_ITEM_TYPES_COLUMN = "embed_item_types"
EMBED_ITEM_TYPE_LIST_COLUMN = "embed_item_type_list"

USER_SEM_EMBED_COLUMN = "user_sem_embed"

URL_METADATA_COLUMN = "url_metadata"


def _check_sequence(x: pd.Series) -> bool:
    return cast(bool, x.apply(lambda x: isinstance(x, (np.ndarray | list))).all())


ITEM_ENRICH_SCHEMA = pa.DataFrameSchema(
    {
        ITEM_COLUMN: pa.Column(str),
        ITEM_SEM_EMBED_COLUMN: pa.Column(checks=pa.Check(_check_sequence)),
        **{label: pa.Column(float) for label in LABEL_COLUMNS},
        ITEM_AI_LABELS_COLUMN: pa.Column(list[str]),
    },
    strict=False,
)

USER_ENRICH_SCHEMA = pa.DataFrameSchema(
    {
        USER_COLUMN: pa.Column(str),
        PROTOCOL_COLUMN: pa.Column(str),
        USER_UPDATE_TIME_COLUMN: pa.Column("datetime64[ns, UTC]"),
        MBD_ID_COLUMN: pa.Column(str, nullable=True, required=False),
        EDGE_TYPE_COLUMN: pa.Column(str),  # for different namespace in pinecone
        USER_SEM_EMBED_COLUMN: pa.Column(
            checks=pa.Check(_check_sequence), nullable=True
        ),
        **{label: pa.Column(float, nullable=True) for label in LABEL_COLUMNS},
    },
    strict=False,
)

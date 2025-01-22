import os

import pandas as pd
import pytest


def pytest_configure():
    # Set environment variables for the entire test session
    os.environ["EMBEDS_METADATA_URL"] = (
        "https://api.modprotocol.org/api/cast-embeds-metadata/by-url"
    )


@pytest.fixture(scope="session")
def farcaster_casts_dataframe():
    return pd.read_json("tests/data/farcaster/farcaster-casts-stream-v1.json")


@pytest.fixture(scope="session")
def farcaster_reactions_dataframe():
    return pd.read_json("tests/data/farcaster/farcaster-reactions-stream-v1.json")


@pytest.fixture(scope="session")
def farcaster_users_dataframe():
    return pd.read_json("tests/data/farcaster/farcaster_users_stream-v1.json")

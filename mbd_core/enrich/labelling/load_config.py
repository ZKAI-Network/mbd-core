"""Load label config."""

import json
from importlib.resources import read_text
from typing import cast

LABELS_MAP = {
    "anger": {"put_items_label": "anger", "api_label": "anger"},
    "anticipation": {"put_items_label": "anticipation", "api_label": "anticipation"},
    "disgust": {"put_items_label": "disgust", "api_label": "disgust"},
    "fear": {"put_items_label": "fear", "api_label": "fear"},
    "joy": {"put_items_label": "joy", "api_label": "joy"},
    "love": {"put_items_label": "love", "api_label": "love"},
    "optimism": {"put_items_label": "optimism", "api_label": "optimism"},
    "pessimism": {"put_items_label": "pessimism", "api_label": "pessimism"},
    "sadness": {"put_items_label": "sadness", "api_label": "sadness"},
    "surprise": {"put_items_label": "surprise", "api_label": "surprise"},
    "trust": {"put_items_label": "trust", "api_label": "trust"},
    "negative": {"put_items_label": "negative", "api_label": "negative"},
    "neutral": {"put_items_label": "neutral", "api_label": "neutral"},
    "positive": {"put_items_label": "positive", "api_label": "positive"},
    "arts_&_culture": {"put_items_label": "arts_culture", "api_label": "arts_culture"},
    "business_&_entrepreneurs": {
        "put_items_label": "business_entrepreneurs",
        "api_label": "business_entrepreneurs",
    },
    "celebrity_&_pop_culture": {
        "put_items_label": "celebrity_pop_culture",
        "api_label": "celebrity_pop_culture",
    },
    "diaries_&_daily_life": {
        "put_items_label": "diaries_daily_life",
        "api_label": "diaries_daily_life",
    },
    "family": {"put_items_label": "family", "api_label": "family"},
    "fashion_&_style": {
        "put_items_label": "fashion_style",
        "api_label": "fashion_style",
    },
    "film_tv_&_video": {
        "put_items_label": "film_tv_video",
        "api_label": "film_tv_video",
    },
    "fitness_&_health": {
        "put_items_label": "fitness_health",
        "api_label": "fitness_health",
    },
    "food_&_dining": {"put_items_label": "food_dining", "api_label": "food_dining"},
    "gaming": {"put_items_label": "gaming", "api_label": "gaming"},
    "learning_&_educational": {
        "put_items_label": "learning_educational",
        "api_label": "learning_educational",
    },
    "music": {"put_items_label": "music", "api_label": "music"},
    "news_&_social_concern": {
        "put_items_label": "news_social_concern",
        "api_label": "news_social_concern",
    },
    "other_hobbies": {"put_items_label": "other_hobbies", "api_label": "other_hobbies"},
    "relationships": {"put_items_label": "relationships", "api_label": "relationships"},
    "science_&_technology": {
        "put_items_label": "science_technology",
        "api_label": "science_technology",
    },
    "sports": {"put_items_label": "sports", "api_label": "sports"},
    "travel_&_adventure": {
        "put_items_label": "travel_adventure",
        "api_label": "travel_adventure",
    },
    "youth_&_student_life": {
        "put_items_label": "youth_student_life",
        "api_label": "youth_student_life",
    },
    "Human": {"put_items_label": "Human", "api_label": "human"},
    "ChatGPT": {"put_items_label": "ChatGPT", "api_label": "llm_generated"},
    "LABEL_0": {"put_items_label": "LABEL_0", "api_label": "not_spam"},
    "LABEL_1": {"put_items_label": "LABEL_1", "api_label": "spam"},
    "S": {"put_items_label": "S", "api_label": "sexual"},
    "H": {"put_items_label": "H", "api_label": "hate"},
    "V": {"put_items_label": "V", "api_label": "violence"},
    "HR": {"put_items_label": "HR", "api_label": "harassment"},
    "SH": {"put_items_label": "SH", "api_label": "selfharm"},
    "S3": {"put_items_label": "S3", "api_label": "sexual_minors"},
    "H2": {"put_items_label": "H2", "api_label": "hate_threatening"},
    "V2": {"put_items_label": "V2", "api_label": "violence_graphic"},
    "OK": {"put_items_label": "OK", "api_label": "ok"},
}


def _get_label_keys(config: dict) -> list:
    labels = []
    for _, conf in config.items():
        if "labels" in conf:
            labels.extend(conf["labels"])
    return labels


def load_config() -> dict:
    """Load label config."""
    config = json.loads(read_text("mbd_core.enrich.labelling", "config.json"))
    labels = _get_label_keys(config)
    assert set(labels) == set(
        LABELS_MAP.keys()
    ), "Labels in config do not match LABELS_MAP"
    return cast(dict, config)


def load_label_columns() -> list:
    """Load api face label columns."""
    label_config = load_config()
    labels = _get_label_keys(label_config)
    return [LABELS_MAP[label]["api_label"] for label in labels]

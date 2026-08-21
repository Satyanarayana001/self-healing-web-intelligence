import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_URL = "https://vercel.com/changelog"


def create_snapshot(data):
    """
    Create a normalized snapshot from
    Bright Data scraper output.
    """

    changelog_entries = []

    # Case 1: Normal dictionary
    if isinstance(data, dict):

        entries = data.get(
            "changelog_entries",
            []
        )

        if isinstance(entries, list):
            changelog_entries = entries

    # Case 2: Bright Data returns a list
    elif isinstance(data, list):

        for item in data:

            if not isinstance(item, dict):
                continue

            entries = item.get(
                "changelog_entries",
                []
            )

            if isinstance(entries, list):

                changelog_entries.extend(
                    entries
                )

    return {
        "source": SOURCE_URL,

        "scraped_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "changelog_entries": changelog_entries
    }


def save_snapshot(snapshot):

    directory = Path(
        "data/history/snapshots"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    path = directory / (
        f"snapshot_{timestamp}.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            snapshot,
            file,
            indent=2,
            ensure_ascii=False
        )

    return str(path)


def save_changes(changes):

    directory = Path(
        "data/history/changes"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    path = directory / (
        f"changes_{timestamp}.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            changes,
            file,
            indent=2,
            ensure_ascii=False
        )

    return str(path)


def save_insight(insight):

    directory = Path(
        "data/history/insights"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    path = directory / (
        f"insight_{timestamp}.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            insight,
            file,
            indent=2,
            ensure_ascii=False
        )

    return str(path)
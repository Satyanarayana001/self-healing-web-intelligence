import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE_URL = "https://vercel.com/changelog"


def create_snapshot(data):
    return {
        "source": SOURCE_URL,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "changelog_entries": data.get("changelog_entries", [])
    }


def save_snapshot(snapshot):
    directory = Path("data/history/snapshots")
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S"
    )

    path = directory / f"snapshot_{timestamp}.json"

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            snapshot,
            file,
            indent=2,
            ensure_ascii=False
        )

    return str(path)


def save_changes(changes):
    directory = Path("data/history/changes")
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S"
    )

    path = directory / f"changes_{timestamp}.json"

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            changes,
            file,
            indent=2,
            ensure_ascii=False
        )

    return str(path)
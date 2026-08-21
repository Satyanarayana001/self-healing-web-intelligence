import json
from datetime import datetime, timezone
from pathlib import Path


BASELINE_FILE = Path(
    "data/baseline.json"
)

SOURCE_URL = (
    "https://vercel.com/changelog"
)


def create_empty_baseline():
    """
    Return a valid empty baseline structure.
    """

    return {
        "source": SOURCE_URL,

        "scraped_at": None,

        "changelog_entries": []
    }


def normalize_baseline(data):
    """
    Normalize old and new baseline formats into
    one consistent structure.

    Supported formats:

    New format:
    {
        "source": "...",
        "scraped_at": "...",
        "changelog_entries": [...]
    }

    Older Bright Data format:
    [
        {
            "changelog_entries": [...],
            "input": {...}
        }
    ]
    """

    # --------------------------------
    # No data
    # --------------------------------

    if data is None:
        return create_empty_baseline()

    # --------------------------------
    # Old list format
    # --------------------------------

    if isinstance(data, list):

        if not data:
            return create_empty_baseline()

        # Use the first valid dictionary.
        for item in data:

            if isinstance(item, dict):

                entries = item.get(
                    "changelog_entries",
                    []
                )

                if not isinstance(entries, list):
                    entries = []

                return {
                    "source":
                        item.get(
                            "source",
                            SOURCE_URL
                        ),

                    "scraped_at":
                        item.get(
                            "scraped_at",
                            None
                        ),

                    "changelog_entries":
                        entries
                }

        return create_empty_baseline()

    # --------------------------------
    # Current dictionary format
    # --------------------------------

    if isinstance(data, dict):

        entries = data.get(
            "changelog_entries",
            []
        )

        if not isinstance(entries, list):
            entries = []

        return {
            "source":
                data.get(
                    "source",
                    SOURCE_URL
                ),

            "scraped_at":
                data.get(
                    "scraped_at",
                    None
                ),

            "changelog_entries":
                entries
        }

    # --------------------------------
    # Unexpected format
    # --------------------------------

    return create_empty_baseline()


def load_baseline():
    """
    Load the current baseline.

    Always returns a valid dictionary.

    If the baseline does not exist, is empty,
    or has an old format, it is normalized into
    the standard baseline structure.
    """

    if not BASELINE_FILE.exists():

        return create_empty_baseline()

    try:

        with open(
            BASELINE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

    except (
        json.JSONDecodeError,
        OSError
    ):

        return create_empty_baseline()

    return normalize_baseline(
        data
    )


def save_baseline(snapshot):
    """
    Save the latest successfully validated
    snapshot as the new baseline.

    Only changelog entries from a valid snapshot
    are stored in the standard format.
    """

    if not isinstance(snapshot, dict):

        raise ValueError(
            "Baseline snapshot must be "
            "a dictionary."
        )

    entries = snapshot.get(
        "changelog_entries",
        []
    )

    if not isinstance(entries, list):

        raise ValueError(
            "changelog_entries must be a list."
        )

    baseline = {
        "source":
            snapshot.get(
                "source",
                SOURCE_URL
            ),

        "scraped_at":
            snapshot.get(
                "scraped_at",
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),

        "changelog_entries":
            entries
    }

    BASELINE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        BASELINE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            baseline,
            file,
            indent=2,
            ensure_ascii=False
        )

    return str(
        BASELINE_FILE
    )
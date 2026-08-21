from urllib.parse import (
    urlparse,
    urlunparse,
)


def normalize_text(value):
    """
    Normalize text so insignificant whitespace
    differences do not trigger modifications.
    """

    if value is None:
        return ""

    return " ".join(
        str(value).split()
    ).strip()


def normalize_url(url):
    """
    Normalize URLs so equivalent URLs are compared
    consistently.

    Examples:

    https://example.com/page/
    https://example.com/page

    will be treated as the same URL.
    """

    if not url:
        return ""

    url = normalize_text(url)

    parsed = urlparse(url)

    normalized_path = parsed.path.rstrip("/")

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            parsed.params,
            parsed.query,
            ""
        )
    )


def normalize_entry(entry):
    """
    Normalize an entry before comparison.
    """

    return {
        "title": normalize_text(
            entry.get("title", "")
        ),

        "description": normalize_text(
            entry.get("description", "")
        ),

        "url": normalize_url(
            entry.get("url", "")
        )
    }


def build_url_map(entries):
    """
    Build a URL -> entry map.

    Entries without a URL are ignored because URL
    is the stable identifier used for comparison.

    Duplicate URLs are automatically collapsed.
    """

    result = {}

    for entry in entries:

        url = entry.get("url", "")

        if not url:
            continue

        result[url] = entry

    return result


def detect_changes(
    baseline,
    latest_snapshot
):
    """
    Compare the previous baseline with the latest
    snapshot.

    Change types:

    - new:
        URL exists in latest snapshot but not baseline.

    - modified:
        Same URL exists, but title or description changed.

    - unchanged:
        Same URL and content.

    - missing_from_latest_snapshot:
        Entry existed in the previous baseline but was
        not returned by the latest extraction.

        This does NOT mean the entry was deleted from
        the source website.
    """

    baseline_entries = (
        baseline.get(
            "changelog_entries",
            []
        )
    )

    latest_entries = (
        latest_snapshot.get(
            "changelog_entries",
            []
        )
    )

    # --------------------------------
    # Normalize entries
    # --------------------------------

    normalized_baseline = [
        normalize_entry(entry)
        for entry in baseline_entries
        if isinstance(entry, dict)
    ]

    normalized_latest = [
        normalize_entry(entry)
        for entry in latest_entries
        if isinstance(entry, dict)
    ]

    # --------------------------------
    # Build stable URL maps
    # --------------------------------

    baseline_by_url = build_url_map(
        normalized_baseline
    )

    latest_by_url = build_url_map(
        normalized_latest
    )

    new_entries = []
    modified_entries = []
    missing_entries = []
    unchanged_entries = []

    # --------------------------------
    # Check latest entries
    # --------------------------------

    for url, latest_entry in (
        latest_by_url.items()
    ):

        baseline_entry = (
            baseline_by_url.get(url)
        )

        # ----------------------------
        # New entry
        # ----------------------------

        if baseline_entry is None:

            new_entries.append(
                latest_entry
            )

            continue

        # ----------------------------
        # Modified entry
        # ----------------------------

        title_changed = (
            baseline_entry["title"]
            != latest_entry["title"]
        )

        description_changed = (
            baseline_entry["description"]
            != latest_entry["description"]
        )

        if (
            title_changed
            or description_changed
        ):

            changed_fields = []

            if title_changed:
                changed_fields.append(
                    "title"
                )

            if description_changed:
                changed_fields.append(
                    "description"
                )

            modified_entries.append(
                {
                    "before":
                        baseline_entry,

                    "after":
                        latest_entry,

                    "changed_fields":
                        changed_fields
                }
            )

        # ----------------------------
        # Unchanged entry
        # ----------------------------

        else:

            unchanged_entries.append(
                latest_entry
            )

    # --------------------------------
    # Check entries missing from the
    # latest extraction
    # --------------------------------

    for url, baseline_entry in (
        baseline_by_url.items()
    ):

        if url in latest_by_url:
            continue

        missing_entries.append(
            {
                **baseline_entry,

                "status":
                    "not_present_in_latest_snapshot",

                "confidence":
                    "low",

                "note": (
                    "This entry was present in "
                    "the previous baseline but "
                    "was not returned in the "
                    "latest extraction. This does "
                    "not confirm that the entry "
                    "was removed from the source "
                    "website."
                )
            }
        )

    # --------------------------------
    # Summary
    # --------------------------------

    summary = {
        "new":
            len(new_entries),

        "modified":
            len(modified_entries),

        "missing_from_latest_snapshot":
            len(missing_entries),

        "unchanged":
            len(unchanged_entries),

        "baseline_records":
            len(baseline_by_url),

        "latest_records":
            len(latest_by_url)
    }

    # --------------------------------
    # Final result
    # --------------------------------

    return {
        "new":
            new_entries,

        "modified":
            modified_entries,

        "missing_from_latest_snapshot":
            missing_entries,

        "unchanged":
            unchanged_entries,

        "summary":
            summary
    }
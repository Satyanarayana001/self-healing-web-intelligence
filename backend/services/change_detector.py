def detect_changes(baseline, latest):
    baseline_entries = {
        entry["url"]: entry
        for entry in baseline.get("changelog_entries", [])
        if entry.get("url")
    }

    latest_entries = {
        entry["url"]: entry
        for entry in latest.get("changelog_entries", [])
        if entry.get("url")
    }

    new_entries = []
    removed_entries = []
    modified_entries = []
    unchanged_entries = []

    # NEW or MODIFIED or UNCHANGED
    for url, latest_entry in latest_entries.items():

        if url not in baseline_entries:
            new_entries.append(latest_entry)
            continue

        baseline_entry = baseline_entries[url]

        if (
            baseline_entry.get("title") != latest_entry.get("title")
            or
            baseline_entry.get("description") != latest_entry.get("description")
        ):
            modified_entries.append({
                "before": baseline_entry,
                "after": latest_entry
            })
        else:
            unchanged_entries.append(latest_entry)

    # REMOVED
    for url, baseline_entry in baseline_entries.items():

        if url not in latest_entries:
            removed_entries.append(baseline_entry)

    return {
        "new": new_entries,
        "modified": modified_entries,
        "removed": removed_entries,
        "unchanged": unchanged_entries,
        "summary": {
            "new": len(new_entries),
            "modified": len(modified_entries),
            "removed": len(removed_entries),
            "unchanged": len(unchanged_entries)
        }
    }
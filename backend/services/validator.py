REQUIRED_FIELDS = [
    "title",
    "description",
    "url",
]


def validate_changelog_data(data):
    entries = data.get("changelog_entries", [])

    errors = []

    if not entries:
        errors.append("No changelog entries were extracted.")

    for index, entry in enumerate(entries):
        for field in REQUIRED_FIELDS:
            value = entry.get(field)

            if value is None or str(value).strip() == "":
                errors.append(
                    f"Entry {index} is missing required field: {field}"
                )

    return {
        "healthy": len(errors) == 0,
        "record_count": len(entries),
        "errors": errors,
    }
REQUIRED_FIELDS = [
    "title",
    "description",
    "url",
]

MIN_RECORDS = 1


def validate_changelog_data(data):
    entries = data.get("changelog_entries", [])

    errors = []

    if len(entries) < MIN_RECORDS:
        errors.append(
            f"Expected at least {MIN_RECORDS} record(s), "
            f"but received {len(entries)}."
        )

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
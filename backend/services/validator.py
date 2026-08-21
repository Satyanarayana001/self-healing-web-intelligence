import os


REQUIRED_FIELDS = [
    "title",
    "description",
    "url",
]

MIN_RECORDS = 1


# Tracks whether the simulated failure
# has already happened in this server process.
simulation_failure_used = False


def validate_changelog_data(data):
    """
    Validate extracted changelog data.

    If FORCE_VALIDATION_FAILURE=true,
    the FIRST validation fails intentionally.

    All subsequent validations run normally,
    allowing the self-healing mechanism to
    recover successfully.
    """

    global simulation_failure_used

    # --------------------------------
    # Controlled one-time failure
    # --------------------------------

    force_failure = os.getenv(
        "FORCE_VALIDATION_FAILURE",
        "false"
    ).lower()

    if (
        force_failure == "true"
        and not simulation_failure_used
    ):

        simulation_failure_used = True

        return {
            "healthy": False,
            "record_count": 0,
            "errors": [
                "Simulated one-time validation "
                "failure for self-healing test."
            ],
            "entries": []
        }

    # --------------------------------
    # Normal validation
    # --------------------------------

    if not isinstance(data, dict):

        return {
            "healthy": False,
            "record_count": 0,
            "errors": [
                "Scraper data must be a dictionary."
            ],
            "entries": []
        }

    entries = data.get(
        "changelog_entries",
        []
    )

    if not isinstance(entries, list):

        return {
            "healthy": False,
            "record_count": 0,
            "errors": [
                "changelog_entries must be a list."
            ],
            "entries": []
        }

    errors = []

    if len(entries) < MIN_RECORDS:

        errors.append(
            f"Expected at least "
            f"{MIN_RECORDS} record(s), "
            f"but received {len(entries)}."
        )

    for index, entry in enumerate(entries):

        if not isinstance(entry, dict):

            errors.append(
                f"Entry {index} "
                f"is not a valid object."
            )

            continue

        for field in REQUIRED_FIELDS:

            value = entry.get(field)

            if (
                value is None
                or str(value).strip() == ""
            ):

                errors.append(
                    f"Entry {index} is missing "
                    f"required field: {field}"
                )

    return {
        "healthy": len(errors) == 0,
        "record_count": len(entries),
        "errors": errors,
        "entries": entries
    }
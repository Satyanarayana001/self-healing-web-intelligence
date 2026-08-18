def simulate_extraction_failure(data):
    """
    Simulates a broken scraper by removing all extracted entries.
    This is used only for testing the self-healing workflow.
    """

    simulated_data = data.copy()

    simulated_data["changelog_entries"] = []

    return simulated_data
import time

from backend.services.baseline import (
    load_baseline,
    save_baseline
)

from backend.services.brightdata import (
    trigger_scraper,
    retrieve_results
)

from backend.services.validator import (
    validate_changelog_data
)

from backend.services.healing import (
    heal_scraper
)

from backend.services.snapshot import (
    create_snapshot,
    save_snapshot,
    save_changes,
    save_insight
)

from backend.services.change_detector import (
    detect_changes
)

from backend.services.ai_analyzer import (
    analyze_changes
)


def wait_for_collection(
    collection_id,
    max_polls=6,
    poll_interval=10
):
    """
    Wait until Bright Data scraper results are ready.

    Expected normalized response:

    While building:
        {
            "status": "building",
            "data": None
        }

    When ready:
        {
            "status": "ready",
            "data": [...]
        }
    """

    result = None

    for poll in range(1, max_polls + 1):

        result = retrieve_results(
            collection_id
        )

        if result.get("status") == "ready":
            return result

        print(
            f"Dataset still building... "
            f"poll {poll}/{max_polls}"
        )

        if poll < max_polls:
            time.sleep(poll_interval)

    return result


def run_monitoring_cycle():
    """
    Complete self-healing monitoring pipeline.

    Flow:

    Trigger Scraper
        ↓
    Wait for Results
        ↓
    Extract Actual Scraper Data
        ↓
    Validate Data
        ↓
    Self-Heal if Broken
        ↓
    Create Snapshot
        ↓
    Load Baseline
        ↓
    Detect Changes
        ↓
    Save Changes
        ↓
    AI Analysis
        ↓
    Save Insight
        ↓
    Update Baseline
    """

    print("\n================================")
    print("SELF-HEALING MONITORING CYCLE")
    print("================================\n")

    # --------------------------------
    # STEP 1 — Trigger scraper
    # --------------------------------

    print("STEP 1: Triggering scraper...")

    trigger_result = trigger_scraper()

    collection_id = trigger_result.get(
        "collection_id"
    )

    if not collection_id:
        raise RuntimeError(
            "Bright Data did not return "
            "a collection_id."
        )

    print(
        f"Collection ID: {collection_id}"
    )

    # --------------------------------
    # STEP 2 — Wait for results
    # --------------------------------

    print("\nSTEP 2: Waiting for results...")

    result = wait_for_collection(
        collection_id
    )

    if result is None:
        raise RuntimeError(
            "Bright Data returned no result."
        )

    if result.get("status") != "ready":
        raise RuntimeError(
            "Dataset was not ready after polling."
        )

    # --------------------------------
    # STEP 3 — Extract scraper data
    # --------------------------------

    print(
        "\nSTEP 3: Extracting scraper data..."
    )

    scraper_data = result.get("data")

    if not scraper_data:
        raise RuntimeError(
            "Bright Data returned no scraper data."
        )

    print(
        "Scraper data received successfully."
    )

    if isinstance(scraper_data, list):

        print(
            f"Scraper result objects: "
            f"{len(scraper_data)}"
        )

        if (
            len(scraper_data) > 0
            and isinstance(scraper_data[0], dict)
        ):

            print(
                "First result keys: "
                f"{list(scraper_data[0].keys())}"
            )

    # --------------------------------
    # STEP 4 — Validate data
    # --------------------------------

    print("\nSTEP 4: Validating data...")

    initial_health = validate_changelog_data(
        scraper_data
    )

    print(
        f"Healthy: "
        f"{initial_health.get('healthy', False)}"
    )

    print(
        f"Record count: "
        f"{initial_health.get('record_count', 0)}"
    )

    # --------------------------------
    # STEP 5 — Self-heal if necessary
    # --------------------------------

    healing_result = None

    final_data = scraper_data

    if not initial_health.get(
        "healthy",
        False
    ):

        print("\nSTEP 5: Data unhealthy.")
        print("Starting self-healing...")

        healing_result = heal_scraper(
            max_attempts=3,
            poll_interval=10,
            max_polls=6
        )

        if not healing_result.get(
            "healed",
            False
        ):

            print(
                "Self-healing failed."
            )

            return {
                "status": "healing_failed",
                "collection_id": collection_id,
                "initial_health": initial_health,
                "healing": healing_result
            }

        final_data = healing_result.get(
            "data"
        )

        if not final_data:
            raise RuntimeError(
                "Healing succeeded but returned no data."
            )

        print(
            "Self-healing successful."
        )

    else:

        print(
            "\nSTEP 5: No healing required."
        )

    # --------------------------------
    # STEP 6 — Create snapshot
    # --------------------------------

    print("\nSTEP 6: Creating snapshot...")

    latest_snapshot = create_snapshot(
        final_data
    )

    snapshot_path = save_snapshot(
        latest_snapshot
    )

    record_count = len(
        latest_snapshot.get(
            "changelog_entries",
            []
        )
    )

    print(
        f"Snapshot saved: {snapshot_path}"
    )

    print(
        f"Snapshot records: {record_count}"
    )

    # --------------------------------
    # Safety check
    # --------------------------------

    if record_count == 0:

        raise RuntimeError(
            "Snapshot contains zero records even "
            "though scraper data was received. "
            "Baseline will not be updated."
        )

    # --------------------------------
    # STEP 7 — Load baseline
    # --------------------------------

    print("\nSTEP 7: Loading baseline...")

    baseline = load_baseline()

    baseline_count = len(
        baseline.get(
            "changelog_entries",
            []
        )
    )

    print(
        f"Baseline records: {baseline_count}"
    )

    # --------------------------------
    # STEP 8 — Detect changes
    # --------------------------------

    print("\nSTEP 8: Detecting changes...")

    changes = detect_changes(
        baseline,
        latest_snapshot
    )

    summary = changes.get(
        "summary",
        {}
    )

    print(
        f"New: "
        f"{summary.get('new', 0)}"
    )

    print(
        f"Modified: "
        f"{summary.get('modified', 0)}"
    )

    print(
        f"Missing: "
        f"{summary.get(
            'missing_from_latest_snapshot',
            0
        )}"
    )

    print(
        f"Unchanged: "
        f"{summary.get('unchanged', 0)}"
    )

    # --------------------------------
    # STEP 9 — Save changes
    # --------------------------------

    print("\nSTEP 9: Saving changes...")

    changes_path = save_changes(
        changes
    )

    print(
        f"Changes saved: {changes_path}"
    )

    # --------------------------------
    # STEP 10 — AI analysis
    # --------------------------------

    print(
        "\nSTEP 10: "
        "Analyzing changes with AI..."
    )

    ai_insight = analyze_changes(
        changes
    )

    insight_path = save_insight(
        ai_insight
    )

    print(
        f"AI provider: "
        f"{ai_insight.get('provider')}"
    )

    print(
        f"Insight saved: {insight_path}"
    )

    # --------------------------------
    # STEP 11 — Update baseline
    # --------------------------------

    print(
        "\nSTEP 11: Updating baseline..."
    )

    save_baseline(
        latest_snapshot
    )

    print(
        "Baseline updated successfully."
    )

    # --------------------------------
    # STEP 12 — Final status
    # --------------------------------

    status = (
        "healing_completed"
        if healing_result
        else "healthy"
    )

    print("\n================================")
    print("MONITORING CYCLE COMPLETED")
    print("================================")

    return {
        "status": status,
        "collection_id": collection_id,
        "initial_health": initial_health,
        "healing": healing_result,

        "snapshot": {
            "path": snapshot_path,
            "record_count": record_count
        },

        "changes": changes,
        "changes_path": changes_path,

        "ai_insight": ai_insight,
        "insight_path": insight_path,

        "baseline_updated": True,

        "data": latest_snapshot
    }
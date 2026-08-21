import json

from backend.services.brightdata import (
    trigger_scraper,
    retrieve_results,
)

from backend.services.validator import validate_changelog_data
from backend.services.healing import heal_scraper

from backend.services.snapshot import (
    create_snapshot,
    save_snapshot,
    save_changes,
    save_insight,
)

from backend.services.change_detector import detect_changes
from backend.services.ai_analyzer import analyze_changes


BASELINE_FILE = "data/baseline.json"


def load_baseline():

    with open(
        BASELINE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    if isinstance(data, list):
        return data[0]

    return data


def main():

    print("\nSELF-HEALING INTELLIGENCE ORCHESTRATOR")
    print("=" * 45)

    # ----------------------------------------
    # STEP 1 — Load previous baseline
    # ----------------------------------------

    print("\nSTEP 1: Loading baseline...")

    baseline = load_baseline()

    print(
        "Baseline records:",
        len(baseline.get("changelog_entries", []))
    )

    # ----------------------------------------
    # STEP 2 — Trigger scraper
    # ----------------------------------------

    print("\nSTEP 2: Triggering Bright Data scraper...")

    trigger_result = trigger_scraper()

    collection_id = trigger_result.get(
        "collection_id"
    )

    if not collection_id:

        raise RuntimeError(
            "Bright Data did not return collection_id"
        )

    print("Collection ID:", collection_id)

    # ----------------------------------------
    # STEP 3 — Retrieve results
    # ----------------------------------------

    print("\nSTEP 3: Retrieving scraper results...")

    result = retrieve_results(collection_id)

    # ----------------------------------------
    # STEP 4 — Validate
    # ----------------------------------------

    print("\nSTEP 4: Validating extracted data...")

    health = validate_changelog_data(result)

    print(
        json.dumps(
            health,
            indent=2
        )
    )

    final_data = result
    healing_result = None

    # ----------------------------------------
    # STEP 5 — Self-heal if unhealthy
    # ----------------------------------------

    if not health["healthy"]:

        print(
            "\nData unhealthy. Starting self-healing..."
        )

        healing_result = heal_scraper(
            max_attempts=3,
            poll_interval=10,
            max_polls=6
        )

        print(
            json.dumps(
                healing_result,
                indent=2,
                default=str
            )
        )

        if not healing_result.get("healed"):

            raise RuntimeError(
                "Self-healing failed"
            )

        final_data = healing_result["data"]

        health = healing_result["health"]

    else:

        print(
            "\nData is healthy. No healing required."
        )

    # ----------------------------------------
    # STEP 6 — Create snapshot
    # ----------------------------------------

    print("\nSTEP 6: Creating snapshot...")

    latest_snapshot = create_snapshot(
        final_data
    )

    snapshot_path = save_snapshot(
        latest_snapshot
    )

    print(
        "Snapshot saved to:",
        snapshot_path
    )

    print(
        "Records:",
        len(
            latest_snapshot.get(
                "changelog_entries",
                []
            )
        )
    )

    # ----------------------------------------
    # STEP 7 — Detect changes
    # ----------------------------------------

    print("\nSTEP 7: Detecting changes...")

    changes = detect_changes(
        baseline,
        latest_snapshot
    )

    print(
        json.dumps(
            changes,
            indent=2,
            ensure_ascii=False
        )
    )

    # ----------------------------------------
    # STEP 8 — Save changes
    # ----------------------------------------

    print("\nSTEP 8: Saving changes...")

    changes_path = save_changes(
        changes
    )

    print(
        "Changes saved to:",
        changes_path
    )

    # ----------------------------------------
    # STEP 9 — AI analysis
    # ----------------------------------------

    print("\nSTEP 9: Analyzing changes with AI...")

    ai_insight = analyze_changes(
        changes
    )

    print(
        json.dumps(
            ai_insight,
            indent=2,
            ensure_ascii=False
        )
    )

    insight_path = save_insight(
        ai_insight
    )

    print(
        "AI insight saved to:",
        insight_path
    )

    # ----------------------------------------
    # FINAL RESULT
    # ----------------------------------------

    print("\n" + "=" * 45)
    print("ORCHESTRATION COMPLETED")
    print("=" * 45)

    print(
        json.dumps(
            {
                "healthy": health["healthy"],
                "record_count": health["record_count"],
                "healing_used": healing_result is not None,
                "changes_summary": changes["summary"],
                "ai_provider": ai_insight.get("provider"),
                "snapshot_path": snapshot_path,
                "changes_path": changes_path,
                "insight_path": insight_path
            },
            indent=2
        )
    )


if __name__ == "__main__":
    main()
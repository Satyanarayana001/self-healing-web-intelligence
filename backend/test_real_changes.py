import json
import time

from backend.services.brightdata import (
    trigger_scraper,
    retrieve_results
)
from backend.services.snapshot import (
    create_snapshot,
    save_snapshot,
    save_changes
)
from backend.services.change_detector import detect_changes


BASELINE_FILE = "data/baseline.json"


def load_baseline():
    with open(BASELINE_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Current baseline.json is an array containing one snapshot.
    if isinstance(data, list):
        return data[0]

    return data


print("STEP 1: Loading baseline...")

baseline = load_baseline()

print(
    f"Baseline records: "
    f"{len(baseline.get('changelog_entries', []))}"
)


print("\nSTEP 2: Triggering Bright Data...")

trigger_result = trigger_scraper()

collection_id = trigger_result.get("collection_id")

if not collection_id:
    raise RuntimeError(
        "Bright Data did not return a collection_id."
    )

print(f"Collection ID: {collection_id}")


print("\nSTEP 3: Waiting for collection...")

result = None

for poll in range(6):

    time.sleep(10)

    result = retrieve_results(collection_id)

    if result.get("status") != "building":
        break

    print(f"Still building... poll {poll + 1}/6")


if result is None or result.get("status") == "building":
    raise RuntimeError(
        "Collection was not ready after polling."
    )


print("\nSTEP 4: Creating latest snapshot...")

latest = create_snapshot(result)

snapshot_path = save_snapshot(latest)

print(
    f"Latest records: "
    f"{len(latest.get('changelog_entries', []))}"
)

print(
    f"Latest snapshot saved to: {snapshot_path}"
)


print("\nSTEP 5: Detecting changes...")

changes = detect_changes(
    baseline,
    latest
)


print("\nCHANGE DETECTION RESULT")
print("======================")

changes_path = save_changes(changes)

print(
    json.dumps(
        changes,
        indent=2,
        ensure_ascii=False
    )
)

print(
    f"\nChanges saved to: {changes_path}"
)
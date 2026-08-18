from backend.services.brightdata import trigger_scraper, retrieve_results
from backend.services.failure_simulator import simulate_extraction_failure
from backend.services.validator import validate_changelog_data
from backend.services.healing import heal_scraper


print("STEP 1: Triggering Bright Data collection...")
trigger_result = trigger_scraper()

collection_id = trigger_result.get("collection_id")

print(f"Collection ID: {collection_id}")


print("\nSTEP 2: Waiting for the collection...")

import time

result = None

for attempt in range(6):
    time.sleep(10)

    result = retrieve_results(collection_id)

    if result.get("status") != "building":
        break

    print(f"Still building... poll {attempt + 1}/6")


if result.get("status") == "building":
    print("Collection was not ready.")
    raise SystemExit(1)


print("\nSTEP 3: Original data health")

original_health = validate_changelog_data(result)

print(original_health)


print("\nSTEP 4: Simulating scraper failure...")

broken_data = simulate_extraction_failure(result)

broken_health = validate_changelog_data(broken_data)

print(broken_health)


if broken_health["healthy"]:
    print("ERROR: Failure simulation did not create an unhealthy result.")
    raise SystemExit(1)


print("\nSTEP 5: FAILURE DETECTED 🚨")

print("Starting self-healing...")


print("\nSTEP 6: SELF-HEALING 🔧")

healing_result = heal_scraper(
    max_attempts=3,
    poll_interval=10,
    max_polls=6
)


print("\nSTEP 7: FINAL RESULT")

print(healing_result)


if healing_result.get("healed"):
    print("\n🎉 SELF-HEALING SUCCESSFUL!")
else:
    print("\n❌ SELF-HEALING FAILED.")
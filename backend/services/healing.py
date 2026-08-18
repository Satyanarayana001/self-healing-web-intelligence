import time

from backend.services.brightdata import (
    trigger_scraper,
    retrieve_results,
)
from backend.services.validator import validate_changelog_data
from backend.services.healing_logger import log_healing_event



def heal_scraper(
    max_attempts=3,
    poll_interval=10,
    max_polls=6
):
    healing_events = []

    for attempt in range(1, max_attempts + 1):

        healing_events.append({
            "attempt": attempt,
            "action": "trigger_new_collection"
        })

        try:
            trigger_result = trigger_scraper()

            collection_id = trigger_result.get("collection_id")

            if not collection_id:
                healing_events.append({
                    "attempt": attempt,
                    "status": "failed",
                    "reason": "No collection_id returned"
                })
                continue

            healing_events.append({
                "attempt": attempt,
                "collection_id": collection_id,
                "status": "collection_triggered"
            })

            # Keep checking the SAME collection.
            for poll in range(1, max_polls + 1):

                result = retrieve_results(collection_id)

                # Bright Data explicitly says it is still building.
                if result.get("status") == "building":

                    healing_events.append({
                        "attempt": attempt,
                        "poll": poll,
                        "status": "dataset_building"
                    })

                    time.sleep(poll_interval)
                    continue

                # Check the actual extracted data.
                validation = validate_changelog_data(result)

                if validation["healthy"]:

                    healing_events.append({
                        "attempt": attempt,
                        "poll": poll,
                        "status": "healed",
                        "record_count": validation["record_count"]
                    })
                    log_healing_event({
                        "event": "self_healing",
                        "healed": True,
                        "attempts": attempt,
                        "collection_id": collection_id,
                        "record_count": validation["record_count"],
                        "errors": validation["errors"],
                        "events": healing_events
                    })

                    return {
                        "healed": True,
                        "attempts": attempt,
                        "collection_id": collection_id,
                        "health": validation,
                        "events": healing_events,
                        "data": result
                    }

                # Dataset exists but is currently unhealthy.
                healing_events.append({
                    "attempt": attempt,
                    "poll": poll,
                    "status": "data_not_healthy_yet",
                    "health": validation
                })

                if poll < max_polls:
                    time.sleep(poll_interval)

            # Only after polling the SAME collection several times
            # do we move to another healing attempt.
            healing_events.append({
                "attempt": attempt,
                "status": "collection_failed_health_checks"
            })

        except Exception as error:

            healing_events.append({
                "attempt": attempt,
                "status": "error",
                "reason": str(error)
            })

    return {
        "healed": False,
        "attempts": max_attempts,
        "events": healing_events
    }
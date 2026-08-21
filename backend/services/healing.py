import time

from backend.services.brightdata import (
    trigger_scraper,
    retrieve_results,
)

from backend.services.validator import (
    validate_changelog_data,
)

from backend.services.healing_logger import (
    log_healing_event,
)


def heal_scraper(
    max_attempts=3,
    poll_interval=10,
    max_polls=6,
):
    """
    Attempt to recover from an unhealthy scraper result.

    Each attempt:

    1. Trigger a new Bright Data collection
    2. Poll the same collection until ready
    3. Extract the actual scraper data
    4. Validate it
    5. Return the healthy data
    """

    healing_events = []

    for attempt in range(1, max_attempts + 1):

        healing_events.append({
            "attempt": attempt,
            "action": "trigger_new_collection",
        })

        try:

            trigger_result = trigger_scraper()

            collection_id = trigger_result.get(
                "collection_id"
            )

            if not collection_id:

                healing_events.append({
                    "attempt": attempt,
                    "status": "failed",
                    "reason": (
                        "No collection_id returned"
                    ),
                })

                continue

            healing_events.append({
                "attempt": attempt,
                "collection_id": collection_id,
                "status": "collection_triggered",
            })

            # --------------------------------
            # Poll the SAME collection
            # --------------------------------

            for poll in range(
                1,
                max_polls + 1,
            ):

                result = retrieve_results(
                    collection_id
                )

                # Dataset still building

                if result.get(
                    "status"
                ) != "ready":

                    healing_events.append({
                        "attempt": attempt,
                        "poll": poll,
                        "status": (
                            "dataset_building"
                        ),
                    })

                    if poll < max_polls:

                        time.sleep(
                            poll_interval
                        )

                    continue

                # --------------------------------
                # Extract actual scraper data
                # --------------------------------

                scraper_data = result.get(
                    "data"
                )

                if not scraper_data:

                    healing_events.append({
                        "attempt": attempt,
                        "poll": poll,
                        "status": (
                            "ready_but_no_data"
                        ),
                    })

                    if poll < max_polls:

                        time.sleep(
                            poll_interval
                        )

                    continue

                # --------------------------------
                # Validate actual data
                # --------------------------------

                validation = (
                    validate_changelog_data(
                        scraper_data
                    )
                )

                if validation.get(
                    "healthy",
                    False,
                ):

                    healing_events.append({
                        "attempt": attempt,
                        "poll": poll,
                        "status": "healed",
                        "record_count": (
                            validation.get(
                                "record_count",
                                0,
                            )
                        ),
                    })

                    log_healing_event({
                        "event": "self_healing",
                        "healed": True,
                        "attempts": attempt,
                        "collection_id": (
                            collection_id
                        ),
                        "record_count": (
                            validation.get(
                                "record_count",
                                0,
                            )
                        ),
                        "errors": (
                            validation.get(
                                "errors",
                                []
                            )
                        ),
                        "events": healing_events,
                    })

                    return {
                        "healed": True,
                        "attempts": attempt,
                        "collection_id": (
                            collection_id
                        ),
                        "health": validation,
                        "events": healing_events,

                        # IMPORTANT:
                        # Return actual scraper data,
                        # not the Bright Data wrapper.
                        "data": scraper_data,
                    }

                # --------------------------------
                # Data exists but unhealthy
                # --------------------------------

                healing_events.append({
                    "attempt": attempt,
                    "poll": poll,
                    "status": (
                        "data_not_healthy"
                    ),
                    "health": validation,
                })

                if poll < max_polls:

                    time.sleep(
                        poll_interval
                    )

            # --------------------------------
            # Current collection failed
            # --------------------------------

            healing_events.append({
                "attempt": attempt,
                "status": (
                    "collection_failed_health_checks"
                ),
            })

        except Exception as error:

            healing_events.append({
                "attempt": attempt,
                "status": "error",
                "reason": str(error),
            })

    # --------------------------------
    # All attempts failed
    # --------------------------------

    log_healing_event({
        "event": "self_healing",
        "healed": False,
        "attempts": max_attempts,
        "events": healing_events,
    })

    return {
        "healed": False,
        "attempts": max_attempts,
        "events": healing_events,
    }
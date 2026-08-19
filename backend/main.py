import json
import os
import time

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from backend.services.brightdata import (
    trigger_scraper,
    retrieve_results
)
from backend.services.validator import validate_changelog_data
from backend.services.healing import heal_scraper
from backend.services.snapshot import (
    create_snapshot,
    save_snapshot,
    save_changes
)
from backend.services.change_detector import detect_changes


load_dotenv()


app = FastAPI(
    title="Self-Healing Web Intelligence",
    version="0.2.0"
)


BASELINE_FILE = "data/baseline.json"


def load_baseline():
    with open(
        BASELINE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    # Current baseline.json is an array
    # containing one snapshot.
    if isinstance(data, list):
        return data[0]

    return data


def wait_for_collection(
    collection_id,
    max_polls=6,
    poll_interval=10
):
    result = None

    for poll in range(1, max_polls + 1):

        result = retrieve_results(collection_id)

        if result.get("status") != "building":
            return result

        if poll < max_polls:
            time.sleep(poll_interval)

    return result


@app.get("/")
def root():
    return {
        "project": "Self-Healing Web Intelligence",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/config-check")
def config_check():

    return {
        "bright_data_token_configured": bool(
            os.getenv("BRIGHT_DATA_API_TOKEN")
        ),
        "bright_data_collector_configured": bool(
            os.getenv("BRIGHT_DATA_COLLECTOR_ID")
        )
    }


@app.post("/scrape")
def scrape():

    try:

        trigger_result = trigger_scraper()

        collection_id = trigger_result.get(
            "collection_id"
        )

        if not collection_id:
            raise RuntimeError(
                "Bright Data did not return a collection_id"
            )

        return {
            "status": "triggered",
            "collection_id": collection_id,
            "message": (
                "Collector started successfully. "
                "Results can now be retrieved."
            )
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.get("/scrape/{collection_id}")
def get_scrape_results(collection_id: str):

    try:

        result = retrieve_results(
            collection_id
        )

        if result.get("status") == "building":

            return {
                "status": "building",
                "collection_id": collection_id,
                "message": result.get(
                    "message",
                    "Dataset is not ready yet."
                )
            }

        validation = validate_changelog_data(
            result
        )

        return {
            "status": "completed",
            "collection_id": collection_id,
            "health": validation,
            "data": result
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.post("/self-heal/{collection_id}")
def self_heal(collection_id: str):

    try:

        result = retrieve_results(
            collection_id
        )

        health_result = validate_changelog_data(
            result
        )

        if health_result["healthy"]:

            return {
                "status": "healthy",
                "healed": False,
                "message": (
                    "No healing was required."
                ),
                "health": health_result
            }

        healing_result = heal_scraper(
            max_attempts=3,
            poll_interval=10,
            max_polls=6
        )

        return {
            "status": "healing_completed",
            "initial_health": health_result,
            "healing": healing_result
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@app.post("/monitor")
def monitor():

    try:

        # --------------------------------
        # STEP 1 — Trigger Bright Data
        # --------------------------------

        trigger_result = trigger_scraper()

        collection_id = trigger_result.get(
            "collection_id"
        )

        if not collection_id:
            raise RuntimeError(
                "Bright Data did not return a collection_id"
            )

        # --------------------------------
        # STEP 2 — Wait for dataset
        # --------------------------------

        result = wait_for_collection(
            collection_id,
            max_polls=6,
            poll_interval=10
        )

        if (
            result is None
            or result.get("status") == "building"
        ):

            raise RuntimeError(
                "Dataset was not ready after polling."
            )

        # --------------------------------
        # STEP 3 — Validate
        # --------------------------------

        initial_health = validate_changelog_data(
            result
        )

        # --------------------------------
        # STEP 4 — Self-heal if required
        # --------------------------------

        healing_result = None

        final_data = result

        if not initial_health["healthy"]:

            healing_result = heal_scraper(
                max_attempts=3,
                poll_interval=10,
                max_polls=6
            )

            if not healing_result.get("healed"):

                return {
                    "status": "healing_failed",
                    "collection_id": collection_id,
                    "initial_health": initial_health,
                    "healing": healing_result
                }

            # Use the recovered data.
            final_data = healing_result["data"]

        # --------------------------------
        # STEP 5 — Create snapshot
        # --------------------------------

        latest_snapshot = create_snapshot(
            final_data
        )

        snapshot_path = save_snapshot(
            latest_snapshot
        )

        # --------------------------------
        # STEP 6 — Load baseline
        # --------------------------------

        baseline = load_baseline()

        # --------------------------------
        # STEP 7 — Detect changes
        # --------------------------------

        changes = detect_changes(
            baseline,
            latest_snapshot
        )

        # --------------------------------
        # STEP 8 — Save changes
        # --------------------------------

        changes_path = save_changes(
            changes
        )

        # --------------------------------
        # STEP 9 — Final response
        # --------------------------------

        if initial_health["healthy"]:

            status = "healthy"

        else:

            status = "healing_completed"

        return {
            "status": status,
            "collection_id": collection_id,

            "initial_health": initial_health,

            "healing": healing_result,

            "snapshot": {
                "path": snapshot_path,
                "record_count": len(
                    latest_snapshot.get(
                        "changelog_entries",
                        []
                    )
                )
            },

            "changes": changes,

            "changes_path": changes_path,

            "data": final_data
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
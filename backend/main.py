from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from backend.services.brightdata import trigger_scraper, retrieve_results
from backend.services.validator import validate_changelog_data
from backend.services.healing import heal_scraper

load_dotenv()

app = FastAPI(
    title="Self-Healing Web Intelligence",
    version="0.1.0"
)


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
    import os

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

        collection_id = trigger_result.get("collection_id")

        if not collection_id:
            raise RuntimeError("Bright Data did not return a collection_id")

        return {
            "status": "triggered",
            "collection_id": collection_id,
            "message": "Collector started successfully. Results can now be retrieved."
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/scrape/{collection_id}")
def get_scrape_results(collection_id: str):
    try:
        result = retrieve_results(collection_id)

        # Bright Data may still be processing the collection
        if result.get("status") == "building":
            return {
                "status": "building",
                "collection_id": collection_id,
                "message": result.get(
                    "message",
                    "Dataset is not ready yet."
                )
            }

        validation = validate_changelog_data(result)

        return {
            "status": "completed",
            "collection_id": collection_id,
            "health": validation,
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/self-heal/{collection_id}")
def self_heal(collection_id: str):
    try:
        result = retrieve_results(collection_id)

        health = validate_changelog_data(result)

        if health["healthy"]:
            return {
                "status": "healthy",
                "healed": False,
                "message": "No healing was required.",
                "health": health
            }

        healing_result = heal_scraper(
            max_attempts=3,
            poll_interval=10,
            max_polls=6
        )

        return {
            "status": "healing_completed",
            "initial_health": health,
            "healing": healing_result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@app.post("/monitor")
def monitor():
    try:
        trigger_result = trigger_scraper()

        collection_id = trigger_result.get("collection_id")

        if not collection_id:
            raise RuntimeError(
                "Bright Data did not return a collection_id"
            )

        import time

        result = None

        for _ in range(6):
            result = retrieve_results(collection_id)

            if result.get("status") != "building":
                break

            time.sleep(10)

        if result is None or result.get("status") == "building":
            raise RuntimeError(
                "Dataset was not ready after polling."
            )

        health = validate_changelog_data(result)

        if health["healthy"]:
            return {
                "status": "healthy",
                "collection_id": collection_id,
                "health": health,
                "data": result
            }

        healing_result = heal_scraper(
            max_attempts=3,
            poll_interval=10,
            max_polls=6
        )

        return {
            "status": "healing_completed",
            "collection_id": collection_id,
            "initial_health": health,
            "healing": healing_result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
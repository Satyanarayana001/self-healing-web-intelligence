from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from backend.services.brightdata import trigger_scraper, retrieve_results
from backend.services.validator import validate_changelog_data

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
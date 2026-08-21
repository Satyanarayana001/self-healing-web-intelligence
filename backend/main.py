import os

from pathlib import Path
import json


from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from backend.services.brightdata import (
    trigger_scraper,
    retrieve_results,
)

from backend.services.validator import (
    validate_changelog_data,
)

from backend.services.healing import (
    heal_scraper,
)

from backend.services.orchestrator import (
    run_monitoring_cycle,
)


load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Self-Healing Web Intelligence",
    version="0.4.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "project": "Self-Healing Web Intelligence",
        "status": "running",
        "version": "0.4.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
    }


# ============================================================
# CONFIG CHECK
# ============================================================

@app.get("/config-check")
def config_check():

    return {
        "bright_data_token_configured": bool(
            os.getenv(
                "BRIGHT_DATA_API_TOKEN"
            )
        ),

        "bright_data_collector_configured": bool(
            os.getenv(
                "BRIGHT_DATA_COLLECTOR_ID"
            )
        ),

        "groq_key_configured": bool(
            os.getenv(
                "GROQ_API_KEY"
            )
        ),
    }


# ============================================================
# SCRAPE
# ============================================================

@app.post("/scrape")
def scrape():

    try:

        trigger_result = trigger_scraper()

        collection_id = trigger_result.get(
            "collection_id"
        )

        if not collection_id:

            raise RuntimeError(
                "Bright Data did not return "
                "a collection_id."
            )

        return {
            "status": "triggered",

            "collection_id":
                collection_id,

            "message": (
                "Collector started successfully. "
                "Results can now be retrieved."
            ),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# GET SCRAPE RESULTS
# ============================================================

@app.get("/scrape/{collection_id}")
def get_scrape_results(
    collection_id: str
):

    try:

        result = retrieve_results(
            collection_id
        )

        if result.get(
            "status"
        ) == "building":

            return {
                "status":
                    "building",

                "collection_id":
                    collection_id,

                "message": (
                    "Dataset is not ready yet."
                ),
            }

        scraper_data = result.get(
            "data"
        )

        if not scraper_data:

            return {
                "status":
                    "empty",

                "collection_id":
                    collection_id,

                "message": (
                    "Dataset is ready but "
                    "contains no data."
                ),

                "data":
                    result,
            }

        validation = validate_changelog_data(
            scraper_data
        )

        return {
            "status":
                "completed",

            "collection_id":
                collection_id,

            "health":
                validation,

            "data":
                scraper_data,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# SELF HEAL
# ============================================================

@app.post("/self-heal/{collection_id}")
def self_heal(
    collection_id: str
):

    try:

        result = retrieve_results(
            collection_id
        )

        if result.get(
            "status"
        ) == "building":

            return {
                "status":
                    "building",

                "collection_id":
                    collection_id,

                "message": (
                    "Dataset is still building."
                ),
            }

        scraper_data = result.get(
            "data"
        )

        if not scraper_data:

            health_result = {
                "healthy": False,

                "record_count": 0,

                "errors": [
                    "No scraper data returned."
                ],
            }

        else:

            health_result = (
                validate_changelog_data(
                    scraper_data
                )
            )

        # No healing necessary
        if health_result.get(
            "healthy",
            False
        ):

            return {
                "status":
                    "healthy",

                "healed":
                    False,

                "message": (
                    "No healing was required."
                ),

                "health":
                    health_result,
            }

        # Start self-healing
        healing_result = heal_scraper(
            max_attempts=3,
            poll_interval=10,
            max_polls=6,
        )

        if not healing_result.get(
            "healed",
            False
        ):

            return {
                "status":
                    "healing_failed",

                "initial_health":
                    health_result,

                "healing":
                    healing_result,
            }

        return {
            "status":
                "healing_completed",

            "initial_health":
                health_result,

            "healing":
                healing_result,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ============================================================
# MONITOR
# ============================================================

@app.post("/monitor")
def monitor():

    try:

        result = run_monitoring_cycle()

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@app.get("/status")
def get_status():
    """
    Return the current monitoring system status.
    """

    baseline_path = Path("data/baseline.json")

    if not baseline_path.exists():

        return {
            "status": "not_initialized",
            "message": (
                "No baseline exists yet. "
                "Run POST /monitor first."
            )
        }

    try:

        with open(
            baseline_path,
            "r",
            encoding="utf-8"
        ) as file:

            baseline = json.load(file)

    except Exception as error:

        return {
            "status": "error",
            "message": str(error)
        }

    # Support old list-format baselines.
    if isinstance(baseline, list):

        baseline = (
            baseline[0]
            if baseline
            else {}
        )

    entries = baseline.get(
        "changelog_entries",
        []
    )

    return {
        "status": "healthy",
        "source": baseline.get(
            "source",
            "https://vercel.com/changelog"
        ),
        "last_scraped_at": baseline.get(
            "scraped_at"
        ),
        "record_count": len(entries),
        "baseline_exists": True
    }
@app.get("/history")
def get_history():
    """
    Return saved monitoring history.
    """

    snapshots_dir = Path(
        "data/history/snapshots"
    )

    changes_dir = Path(
        "data/history/changes"
    )

    insights_dir = Path(
        "data/history/insights"
    )

    def get_files(directory):
        if not directory.exists():
            return []

        files = sorted(
            directory.glob("*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True
        )

        return [
            {
                "filename": file.name,
                "path": str(file)
            }
            for file in files
        ]

    return {
        "snapshots": get_files(
            snapshots_dir
        ),
        "changes": get_files(
            changes_dir
        ),
        "insights": get_files(
            insights_dir
        )
    }
@app.get("/latest")
def get_latest():
    """
    Return the latest monitoring snapshot,
    change report, and AI insight.
    """

    snapshots_dir = Path(
        "data/history/snapshots"
    )

    changes_dir = Path(
        "data/history/changes"
    )

    insights_dir = Path(
        "data/history/insights"
    )

    def get_latest_json(directory):

        if not directory.exists():

            return None

        files = sorted(
            directory.glob("*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True
        )

        if not files:

            return None

        latest_file = files[0]

        try:

            with open(
                latest_file,
                "r",
                encoding="utf-8"
            ) as file:

                return {
                    "filename": latest_file.name,
                    "data": json.load(file)
                }

        except (
            json.JSONDecodeError,
            OSError
        ) as error:

            return {
                "filename": latest_file.name,
                "error": str(error)
            }

    latest_snapshot = get_latest_json(
        snapshots_dir
    )

    latest_changes = get_latest_json(
        changes_dir
    )

    latest_insight = get_latest_json(
        insights_dir
    )

    return {
        "snapshot": latest_snapshot,
        "changes": latest_changes,
        "ai_insight": latest_insight
    }
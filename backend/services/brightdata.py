import os
import requests

from dotenv import load_dotenv


load_dotenv()


BRIGHT_DATA_API_TOKEN = os.getenv(
    "BRIGHT_DATA_API_TOKEN"
)

BRIGHT_DATA_COLLECTOR_ID = os.getenv(
    "BRIGHT_DATA_COLLECTOR_ID"
)

TARGET_URL = "https://vercel.com/changelog"


def get_headers():
    """
    Return authorization headers for Bright Data API.
    """

    if not BRIGHT_DATA_API_TOKEN:
        raise RuntimeError(
            "BRIGHT_DATA_API_TOKEN is not configured"
        )

    return {
        "Authorization": (
            f"Bearer {BRIGHT_DATA_API_TOKEN}"
        )
    }


def trigger_scraper():
    """
    Trigger the Bright Data scraper.

    Returns the collection information including
    the collection ID used to retrieve results.
    """

    if not BRIGHT_DATA_COLLECTOR_ID:
        raise RuntimeError(
            "BRIGHT_DATA_COLLECTOR_ID "
            "is not configured"
        )

    trigger_url = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_COLLECTOR_ID}"
        "&queue_next=1"
    )

    headers = {
        **get_headers(),
        "Content-Type": "application/json",
    }

    payload = [
        {
            "url": TARGET_URL
        }
    ]

    response = requests.post(
        trigger_url,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    return result


def retrieve_results(collection_id):
    """
    Retrieve scraper results.

    Returns a normalized response:

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

    if not collection_id:
        raise RuntimeError(
            "collection_id is required"
        )

    dataset_url = (
        "https://api.brightdata.com/dca/dataset"
        f"?id={collection_id}"
    )

    response = requests.get(
        dataset_url,
        headers=get_headers(),
        timeout=120,
    )

    response.raise_for_status()

    result = response.json()

    # --------------------------------
    # CASE 1 — Dataset still building
    # --------------------------------

    if isinstance(result, dict):

        status = result.get("status")

        if status in [
            "building",
            "pending",
            "processing"
        ]:

            return {
                "status": "building",
                "data": None
            }

    # --------------------------------
    # CASE 2 — Empty response
    # --------------------------------

    if result is None:

        return {
            "status": "building",
            "data": None
        }

    # --------------------------------
    # CASE 3 — Bright Data returns list
    # --------------------------------

    if isinstance(result, list):

        # An empty list can mean the dataset
        # is not ready yet.
        if len(result) == 0:

            return {
                "status": "building",
                "data": None
            }

        return {
            "status": "ready",
            "data": result
        }

    # --------------------------------
    # CASE 4 — Bright Data returns dict
    # containing actual scraper data
    # --------------------------------

    if isinstance(result, dict):

        # If Bright Data returns a data field,
        # normalize it.
        if "data" in result:

            data = result.get("data")

            if not data:

                return {
                    "status": "building",
                    "data": None
                }

            return {
                "status": "ready",
                "data": data
            }

        # Otherwise treat the dictionary itself
        # as completed scraper data.
        return {
            "status": "ready",
            "data": result
        }

    raise RuntimeError(
        "Unexpected Bright Data response format."
    )
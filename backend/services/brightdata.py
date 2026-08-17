import os
import requests
from dotenv import load_dotenv

load_dotenv()

BRIGHT_DATA_API_TOKEN = os.getenv("BRIGHT_DATA_API_TOKEN")
BRIGHT_DATA_COLLECTOR_ID = os.getenv("BRIGHT_DATA_COLLECTOR_ID")

TARGET_URL = "https://vercel.com/changelog"


def get_headers():
    return {
        "Authorization": f"Bearer {BRIGHT_DATA_API_TOKEN}",
    }


def trigger_scraper():
    if not BRIGHT_DATA_API_TOKEN:
        raise RuntimeError("BRIGHT_DATA_API_TOKEN is not configured")

    if not BRIGHT_DATA_COLLECTOR_ID:
        raise RuntimeError("BRIGHT_DATA_COLLECTOR_ID is not configured")

    trigger_url = (
        "https://api.brightdata.com/dca/trigger"
        f"?collector={BRIGHT_DATA_COLLECTOR_ID}"
        "&queue_next=1"
    )

    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_TOKEN}",
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

    return response.json()


def retrieve_results(collection_id):
    if not BRIGHT_DATA_API_TOKEN:
        raise RuntimeError("BRIGHT_DATA_API_TOKEN is not configured")

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

    return response.json()
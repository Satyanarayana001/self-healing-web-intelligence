import json
from datetime import datetime, timezone
from pathlib import Path


HISTORY_DIR = Path("data/history")
LOG_FILE = HISTORY_DIR / "healing_events.json"


def log_healing_event(event):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as file:
                events = json.load(file)
        except (json.JSONDecodeError, OSError):
            events = []
    else:
        events = []

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event
    }

    events.append(record)

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=2, ensure_ascii=False)

    return record
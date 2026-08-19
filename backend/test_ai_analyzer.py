from backend.services.ai_analyzer import analyze_changes
from backend.services.snapshot import save_insight


changes = {
    "new": [
        {
            "title": "New AI SDK feature",
            "description": (
                "A new feature has been added to the AI SDK."
            ),
            "url": "https://example.com/new"
        }
    ],
    "modified": [],
    "removed": [],
    "unchanged": [],
    "summary": {
        "new": 1,
        "modified": 0,
        "removed": 0,
        "unchanged": 0
    }
}


print("Analyzing changes...")

result = analyze_changes(changes)


print("\nANALYSIS")
print("========")

print(result)


path = save_insight(result)

print("\nInsight saved to:")
print(path)
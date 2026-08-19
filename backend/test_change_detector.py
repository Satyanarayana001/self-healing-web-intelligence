from backend.services.change_detector import detect_changes


baseline = {
    "changelog_entries": [
        {
            "title": "Existing entry",
            "description": "Original description",
            "url": "https://example.com/existing"
        },
        {
            "title": "Removed entry",
            "description": "This will disappear",
            "url": "https://example.com/removed"
        }
    ]
}


latest = {
    "changelog_entries": [
        {
            "title": "Existing entry",
            "description": "Updated description",
            "url": "https://example.com/existing"
        },
        {
            "title": "New entry",
            "description": "This is new",
            "url": "https://example.com/new"
        }
    ]
}


result = detect_changes(
    baseline,
    latest
)


print("CHANGE DETECTION RESULT")
print("=======================")

print(result)
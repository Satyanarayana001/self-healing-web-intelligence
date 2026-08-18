from backend.services.failure_simulator import simulate_extraction_failure
from backend.services.validator import validate_changelog_data


healthy_data = {
    "changelog_entries": [
        {
            "title": "Test entry",
            "description": "Test description",
            "url": "https://example.com"
        }
    ]
}


broken_data = simulate_extraction_failure(healthy_data)

result = validate_changelog_data(broken_data)

print("Simulated data:")
print(broken_data)

print("\nValidation result:")
print(result)
import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-20b"

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
        base_url=GROQ_BASE_URL
    )


def local_analysis(changes):
    """
    Deterministic fallback.

    This is NOT an AI model.
    It is used only when the LLM provider is unavailable.
    """

    new_count = changes.get(
        "summary", {}
    ).get("new", 0)

    modified_count = changes.get(
        "summary", {}
    ).get("modified", 0)

    removed_count = changes.get(
        "summary", {}
    ).get("removed", 0)

    key_changes = []

    for entry in changes.get("new", [])[:5]:

        key_changes.append({
            "title": entry.get(
                "title",
                "Untitled"
            ),

            "type": "new",

            "importance": "medium",

            "impact": (
                "A new entry appeared in "
                "the latest extracted feed."
            ),

            "explanation": entry.get(
                "description",
                "New entry detected."
            )
        })

    for entry in changes.get(
        "modified", []
    )[:5]:

        after = entry.get(
            "after",
            {}
        )

        key_changes.append({
            "title": after.get(
                "title",
                "Modified entry"
            ),

            "type": "modified",

            "importance": "high",

            "impact": (
                "An existing entry changed "
                "in the latest extraction."
            ),

            "explanation": after.get(
                "description",
                "Existing entry was modified."
            )
        })

    for entry in changes.get(
        "removed", []
    )[:5]:

        key_changes.append({
            "title": entry.get(
                "title",
                "Entry"
            ),

            "type": "removed",

            "importance": "medium",

            "impact": (
                "The entry is no longer present "
                "in the latest extracted feed."
            ),

            "explanation": entry.get(
                "description",
                "Entry is absent from the latest feed."
            )
        })

    total_changes = (
        new_count
        + modified_count
        + removed_count
    )

    if total_changes == 0:

        overall_impact = "low"

    elif modified_count > 0:

        overall_impact = "high"

    else:

        overall_impact = "medium"

    return {
        "provider": "local-rule-based",

        "summary": (
            f"Detected {new_count} new, "
            f"{modified_count} modified, and "
            f"{removed_count} entries absent "
            f"from the latest feed."
        ),

        "overall_impact": overall_impact,

        "categories": [
            "Web Changes",
            "Developer Information"
        ],

        "key_changes": key_changes
    }


def analyze_with_groq(changes):

    client = get_groq_client()

    if client is None:

        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    prompt = f"""
You are the AI analysis layer of a
self-healing web intelligence system.

The system has already scraped a public website
using Bright Data and detected factual changes.

Analyze ONLY the supplied change data.

IMPORTANT:
A "removed" entry means it is no longer present
in the latest extracted feed. It does NOT
necessarily mean the source website permanently
deleted it.

Change data:

{json.dumps(
    changes,
    indent=2,
    ensure_ascii=False
)}

Return ONLY valid JSON using this exact structure:

{{
  "provider": "groq",
  "summary": "Concise summary of the important changes.",
  "overall_impact": "low | medium | high",
  "categories": [
    "category1",
    "category2"
  ],
  "key_changes": [
    {{
      "title": "Change title",
      "type": "new | modified | removed",
      "importance": "low | medium | high",
      "impact": "Why this change matters.",
      "explanation": "Clear concise explanation."
    }}
  ]
}}

Rules:

1. Use only information contained in the input.
2. Never invent facts.
3. Prioritize meaningful changes.
4. Keep explanations concise.
5. Analyze new, modified, and removed entries.
6. If many changes exist, prioritize the most meaningful ones.
7. For "removed" entries, NEVER claim that a feature,
   product, discount, or capability was discontinued.
   Only say that the corresponding entry is no longer
   present in the latest extracted feed.
8. Do not infer business decisions from an entry being removed.
9. Return valid JSON only.
"""

    response = client.chat.completions.create(

        model=GROQ_MODEL,

        temperature=0.2,

        response_format={
            "type": "json_object"
        },

        messages=[

            {
                "role": "system",

                "content": (
                    "You are a precise web-change "
                    "analysis assistant."
                )
            },

            {
                "role": "user",

                "content": prompt
            }
        ]
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    if not content:

        raise RuntimeError(
            "Groq returned an empty response."
        )

    result = json.loads(
        content
    )

    result["provider"] = "groq"

    return result


def analyze_changes(changes):

    try:

        result = analyze_with_groq(
            changes
        )

        return result

    except Exception as error:

        print(
            f"Groq analysis unavailable: {error}"
        )

        print(
            "Using local rule-based "
            "analysis fallback."
        )

        return local_analysis(
            changes
        )
import json
import os

from dotenv import load_dotenv
from openai import OpenAI


# --------------------------------
# Load environment variables
# --------------------------------

load_dotenv()


# --------------------------------
# Groq configuration
# --------------------------------

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

GROQ_MODEL = "openai/gpt-oss-20b"


# --------------------------------
# Create Groq client
# --------------------------------

def get_groq_client():
    """
    Create and return a Groq client.

    Returns None if GROQ_API_KEY
    is not configured.
    """

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:

        return None

    return OpenAI(
        api_key=api_key,
        base_url=GROQ_BASE_URL
    )


# --------------------------------
# Local fallback analysis
# --------------------------------

def local_analysis(changes):
    """
    Deterministic fallback analysis.

    This is NOT an AI model.

    It is used only when the Groq API
    is unavailable or fails.

    IMPORTANT:

    An entry in
    "missing_from_latest_snapshot"
    means the entry was not found in the
    latest extracted snapshot.

    It does NOT necessarily mean the entry
    was permanently deleted from the website.
    """

    summary = changes.get(
        "summary",
        {}
    )

    new_count = summary.get(
        "new",
        0
    )

    modified_count = summary.get(
        "modified",
        0
    )

    missing_count = summary.get(
        "missing_from_latest_snapshot",
        0
    )

    key_changes = []


    # --------------------------------
    # Analyze new entries
    # --------------------------------

    for entry in changes.get(
        "new",
        []
    )[:5]:

        key_changes.append({

            "title": entry.get(
                "title",
                "Untitled"
            ),

            "type": "new",

            "importance": "medium",

            "impact": (
                "A new entry appeared in "
                "the latest extracted snapshot."
            ),

            "explanation": entry.get(
                "description",
                "New entry detected."
            )
        })


    # --------------------------------
    # Analyze modified entries
    # --------------------------------

    for entry in changes.get(
        "modified",
        []
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
                "compared with the baseline snapshot."
            ),

            "explanation": after.get(
                "description",
                "Existing entry was modified."
            )
        })


    # --------------------------------
    # Analyze missing entries
    # --------------------------------

    for entry in changes.get(
        "missing_from_latest_snapshot",
        []
    )[:5]:

        key_changes.append({

            "title": entry.get(
                "title",
                "Entry"
            ),

            "type": (
                "missing_from_latest_snapshot"
            ),

            "importance": "medium",

            "impact": (
                "This entry was present in the "
                "baseline but was not found in the "
                "latest extracted snapshot."
            ),

            "explanation": (
                "The entry is absent from the latest "
                "snapshot. This does not necessarily "
                "mean it was deleted from the source website."
            )
        })


    # --------------------------------
    # Calculate total changes
    # --------------------------------

    total_changes = (

        new_count

        + modified_count

        + missing_count
    )


    # --------------------------------
    # Determine overall impact
    # --------------------------------

    if total_changes == 0:

        overall_impact = "low"

    elif modified_count > 0:

        overall_impact = "high"

    elif total_changes >= 5:

        overall_impact = "medium"

    else:

        overall_impact = "medium"


    # --------------------------------
    # Return fallback analysis
    # --------------------------------

    return {

        "provider": "local-rule-based",

        "summary": (

            f"Detected {new_count} new, "

            f"{modified_count} modified, and "

            f"{missing_count} entries missing "

            f"from the latest snapshot."
        ),

        "overall_impact": overall_impact,

        "categories": [

            "Web Changes",

            "Developer Information"
        ],

        "key_changes": key_changes
    }


# --------------------------------
# Analyze changes using Groq
# --------------------------------

def analyze_with_groq(changes):
    """
    Send detected changes to Groq
    for AI-powered analysis.
    """

    client = get_groq_client()


    # --------------------------------
    # Validate API configuration
    # --------------------------------

    if client is None:

        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )


    # --------------------------------
    # Build AI prompt
    # --------------------------------

    prompt = f"""
You are the AI analysis layer of a
self-healing web intelligence system.

The system has already:

1. Scraped a public website using Bright Data.
2. Validated the extracted data.
3. Compared the latest snapshot with a baseline.
4. Detected factual differences.

Your job is to analyze ONLY the supplied
change data.

IMPORTANT TERMINOLOGY:

The change data may contain:

- "new"
- "modified"
- "missing_from_latest_snapshot"

IMPORTANT:

An entry inside
"missing_from_latest_snapshot"

means that the entry existed in the baseline
but was NOT found in the latest extracted
snapshot.

It DOES NOT necessarily mean:

- the website deleted the feature
- the product was discontinued
- the capability was removed
- the discount ended
- the source permanently removed the content

Never claim any of those things unless they
are explicitly supported by the supplied data.

Analyze ONLY the following change data:

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

            "type": "new | modified | missing_from_latest_snapshot",

            "importance": "low | medium | high",

            "impact": "Why this change matters.",

            "explanation": "Clear concise explanation."
        }}
    ]
}}

Rules:

1. Use ONLY information contained in the input.

2. Never invent facts.

3. Never assume information that is not present.

4. Prioritize meaningful changes.

5. Keep explanations concise and useful.

6. Analyze new, modified, and
   missing_from_latest_snapshot entries.

7. If many changes exist, prioritize the
   most meaningful ones.

8. For entries with the type
   "missing_from_latest_snapshot":

   NEVER claim that a feature, product,
   discount, model, capability, or service
   was removed, discontinued, deleted,
   or ended.

9. For missing entries, clearly state only
   that the entry was not present in the
   latest extracted snapshot.

10. Do not infer business decisions from
    an entry being absent.

11. Return valid JSON only.

12. Do not include markdown.

13. Do not include ```json code fences.
"""


    # --------------------------------
    # Call Groq
    # --------------------------------

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
                    "You are a precise and reliable "
                    "web-change analysis assistant. "
                    "Use only supplied evidence and "
                    "do not invent facts."
                )
            },

            {

                "role": "user",

                "content": prompt
            }
        ]
    )


    # --------------------------------
    # Extract response content
    # --------------------------------

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


    # --------------------------------
    # Parse JSON response
    # --------------------------------

    result = json.loads(
        content
    )


    # --------------------------------
    # Force correct provider name
    # --------------------------------

    result["provider"] = "groq"


    return result


# --------------------------------
# Main analysis function
# --------------------------------

def analyze_changes(changes):
    """
    Analyze detected changes.

    First attempts Groq AI analysis.

    If Groq is unavailable, automatically
    falls back to deterministic local analysis.
    """

    try:

        result = analyze_with_groq(
            changes
        )

        return result


    except Exception as error:

        print(
            f"Groq analysis unavailable: "
            f"{error}"
        )

        print(
            "Using local rule-based "
            "analysis fallback."
        )

        return local_analysis(
            changes
        )
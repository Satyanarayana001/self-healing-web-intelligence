# Bright Data Scraper Studio

## Overview

This project uses Bright Data Scraper Studio as the primary web extraction layer.

The project uses a custom scraper created for the Vercel Changelog website.

Target website:

https://vercel.com/changelog

The custom scraper extracts structured changelog information and sends it to the backend monitoring pipeline.

## Custom Scraper

The scraper extracts structured changelog information including:

- Title
- Description
- URL

Example extracted record:

```json
{
  "title": "Example Changelog Update",
  "description": "Description of the changelog update.",
  "url": "https://vercel.com/changelog/example"
}
```

The scraper is created and configured through Bright Data Scraper Studio rather than relying only on an existing scraper from the Bright Data Scrapers Library.

## Extraction Workflow

The application communicates with the Bright Data collector using the Bright Data API.

The workflow is:

1. Trigger the custom Bright Data scraper.
2. Receive a collection ID.
3. Poll the collection until the dataset is ready.
4. Retrieve the structured dataset.
5. Validate the extracted records.
6. Create a normalized snapshot.
7. Compare the latest snapshot with the baseline.
8. Detect changes.
9. Store snapshots and detected changes in project history.
10. Analyze detected changes using AI.
11. Update the baseline with the latest successfully validated snapshot.

The dataset may not be immediately available after triggering the scraper. The backend receives a collection ID and repeatedly checks the collection status until the data is ready.

```text
Trigger Bright Data Scraper
            |
            v
Receive Collection ID
            |
            v
Poll Collection Status
            |
            v
Retrieve Structured Dataset
            |
            v
Validate Extracted Data
```

## Health Monitoring

The extracted data is validated before it is considered healthy.

The validation layer checks whether:

- Data was returned successfully.
- The expected structure is present.
- Changelog entries exist.
- The extracted records contain valid data.

Example health result:

```json
{
  "healthy": true,
  "record_count": 8,
  "errors": []
}
```

If the extraction is healthy, the monitoring pipeline continues normally.

## Self-Healing Workflow

If the extracted data fails validation, the self-healing engine automatically attempts to recover from the failure.

The recovery process triggers a new Bright Data collection and validates the recovered dataset.

```text
Bright Data Scraper
        |
        v
Structured Dataset
        |
        v
Health Validation
        |
   +----+----+
   |         |
Healthy   Unhealthy
   |         |
   |         v
   |    Self-Healing
   |         |
   |         v
   |   New Collection
   |         |
   |         v
   |   Poll for Results
   |         |
   |         v
   |   Validate Again
   |         |
   +---------+
        |
        v
Validated Dataset
```

The self-healing system performs recovery attempts up to a configured limit.

During each recovery attempt:

1. A new Bright Data collection is triggered.
2. A new collection ID is received.
3. The collection is polled until the dataset is ready.
4. The recovered data is validated.
5. If validation succeeds, the monitoring pipeline continues.

If all recovery attempts fail, the monitoring cycle returns a `healing_failed` status.

If recovery succeeds, the monitoring cycle returns a `healing_completed` status.

Possible monitoring statuses include:

- `healthy`
- `healing_completed`
- `healing_failed`

## Snapshot Creation

After the data has been successfully validated, the system creates a normalized snapshot.

Example:

```json
{
  "source": "https://vercel.com/changelog",
  "scraped_at": "2026-08-21T17:18:09+00:00",
  "changelog_entries": [
    {
      "title": "Example Update",
      "description": "Example description",
      "url": "https://vercel.com/changelog/example"
    }
  ]
}
```

Snapshots are stored in:

```text
data/history/snapshots/
```

Each successful monitoring cycle creates a timestamped snapshot.

Example:

```text
snapshot_20260821_171809.json
```

## Baseline Management

The system maintains a baseline representing the latest successfully validated state of the monitored website.

The baseline is stored in:

```text
data/baseline.json
```

The normalized baseline structure contains:

```json
{
  "source": "https://vercel.com/changelog",
  "scraped_at": "timestamp",
  "changelog_entries": []
}
```

The application supports older baseline formats and normalizes them when loading the baseline.

The baseline is updated only after a successful monitoring cycle.

This prevents empty, invalid, or unhealthy scraper responses from replacing the last known healthy baseline.

## Change Detection

The latest snapshot is compared with the existing baseline.

The system detects four types of changes.

### New Entries

Entries that exist in the latest snapshot but were not present in the previous baseline.

### Modified Entries

Entries that existed previously but whose content has changed.

For example:

```text
Previous:
Deployment Storage keeps your deployments rollback-ready TEST

Latest:
Deployment Storage keeps your deployments rollback-ready
```

This is detected as a modified entry.

### Missing Entries

Entries that existed in the baseline but are not present in the latest snapshot.

### Unchanged Entries

Entries that remain the same between the baseline and the latest snapshot.

Example change summary:

```json
{
  "new": 0,
  "modified": 0,
  "missing_from_latest_snapshot": 0,
  "unchanged": 8
}
```

Detected changes are stored in:

```text
data/history/changes/
```

Example:

```text
changes_20260821_171809.json
```

## AI Analysis

After change detection, the detected changes are sent to the AI analysis layer.

The AI analysis generates information such as:

- A summary of detected changes.
- The overall impact.
- Change categories.
- Important updates.

The current project uses Groq as the AI provider.

Example insight:

```json
{
  "provider": "groq",
  "summary": "No new, modified, or missing entries detected; all eight records remain unchanged.",
  "overall_impact": "low"
}
```

AI insights are stored in:

```text
data/history/insights/
```

Example:

```text
insight_20260821_171810.json
```

## Complete Monitoring Pipeline

```text
Bright Data Scraper
        |
        v
Trigger Collection
        |
        v
Receive Collection ID
        |
        v
Poll Until Dataset Is Ready
        |
        v
Retrieve Structured Dataset
        |
        v
Health Validation
        |
   +----+----------------+
   |                     |
Healthy               Unhealthy
   |                     |
   |                     v
   |              Self-Healing
   |                     |
   |              New Collection
   |                     |
   |              Poll and Validate
   |                     |
   +----------+----------+
              |
              v
       Validated Dataset
              |
              v
       Create Snapshot
              |
              v
        Load Baseline
              |
              v
       Detect Changes
              |
              v
      Save Change History
              |
              v
         AI Analysis
              |
              v
         Save AI Insight
              |
              v
        Update Baseline
```

## API Endpoints

The backend provides API endpoints for monitoring and inspecting the system.

### Run Monitoring

```text
POST /monitor
```

This triggers the complete monitoring cycle.

The response includes information about:

- Monitoring status.
- Bright Data collection ID.
- Initial health.
- Self-healing result.
- Snapshot.
- Detected changes.
- AI insight.
- Baseline update status.

### System Status

```text
GET /status
```

This returns the current monitoring state, including:

- System status.
- Monitored source.
- Last scraped timestamp.
- Record count.
- Baseline availability.

### Monitoring History

```text
GET /history
```

This provides access to previously generated snapshots and monitoring history.

Snapshots are stored in:

```text
data/history/snapshots/
```

Change records are stored in:

```text
data/history/changes/
```

AI insights are stored in:

```text
data/history/insights/
```

### Latest Result

```text
GET /latest
```

This returns the latest available:

- Snapshot.
- Change detection result.
- AI insight.

## Why Bright Data

Bright Data provides the web extraction layer for the Self-Healing Web Intelligence system.

The custom scraper retrieves structured data from the monitored website, while the backend adds additional intelligence through:

- Data validation.
- Health monitoring.
- Automatic self-healing.
- Snapshot creation.
- Baseline management.
- Change detection.
- Historical storage.
- AI-powered analysis.

Together, these components create a resilient web monitoring system capable of detecting changes in the monitored website and automatically attempting recovery when data extraction fails.
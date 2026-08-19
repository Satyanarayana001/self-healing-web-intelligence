# Bright Data Scraper Studio

## Overview

This project uses Bright Data Scraper Studio as the primary web
extraction layer.

The project uses a custom scraper created for the Vercel Changelog
website.

Target website:

https://vercel.com/changelog

## Custom Scraper

The scraper extracts structured changelog information including:

- title
- description
- URL

The scraper is created and configured through Bright Data Scraper
Studio rather than relying only on an existing scraper from the
Bright Data Scrapers Library.

## Extraction Workflow

The application communicates with the Bright Data collector using
the Bright Data API.

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

## Health Monitoring

The extracted data is validated before it is considered healthy.

The current validation checks whether the expected changelog records
are present.

If the extraction is unhealthy, the self-healing engine starts a new
Bright Data collection and repeatedly checks the recovered collection.

## Self-Healing Workflow

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
Healthy   Failure
   |         |
   |         v
   |    Self-Healing
   |         |
   |         v
   |    New Collection
   |         |
   +---------+
        |
        v
Normalized Snapshot
        |
        v
Change Detection
        |
        v
Change History